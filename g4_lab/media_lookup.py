"""Known published-media cache attack against the new owned loopback server.

Attacker sees only opaque media URL/bytes during a challenge and has a prior
copy of the eight published media/reference files. No server state is consulted
to select the answer; server state is read only afterwards for audit labels.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import threading
import time
from .actual import ActualEvaluator,LANDMARK_NAMES
from .run import LocalClient
from .server import LabService,create_server

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--run-id',default='G4-MEDIA-CACHE-002');args=parser.parse_args()
    if args.output.exists():raise FileExistsError('preserve prior lookup output')
    root=args.source_root.resolve();manifest=json.loads((root/'pool_manifest.json').read_text(encoding='utf-8'))
    cache={};references={};setup=time.perf_counter()
    for clip in manifest['clips']:
        digest=hashlib.sha256((root/clip['video_file']).read_bytes()).hexdigest()
        cache.setdefault(digest,[]).append(clip['clip_id'])
        data=json.loads((root/clip['landmarks_file']).read_text(encoding='utf-8'));info=data['video_info'];frames=[]
        for i,frame in enumerate(data['frames']):
            lm=frame.get('landmarks_px') if frame.get('detected') else None
            frames.append({'t_ms':frame.get('frame_idx',i)*1000/info['fps'],'lm':[[lm[n]['x']/info['width'],lm[n]['y']/info['height']] for n in LANDMARK_NAMES] if lm else None})
        references[clip['clip_id']]=frames
    setup_s=time.perf_counter()-setup;rows=[]
    with ActualEvaluator(root) as evaluator:
        # Balanced coverage in an unpredictable order; order is never given
        # to the client/predictor. This removes the sorted-order confound.
        service=LabService(evaluator,source_order=secrets.SystemRandom().sample(sorted(references),len(references)))
        server=create_server(service);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            client=LocalClient(server.server_port);client.post('/api/session',{})
            for _ in references:
                started=time.perf_counter();_,challenge=client.post('/api/challenge',{})
                with client.opener.open(client.base+challenge['media_url'],timeout=20) as response:video=response.read()
                candidates=cache.get(hashlib.sha256(video).hexdigest(),[])
                if len(candidates)!=1:
                    rows.append({'identified':False,'candidate_count':len(candidates),'local_l3_allowed':False});continue
                predicted=candidates[0]
                status,result=client.post('/api/submit',{'challenge_id':challenge['challenge_id'],'frames':references[predicted]})
                grant=result.get('grant_id');allowed=False
                if grant:
                    _,action=client.post('/api/protected_action',{'grant_id':grant});allowed=action['protected_action_allowed']
                actual=service.challenges[challenge['challenge_id']]['key']  # audit only, after answering
                rows.append({'identified':predicted==actual,'candidate_count':1,'http_status':status,'score_pass':result.get('score_pass'),'offline_gate_pass':result.get('gate_pass'),'local_l3_allowed':allowed,'media_bytes':len(video),'attempt_wall_ms':(time.perf_counter()-started)*1000})
        finally:server.shutdown();server.server_close();worker.join(timeout=5)
    summary={'run_id':args.run_id,'assignment':'balanced_secret_random_order_not_supplied_to_predictor','knowledge':'prior published eight media and reference files; challenge exposes only opaque URL and video bytes','source_families':8,'n':len(rows),'identified':sum(r['identified'] for r in rows),'score_pass':sum(bool(r.get('score_pass')) for r in rows),'offline_gate_pass':sum(bool(r.get('offline_gate_pass')) for r in rows),'local_l3_allowed':sum(r['local_l3_allowed'] for r in rows),'setup_s':setup_s,'median_attempt_wall_ms':sorted(r['attempt_wall_ms'] for r in rows)[len(rows)//2],'scope':'new loopback server, offline landmark replay, closed-set development; no browser camera or historical L3 claim','rows':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
