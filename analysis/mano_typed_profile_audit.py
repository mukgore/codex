"""Assess recorded native MANO points without treating surface tips as rigid joints."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,decode,_read,_private


def run(source,source_record,worker_root,output):
    source=Path(source).resolve(strict=True);worker_root=Path(worker_root).resolve(strict=True)
    output=_private(output)
    if output.exists():raise FileExistsError('New private audit directory required')
    before=verify(source_record)
    receipt=decode(_read(Path(source_record)/'receipt.private.json'))
    if before['state']!='EXITED_ZERO' or [Path(p).resolve() for p in receipt['artifact_roots']]!=[source]:
        raise ValueError('Completed recorded producer root required')
    sys.path.insert(0,str(worker_root))
    from experiments.motion_fixture.biomechanical_profile import pending_profile,assess
    contract=decode(_read(source/'point_contract.private.json'))
    kinds=[p['point_kind'] for p in contract['canonical_points']]
    if contract['physical_SI_unit_verified'] is not False or contract['fixed_all_20_bone_policy_applicable'] is not False:
        raise ValueError('Explicit native-unit/surface-tip source contract required')
    profile=pending_profile();profile.update(length_unit='model_native_units',profile_version='mano_native_pending_limits_v1')
    output.mkdir(parents=True)
    (output/'applied_profile.private.json').write_bytes(canonical(profile))
    rows=[]
    for hand in ('right','left'):
        with np.load(source/(hand+'_flat_pc1')/'native_sdk_output.private.npz',allow_pickle=False) as data:
            points=data['canonical_joints']
            if points.shape!=(24,21,3) or data['raw_joints'].shape!=(24,16,3):raise ValueError('Recorded native topology required')
            result=assess(points,np.arange(24)/12,profile,handedness=hand,
                length_unit='model_native_units',point_kinds=kinds)
            if result['rigid_edges_checked_n']!=15:raise ValueError('Native joint edge denominator mismatch')
            (output/(hand+'.assessment.private.json')).write_bytes(canonical(result))
            rows.append({'hand':hand,**{k:result[k] for k in ('state','frames_n','measurable_frames_n',
                'rig_policy','rigid_edges_checked_n','rig_relative_numeric_tolerance','unresolved_rules',
                'violations','declared_rules_pass','evidence_backed_rule_checks_pass')}})
    if verify(source_record)!=before:raise ValueError('Recorded source changed during assessment')
    summary={'scope':'recorded_native_mano_sampled_profile_diagnostic_not_new_inference',
        'cases':rows,'cases_n':len(rows),'frames_n':sum(r['frames_n'] for r in rows),
        'measurable_frames_n':sum(r['measurable_frames_n'] for r in rows),
        'rig_length_violation_cases_n':sum(any(v['rule']=='fixed_generated_rig_bone_lengths' for v in r['violations']) for r in rows),
        'new_model_inference':False,'random_motion_sampled':False,'physical_unit_verified':False,
        'biological_validity_proven':False,'full_generator_ready':False,'release_allowed':False}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','worker-root','output'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();print(json.dumps(run(a.source,a.source_record,a.worker_root,a.output)))
