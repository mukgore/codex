"""FPS/noise/smoothing stress test of one preserved estimate, not motion truth."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from scipy.signal import savgol_filter

from g4_lab.actual import LANDMARK_NAMES
from validation_v03.adapters import InputSpec, normalize_frame
from validation_v03.standard_metrics import time_derivatives


def kinematics(points, times, *, window, max_gap):
    points=np.asarray(points,dtype=float);times=np.asarray(times,dtype=float)
    if points.shape!=(len(times),21,2):raise ValueError('Complete 21-point XY sequence required')
    if type(window) is not int or window not in (0,5):
        raise ValueError('This predeclared diagnostic only supports unfiltered or SG-5/poly2')
    values=points.reshape(len(times),42)
    if window:
        if len(times)<window or not np.allclose(np.diff(times),times[1]-times[0],rtol=0,atol=1e-9):
            raise ValueError('SG diagnostic requires uniform timestamps and at least five samples')
        values=savgol_filter(values,window_length=window,polyorder=2,axis=0,mode='interp')
    velocity,acceleration=time_derivatives(values,times,max_gap_seconds=max_gap)
    return values.reshape(-1,21,2),velocity.reshape(-1,21,2),acceleration.reshape(-1,21,2)


def vector_rms(values):
    values=np.asarray(values)
    return float(np.sqrt(np.mean(np.sum(values**2,axis=-1))))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();out=args.output.resolve()
    if (out.exists() or 'private_artifacts' not in out.parts
            or any((parent/'.git').exists() for parent in out.parents)):
        p.error('New private output outside repositories required')
    with ZipFile(args.archive) as archive:
        raw=archive.read('left_1_experiment/experiment_data.json')
        data=json.loads(raw)
    info=data['video_info'];fps=float(info['fps']);width,height=info['width'],info['height']
    if fps!=24 or (width,height)!=(720,720):
        raise ValueError('Frozen 24Hz/720-square diagnostic required; use a new protocol for other sources')
    if len(data['frames'])!=113 or any(not f['detected'] or f['frame_idx']!=i for i,f in enumerate(data['frames'])):
        raise ValueError('This frozen one-source stress test requires complete 113-frame estimates')
    pixels=np.array([[[f['landmarks_px'][name][axis] for axis in ('x','y')]
                       for name in LANDMARK_NAMES] for f in data['frames']])
    times=np.arange(len(pixels))/fps
    spec=InputSpec(width,height,'pixel_xy','s',False,2/fps)
    normalized=np.array([normalize_frame(frame.tolist(),spec)[0] for frame in pixels])
    full_reference=kinematics(normalized,times,window=0,max_gap=2/fps)
    rows=[]
    for step in (1,2,4):
        indices=np.arange(0,len(pixels),step)
        if indices[-1]!=len(pixels)-1:raise ValueError('Decimation endpoints must match')
        sample_times=times[indices];gap=2*step/fps
        for window in (0,5):
            baseline=kinematics(normalized[indices],sample_times,window=window,max_gap=gap)
            for sigma_pixels in (0.,.5,1.,2.):
                for seed in (7,19,43):
                    # Same full-rate perturbation for a seed/sigma, then decimate.
                    noisy=pixels+np.random.default_rng(seed).normal(0,sigma_pixels,pixels.shape)
                    noisy_xy=np.array([normalize_frame(frame.tolist(),spec)[0] for frame in noisy[indices]])
                    trial=kinematics(noisy_xy,sample_times,window=window,max_gap=gap)
                    rows.append({'effective_sampling_hz':fps/step,'sample_step':step,
                        'samples':len(indices),'sigma_pixels':sigma_pixels,'seed':seed,
                        'smoothing_samples':window,'smoothing_span_seconds':(window-1)*step/fps if window else 0,
                        'speed_rms_hand_lengths_per_s':vector_rms(trial[1]),
                        'acceleration_rms_hand_lengths_per_s2':vector_rms(trial[2]),
                        'position_error_vs_same_sampling_filter_baseline':vector_rms(trial[0]-baseline[0]),
                        'velocity_error_vs_same_sampling_filter_baseline':vector_rms(trial[1]-baseline[1]),
                        'acceleration_error_vs_same_sampling_filter_baseline':vector_rms(trial[2]-baseline[2]),
                        'velocity_error_vs_24hz_unfiltered_estimate':vector_rms(trial[1]-full_reference[1][indices]),
                        'acceleration_error_vs_24hz_unfiltered_estimate':vector_rms(trial[2]-full_reference[2][indices])})
    report={'scope':'one_preserved_estimate_synthetic_perturbation_diagnostic',
        'source_families':1,'source_frames':113,'combinations':len(rows),
        'distinct_factor_settings':24,'perturbation_seeds':[7,19,43],
        'zero_noise_seeds_are_identical_controls':True,
        'versions':{name:importlib.metadata.version(name) for name in ('numpy','scipy')},
        'time_basis':'nominal source frame_idx/fps; uniformly decimated, endpoints retained',
        'smoothing':'post wrist/scale normalization; SG window5 poly2 interp; no production adoption',
        'rows':rows,'limitations':[
            'The unperturbed input is a tracker estimate, not noise-free human motion truth.',
            'Injected independent pixel Gaussian noise is synthetic, not measured camera jitter.',
            'Lower sampling omits information and is not a new recording/device trial.',
            'SG window has a different temporal span at each sampling rate; not fixed-bandwidth comparison.',
            'Smoothing can change genuine motion; lower stress error is not evidence of better imitation scoring.',
            'No missing frames interpolated, no legacy metric/weight/threshold/UI changed.']}
    out.mkdir(parents=True)
    (out/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'source.private.json').write_text(json.dumps({'input_sha256':hashlib.sha256(raw).hexdigest()})+'\n')
    print(json.dumps({'combinations':len(rows),'sample_rates':[fps,fps/2,fps/4],'source_families':1}))


if __name__=='__main__':main()
