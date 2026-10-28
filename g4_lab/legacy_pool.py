"""Exploratory current-scorer inputs from published legacy reference records.

These six records are outside the current 8-clip manifest, but are previously
published historical study assets, not established unused source holdouts.
Their left/right/action links are not six independent population samples.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from .actual import ActualEvaluator
from .run import resample

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--run-dir',type=Path,required=True);parser.add_argument('--summary',type=Path,required=True);args=parser.parse_args()
    if args.summary.exists():raise FileExistsError('preserve legacy result')
    args.run_dir.mkdir(parents=True,exist_ok=False)
    legacy=json.loads((args.source_root/'landmarks_base.json').read_text(encoding='utf-8'));rows=[]
    with ActualEvaluator(args.source_root) as evaluator:
        foreign=np.asarray(evaluator.sources[sorted(evaluator.sources)[0]]['base'])
        for record_index,data in enumerate(legacy.values(),1):
            prepared=evaluator.call({'op':'prepare','data':data});base=np.asarray(prepared['frames']);n=len(base)
            fraction=np.linspace(0,1,n)[:,None,None]
            responses={'exact_replay':base,'hold_first':np.repeat(base[:1],n,axis=0),'endpoint_interpolation':base[0]*(1-fraction)+base[-1]*fraction,'fixed_current_pool_reference':resample(foreign,n)}
            for attack,array in responses.items():
                frames=[{'t_ms':prepared['origIdx'][i]*1000/data['video_info']['fps'],'lm':lm.tolist()} for i,lm in enumerate(array)]
                result=evaluator.call({'op':'evaluate','base':base.tolist(),'frames':frames})
                rows.append({'legacy_record':record_index,'attack_id':attack,'result':result})
    (args.run_dir/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    summary={'run_id':'G4-LEGACY-SUPPLEMENT-001','legacy_reference_records':6,'current_manifest_membership':False,'independent_holdout':False,'local_l3_tested':False,'scope':'current actual HTML functions; legacy reference coordinate fixtures outside current pool; unknown historical development/calibration lineage; not a browser session','rows':[]}
    for attack in responses:
        selected=[r for r in rows if r['attack_id']==attack]
        summary['rows'].append({'attack_id':attack,'n':len(selected),'score_pass':sum(r['result']['score_pass'] for r in selected),'offline_gate_pass':sum(r['result']['gate_pass'] for r in selected),'mean_score':float(np.mean([r['result']['score']['captcha'] for r in selected]))})
    args.summary.parent.mkdir(parents=True,exist_ok=True);args.summary.write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
