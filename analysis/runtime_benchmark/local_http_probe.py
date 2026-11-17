"""New loopback timing assay of known reference/static replays, not a camera.

Uses the frozen owned HTML JS adapter and existing coordinates. No detector,
renderer or model runs. The source is fixed and known before issuing problems.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import threading
import time

from g4_lab.actual import ActualEvaluator
from g4_lab.server import LabService,create_server
from g4_lab.validation import validate_frames
from .http_client_timing import TimedLocalClient,measure_attempt,reconcile
from .http_timing import ServerTiming,TimedEvaluator
from .journal import _private

PROD_SHA256='0d82dd439fe7976f8b860eb82e654e6f5637b2d7a3fcce2d02f2f99e5f5bea11'


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def make_cases(raw_frames):
    reference=validate_frames(raw_frames)
    first=next((f['lm'] for f in reference if f['lm'] is not None),None)
    if first is None:raise ValueError('Registered source has no detected pose')
    static=[dict(t_ms=f['t_ms'],lm=None if f['lm'] is None else copy.deepcopy(first)) for f in reference]
    return [('known_reference',reference),('static_first_detected',validate_frames(static))]


def schema_control(client,frames):
    start=time.perf_counter_ns()
    issued,challenge=client.post('/api/challenge',{})
    if issued!=200:raise ValueError('Schema control challenge unavailable')
    status,reply=client.post('/api/submit',dict(challenge_id=challenge['challenge_id'],frames=frames,passed=True,score=1))
    if status!=400 or reply.get('grant_id'):raise ValueError('Client assertion schema control was not denied')
    return dict(challenge_http_status=issued,submit_http_status=status,score_pass=None,gate_pass=None,
                validation_pass=None,server_grant_issued=False,protected_action_allowed=None,repeat_action_allowed=None,
                issue_to_submit_body_received_ns=client.last_body_received_ns-start,
                issue_to_action_body_received_ns=None,first_pixel_presented_ns=None,
                endpoint='invalid_schema_control_not_a_complete_media_attempt')


def run(source_root,output):
    started=time.perf_counter_ns();cpu_started=time.process_time_ns()
    source_root=Path(source_root).resolve(strict=True);output=_private(output)
    if output.exists():raise FileExistsError('Fresh probe output required')
    if hashlib.sha256((source_root/'hand_captcha_prod.html').read_bytes()).hexdigest()!=PROD_SHA256:
        raise ValueError('Frozen root prod differs')
    manifest=json.loads((source_root/'pool_manifest.json').read_text(encoding='utf-8'))
    clips={c['clip_id']:c for c in manifest['clips']}
    if len(clips)!=len(manifest['clips']) or not clips:raise ValueError('Unique manifest sources required')
    key=sorted(clips)[0];clip=clips[key]
    for item in clips.values():
        for field in ('video_file','landmarks_file'):
            path=(source_root/item[field]).resolve(strict=True)
            if not path.is_relative_to(source_root) or not path.is_file():raise ValueError('Source escapes/unavailable')
    video=(source_root/clip['video_file']).read_bytes();video_hash=hashlib.sha256(video).hexdigest()
    output.mkdir(parents=True,exist_ok=False)
    write(output/'plan.private.json',dict(source_root=str(source_root),fixed_known_source=key,
          media_sha256=video_hash,source_pool_n=len(clips),cases=['known_reference','static_first_detected','invalid_schema_claims'],
          prior_knowledge='fixed source, full existing coordinates and video before challenge; reference assay, not pixel inference',
          stationary_filter=False,ttl_seconds=60,session_ttl_seconds=300,evaluator_call_timeout_seconds=15,
          client_request_timeout_seconds=20,server_request_timeout_seconds=20,max_issues_per_session=3))
    timing=ServerTiming(output/'server.private.jsonl');evaluator=None;server=None;thread=None;client=None
    rows=[];service=None;setup_ns=None;error_type=None
    try:
        evaluator=ActualEvaluator(source_root,call_timeout=15)
        cases=make_cases(evaluator.frames(key))
        service=LabService(TimedEvaluator(evaluator,timing),source_order=[key],max_issues_per_session=3)
        server=create_server(service,timing=timing,request_timeout=20)
        thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.01),daemon=True);thread.start()
        client=TimedLocalClient(server.server_port,output/'client.private.jsonl',timeout_seconds=20)
        if client.post('/api/session',{})[0]!=200:raise ValueError('Session creation failed')
        setup_ns=time.perf_counter_ns()-started
        for name,frames in cases:
            first_event=len(client.events)
            def provide(received,frames=frames):
                if hashlib.sha256(received).hexdigest()!=video_hash:raise ValueError('Issued media bytes differ from fixed source')
                return copy.deepcopy(frames)
            result=measure_attempt(client,provide)
            rows.append(dict(case=name,planned_frames_n=len(frames),detected_frames_n=sum(f['lm'] is not None for f in frames),
                             correlations=[e['correlation'] for e in client.events[first_event:] if e['kind']=='request_started'],**result))
        first_event=len(client.events);result=schema_control(client,cases[0][1])
        rows.append(dict(case='invalid_schema_claims',correlations=[e['correlation'] for e in client.events[first_event:] if e['kind']=='request_started'],**result))
    except BaseException as error:
        error_type=type(error).__name__
        raise
    finally:
        # Preserve partial attempts on command failure; no manufactured completion.
        write(output/'attempts.private.json',dict(cases=rows,error_type=error_type))
        if client is not None:client.close()
        if server is not None:server.shutdown();server.server_close()
        if thread is not None:
            thread.join(timeout=3)
            if thread.is_alive():raise RuntimeError('Owned serving thread did not stop')
        try:
            if not timing.wait_idle(timeout=20):raise RuntimeError('Owned requests still running')
            timing.close()
        finally:
            if evaluator is not None:
                evaluator.close()
                write(output/'node_stderr_tail.private.json',list(evaluator.stderr_tail))
        if service is not None:write(output/'server_events.private.json',service.events)
    joined=reconcile((output/'client.private.jsonl').read_bytes(),(output/'server.private.jsonl').read_bytes())
    if joined['unmatched_server_requests_n'] or any(r['server'] is None for r in joined['requests']):
        raise ValueError('Unmatched client/server requests')
    write(output/'joined.private.json',joined)
    allowed=sum(r.get('protected_action_allowed') is True for r in rows)
    if service.protected_actions!=allowed or any(r.get('repeat_action_allowed') is True for r in rows):
        raise ValueError('One-time action outcome/counter mismatch')
    summary=dict(scope='new_loopback_known_reference_and_static_replay_timing',cases_n=3,
                 source_families_n=1,independent_holdout=False,knowledge='known_source_full_reference_before_issue',
                 source_pool_prepared_n=len(clips),actual_models_executed_n=0,past_model_runs_repeated_n=0,
                 new_videos_n=0,new_human_trials_n=0,actual_camera_or_hold_observed=False,
                 first_pixel_presented=False,historical_or_deployed_authentication_proven=False,
                 client_server_clock_subtraction_performed=False,protected_test_actions_n=service.protected_actions,
                 matched_requests_n=len(joined['requests']),setup_wall_ns=setup_ns,
                 core_wall_ns=time.perf_counter_ns()-started,core_own_cpu_ns=time.process_time_ns()-cpu_started,
                 node_child_cpu_ns=None,release_allowed=False)
    write(output/'summary.private.json',summary)
    return dict(cases_n=3,matched_requests_n=summary['matched_requests_n'],actual_models_executed_n=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source-root','output'):parser.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(run(**vars(parser.parse_args()))))
