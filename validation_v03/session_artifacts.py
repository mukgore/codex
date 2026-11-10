"""Private round-trip validation for existing exports; no UI or capture changes.

Checks local structure, saved counts and accidental corruption. Hashes do not
authenticate the capture source or prove that an export is a complete session.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import sys

MAX_BYTES=32*1024*1024
POLICY={'version':'selected_hand_gate_v1','maxGateGapMs':200,
        'maxTrackingGapMs':500,'maxTrialMs':60000,'maxEvents':1000}
PHASES={'idle','detecting_hand','matching','recording','done','aborted'}
BRIDGE_REASONS={'stable_largest_hand','callback_gap','original_score_flow','tracking_gap',
                'hand_lost_or_ambiguous','timeout','pagehide','original_gate','original_flow'}
BRIDGE_EVENTS={'selected','completed','aborted','gate_reset','gate_hold_started',
               'gate_hold_reset','phase_changed'}
DEMO_EVENTS={'preparation_started','selection_stabilizing','selected','lost',
             'palm_self_report','attempt_started','attempt_finished','technical_error',
             'aborted','reselect','ui_configured'}
DEMO_REASONS={'camera_or_detector_error','detector_error','user_reset','pagehide',
              'selection_lost','user_finished'}


def _number(value):
    return type(value) in (int,float) and abs(value)<=2**53-1 and math.isfinite(value)


def _integer(value,low=0,high=2**53-1):
    return type(value) is int and low<=value<=high


def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON object key')
        result[key]=value
    return result


def decode(raw):
    if not raw or len(raw)>MAX_BYTES:raise ValueError('Empty or oversized saved JSON')
    def invalid(_):raise ValueError('Nonfinite JSON literal')
    def finite(text):
        value=float(text)
        if not math.isfinite(value):raise ValueError('Nonfinite JSON number')
        return value
    return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=_pairs,parse_constant=invalid,parse_float=finite)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def _read(path):
    with Path(path).open('rb') as stream:raw=stream.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise ValueError('Saved artifact exceeds byte budget')
    return raw


def _time_series(rows,*,strict=False):
    previous=-1
    for row in rows:
        t=row.get('t_ms',row.get('t'))
        if not _number(t) or t<0 or t<previous or (strict and t==previous):
            raise ValueError('Invalid or reversed saved timeline')
        previous=t


def _landmarks(value):
    if value is None:return
    if (not isinstance(value,list) or len(value)!=21 or any(
            not isinstance(point,list) or len(point)!=3 or not all(_number(v) for v in point)
            for point in value)):
        raise ValueError('Legacy export requires 21 finite XYZ points or null')


def _legacy(payload):
    if set(payload)!={'experimentInfo','keyframes','segments','scores','sessionLog'}:
        raise ValueError('Unknown legacy export fields')
    if not isinstance(payload['experimentInfo'],dict) or payload['experimentInfo'].get('version')!='prod_v2_pool':
        raise ValueError('Unsupported saved production version')
    segments,logs,scores=payload['segments'],payload['sessionLog'],payload['scores']
    if (not isinstance(segments,list) or not 1<=len(segments)<=100 or
            not isinstance(logs,list) or len(logs)>200000 or not isinstance(scores,dict)
            or not isinstance(payload['keyframes'],list)):
        raise ValueError('Malformed legacy session collections')
    frames=[]
    for segment in segments:
        if not isinstance(segment,dict) or not isinstance(segment.get('frames'),list):
            raise ValueError('Malformed legacy segment')
        current=segment['frames']
        for frame in current:
            if not isinstance(frame,dict) or set(frame)!={'t','lm'}:raise ValueError('Unexpected segment frame fields')
            _landmarks(frame['lm'])
        _time_series(current,strict=True);frames.extend(current)
        if len(frames)>100000:raise ValueError('Legacy frame budget exceeded')
        detected=sum(f['lm'] is not None for f in current)
        if (not _integer(segment.get('totalFrames')) or not _integer(segment.get('detectedFrames')) or
                segment['totalFrames']!=len(current) or segment['detectedFrames']!=detected):
            raise ValueError('Stored segment counts differ from frames')
    for frame in logs:
        if (not isinstance(frame,dict) or set(frame)!={'t','phase','detected','lm'} or
                frame['phase'] not in PHASES or type(frame['detected']) is not bool or
                frame['detected']!=(frame['lm'] is not None)):
            raise ValueError('Malformed legacy log frame')
        _landmarks(frame['lm'])
    _time_series(logs)
    detected=sum(f['lm'] is not None for f in frames)
    if (not frames or not _integer(scores.get('totalFrames')) or not _integer(scores.get('detectedFrames'))
            or scores['totalFrames']!=len(frames) or scores['detectedFrames']!=detected
            or not _number(scores.get('detectionRate')) or
            abs(scores['detectionRate']-detected/len(frames))>1e-9):
        raise ValueError('Stored score detection counts differ from saved frames')
    return {'format':'legacy_prod_v2_pool','segments_n':len(segments),'segment_frames_n':len(frames),
            'detected_segment_frames_n':detected,'missing_segment_frames_n':len(frames)-detected,
            'stored_frame_detection_rate':detected/len(frames),'session_log_frames_n':len(logs),
            'phase_counts':dict(Counter(f['phase'] for f in logs)),
            'historical_build_verified':False,'playback_wait_separated':False,
            'camera_frame_coverage':None,'scope':'saved counts/timeline/layout; scoring formula not re-evaluated'}


def _events(payload):
    if type(payload.get('schema_version')) is not int or payload['schema_version']!=1:
        raise ValueError('Unsupported event schema')
    bridge=payload.get('scope')=='local_selection_events_only'
    if bridge:
        if (set(payload)!={'schema_version','scope','policy','dropped_events','events','aborted'} or
                payload['policy']!=POLICY or any(type(payload['policy'].get(k)) is not int for k in POLICY if k!='version')
                or not _integer(payload['dropped_events']) or type(payload['aborted']) is not bool):
            raise ValueError('Unsupported selected-hand policy or envelope')
        truncated=payload['dropped_events']>0
    else:
        if (set(payload)!={'schema_version','protocol_version','endpoint','palm_assessment','truncated','events'} or
                payload['protocol_version']!='palm_guidance_v1' or payload['endpoint']!='unscored_local_demo' or
                payload['palm_assessment']!='user_self_report_only' or type(payload['truncated']) is not bool):
            raise ValueError('Unsupported demo envelope')
        truncated=payload['truncated']
    events=payload['events']
    if not isinstance(events,list) or len(events)>1000:raise ValueError('Bounded event list required')
    terminals=[]
    for event in events:
        if not isinstance(event,dict) or not {'t_ms','event'}.issubset(event):raise ValueError('Malformed event')
        if bridge:
            if (set(event)!={'t_ms','event','reason','phase'} or event['event'] not in BRIDGE_EVENTS or
                    event['reason'] not in BRIDGE_REASONS or event['phase'] not in PHASES):
                raise ValueError('Unknown bridge event payload')
            if event['event'] in ('completed','aborted'):terminals.append(event['event'])
        else:
            if event['event'] not in DEMO_EVENTS:raise ValueError('Unknown demo event')
            for key,value in event.items():
                if key in ('t_ms','event'):continue
                valid={'reason':lambda v:v in DEMO_REASONS,
                    'outcome':lambda v:v in ('demo_finished','aborted','technical_error'),
                    'trial_index':lambda v:_integer(v,1,1000000),
                    'ui_condition':lambda v:v in ('split','overlay'),
                    'guide_hand':lambda v:v in ('left','right'),
                    'mirror':lambda v:type(v) is bool,'palm_confirmed':lambda v:type(v) is bool,
                    'opacity':lambda v:_number(v) and 0<=v<=1}.get(key)
                if valid is None or not valid(value):raise ValueError('Unexpected demo event field')
            if event['event'] in ('attempt_finished','technical_error','aborted'):terminals.append(event['event'])
    _time_series(events)
    if bridge:
        if len(terminals)>1 or payload['aborted']!=('aborted' in terminals):
            raise ValueError('Selected-hand terminal flags conflict')
    return {'format':'selected_hand_gate_v1' if bridge else 'palm_guidance_v1',
            'saved_events_n':len(events),'event_counts':dict(Counter(e['event'] for e in events)),
            'truncated':truncated,'observed_terminal_events':dict(Counter(terminals)),
            'timeline_span_ms':events[-1]['t_ms']-events[0]['t_ms'] if events else None,
            'reconstruction_status':'TRUNCATED_PARTIAL_LOG' if truncated else
                'TERMINAL_EVENT_OBSERVED' if terminals else 'OPEN_OR_EMPTY_LOG',
            'camera_frame_coverage':None,'score_observed':False,
            'scope':'saved local events only; no per-frame capture or authentication proof'}


def inspect(payload):
    if not isinstance(payload,dict):raise ValueError('JSON export object required')
    result=_legacy(payload) if 'experimentInfo' in payload else _events(payload)
    return {'schema_valid':True,'input_source_authenticated':False,**result}


def _private(path):
    path=Path(path).resolve()
    if 'private_artifacts' not in path.parts or any((parent/'.git').exists() for parent in path.parents):
        raise ValueError('Private artifact directory outside repositories required')
    return path


def load(directory):
    directory=_private(directory)
    files=[directory/name for name in ('source.json','canonical.json','receipt.json')]
    if any(not path.resolve().is_relative_to(directory) for path in files):raise ValueError('Artifact path escapes directory')
    raw,encoded,receipt_raw=map(_read,files)
    payload=decode(raw);expected=canonical(payload);decode(receipt_raw)
    summary=inspect(payload)
    expected_receipt={'artifact_version':1,'source_sha256':digest(raw),
                      'canonical_sha256':digest(encoded),'inspection':summary}
    if (encoded!=expected or decode(encoded)!=payload or receipt_raw!=canonical(expected_receipt)):
        raise ValueError('Artifact round-trip or receipt mismatch')
    return payload,summary


def save(source,directory):
    raw=_read(source);payload=decode(raw);summary=inspect(payload);encoded=canonical(payload)
    if len(encoded)>MAX_BYTES:raise ValueError('Canonical export exceeds byte budget')
    directory=_private(directory);directory.mkdir(parents=True,exist_ok=False)
    receipt={'artifact_version':1,'source_sha256':digest(raw),
             'canonical_sha256':digest(encoded),'inspection':summary}
    # Receipt is written last. A partial write remains detectable and is never overwritten.
    for name,value in [('source.json',raw),('canonical.json',encoded),('receipt.json',canonical(receipt))]:
        with (directory/name).open('xb') as stream:stream.write(value);stream.flush();os.fsync(stream.fileno())
    restored,verified=load(directory)
    if canonical(restored)!=encoded or verified!=summary:raise ValueError('Reload differs from saved export')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--input',type=Path);group.add_argument('--verify',type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    try:
        if args.input:
            if not args.output:p.error('Output artifact directory required')
            result=save(args.input,args.output)
        else:
            if args.output:p.error('Verify never writes an output')
            _,result=load(args.verify)
    except (OSError,ValueError,TypeError,RecursionError) as error:
        print(json.dumps({'status':'REJECTED','error_type':type(error).__name__}),file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(result,allow_nan=False))


if __name__=='__main__':main()
