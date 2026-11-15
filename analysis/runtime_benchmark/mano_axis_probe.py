"""Forward-only native MANO axis perturbations; not clinical-axis calibration.

Flat model mean and systematic +/- engineering perturbations, not a random
motion or human safety limit. SDK arrays/Jacobians remain private research data.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np

from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from analysis.runtime_benchmark.mano_recorded_producer import (
    RAW_PARENTS,TIP_NAMES,ORDER,authorize_inputs,canonicalize,point_contract,
)
from validation_v03.run_manifest import snapshot_file
from validation_v03.session_artifacts import canonical,_private

VERSION='mano_flat_native_axis_central_probe_v1'
DELTA=.02


def design(delta=DELTA):
    if type(delta) not in (int,float) or not np.isfinite(delta) or not 0<delta<=.05:
        raise ValueError('Explicit bounded engineering perturbation required')
    poses=np.zeros((91,45),np.float32);rows=[{'frame_idx':0,'kind':'flat_neutral'}]
    for joint in range(1,16):
        for axis in range(3):
            for sign in (-1,1):
                index=len(rows);poses[index,(joint-1)*3+axis]=sign*delta
                rows.append({'frame_idx':index,'kind':'native_axis_probe','native_joint_index':joint,
                    'native_axis_index':axis,'sign':sign,'delta_radians':delta,
                    'parameter_semantics':'diagnostic axis-angle coordinate, not anatomical safe excursion'})
    return poses,rows


def descendants(joint):
    if type(joint) is not int or not 1<=joint<16:raise ValueError('Nonroot native joint required')
    result=[]
    for candidate in range(16):
        cursor=candidate
        while cursor>0 and cursor!=joint:cursor=RAW_PARENTS[cursor]
        if cursor==joint:result.append(candidate)
    return result


def expected_native_rotation(neutral,joint,axis,angle):
    neutral=np.asarray(neutral,float)
    if neutral.shape!=(16,3) or not np.isfinite(neutral).all() or type(axis) is not int or not 0<=axis<3:
        raise ValueError('Complete neutral joints and native coordinate axis required')
    unit=np.eye(3)[axis];r=neutral-neutral[joint]
    rotated=r*np.cos(angle)+np.cross(unit,r)*np.sin(angle)+np.outer(r@unit,unit)*(1-np.cos(angle))
    result=neutral.copy();indices=descendants(joint)
    result[indices]=neutral[joint]+rotated[indices]
    return result


def pair_delta(plus,minus):
    plus=np.asarray(plus,float);minus=np.asarray(minus,float)
    if plus.shape!=(15,2) or minus.shape!=plus.shape or not np.isfinite(plus).all() or not np.isfinite(minus).all():
        raise ValueError('Complete finite BMC angle pairs required')
    difference=plus-minus
    difference[:,0]=np.arctan2(np.sin(difference[:,0]),np.cos(difference[:,0]))
    return difference


def execute(intake,research_record,worker_root,output):
    sources=authorize_inputs(intake,research_record);output=_private(output)
    if output.exists():raise FileExistsError('Fresh private probe root required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from dataset_pipeline.common import LANDMARK_NAMES
    from experiments.motion_fixture.biomechanical_features import extract,GeometryError,ANGLE_RECORDS
    poses,rows=design();journal=Journal(output/'journal',{'condition_id':'G03_MANO_NATIVE_AXIS_PROBE_20261115',
        'endpoint':'flat_neutral_native_forward_and_axis_response','input_exposure':'existing private user-provided research model',
        'cache_state':'CPU OS/module cache uncontrolled','planned_frames':182,'timeout_seconds':300,
        'scope':'forward model coordinate diagnostic, not clinical/human/safety measurement'})
    cases=[]
    try:
        with journal.stage('verify_runtime_and_scope'):
            import torch
            import smplx
            from smplx.vertex_ids import vertex_ids
            if str(torch.__version__)!='2.5.1+cpu' or importlib.metadata.version('smplx')!='0.1.28':
                raise ValueError('Existing explicit CPU runtime required')
            torch.set_num_threads(1);torch.manual_seed(0)
            tips={name:vertex_ids['mano'][name] for name in TIP_NAMES}
            contract=point_contract(LANDMARK_NAMES,tips)
            target={ORDER[LANDMARK_NAMES.index(r['canonical_center_point'])]:r['angle_index'] for r in ANGLE_RECORDS}
            if set(target)!=set(range(1,16)):raise ValueError('Explicit native-joint to BMC-center bijection required')
            (output/'design.private.json').write_bytes(canonical({'version':VERSION,'rows':rows,'delta_radians':DELTA,
                'sample_order_not_motion_time':True,'unit':'model_native_units_not_verified_SI'}))
            (output/'point_contract.private.json').write_bytes(canonical(contract))
        for hand_number,hand in enumerate(('right','left')):
            case=output/hand;case.mkdir()
            with journal.stage(hand+'_native_forward'):
                authorize_inputs(intake,research_record)
                model=smplx.MANO(str(Path(intake).resolve()/'models'),is_rhand=hand=='right',use_pca=False,
                    flat_hand_mean=True,batch_size=len(poses),dtype=torch.float32).to('cpu')
                model.eval()
                if tuple(model.parents.tolist())!=RAW_PARENTS:raise ValueError('Native parent table changed')
                with torch.no_grad():result=model(hand_pose=torch.from_numpy(poses),return_verts=True,return_full_pose=True)
                vertices=result.vertices.numpy();raw=result.joints.numpy();full=result.full_pose.numpy()
                points=canonicalize(vertices,raw,tips)
                if full.shape!=(91,48) or not np.array_equal(full[:,3:],poses) or np.any(full[:,:3]):
                    raise ValueError('Flat local axis-angle and zero root contract required')
                np.savez_compressed(case/'native_output.private.npz',vertices=vertices,raw_joints=raw,
                    canonical_joints=points,full_pose_axis_angle=full,pose_axis_angle=poses,
                    faces=model.faces,parents=model.parents.numpy())
                for frame in range(len(poses)):journal.frame_completed(hand_number*91+frame,True)
            with journal.stage(hand+'_native_rotation_and_bmc_response'):
                neutral=raw[0].astype(float);scale=float(np.linalg.norm(np.ptp(neutral,axis=0)))
                tolerance=max(1e-10,scale*64*np.finfo(np.float32).eps)
                errors=[];features=[];geometry_errors=[]
                for row,pose in zip(rows,points):
                    if row['kind']=='native_axis_probe':
                        expected=expected_native_rotation(neutral,row['native_joint_index'],row['native_axis_index'],row['sign']*DELTA)
                        error=float(np.abs(raw[row['frame_idx']]-expected).max());errors.append(error)
                        if error>tolerance:raise ValueError('Native forward differs from neutral parent-frame rotation expectation')
                    try:features.append(extract(pose,handedness=hand)['joint_angles_radians'])
                    except GeometryError as error:features.append(None);geometry_errors.append({'frame_idx':row['frame_idx'],'code':error.code})
                jacobians=[];rank_counts={};measurable_pairs=0
                for joint in range(1,16):
                    derivatives=[]
                    for axis in range(3):
                        minus=1+((joint-1)*3+axis)*2;plus=minus+1
                        if features[minus] is None or features[plus] is None:derivatives.append(None)
                        else:derivatives.append(pair_delta(features[plus],features[minus])/(2*DELTA));measurable_pairs+=1
                    entry={'native_joint_index':joint,'target_bmc_angle_index':target[joint],
                        'clinical_axis_mapping_verified':False}
                    if all(d is not None for d in derivatives):
                        all_features=np.stack(derivatives,axis=-1);matrix=all_features[target[joint]]
                        singular=np.linalg.svd(matrix,compute_uv=False)
                        rank=int((singular>max(1e-8,float(singular[0])*1e-6)).sum())
                        rank_counts[str(rank)]=rank_counts.get(str(rank),0)+1
                        entry.update(all_bmc_response_jacobian=all_features.tolist(),target_bmc_response_jacobian=matrix.tolist(),
                            singular_values=singular.tolist(),numeric_local_rank=rank)
                    else:entry['state']='INCOMPLETE_GEOMETRY_RESPONSE'
                    jacobians.append(entry)
                (case/'axis_response.private.json').write_bytes(canonical({'joint_responses':jacobians,
                    'geometry_errors':geometry_errors,'neutral_bmc_angles':None if features[0] is None else features[0].tolist(),
                    'rank_threshold_scope':'numerical diagnostic only, not anatomy or clinical identifiability'}))
                row={'hand':hand,'forward_samples_n':91,'native_rotation_checks_n':len(errors),
                    'max_native_rotation_abs_error':max(errors),'native_numeric_tolerance':tolerance,
                    'measurable_bmc_samples_n':len(features)-len(geometry_errors),'measurable_axis_pairs_n':measurable_pairs,
                    'target_response_rank_counts':rank_counts,'geometry_errors_n':len(geometry_errors),
                    'clinical_axis_mapping_verified':False,'release_allowed':False}
                (case/'summary.private.json').write_bytes(canonical(row));cases.append(row)
            del model,result
        with journal.stage('source_scope_recheck'):
            authorize_inputs(intake,research_record)
            for row in sources.values():
                if snapshot_file(row['path'])!=row:raise ValueError('Original model input changed during forward probe')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');recovered=verify_bundle(output/'journal_bundle.private.zip')
    summary={'scope':'systematic_flat_native_axis_forward_probe_not_motion_or_clinical_calibration','version':VERSION,
        'cases':cases,'hands_n':2,'native_forward_samples_n':182,'native_rotation_checks_n':sum(r['native_rotation_checks_n'] for r in cases),
        'measurable_bmc_samples_n':sum(r['measurable_bmc_samples_n'] for r in cases),
        'measurable_axis_pairs_n':sum(r['measurable_axis_pairs_n'] for r in cases),
        'runtime_journal_status':recovered['status'],'runtime_journal_completed_frames_n':recovered['completed_frames'],
        'new_model_inference':True,'clinical_axes_verified_n':0,'numeric_biomechanical_profile_changed':False,
        'biological_validity_proven':False,'physical_unit_verified':False,'release_allowed':False,
        'limitations':['Input +/-0.02 radians is an engineering probe, not a biological admissibility or safety bound.',
            'Native parent-frame coordinate axes at flat model mean are not measured clinical/MDH flexion axes.',
            'A single BMC pair has two scalar outputs; local rank does not establish a unique three-axis anatomical inverse.',
            'Surface tips and pose blendshapes can respond beyond rigid joint-center motion; all BMC responses retained.',
            'Sample index orders independent probes, not a continuous trajectory; no speed or acceleration derived.',
            'No collision, hand-object mechanics, human comfort, final masked rendering or pool admission.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('intake','research-record','worker-root','output'):parser.add_argument('--'+n,type=Path,required=True)
    a=parser.parse_args();print(json.dumps(execute(a.intake,a.research_record,a.worker_root,a.output)))
