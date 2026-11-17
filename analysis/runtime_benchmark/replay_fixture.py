"""Registered synthetic process/replay fixture; never model performance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from .arrival_replay import ScheduledFrame, run
from .arrival_record import verify_directory
from .journal import _private


def observe(frames):
    pixels=frames[0]['pixels']
    if pixels==b'slow':time.sleep(.15)
    if pixels==b'hang':time.sleep(60)
    if pixels==b'error':raise RuntimeError('Synthetic handler failure')
    if pixels==b'crash':os._exit(7)
    return dict(outcome='response_ready',seen=[dict(sequence=f['sequence'],
                sha256=hashlib.sha256(f['pixels']).hexdigest(),keys=sorted(f)) for f in frames])


def no_detection(frames):
    return dict(outcome='no_detection')


def registered_cases():
    four=[ScheduledFrame(0,900000000,b'slow')]+[ScheduledFrame(i*10000000,i,bytes([i])) for i in range(1,4)]
    return (
        ('fifo',four,{},'COMPLETED',(4,2,2,0,0)),
        ('latest',four,{'policy':'latest'},'COMPLETED',(4,2,2,0,0)),
        ('partial_no_detection',[ScheduledFrame(0,0,b'x')],
         {'capacity':2,'min_batch':2,'max_batch':2,'max_wait_ns':10**9,
          'worker_entry':'analysis.runtime_benchmark.replay_fixture:no_detection'},'COMPLETED',(1,1,0,0,0)),
        ('timeout',[ScheduledFrame(0,0,b'hang'),ScheduledFrame(10**9,1,b'x')],
         {'timeout_seconds':.2},'TIMEOUT',(1,0,0,1,1)),
        ('handler_error',[ScheduledFrame(0,0,b'error')],{},'ERROR',(1,1,0,0,0)),
        ('worker_crash',[ScheduledFrame(0,0,b'crash')],{},'ERROR',(1,0,0,1,0)),
        ('setup_error',[],{'worker_entry':'missing_fixture_module:handler'},'ERROR',None),
    )


def execute(output):
    output=_private(output);output.mkdir(parents=True,exist_ok=False);rows=[]
    for name,schedule,options,expected_status,expected_counts in registered_cases():
        options=dict(options);entry=options.pop('worker_entry','analysis.runtime_benchmark.replay_fixture:observe')
        result=run(schedule,entry,output/name,input_role='synthetic_fixture',**options)
        if result['status']!=expected_status:raise ValueError('Registered case status differs: '+name)
        recovery=result['queue_recovery']
        if expected_counts is None:
            if recovery is not None or result['phase']!='setup':raise ValueError('Setup failure fabricated queue')
        else:
            if verify_directory(output/name/'queue')!=recovery:raise ValueError('Queue stored reconstruction differs')
            summary=recovery['recovery']['summary']
            actual=tuple(summary[k] for k in ('arrived_frames_n','finished_frames_n','dropped_frames_n',
                                              'unfinished_frames_n','not_arrived_frames_n'))
            if actual!=expected_counts:raise ValueError('Registered frame denominator differs: '+name)
        transport=[json.loads(line) for line in (output/name/'transport.private.jsonl').read_bytes().splitlines()]
        dispatched={e['token']:e['sequences'] for e in transport if e['kind']=='dispatch'}
        for event in transport:
            if event['kind']=='worker_message' and event['message']['kind']=='result':
                reply=event['message']
                if reply['sequences']!=dispatched[reply['token']]:raise ValueError('Unexpected worker exposure')
                if 'seen' in reply['result']:
                    for seen in reply['result']['seen']:
                        if (seen['sequence'] not in reply['sequences'] or seen['keys']!=['pixels','sequence','source_pts_ns']
                                or seen['sha256']!=hashlib.sha256(schedule[seen['sequence']].pixels).hexdigest()):
                            raise ValueError('Worker current-batch pixels differ')
        rows.append(dict(case=name,status=result['status'],queue_recovery=None if recovery is None else recovery['recovery'],
                         exposure_correspondence_match=True,worker_returncode=result['worker_returncode']))
    summary=dict(scope='synthetic_preloaded_timed_release_transport_fixture',cases_n=7,cases=rows,
                 actual_models_executed_n=0,past_model_runs_repeated_n=0,new_videos_n=0,new_human_trials_n=0,
                 model_performance_proven=False,authentication_proven=False,release_allowed=False)
    with (output/'summary.private.json').open('x',encoding='utf-8') as stream:
        json.dump(summary,stream,indent=2,allow_nan=False);stream.write('\n')
    return dict(cases_n=7,actual_models_executed_n=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    print(json.dumps(execute(**vars(parser.parse_args()))))
