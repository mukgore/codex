"""Bounded exploratory attacks against actual HTML computation and local L3."""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime,timezone
import hashlib
import http.cookiejar
import json
from pathlib import Path
import platform
import subprocess
import threading
import time
import urllib.request
import urllib.error
import numpy as np
from .actual import ActualEvaluator
from .attacks import generate_attacks
from .server import LabService,create_server
from .validation import validate_frames

SEED=20261028

def resample(array,n):
    array=np.asarray(array,dtype=float)
    old=np.linspace(0,1,len(array));new=np.linspace(0,1,n)
    return np.stack([np.interp(new,old,array[:,j,c]) for j in range(21) for c in range(2)],axis=1).reshape(n,21,2)

class LocalClient:
    def __init__(self,port):
        self.base=f'http://127.0.0.1:{port}'
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def post(self,path,payload):
        request=urllib.request.Request(self.base+path,data=json.dumps(payload,allow_nan=False).encode(),headers={'Content-Type':'application/json'},method='POST')
        try:
            with self.opener.open(request,timeout=20) as response:return response.status,json.load(response)
        except urllib.error.HTTPError as response:return response.code,json.load(response)

def server_trials(evaluator,rows,inputs,stationary_filter):
    service=LabService(evaluator,source_order=[r['source_family'] for r in rows],stationary_filter=stationary_filter)
    server=create_server(service);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    outcomes=[]
    try:
        client=LocalClient(server.server_port);client.post('/api/session',{})
        for row,frames in zip(rows,inputs):
            started=time.perf_counter()
            _,challenge=client.post('/api/challenge',{})
            status,result=client.post('/api/submit',{'challenge_id':challenge['challenge_id'],'frames':frames})
            grant=result.pop('grant_id',None)
            allowed=False
            if grant:
                _,action=client.post('/api/protected_action',{'grant_id':grant});allowed=action['protected_action_allowed']
            outcomes.append({'http_status':status,'local_l3_allowed':allowed,'wall_ms':(time.perf_counter()-started)*1000,'evaluation':result})
        return outcomes,service.events
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)

def finalize_manifest(args,summary):
    path=args.run_dir/'manifest.json'
    if path.exists():raise FileExistsError('manifest already exists; preserve prior record')
    source_root=args.source_root.resolve()
    source_commit=subprocess.check_output(['git','-c',f'safe.directory={source_root.as_posix()}','-C',str(source_root),'rev-parse','HEAD'],text=True).strip()
    counts={}
    for clip in json.loads((source_root/'pool_manifest.json').read_text(encoding='utf-8'))['clips']:
        data=json.loads((source_root/clip['landmarks_file']).read_text(encoding='utf-8'))
        counts[clip['clip_id']]={'raw':len(data['frames']),'detected':sum(bool(f.get('detected') and f.get('landmarks_px')) for f in data['frames'])}
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'hash_capture':'post_run_snapshot; not a preregistration freeze','python':platform.python_version(),'numpy':np.__version__,'node':subprocess.check_output(['node','--version'],text=True).strip(),'seed':SEED,'cpu_only':True,'source_commit':source_commit,'code_files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('g4_lab').glob('*') if p.is_file()},'elapsed_s':summary['elapsed_s'],'original_html_sha256':hashlib.sha256((source_root/'hand_captcha_prod.html').read_bytes()).hexdigest(),'source_counts':counts}
    path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--run-dir',type=Path,required=True);parser.add_argument('--summary',type=Path,required=True);parser.add_argument('--finalize-existing',action='store_true');parser.add_argument('--run-id',default=None);args=parser.parse_args()
    if args.finalize_existing:
        finalize_manifest(args,json.loads(args.summary.read_text(encoding='utf-8')))
        print('Completed missing post-run manifest; no experiments repeated.')
        return
    if args.run_id is None:args.run_id='G4-ACTUAL-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if args.summary.exists():raise FileExistsError('summary already exists; choose new output path')
    args.run_dir.mkdir(parents=True,exist_ok=False);(args.run_dir/'inputs').mkdir()
    started=time.perf_counter();rows=[];inputs=[]
    with ActualEvaluator(args.source_root) as evaluator:
        for key,source in evaluator.sources.items():
            base=np.asarray(source['base'])
            attacks=generate_attacks(base,SEED)
            # Explicit counterexample to exact-stationary rejection. No tuning.
            attacks['hold_first_epsilon']=attacks['hold_first']+np.random.default_rng(SEED).normal(0,1e-8,base.shape)
            for other,other_source in evaluator.sources.items():
                if other!=key:attacks['wrong_library_'+other]=resample(other_source['base'],len(base))
            for attack_id,response in attacks.items():
                frames=evaluator.frames(key,response)
                input_ref=f'inputs/{key}_{attack_id}.json'
                (args.run_dir/input_ref).write_text(json.dumps(frames,separators=(',',':'),allow_nan=False),encoding='utf-8')
                then=time.perf_counter();result=evaluator.evaluate(key,frames)
                try:validate_frames(frames);valid=True
                except ValueError:valid=False
                rows.append({'run_id':args.run_id,'attempt_id':len(rows)+1,'source_family':key,'attack_id':attack_id,'knowledge':'published_source_library; exact_replay is oracle','input_ref':input_ref,'legacy_result':result,'validation_pass':valid,'compute_ms':(time.perf_counter()-then)*1000,'retries':0,'technical_failure':False})
                inputs.append(frames)
        defended,events=server_trials(evaluator,rows,inputs,False)
        stationary,events2=server_trials(evaluator,rows,inputs,True)
        for row,guard,filter_result in zip(rows,defended,stationary):
            row['guarded_server']=guard;row['stationary_candidate']=filter_result
        (args.run_dir/'attempts.jsonl').write_text(''.join(json.dumps(row,allow_nan=False)+'\n' for row in rows),encoding='utf-8')
        (args.run_dir/'server_events.json').write_text(json.dumps({'guarded':events,'stationary_candidate':events2}),encoding='utf-8')
        grouped=defaultdict(list)
        for row in rows:grouped['wrong_library' if row['attack_id'].startswith('wrong_library_') else row['attack_id']].append(row)
        summary={'run_id':args.run_id,'evidence':'exploratory_known_source_offline_coordinates_and_new_loopback_server','source_families':len(evaluator.sources),'attempts':len(rows),'independent_holdout':False,'human_evaluation':False,'browser_camera_evaluation':False,'historical_l3':None,'rows':[]}
        for attack,group in grouped.items():
            summary['rows'].append({'attack_id':attack,'n':len(group),'score_pass':sum(r['legacy_result']['score_pass'] for r in group),'offline_gate_pass':sum(r['legacy_result']['gate_pass'] for r in group),'validation_pass':sum(r['validation_pass'] for r in group),'guarded_local_l3':sum(r['guarded_server']['local_l3_allowed'] for r in group),'stationary_candidate_local_l3':sum(r['stationary_candidate']['local_l3_allowed'] for r in group),'mean_score':float(np.mean([r['legacy_result']['score']['captcha'] for r in group])),'median_compute_ms':float(np.median([r['compute_ms'] for r in group]))})
        summary['elapsed_s']=time.perf_counter()-started
        args.summary.parent.mkdir(parents=True,exist_ok=True);args.summary.write_text(json.dumps(summary,indent=2),encoding='utf-8')
        finalize_manifest(args,summary)
        print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
