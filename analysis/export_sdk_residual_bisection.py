"""Check saved residual partitions and publish aggregate conditional results."""
import argparse
import json
from pathlib import Path

import numpy as np

from analysis.audit_exact_shared_residuals import bound
from validation_v03.execution_record import verify


def export(source, record, report):
    source,record,checked=bound(source,record)
    report=Path(report).resolve()
    if report.exists() or any(report.is_relative_to(p) for p in (source,record)):
        raise ValueError('Fresh public report outside immutable evidence required')
    summary=json.loads((source/'summary.json').read_text())
    if (summary['residual_parents_n']!=4 or summary['max_depth']!=6 or summary['maximum_attempts_n']!=508
            or any(summary[k] is not False for k in ('backend_error_bounds_validated','continuous_collision_free_proven','CCD_clearance','release_allowed'))
            or any(summary[k]!=0 for k in ('SDK_forwards_n','model_instantiations_n','new_observation_frames_n','prior_finite_leaves_recomputed_n'))):
        raise ValueError('Registered conditional residual scope required')
    total_attempts=total_terminals=total_finite=total_complete=0
    details=sorted(source.glob('*.refinement.private.json'))
    if len(details)!=4:raise ValueError('Exactly four partition records required')
    parent_keys=set();event_keys=set()
    for path in details:
        detail=json.loads(path.read_text());parent=detail['parent'];attempts=detail['attempts'];terminals=detail['terminals']
        key=(parent['case_id'],parent['interval_idx'],parent['subdivision_idx'])
        if key in parent_keys:raise ValueError('Repeated parent')
        parent_keys.add(key)
        tree={r['address']:r for r in attempts}
        if len(tree)!=len(attempts) or len(tree)>127:raise ValueError('Tree address/budget mismatch')
        def check(address,a,b,depth):
            row=tree[address]
            if (row['start'],row['end'],row['depth'])!=(a,b,depth) or not 0<=depth<=6:
                raise ValueError('Tree interval/depth mismatch')
            if row['status']=='SPLIT':
                if depth==6 or row['reason']!='SDK_SHIFTED_NORM_INCLUDES_ZERO':raise ValueError('Invalid split')
                midpoint=a+(b-a)/2
                return check(address+'0',a,midpoint,depth+1)+check(address+'1',midpoint,b,depth+1)
            if row['status'] not in ('CONDITIONAL_CANDIDATE','UNRESOLVED'):raise ValueError('Invalid terminal')
            return [row]
        leaves=check('r',parent['t0_seconds'],parent['t1_seconds'],0)
        if [r['address'] for r in leaves]!=[r['address'] for r in terminals]:raise ValueError('Terminal order mismatch')
        for a,b in zip(leaves,terminals):
            if any(a[k]!=b[k] for k in ('address','start','end','depth','status')):raise ValueError('Terminal mismatch')
        finite=[r for r in terminals if r['status']=='CONDITIONAL_CANDIDATE']
        with np.load(path.with_name(path.name.replace('.refinement.private.json','.boxes.private.npz')),allow_pickle=False) as raw:
            lower,upper,rem=raw['lower'],raw['upper'],raw['conditional_chord_remainder_upper']
            if (lower.shape!=(len(finite),778,3) or upper.shape!=lower.shape or rem.shape!=(len(finite),778)
                    or not all(np.isfinite(a).all() for a in (lower,upper,rem))
                    or not (lower<=upper).all() or not (rem>=0).all()
                    or [r['bounds_index'] for r in finite]!=list(range(len(finite)))):
                raise ValueError('Finite bounds/index correspondence mismatch')
        case=next(r for r in summary['cases'] if (r['case_id'],r['original_interval_idx'],r['subdivision_idx'])==key)
        complete=len(finite)==len(terminals)
        if (case['attempted_intervals_n']!=len(attempts) or case['terminal_intervals_n']!=len(terminals)
                or case['finite_terminal_intervals_n']!=len(finite) or case['complete_conditional_parent']!=complete
                or detail['complete_conditional_parent']!=complete):raise ValueError('Case counts mismatch')
        for row in attempts:
            if row['wall_ns']<0 or row['own_cpu_ns']<0:raise ValueError('Negative timing')
            event_keys.add((key,row['start'],row['end']))
        total_attempts+=len(attempts);total_terminals+=len(terminals);total_finite+=len(finite);total_complete+=complete
    log=[json.loads(line) for line in (source/'attempts.private.jsonl').read_text().splitlines()]
    if len(log)!=2*total_attempts:raise ValueError('Incomplete operation log')
    keys_by_index=[(r['case_id'],r['original_interval_idx'],r['subdivision_idx']) for r in summary['cases']]
    logged=set()
    for start,finish in zip(log[::2],log[1::2]):
        if start['phase']!='STARTED' or finish['phase']!='FINISHED' or any(start[k]!=finish[k] for k in ('parent','start','end')):
            raise ValueError('Operation log ordering mismatch')
        key=(keys_by_index[start['parent']],start['start'],start['end'])
        if key in logged:raise ValueError('Duplicate operation')
        logged.add(key)
    if logged!=event_keys:raise ValueError('Log/tree interval mismatch')
    actual=(total_attempts,total_terminals,total_finite,total_terminals-total_finite,total_complete)
    expected=tuple(summary[k] for k in ('attempted_intervals_n','terminal_intervals_n','finite_terminal_intervals_n','unresolved_terminal_intervals_n','complete_conditional_parents_n'))
    if actual!=expected:raise ValueError('Summary denominator mismatch')
    manifest=json.loads((record/'provenance/manifest.json').read_text())
    public=dict(summary,execution_record=checked,producer_code_commit=manifest['code_commit'],
                recorded_input_files_n=len(manifest['inputs']),recorded_dependency_pins_n=len(manifest['pinned_versions']),
                partition_tree_and_log_checked=True,finite_arrays_shape_and_order_checked=True,
                limitations=['Finite interval candidates retain the original unvalidated backend error assumptions.',
                             'The 764 prior finite leaves were not recomputed; terminal counts are a new unequal-width partition.',
                             'Two complete residual parents are conditional enclosures, not CCD, biological or security admission.'])
    if verify(record)!=checked:raise ValueError('Evidence changed during export')
    with report.open('x',encoding='utf-8') as stream:json.dump(public,stream,indent=2,allow_nan=False);stream.write('\n')
    return {'partition_tree_and_log_checked':True,'attempted_intervals_n':total_attempts,'CCD_clearance':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','record','report'):parser.add_argument('--'+name,required=True,type=Path)
    print(json.dumps(export(**vars(parser.parse_args()))))
