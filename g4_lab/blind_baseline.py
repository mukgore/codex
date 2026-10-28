"""Low-information uniform-coordinate baseline, separate from library-bounded random."""
import argparse
import json
from pathlib import Path
import numpy as np
from .actual import ActualEvaluator
from .run import server_trials

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--run-dir',type=Path,required=True);parser.add_argument('--summary',type=Path,required=True);args=parser.parse_args()
    if args.summary.exists():raise FileExistsError('summary already exists; preserve prior run')
    args.run_dir.mkdir(parents=True,exist_ok=False);rows=[];inputs=[]
    with ActualEvaluator(args.source_root) as evaluator:
        rng=np.random.default_rng(20261028)
        for key,source in evaluator.sources.items():
            # Only length/timing (observable media metadata), no target pose
            # coordinates or per-joint bounding box enter response generation.
            frames=[{'t_ms':i*1000/source['fps'],'lm':rng.uniform(0,1,(21,2)).tolist()} for i in range(len(source['raw_frames']))]
            input_ref=f'{key}.json';(args.run_dir/input_ref).write_text(json.dumps(frames),encoding='utf-8')
            rows.append({'source_family':key,'input_ref':input_ref,'legacy_result':evaluator.evaluate(key,frames)});inputs.append(frames)
        guarded,_=server_trials(evaluator,rows,inputs,False)
        for row,result in zip(rows,guarded):row['guarded_server']=result
    (args.run_dir/'attempts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    summary={'run_id':'G4-BLIND-001','n':len(rows),'seed':20261028,'knowledge':'media length/fps only; coordinates iid uniform [0,1]; no anatomical validity assumption','score_pass':sum(r['legacy_result']['score_pass'] for r in rows),'offline_gate_pass':sum(r['legacy_result']['gate_pass'] for r in rows),'guarded_local_l3':sum(r['guarded_server']['local_l3_allowed'] for r in rows),'scope':'exploratory eight known-source inputs, no holdout/browser/camera/human claim'}
    args.summary.parent.mkdir(parents=True,exist_ok=True);args.summary.write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()
