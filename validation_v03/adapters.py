"""Explicit private segment adapter; never infer image size or time units.

Missing/invalid frames and long gaps split contiguous blocks. Short blocks
remain in denominators. This does not change the historical production score.
"""
import argparse
from dataclasses import dataclass, asdict
import json
import math
from pathlib import Path

import numpy as np

from validation_v03.standard_metrics import constrained_dtw, time_derivatives

ANGLE_TRIPLES = ((0,5,6),(5,6,7),(6,7,8),(0,9,10),(9,10,11),(10,11,12),
                 (0,13,14),(13,14,15),(14,15,16),(0,17,18),(17,18,19),(18,19,20),
                 (0,1,2),(1,2,3),(2,3,4))


@dataclass(frozen=True)
class InputSpec:
    width: float
    height: float
    coordinate_space: str
    time_unit: str
    mirror_x: bool
    max_gap_seconds: float
    min_scale_pixels: float = 1e-6
    min_contiguous_frames: int = 3

    def __post_init__(self):
        for value in (self.width, self.height, self.max_gap_seconds, self.min_scale_pixels):
            if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('Positive finite image size, scale and gap limits required')
        if self.coordinate_space not in ('normalized_xy','pixel_xy') or self.time_unit not in ('ms','s'):
            raise ValueError('Explicit coordinate_space and time_unit required')
        if not isinstance(self.mirror_x,bool):
            raise ValueError('mirror_x must be an explicit boolean')
        if isinstance(self.min_contiguous_frames,bool) or not isinstance(self.min_contiguous_frames,int) or self.min_contiguous_frames < 3:
            raise ValueError('At least three contiguous frames required')


def normalize_frame(landmarks, spec):
    points=np.asarray(landmarks,dtype=float)
    if points.ndim!=2 or points.shape[0]!=21 or points.shape[1] not in (2,3) or not np.isfinite(points[:,:2]).all():
        raise ValueError('Expected 21 finite x/y points; optional z is not used')
    if any(isinstance(v,(bool,np.bool_)) or not isinstance(v,(int,float,np.integer,np.floating))
           for p in landmarks for v in p[:2]):
        raise ValueError('Coordinates must be numeric, not booleans or numeric strings')
    xy=points[:,:2].copy()
    if spec.coordinate_space=='normalized_xy':
        xy*=np.array([spec.width,spec.height])
    if spec.mirror_x:
        xy[:,0]=spec.width-xy[:,0]
    scale=float(np.linalg.norm(xy[9]-xy[0]))
    if not math.isfinite(scale) or scale < spec.min_scale_pixels:
        raise ValueError('Degenerate wrist-to-middle-MCP scale')
    xy=(xy-xy[0])/scale
    angles=[]
    for a,b,c in ANGLE_TRIPLES:
        u,v=xy[a]-xy[b],xy[c]-xy[b]
        lengths=float(np.linalg.norm(u)*np.linalg.norm(v))
        if not math.isfinite(lengths) or lengths<=1e-12:
            raise ValueError('Degenerate angle bones')
        angles.append(math.degrees(math.acos(float(np.clip(np.dot(u,v)/lengths,-1,1)))))
    if not np.isfinite(xy).all():
        raise ValueError('Nonfinite normalized geometry')
    return xy.tolist(),angles


def adapt_segment(frames, spec):
    report={'attempted_frames':len(frames),'detected_frames':0,'invalid_geometry_frames':0,
            'missing_frames':0,'excluded_short_block_frames':0,'gap_boundary_count':0,'blocks':[]}
    current=[]
    def flush():
        if len(current)>=spec.min_contiguous_frames:
            report['blocks'].append({'source_frame_indices':[x[0] for x in current],
                'times_seconds':[x[1] for x in current],
                'normalized_xy':[x[2] for x in current], 'angles_degrees':[x[3] for x in current]})
        else:
            report['excluded_short_block_frames']+=len(current)
        current.clear()
    previous=None
    for index,frame in enumerate(frames):
        if not isinstance(frame,dict) or 't' not in frame or 'lm' not in frame:
            raise ValueError('Each frame must explicitly contain t and lm')
        time=frame['t']
        if isinstance(time,bool) or not isinstance(time,(int,float)) or not math.isfinite(time) or time<0:
            raise ValueError('Finite nonnegative timestamps required')
        time=float(time)/(1000 if spec.time_unit=='ms' else 1)
        if previous is not None:
            if time<=previous:
                raise ValueError('Duplicate or reversed timestamps')
            if time-previous > spec.max_gap_seconds:
                flush();report['gap_boundary_count']+=1
        previous=time
        if frame['lm'] is None:
            flush();report['missing_frames']+=1;continue
        report['detected_frames']+=1
        try:
            xy,angles=normalize_frame(frame['lm'],spec)
        except (ValueError,TypeError,OverflowError):
            flush();report['invalid_geometry_frames']+=1;continue
        current.append((index,time,xy,angles))
    flush()
    report['analyzed_frames']=sum(len(b['times_seconds']) for b in report['blocks'])
    return report


