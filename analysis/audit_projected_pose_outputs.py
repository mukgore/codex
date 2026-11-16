"""Separate read-only aggregation of complete SDK outputs from a failed producer."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from analysis.runtime_benchmark.projected_pose_pilot import project,VERSION
from analysis.runtime_benchmark.mano_model_prior_audit import assess
from analysis.runtime_benchmark.mano_anatomical_frame_probe import extract_anatomical,compose_anatomical
from analysis.runtime_benchmark.template_free_pose import decide
from analysis.runtime_benchmark.journal import verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,_private


def summary_from_cases(cases,unique_payloads):
    if len(cases)!=32 or len({r['case_id'] for r in cases})!=32:
        raise ValueError('Exactly32 unique projected cases required')
    return {'projected_proposals_n':32,
      'model_prior_zero_n':sum(r['masked_excess_components_n']==0 for r in cases),
      'sampled_surface_clear_n':sum(r['surface_state']=='NO_TESTED_PAIR_INTERSECTION' for r in cases),
      'model_surface_eligible_n':sum(r['model_surface_eligible'] for r in cases),
      'bmc_geometry_measurable_n':sum(r['bmc_geometry_error'] is None for r in cases),
      'changed_proposals_n':sum(r['changed_axis_components_n']>0 for r in cases),
      'changed_axis_components_n':sum(r['changed_axis_components_n'] for r in cases),
      'correction_max_degrees':max(r['max_absolute_correction_degrees'] for r in cases),
      'correction_l2_degrees_min':min(r['l2_correction_degrees'] for r in cases),
      'correction_l2_degrees_max':max(r['l2_correction_degrees'] for r in cases),
      'unique_actual_geometry_payloads_n':unique_payloads,
      'exact_neutral_geometry_n':sum(r['exact_neutral_geometry'] for r in cases),
      'rejection_reason_counts':dict(Counter(x for r in cases for x in r['rejection_reasons']))}


def execute(source,source_record,output):
    source=_private(source);record=_private(source_record);output=_private(output)
    status=verify(record);receipt=json.loads((record/'receipt.private.json').read_text())
    if status['state']!='PROCESS_ERROR' or receipt['artifact_roots']!=[str(source)] or receipt['postflight_snapshot_matched'] is not True:
        raise ValueError('Complete preserved process-error outputs with matching snapshot required')
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (source,record)):
        raise ValueError('Fresh audit outside immutable producer roots required')
    journal=verify_bundle(source/'journal_bundle.private.zip')
    if journal['status']!='COMPLETED' or journal['completed_frames']!=34:
        raise ValueError('All34 SDK outcomes must precede failed summary')
    output.mkdir();wall=time.perf_counter_ns();cpu=time.process_time_ns();utc=time.time_ns()
    prior=json.loads((source/'applied_model_prior.private.json').read_text());cases=[];buckets={}
    for hand in ('right','left'):
        with np.load(source/(hand+'_setup.private.npz'),allow_pickle=False) as setup:
            basis=setup['basis'].copy();neutral_v=setup['vertices'].copy();neutral_j=setup['joints'].copy()
        for seed in (7,19):
            for attempt in range(8):
                case_id=f'P_B_{hand}_s{seed}_a{attempt}';folder=source/case_id
                row=json.loads((folder/'decision.private.json').read_text());surface=json.loads((folder/'surface_QA.private.json').read_text())
                if row['case_id']!=case_id or row['hand']!=hand:raise ValueError('Case identity mismatch')
                with np.load(folder/'native_output.private.npz',allow_pickle=False) as saved:
                    corrected,change=project(saved['original_angles'],prior)
                    if not np.array_equal(corrected,saved['projected_angles']):raise ValueError('Saved projection differs from fixed rule')
                    angles=extract_anatomical(saved['full_pose'][:,3:],basis)
                    strict,effective=assess(angles,prior)
                    if not np.array_equal(strict,saved['strict_excess_radians']) or not np.array_equal(effective,saved['masked_excess_radians']):
                        raise ValueError('Saved model prior losses differ')
                    if np.max(np.abs(compose_anatomical(angles,basis)-saved['full_pose'][:,3:]))>1e-6:
                        raise ValueError('Stored native/anatomical roundtrip differs')
                    verdict=decide(effective,surface)
                    if any(row[k]!=v for k,v in verdict.items()) or any(row[k]!=v for k,v in change.items()):
                        raise ValueError('Recorded decision/correction differs from raw output')
                    payload=saved['vertices'].tobytes()+saved['joints'].tobytes();key=hashlib.sha256(payload).hexdigest()
                    bucket=buckets.setdefault(key,{'payload':payload,'cases':[]})
                    if bucket['payload']!=payload:raise ValueError('Exact payload hash bucket differs')
                    bucket['cases'].append(case_id)
                    neutral=np.array_equal(saved['vertices'],neutral_v) and np.array_equal(saved['joints'],neutral_j)
                    if neutral!=row['exact_neutral_geometry']:raise ValueError('Neutral duplicate state differs')
                # The failed producer omitted this aggregate field; reconstruct
                # only in this separate output, keeping original files intact.
                cases.append({**row,'surface_state':surface['state']})
    if verify(record)!=status:raise ValueError('Failed producer evidence changed during audit')
    summary={'version':VERSION,**summary_from_cases(cases,len(buckets)),
      'original_producer_state':'PROCESS_ERROR','original_sdk_journal_state':'COMPLETED',
      'original_actual_forward_poses_n':34,'new_actual_forward_poses_n':0,'new_random_draws_n':0,
      'new_motion_sequences_n':0,'new_videos_n':0,'human_trials_n':0,'new_independent_families_n':0,
      'release_allowed':False,'accepted_into_pool_n':0,'pending_BMC_state':'UNRESOLVED_LIMITS',
      'scope':'separate raw-output audit; original failed producer is not relabeled EXITED_ZERO',
      'timing':{'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),'wall_ns':time.perf_counter_ns()-wall,
        'own_cpu_ns':time.process_time_ns()-cpu,'scope':'raw-output algebra/decision/duplicate audit; producer verification and recorder snapshot/sealing excluded'}}
    (output/'summary.json').write_bytes(canonical(summary))
    (output/'cases.private.json').write_bytes(canonical({'cases':cases}))
    (output/'duplicate_groups.private.json').write_bytes(canonical({'groups':{k:v['cases'] for k,v in buckets.items()}}))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(execute(a.source,a.source_record,a.output)))
