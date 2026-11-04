"""Persist five model-free journal scenarios; no attack performance claim."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import time

from .journal import Journal, _private, export_bundle, verify_bundle


def run(output):
    root=_private(output);root.mkdir(parents=True,exist_ok=False)
    rows=[]
    for case in ('completed','error','timeout','unavailable','worker_exit'):
        manifest={'condition_id':'logging_smoke_'+case,'endpoint':'logging_only',
                  'input_exposure':'synthetic_no_model','cache_state':'no_model',
                  'planned_frames':32,'timeout_seconds':.005 if case=='timeout' else 30}
        folder=root/case
        if case=='worker_exit':
            command='import json,os,sys;from analysis.runtime_benchmark.journal import Journal;j=Journal(sys.argv[1],json.loads(sys.argv[2]));j.frame_completed(0,True);os._exit(17)'
            result=subprocess.run([sys.executable,'-c',command,str(folder),json.dumps(manifest)],capture_output=True)
            if result.returncode!=17:raise ValueError('Synthetic worker did not reach its planned exit')
        else:
            journal=Journal(folder,manifest)
            if case=='unavailable':journal.finish('UNAVAILABLE',reason='synthetic_missing_model')
            else:
                try:
                    with journal.stage('journal_overhead_fixture'):
                        if case=='error':raise ValueError('synthetic_error')
                        if case=='timeout':time.sleep(.02)
                        for index in range(32):journal.frame_completed(index,True)
                    journal.finish('COMPLETED')
                except (ValueError,TimeoutError):
                    if not journal.closed:journal.close_without_terminal()
        bundle=root/(case+'.zip');export_bundle(folder,bundle)
        local=verify_bundle(bundle)
        external=subprocess.run([sys.executable,'-c',
            'import json,sys;from analysis.runtime_benchmark.journal import verify_bundle;print(json.dumps(verify_bundle(sys.argv[1])))',str(bundle)],capture_output=True,text=True,check=True)
        if json.loads(external.stdout)!=local:raise ValueError('Independent bundle recovery mismatch')
        rows.append({'case':case,'status':local['status'],'completed_frames':local.get('completed_frames'),
                     'elapsed_ns':local.get('elapsed_ns'),'independent_recovery_matches':True})
    summary={'schema_version':1,'scope':'model_free_journal_logging_only','planned_cases':5,
             'statuses':dict(Counter(row['status'] for row in rows)),'cases':rows,
             'limitations':['no model inference or attack benchmark','no camera or authentication trial',
                            'logging overhead included','timeout checks are cooperative, not GPU preemption',
                            'local separate-process recovery, not a Colab VM reset experiment']}
    (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    print(json.dumps(run(parser.parse_args().output)))
