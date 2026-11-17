"""Recorded bounded refinement of only four prior unresolved SDK time leaves."""
import argparse
import json
import os
from pathlib import Path
import time

import numpy as np

from analysis.audit_exact_shared_residuals import bound
from analysis.runtime_benchmark.bounded_interval_refinement import refine
from analysis.runtime_benchmark.interval_boxes import Unresolved
from analysis.runtime_benchmark.sdk_path_boxes import ASSUMPTIONS, VERSION, local_rotations, lbs_box, chord_remainder
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private, canonical

DEPTH = 6
REASON = 'SDK_SHIFTED_NORM_INCLUDES_ZERO'


def execute(source, source_record, prior, prior_record, output):
    source, source_record, source_checked = bound(source, source_record)
    prior, prior_record, prior_checked = bound(prior, prior_record)
    output = _private(output)
    if output.exists() or any(output.is_relative_to(r) or r.is_relative_to(output)
                              for r in (source, source_record, prior, prior_record)):
        raise ValueError('Fresh independent residual output required')
    summary = json.loads((prior/'summary.json').read_text())
    if (summary['attempted_leaves_n'] != 768 or summary['unresolved_leaves_n'] != 4
            or summary['finite_candidate_leaves_n'] != 764 or summary['assumptions'] != ASSUMPTIONS
            or summary['backend_error_bounds_validated'] is not False or summary['CCD_clearance'] is not False):
        raise ValueError('Exact conditional v2 parent scope required')
    planned = []
    for case in summary['cases']:
        name = case['case_id']
        if name not in ('right_s7','right_s19','left_s7','left_s19'):
            raise ValueError('Known saved cases required')
        rows = json.loads((prior/(name+'.leaves.private.json')).read_text())
        if len(rows) != 192:raise ValueError('Complete prior case required')
        with np.load(prior/(name+'.boxes.private.npz'),allow_pickle=False) as stored:
            valid = stored['valid'].copy()
        if valid.shape != (192,):raise ValueError('Complete parent validity mask required')
        for idx,row in enumerate(rows):
            if bool(valid[idx]) != (row['status'] != 'UNRESOLVED'):
                raise ValueError('Prior row and validity mask differ')
            if row['status'] == 'UNRESOLVED':
                if row.get('reason') != REASON or row['case_id'] != name:
                    raise ValueError('Only registered shifted norm residuals may be refined')
                interval,part=row['interval_idx'],row['subdivision_idx']
                if (idx != 8*interval+part or not 0 <= interval < 24 or not 0 <= part < 8
                        or row['t0_seconds'] != interval*.125+part*.015625
                        or row['t1_seconds'] != interval*.125+(part+1)*.015625):
                    raise ValueError('Exact registered residual time interval required')
                planned.append((name,dict(row)))
    if len(planned) != 4:raise ValueError('Exactly four residual parents required')
    output.mkdir()
    utc,wall,cpu=time.time_ns(),time.perf_counter_ns(),time.process_time_ns()
    (output/'assumptions.private.json').write_bytes(canonical(ASSUMPTIONS))
    cases=[]
    with (output/'attempts.private.jsonl').open('xb') as log:
        def event(value):
            log.write(canonical(value)+b'\n');log.flush();os.fsync(log.fileno())
        for index,(name,parent) in enumerate(planned):
            hand=name.split('_')[0]
            with np.load(source/(hand+'_setup.private.npz'),allow_pickle=False) as setup:
                basis=setup['basis'].copy()
            with np.load(source/name/'native_output.private.npz',allow_pickle=False) as native:
                waypoints=native['proposed_angles'][[0,12,24]].copy()
                ends=native['vertices'][[parent['interval_idx'],parent['interval_idx']+1]].copy()
            with np.load(prior/(hand+'_buffers.private.npz'),allow_pickle=False) as saved:
                buffers={key:saved[key].copy() for key in ('template','regressor','posedirs','weights','parents')}
            timings={}
            def evaluate(a,b):
                if (time.perf_counter_ns()-wall)/1e9 > 650:
                    raise TimeoutError('Declared residual evaluation budget exceeded')
                event(dict(parent=index,phase='STARTED',start=a,end=b))
                start,own=time.perf_counter_ns(),time.process_time_ns()
                status='ERROR';reason=None
                try:
                    rotations=local_rotations(waypoints,basis,a,b)
                    box=lbs_box(rotations,**buffers)
                    origin=parent['interval_idx']*.125
                    remainder=chord_remainder(box,ends[0],ends[1],(a-origin)/.125,(b-origin)/.125)
                    status='CONDITIONAL_CANDIDATE'
                    return box,remainder
                except Unresolved as error:
                    status='UNRESOLVED';reason=str(error);raise
                finally:
                    elapsed=dict(wall_ns=time.perf_counter_ns()-start,own_cpu_ns=time.process_time_ns()-own)
                    timings[(a,b)]=elapsed
                    event(dict(parent=index,phase='FINISHED',start=a,end=b,status=status,reason=reason,**elapsed))
            result=refine(evaluate,parent['t0_seconds'],parent['t1_seconds'],max_depth=DEPTH,
                          unresolved_type=Unresolved,retry_reason=REASON)
            attempts=[dict(r,**timings[(r['start'],r['end'])]) for r in result['attempts']]
            terminals=[];lower=[];upper=[];remainders=[]
            for row in result['terminals']:
                row=dict(row)
                if row['status']=='CONDITIONAL_CANDIDATE':
                    box,remainder=result['values'][row['address']]
                    row.update(bounds_index=len(lower),maximum_vertex_box_width_native=float((box.hi-box.lo).max()),
                               maximum_chord_remainder_native=float(remainder.max()))
                    lower.append(box.lo);upper.append(box.hi);remainders.append(remainder)
                terminals.append(row)
            stem=f'{name}_i{parent["interval_idx"]}_p{parent["subdivision_idx"]}'
            np.savez_compressed(output/(stem+'.boxes.private.npz'),
                                lower=np.asarray(lower).reshape(-1,778,3),upper=np.asarray(upper).reshape(-1,778,3),
                                conditional_chord_remainder_upper=np.asarray(remainders).reshape(-1,778))
            detail=dict(parent=parent,max_depth=DEPTH,attempts=attempts,terminals=terminals,
                        complete_conditional_parent=result['complete'],backend_error_bounds_validated=False,CCD_clearance=False)
            (output/(stem+'.refinement.private.json')).write_bytes(canonical(detail))
            cases.append(dict(case_id=name,original_interval_idx=parent['interval_idx'],subdivision_idx=parent['subdivision_idx'],
                              attempted_intervals_n=len(attempts),terminal_intervals_n=len(terminals),
                              finite_terminal_intervals_n=len(lower),unresolved_terminal_intervals_n=len(terminals)-len(lower),
                              complete_conditional_parent=result['complete'],
                              unresolved_reasons=sorted({r['reason'] for r in terminals if r['status']=='UNRESOLVED'}),
                              maximum_finite_chord_remainder_native=max((float(x.max()) for x in remainders),default=None)))
            print(f'Residual parents completed {index+1}/4',flush=True)
    if verify(source_record) != source_checked or verify(prior_record) != prior_checked:
        raise ValueError('Original source evidence changed')
    result=dict(scope='four_v2_residual_time_intervals_bounded_conditional_refinement',
                base_version=VERSION,assumptions=dict(ASSUMPTIONS),max_depth=DEPTH,cases=cases,
                residual_parents_n=4,maximum_attempts_n=508,
                attempted_intervals_n=sum(r['attempted_intervals_n'] for r in cases),
                terminal_intervals_n=sum(r['terminal_intervals_n'] for r in cases),
                finite_terminal_intervals_n=sum(r['finite_terminal_intervals_n'] for r in cases),
                unresolved_terminal_intervals_n=sum(r['unresolved_terminal_intervals_n'] for r in cases),
                complete_conditional_parents_n=sum(r['complete_conditional_parent'] for r in cases),
                prior_finite_leaves_recomputed_n=0,SDK_forwards_n=0,new_observation_frames_n=0,
                model_buffers_loaded_from_saved_npz=True,model_instantiations_n=0,
                backend_error_bounds_validated=False,continuous_collision_free_proven=False,CCD_clearance=False,
                release_allowed=False,accepted_into_pool_n=0,
                timing=dict(started_utc_epoch_ns=utc,ended_utc_epoch_ns=time.time_ns(),
                            wall_ns=time.perf_counter_ns()-wall,own_cpu_ns=time.process_time_ns()-cpu,
                            scope='residual preparation/evaluation/store and source rechecks; initial receipt verification excluded'))
    (output/'summary.json').write_bytes(canonical(result))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','prior','prior-record','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    result=execute(**vars(parser.parse_args()))
    print(json.dumps({k:result[k] for k in ('attempted_intervals_n','finite_terminal_intervals_n','unresolved_terminal_intervals_n','complete_conditional_parents_n')}))