def adapt_session(session,spec):
    if not isinstance(session,dict) or not isinstance(session.get('segments'),list):
        raise ValueError('Expected explicit segments[].frames[] input')
    segments=[]
    for i,segment in enumerate(session['segments']):
        if not isinstance(segment,dict) or not isinstance(segment.get('frames'),list):
            raise ValueError('Every segment needs an explicit frames array')
        segments.append({'segment_index':i,**adapt_segment(segment['frames'],spec)})
    return {'schema_version':1,'adapter_version':'image_xy_segment_seconds_v1',
            'privacy':'private_features_not_for_public_git','input_spec':asdict(spec),
            'segments':segments,'attempted_frames':sum(s['attempted_frames'] for s in segments),
            'analyzed_frames':sum(s['analyzed_frames'] for s in segments)}


def compare_contiguous_blocks(reference,response,*,dtw_radius,max_gap_seconds,phase_samples=32):
    """Raw candidate features only; no fitted normalization/weights/threshold."""
    if isinstance(phase_samples,bool) or not isinstance(phase_samples,int) or not 3<=phase_samples<=1000:
        raise ValueError('phase_samples must be an explicit integer from 3 to 1000')
    grid=np.linspace(0,1,phase_samples)
    features=[]
    for block in (reference,response):
        times=np.asarray(block['times_seconds'],dtype=float)
        xy=np.asarray(block['normalized_xy'],dtype=float)
        angles=np.asarray(block['angles_degrees'],dtype=float)
        if (xy.shape!=(len(times),21,2) or angles.shape!=(len(times),15) or len(times)<3
                or not np.isfinite(angles).all()):
            raise ValueError('Expected a complete contiguous 21-point / 15-angle block')
        _,accel=time_derivatives(xy.reshape(len(times),42),times,max_gap_seconds=max_gap_seconds)
        if not np.isfinite(accel).all():
            raise ValueError('Nonfinite time derivatives')
        phase=(times-times[0])/(times[-1]-times[0])
        resample=lambda values:np.stack([np.interp(grid,phase,values[:,j]) for j in range(values.shape[1])],axis=1)
        features.append((angles,resample(angles),resample(accel)))
    dtw=constrained_dtw(features[0][0],features[1][0],radius=dtw_radius)
    return {'schema_version':1,'endpoint':'candidate_raw_features_only',
        'angle_phase_grid_mae_degrees':float(np.mean(np.abs(features[0][1]-features[1][1]))),
        'dtw_angle_distance':dtw.distance,'dtw_angle_path_rmse':dtw.path_rmse,
        'acceleration_phase_aligned_mae_hand_lengths_per_second_squared':float(np.mean(np.abs(features[0][2]-features[1][2]))),
        'phase_samples':phase_samples,'dtw_radius':dtw_radius,'score':None,
        'limitations':['no historical B0 score change','no fitted classifier or calibrated score',
                       'phase alignment is explicit; derivatives use actual seconds']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--width',type=float,required=True);parser.add_argument('--height',type=float,required=True)
    parser.add_argument('--coordinate-space',choices=('normalized_xy','pixel_xy'),required=True)
    parser.add_argument('--time-unit',choices=('ms','s'),required=True)
    parser.add_argument('--mirror-x',choices=('yes','no'),required=True)
    parser.add_argument('--max-gap-seconds',type=float,required=True)
    args=parser.parse_args()
    spec=InputSpec(args.width,args.height,args.coordinate_space,args.time_unit,args.mirror_x=='yes',args.max_gap_seconds)
    report=adapt_session(json.loads(args.input.read_text(encoding='utf-8-sig')),spec)
    with args.output.open('x',encoding='utf8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


if __name__=='__main__':main()
