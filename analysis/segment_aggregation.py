"""Conditional saved-coordinate diagnostic: concatenated vs per-segment scoring.

No historical build identification, new people, accuracy or threshold calibration.
Source/code/input snapshots stay private; only identifier-free aggregates are public.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

from g4_lab.actual import ActualEvaluator
from validation_v03.session_artifacts import _private,_read,decode,canonical,inspect
from validation_v03.run_manifest import prepare,verify_current


def combine(concatenated,parts,frame_counts,*,threshold=.25):
    if (not parts or len(parts)!=len(frame_counts) or any(type(n) is not int or n<0 for n in frame_counts)
            or sum(frame_counts)==0 or type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<threshold<1):
        raise ValueError('Explicit segment/frame denominator and fixed diagnostic threshold required')
    scores=[row['captcha'] for row in parts]
    for score in [concatenated['captcha'],*scores]:
        if type(score) not in (int,float) or not math.isfinite(score) or not 0<=score<=1:
            raise ValueError('Finite score in the original range required')
    if concatenated['tF']!=sum(frame_counts) or any(row['tF']!=n for row,n in zip(parts,frame_counts)):
        raise ValueError('Original frame denominators must be preserved')
    low=sum(score<threshold for score in scores)
    return {'concatenated':concatenated['captcha'],'segment_equal_mean':statistics.mean(scores),
        'segment_frame_weighted_mean':sum(s*n for s,n in zip(scores,frame_counts))/sum(frame_counts),
        'segment_minimum':min(scores),'segments_n':len(scores),'segment_frames_n':sum(frame_counts),
        'segments_below_fixed_diagnostic_threshold':low,'zero_frame_segments_n':frame_counts.count(0),
        'concat_at_or_above_with_low_segment':concatenated['captcha']>=threshold and low>0,
        'all_segments_at_or_above':low==0,'threshold':threshold}


def evaluate(data,keyframes,score):
    segments=data['segments']
    if len(segments)!=len(keyframes)-1 or any(type(s['fromKf']) is not int or type(s['toKf']) is not int or
            (s['fromKf'],s['toKf'])!=(i,i+1) for i,s in enumerate(segments)):
        raise ValueError('Complete ordered saved transitions required; missing transitions are not fabricated')
    for kf in keyframes:
        if type(kf['frameIdx']) is not int or not 0<=kf['frameIdx']<len(kf['allBaseLm']):
            raise ValueError('Saved keyframe index outside current conditional reference')
    concatenated=score(segments,keyframes)
    if abs(concatenated['captcha']-data['scores']['captcha'])>1e-10:
        raise ValueError('Stored score replay not established; do not compare candidate aggregation')
    parts=[score([segment],keyframes) for segment in segments]
    diagnostics=[]
    for segment,part in zip(segments,parts):
        a,b=keyframes[segment['fromKf']],keyframes[segment['toKf']]
        cross=a['clip']['clip_id']!=b['clip']['clip_id']
        reference_frames=(len(a['allBaseLm'])-a['frameIdx']+b['frameIdx']+1 if cross else b['frameIdx']-a['frameIdx']+1)
        if reference_frames<1:raise ValueError('Reversed or empty reference interval')
        diagnostics.append({'kind':'cross_clip' if cross else 'within_clip',
            'reference_frames_n':reference_frames,'response_frames_n':part['tF'],
            'response_used_detected_frames_n':part['dC'],'score':part['captcha'],
            'legacy_angle_metric_available':part['rA'] is not None,
            'legacy_dtw_metric_available':part['rDA'] is not None,
            'legacy_accel_metric_available':part['rAc'] is not None})
    result=combine(concatenated,parts,[len(s['frames']) for s in segments])
    result.update({'stored_replay_abs_error':abs(concatenated['captcha']-data['scores']['captcha']),
        'cross_clip_segments_n':sum(keyframes[s['fromKf']]['clip']['clip_id']!=keyframes[s['toKf']]['clip']['clip_id'] for s in segments),
        'segments_with_fewer_than_three_detected_frames':sum(sum(f['lm'] is not None for f in s['frames'])<3 for s in segments)})
    return {'aggregations':result,'concatenated_score':concatenated,'segment_scores':parts,
            'segment_diagnostics':diagnostics}


def describe(values):
    return {'n':len(values),'mean':statistics.mean(values),'median':statistics.median(values),
            'min':min(values),'max':max(values)}


def run(raw_root,source_root,output,config):
    raw_root=Path(raw_root).resolve(strict=True);source_root=Path(source_root).resolve(strict=True)
    paths=sorted(raw_root.glob('2*/2*/*.json'))
    if not paths:raise ValueError('No saved source sessions')
    output=_private(output);output.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parents[1]
    manifest,_=prepare(config,repo,output/'provenance')
    if manifest['configuration']['parameters'].get('expected_sessions')!=len(paths):
        raise ValueError('Actual session count differs from the declared diagnostic corpus')
    config_inputs={Path(row['path']) for row in manifest['inputs']}
    reference_paths=[source_root/'pool_manifest.json',source_root/'hand_captcha_prod.html']
    pool=decode(_read(source_root/'pool_manifest.json'));clips={c['clip_id']:c for c in pool['clips']}
    reference_paths.extend((source_root/c['landmarks_file']).resolve(strict=True) for c in pool['clips'])
    if any(not p.is_relative_to(source_root) for p in reference_paths):raise ValueError('Reference escapes source root')
    if not set(paths+reference_paths).issubset(config_inputs):raise ValueError('Every actual input must be in the pre-execution snapshot')
    rows=[];cache={}
    with ActualEvaluator(source_root) as evaluator:
        for path in paths:
            raw=_read(path);data=decode(raw);inspect(data)
            hand=data['experimentInfo']['selectedHand'].lower();kfs=[]
            for stored in data['keyframes']:
                cid=stored['clip'];cid=cid['clip_id'] if isinstance(cid,dict) else cid
                clip=clips[cid];mirror=clip['handedness'].lower()!=hand
                if (cid,mirror) not in cache:
                    points=decode(_read(source_root/clip['landmarks_file']))
                    cache[cid,mirror]=evaluator.call({'op':'prepare','data':points,'mirror':mirror})['frames']
                kfs.append({'clip':{'clip_id':cid},'frameIdx':stored['frameIdx'],'allBaseLm':cache[cid,mirror]})
            def score(segments,keyframes):return evaluator.call({'op':'score_saved','segments':segments,'keyframes':keyframes})
            result=evaluate(data,kfs,score)
            rows.append({'input_sha256':hashlib.sha256(raw).hexdigest(),**result})
    post=verify_current(output/'provenance')
    (output/'postflight.private.json').write_bytes(canonical(post))
    values=[row['aggregations'] for row in rows]
    groups={}
    for kind in ('within_clip','cross_clip'):
        group=[part for row in rows for part in row['segment_diagnostics'] if part['kind']==kind]
        groups[kind]={'segments_n':len(group),'zero_scores_n':sum(r['score']==0 for r in group),
            'below_fixed_025_n':sum(r['score']<.25 for r in group),
            'missing_legacy_angle_metric_n':sum(not r['legacy_angle_metric_available'] for r in group),
            'missing_legacy_dtw_metric_n':sum(not r['legacy_dtw_metric_available'] for r in group),
            'missing_legacy_accel_metric_n':sum(not r['legacy_accel_metric_available'] for r in group),
            'reference_frames':describe([r['reference_frames_n'] for r in group]) if group else None}
    summary={'scope':'conditional_legacy_saved_coordinates_segment_aggregation_diagnostic',
        'sessions_n':len(rows),'segments_n':sum(r['segments_n'] for r in values),
        'segment_frames_n':sum(r['segment_frames_n'] for r in values),
        'aggregations':{name:describe([r[name] for r in values]) for name in
            ('concatenated','segment_equal_mean','segment_frame_weighted_mean','segment_minimum')},
        'below_fixed_025_counts':{name:sum(r[name]<.25 for r in values) for name in
            ('concatenated','segment_equal_mean','segment_frame_weighted_mean','segment_minimum')},
        'concat_at_or_above_with_low_segment_sessions_n':sum(r['concat_at_or_above_with_low_segment'] for r in values),
        'segments_below_fixed_025_n':sum(r['segments_below_fixed_diagnostic_threshold'] for r in values),
        'segments_fewer_than_three_detected_frames_n':sum(r['segments_with_fewer_than_three_detected_frames'] for r in values),
        'cross_clip_segments_n':sum(r['cross_clip_segments_n'] for r in values),
        'by_transition_kind':groups,
        'sessions_with_unavailable_required_metric_n':sum(any(not all((p['legacy_angle_metric_available'],
            p['legacy_dtw_metric_available'],p['legacy_accel_metric_available'])) for p in row['segment_diagnostics']) for row in rows),
        'all_required_segment_replacement_rule_status':'NOT_CALIBRATED_AND_INCOMPLETE_REFERENCE_COVERAGE',
        'stored_replay_max_abs_error':max(r['stored_replay_abs_error'] for r in values),
        'pre_execution_snapshot':True,'postflight_snapshot_matched':post['status']=='CURRENT_SNAPSHOT_MATCHES',
        'new_human_observations_n':0,'historical_build_proven':False,'human_motion_errors_proven':False,
        'limitations':['The current reference/HTML reproduce saved values conditionally; executed historical build is unknown.',
            'The existing 0.25 boundary is illustrative on new aggregations, not a calibrated operating threshold.',
            'Nonlinear scoring, normalization and concatenation differ from segment means; no single cause attribution.',
            'Too-short references can produce zero with no available legacy features; this is not observed motion failure.',
            'No response video, independent correctness labels, new people or attack discrimination measured.']}
    (output/'sessions.private.json').write_bytes(canonical(rows))
    (output/'summary.json').write_bytes(canonical(summary))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('raw-root','source-root','output','config'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps(run(args.raw_root,args.source_root,args.output,args.config)))
    except (ValueError,TypeError,KeyError,OSError,RuntimeError) as error:
        print(json.dumps({'status':'REJECTED','error_type':type(error).__name__}),file=sys.stderr)
        sys.exit(2)
