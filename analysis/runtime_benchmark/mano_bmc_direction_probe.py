"""Forward checks along BMC-derived geometric axes; no clinical calibration.

Neutral geometry-derived axes, two engineering step sizes, and a left-hand
reflection-sign control. Native rigid child joints and mesh tips are separated.
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
from analysis.runtime_benchmark.mano_axis_probe import pair_delta
from validation_v03.run_manifest import snapshot_file
from validation_v03.session_artifacts import canonical,_private

VERSION='mano_bmc_neutral_geometric_direction_probe_v1'
STEPS=(.01,.03)


def geometric_axes(frames,angles):
    frames=np.asarray(frames,float);angles=np.asarray(angles,float)
    if frames.shape!=(15,3,3) or angles.shape!=(15,2) or not np.isfinite(frames).all() or not np.isfinite(angles).all():
        raise ValueError('Complete finite BMC neutral frames/angles required')
    axes=[]
    for frame,(f,a) in zip(frames,angles):
        if not np.allclose(frame.T@frame,np.eye(3),atol=1e-9,rtol=0) or np.linalg.det(frame)<0:
            raise ValueError('Proper column rotation frame required')
        cf,sf,ca,sa=np.cos(f),np.sin(f),np.cos(a),np.sin(a)
        # Ry(f) Rx(-a) z. Abduction axis is -Ry(f)x, not simply -x.
        axes.append([frame[:,1],-frame@np.array([cf,0.,-sf]),frame@np.array([sf*ca,sa,cf*ca])])
    return np.asarray(axes)


def native_axial_axes(canonical_axes,hand,*,incorrect_polar_control=False):
    axes=np.asarray(canonical_axes,float)
    if axes.shape!=(15,3,3) or not np.isfinite(axes).all() or not np.allclose(np.linalg.norm(axes,axis=2),1.,atol=1e-9):
        raise ValueError('Fifteen sets of unit geometric axes required')
    if hand not in ('right','left'):raise ValueError('Explicit hand required')
    if incorrect_polar_control and hand!='left':raise ValueError('Polar sign control is specifically for left reflection')
    if hand=='right':return axes.copy()
    reflection=np.array([-1.,1.,1.])
    return axes*reflection*(1. if incorrect_polar_control else -1.)


def build_design(axes,angle_native,hand):
    axes=native_axial_axes(axes,hand);poses=[np.zeros(45,np.float32)]
    rows=[{'frame_idx':0,'kind':'neutral_repeat'}]
    for step in STEPS:
        for angle in range(15):
            native=angle_native[angle]
            if type(native) is not int or not 1<=native<16:raise ValueError('Explicit native center mapping required')
            for direction,name in enumerate(('flexion','abduction','outgoing_twist')):
                for sign in (-1,1):
                    pose=np.zeros(45,np.float32);pose[(native-1)*3:native*3]=axes[angle,direction]*step*sign
                    rows.append({'frame_idx':len(poses),'kind':'geometric_direction','angle_index':angle,
                        'native_joint_index':native,'direction':name,'sign':sign,'step_radians':step});poses.append(pose)
    if hand=='left':
        for angle in range(15):
            native=angle_native[angle]
            for direction,name in enumerate(('flexion','abduction','outgoing_twist')):
                pose=np.zeros(45,np.float32);pose[(native-1)*3:native*3]=-axes[angle,direction]*STEPS[-1]
                rows.append({'frame_idx':len(poses),'kind':'incorrect_polar_sign_control','angle_index':angle,
                    'native_joint_index':native,'direction':name,'sign':1,'step_radians':STEPS[-1]});poses.append(pose)
    return np.array(poses),rows


def expected_target_change(row):
    result=np.zeros(2)
    if row['direction']=='flexion':result[0]=row['sign']*row['step_radians']
    if row['direction']=='abduction':result[1]=row['sign']*row['step_radians']
    return result


def execute(intake,research_record,worker_root,output):
    sources=authorize_inputs(intake,research_record);output=_private(output)
    if output.exists():raise FileExistsError('Fresh private forward diagnostic required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from dataset_pipeline.common import LANDMARK_NAMES
    from experiments.motion_fixture.biomechanical_features import extract,GeometryError,ANGLE_RECORDS
    angle_native=[ORDER[LANDMARK_NAMES.index(r['canonical_center_point'])] for r in ANGLE_RECORDS]
    kinds=['mesh_surface_tip' if r['outgoing_bone_child_point'].endswith('_TIP') else 'native_child_joint' for r in ANGLE_RECORDS]
    journal=Journal(output/'journal',{'condition_id':'G03_MANO_BMC_GEOMETRIC_DIRECTIONS',
        'endpoint':'neutral_geometry_derived_direction_forward_check','input_exposure':'existing private research model',
        'cache_state':'CPU OS/module cache uncontrolled','planned_frames':409,'timeout_seconds':300,
        'scope':'two neutral constructions plus407 independent probe/repeat samples; not motion/human/clinical limits'})
    cases=[];counter=0
    try:
        with journal.stage('runtime_and_source_before_load'):
            import torch
            import smplx
            from smplx.vertex_ids import vertex_ids
            if str(torch.__version__)!='2.5.1+cpu' or importlib.metadata.version('smplx')!='0.1.28':raise ValueError('Existing CPU runtime required')
            torch.set_num_threads(1);torch.manual_seed(0);tips={n:vertex_ids['mano'][n] for n in TIP_NAMES}
            (output/'point_contract.private.json').write_bytes(canonical(point_contract(LANDMARK_NAMES,tips)))
        for hand in ('right','left'):
            case=output/hand;case.mkdir()
            with journal.stage(hand+'_neutral_geometry_and_axes'):
                authorize_inputs(intake,research_record)
                model=smplx.MANO(str(Path(intake).resolve()/'models'),is_rhand=hand=='right',use_pca=False,
                    flat_hand_mean=True,batch_size=1,dtype=torch.float32).to('cpu');model.eval()
                if tuple(model.parents.tolist())!=RAW_PARENTS:raise ValueError('Native parent table changed')
                with torch.no_grad():neutral_result=model(hand_pose=torch.zeros(1,45),return_verts=True,return_full_pose=True)
                neutral=canonicalize(neutral_result.vertices.numpy(),neutral_result.joints.numpy(),tips)[0]
                features=extract(neutral,handedness=hand)
                axes=geometric_axes(features['local_frames'],features['joint_angles_radians'])
                poses,rows=build_design(axes,angle_native,hand)
                journal.frame_completed(counter,True);counter+=1
                (case/'design.private.json').write_bytes(canonical({'rows':rows,'angle_native_mapping':angle_native,
                    'canonical_geometric_axes':axes.tolist(),'native_axial_axes':native_axial_axes(axes,hand).tolist(),
                    'steps_are_engineering_not_biological_bounds':True,'sample_order_is_not_time':True}))
            with journal.stage(hand+'_batch_forward'):
                # MANO.forward concatenates root and hand pose directly; supply
                # explicit matching batches rather than assuming root expansion.
                with torch.no_grad():result=model(hand_pose=torch.from_numpy(poses),
                    betas=model.betas.expand(len(poses),-1),global_orient=torch.zeros(len(poses),3),
                    transl=torch.zeros(len(poses),3),return_verts=True,return_full_pose=True)
                points=canonicalize(result.vertices.numpy(),result.joints.numpy(),tips)
                if not np.array_equal(result.full_pose.numpy()[:,3:],poses) or np.any(result.full_pose.numpy()[:,:3]):
                    raise ValueError('Explicit axis-angle/root input contract changed')
                neutral_error=float(np.abs(points[0].astype(float)-neutral).max())
                neutral_tolerance=max(1e-10,float(np.linalg.norm(np.ptp(neutral,axis=0)))*64*np.finfo(np.float32).eps)
                if neutral_error>neutral_tolerance:raise ValueError('Neutral repeat differs beyond float32 precision across batch shapes')
                np.savez_compressed(case/'native_output.private.npz',vertices=result.vertices.numpy(),raw_joints=result.joints.numpy(),
                    canonical_joints=points,full_pose_axis_angle=result.full_pose.numpy(),pose_axis_angle=poses,faces=model.faces)
                for frame in range(len(poses)):journal.frame_completed(counter,True);counter+=1
            with journal.stage(hand+'_bmc_direction_comparison'):
                observations=[];errors=[]
                for row,pose in zip(rows[1:],points[1:]):
                    try:changed=extract(pose,handedness=hand)['joint_angles_radians']
                    except GeometryError as error:errors.append({'frame_idx':row['frame_idx'],'code':error.code});continue
                    delta=pair_delta(changed,features['joint_angles_radians'])[row['angle_index']]
                    expected=expected_target_change(row);residual=float(np.abs(delta-expected).max())
                    observations.append({**row,'child_kind':kinds[row['angle_index']],
                        'target_change_radians':delta.tolist(),'expected_radians':expected.tolist(),'max_abs_residual_radians':residual})
                (case/'observations.private.json').write_bytes(canonical({'observations':observations,'geometry_errors':errors}))
                groups={}
                for kind in ('native_child_joint','mesh_surface_tip'):
                    selected=[r for r in observations if r['kind']=='geometric_direction' and r['child_kind']==kind]
                    groups[kind]={'samples_n':len(selected),'max_abs_residual_radians':max(r['max_abs_residual_radians'] for r in selected)}
                wrong=[r for r in observations if r['kind']=='incorrect_polar_sign_control' and r['direction']!='outgoing_twist']
                cases.append({'hand':hand,'neutral_forward_samples_n':1,'designed_forward_samples_n':len(poses),
                    'neutral_repeat_abs_error':neutral_error,'neutral_numeric_tolerance':neutral_tolerance,
                    'geometry_errors_n':len(errors),'groups':groups,'incorrect_left_polar_sign_non_twist_controls_n':len(wrong),
                    'wrong_sign_max_residual_radians':max((r['max_abs_residual_radians'] for r in wrong),default=None),
                    'clinical_axis_verified':False})
            del model,result,neutral_result
        with journal.stage('scope_and_original_inputs_recheck'):
            authorize_inputs(intake,research_record)
            for row in sources.values():
                if snapshot_file(row['path'])!=row:raise ValueError('Original model input changed')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');verified=verify_bundle(output/'journal_bundle.private.zip')
    summary={'scope':'neutral_bmc_geometric_direction_forward_check_not_clinical_calibration','version':VERSION,'cases':cases,
        'native_forward_samples_n':counter,'runtime_journal_status':verified['status'],
        'runtime_journal_completed_frames_n':verified['completed_frames'],'steps_radians':list(STEPS),
        'new_model_inference':True,'clinical_axes_verified_n':0,'numeric_profile_changed':False,'biological_validity_proven':False,
        'release_allowed':False,'limitations':['Axes are derived from neutral BMC geometry, not clinical anatomy or a measured participant.',
            'Only neutral mean shape and two local step sizes; no global pose-dependent mapping or safety range.',
            'Mesh-tip shape/skinning response is separate from native rigid child-joint behavior.',
            'Independent probes are not a temporal motion; no velocity, comfort, physics or pool admission.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('intake','research-record','worker-root','output'):parser.add_argument('--'+n,type=Path,required=True)
    a=parser.parse_args();print(json.dumps(execute(a.intake,a.research_record,a.worker_root,a.output)))
