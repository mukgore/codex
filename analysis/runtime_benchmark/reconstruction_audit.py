"""Four separately launched read-only reconstructions; no original-run restart."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from validation_v03.session_artifacts import _private
from .reconstruction_worker import read


def run(plan,output):
    plan=_private(plan);output=_private(output);data=read(plan)
    jobs=data['jobs']
    if [j['kind'] for j in jobs]!=['mediapipe','stage_profile','process_replay','local_http']:
        raise ValueError('Registered ordered four-job roster required')
    if len({j['id'] for j in jobs})!=4:raise ValueError('Unique job IDs required')
    if any(j['id']!=j['kind'] for j in jobs):raise ValueError('Fixed bounded job IDs required')
    for job in jobs:
        for key in ('root','record','display','display_record'):
            if key in job:
                source=_private(job[key])
                if output.is_relative_to(source) or source.is_relative_to(output):raise ValueError('Audit overlaps source evidence')
    output.mkdir(parents=True,exist_ok=False)
    with (output/'plan.private.json').open('x',encoding='utf-8') as stream:json.dump(data,stream,indent=2);stream.write('\n')
    results=[]
    for job in jobs:
        directory=output/job['id'];directory.mkdir()
        command=[sys.executable,'-m','analysis.runtime_benchmark.reconstruction_worker','--plan',str(plan),
                 '--job',job['id'],'--output',str(directory/'reconstructed')]
        start=time.perf_counter_ns();status='ERROR';returncode=None
        with (directory/'stdout.private.log').open('xb') as stdout,(directory/'stderr.private.log').open('xb') as stderr:
            try:
                process=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=60,check=False)
                returncode=process.returncode;status='EXITED_ZERO' if returncode==0 else 'ERROR'
            except subprocess.TimeoutExpired:status='TIMEOUT'
        result=dict(id=job['id'],kind=job['kind'],status=status,returncode=returncode,
                    elapsed_ns=time.perf_counter_ns()-start,command=command,worker=None)
        path=directory/'reconstructed/worker_result.private.json'
        if status=='EXITED_ZERO':
            if not path.is_file():raise ValueError('Zero exit without reconstruction result')
            result['worker']=read(path)
            if result['worker']['kind']!=job['kind'] or result['worker']['worker_pid']==os.getpid():
                raise ValueError('Worker identity/kind differs')
        with (directory/'process_result.private.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
        results.append(result)
    summary=dict(scope='fresh_process_readonly_reconstruction_not_measurement_reexecution',
                 jobs_n=4,jobs=results,parent_pid=os.getpid(),all_reconstructions_match=all(r['status']=='EXITED_ZERO' for r in results),
                 actual_models_executed_n=0,prior_model_or_service_runs_repeated_n=0,new_videos_n=0,new_human_trials_n=0,
                 independent_implementation=False,new_measurement_session=False,third_party_authentication_proven=False,
                 runtime_R9_fully_complete=False,release_allowed=False)
    with (output/'summary.private.json').open('x',encoding='utf-8') as stream:json.dump(summary,stream,indent=2);stream.write('\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    result=run(**vars(parser.parse_args()))
    print(json.dumps(dict(jobs_n=4,all_reconstructions_match=result['all_reconstructions_match'],actual_models_executed_n=0)))
    if not result['all_reconstructions_match']:raise SystemExit(2)
