"""Controlled private MANO replay with raw SDK output and typed point records.

Uses the previously user-provided research model and installed CPU runtime.
No learned/admissible motion limits or anatomical/operating approval supplied.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np

from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from validation_v03.run_manifest import snapshot_file
from validation_v03.session_artifacts import canonical,decode,_private,_read

VERSION='recorded_mano_native_replay_v1'
ORDER=(0,13,14,15,16,1,2,3,17,4,5,6,18,10,11,12,19,7,8,9,20)
RAW_PARENTS=(-1,0,1,2,0,4,5,0,7,8,0,10,11,0,13,14)
TIP_NAMES=('thumb','index','middle','ring','pinky')


def canonicalize(vertices,raw_joints,tip_ids):
    if vertices.ndim!=3 or vertices.shape[1:]!=(778,3) or raw_joints.shape!=(len(vertices),16,3):
        raise ValueError('Explicit 778-vertex/16-native-joint SDK topology required')
    if not np.isfinite(vertices).all() or not np.isfinite(raw_joints).all():raise ValueError('Finite native output required')
    if set(tip_ids)!=set(TIP_NAMES) or any(type(v) is not int or not 0<=v<778 for v in tip_ids.values()) or len(set(tip_ids.values()))!=5:
        raise ValueError('Five unique named surface tips required')
    extended=np.concatenate((raw_joints,vertices[:,[tip_ids[n] for n in TIP_NAMES],:]),axis=1)
    return extended[:,ORDER,:]


def point_contract(names,tip_ids):
    if len(names)!=21 or len(set(names))!=21:raise ValueError('Explicit 21 unique canonical labels required')
    result=[]
    for name,index in zip(names,ORDER):
        result.append({'name':name,'point_kind':'sdk_joint' if index<16 else 'mesh_surface_tip',
                       'native_joint_index':index if index<16 else None,
                       'mesh_vertex_index':None if index<16 else tip_ids[TIP_NAMES[index-16]]})
    return {'version':VERSION,'length_unit':'model_native_units','physical_SI_unit_verified':False,
            'canonical_points':result,'native_parent_contract':list(RAW_PARENTS),
            'interpretation':'Explicit producer mapping, not independent human anatomical annotation.',
            'fixed_all_20_bone_policy_applicable':False,'release_allowed':False}


def authorize_inputs(intake,research_record):
    intake=Path(intake).resolve(strict=True);packet=decode(_read(intake/'asset_manifest.json'))
    scope=decode(_read(research_record))
    if packet.get('state')!='FILES_STAGED_NOT_LOADED' or packet.get('release_allowed') is not False:
        raise ValueError('Explicit original staged private model required')
    if (scope.get('purpose')!='private_noncommercial_scientific_research' or scope.get('operating_or_commercial_clearance') is not False
            or scope.get('basis')!='prior_user_provided_model_and_continuing_private_research_task'
            or scope.get('intake_manifest_sha256')!=snapshot_file(intake/'asset_manifest.json')['sha256']):
        raise ValueError('Recorded continuing private research scope required')
    evidence=scope.get('existing_session_evidence')
    if not isinstance(evidence,list) or not evidence:raise ValueError('Prior session scope evidence required')
    for row in evidence:
        if snapshot_file(row['path'])['sha256']!=row['sha256']:raise ValueError('Research scope evidence changed')
    rows={}
    for name in ('MANO_LEFT.pkl','MANO_RIGHT.pkl','LICENSE.txt','info.txt'):
        entries=[r for r in packet['files'] if r['filename']==name]
        if len(entries)!=1:raise ValueError('Unique original model/license/info entries required')
        path=intake/'models'/name;actual=snapshot_file(path)
        if any(actual[k]!=entries[0][k] for k in ('bytes','sha256')):raise ValueError('Staged original input changed')
        rows[name]=actual
    return rows


def camera(vertices,joints):
    v=np.asarray(vertices,float);j=np.asarray(joints,float)
    y=j[0,9]-j[0,0];norm=np.linalg.norm(y)
    if norm<=1e-10:raise ValueError('Degenerate camera root axis')
    y/=norm;x=j[0,17]-j[0,5];x-=np.dot(x,y)*y;norm=np.linalg.norm(x)
    if norm<=1e-10:raise ValueError('Degenerate camera palm axis')
    x/=norm;normal=np.cross(x,y);basis=np.column_stack((x,y))
    flat=v@basis;lo=flat.min(axis=(0,1));hi=flat.max(axis=(0,1));extent=hi-lo
    if (extent<=1e-10).any():raise ValueError('Degenerate projected model extent')
    scale=float(min(442/extent[0],350/extent[1]));center=(lo+hi)/2
    def project(points):
        a=(np.asarray(points,float)@basis-center)*scale;a[...,0]+=256;a[...,1]=210-a[...,1];return a
    metadata={'projection':'fixed_orthographic','width':512,'height':420,'border_pixels':35,
              'basis_columns':basis.tolist(),'normal':normal.tolist(),'center':center.tolist(),
              'pixels_per_model_native_unit':scale,'physical_camera_calibrated':False}
    return project(vertices),project(joints),v@normal,normal,metadata


def execute(intake,research_record,worker_root,legacy_root,output):
    sources=authorize_inputs(intake,research_record)
    output=_private(output)
    if output.exists():raise FileExistsError('New private producer directory required')
    worker_root=Path(worker_root).resolve(strict=True);legacy_root=Path(legacy_root).resolve(strict=True)
    sys.path.insert(0,str(worker_root))
    from dataset_pipeline.common import LANDMARK_NAMES
    from experiments.motion_fixture.biomechanical_features import extract,GeometryError
    from experiments.motion_fixture.accept_mano_pilot import load_bound_pilot,verify_pilot
    journal=Journal(output/'journal',{'condition_id':'MANO_CONTROLLED_NATIVE_REPLAY_20261114',
        'endpoint':'cpu_native_mano_forward_render_and_stored_reference_comparison',
        'input_exposure':'previously used user-provided MANO model; deterministic legacy replay',
        'cache_state':'CPU OS/module cache uncontrolled','planned_frames':48,'timeout_seconds':300,
        'scope':'model_output_and_render_availability_not_camera_or_human_measurement'})
    cases=[]
    try:
        with journal.stage('verify_cpu_runtime_and_sources_before_load'):
            import torch
            import smplx
            from smplx.vertex_ids import vertex_ids
            if str(torch.__version__)!='2.5.1+cpu' or importlib.metadata.version('smplx')!='0.1.28':
                raise ValueError('Use the existing explicit torch CPU/SMPL-X runtime')
            torch.set_num_threads(1);torch.manual_seed(0)
            for row in sources.values():
                if snapshot_file(row['path'])!=row:raise ValueError('Source changed before model loading')
            tips={name:vertex_ids['mano'][name] for name in TIP_NAMES}
            contract=point_contract(LANDMARK_NAMES,tips)
            (output/'point_contract.private.json').write_bytes(canonical(contract))
        for hand in ('right','left'):
            case=output/(hand+'_flat_pc1');case.mkdir()
            with journal.stage(hand+'_cpu_native_forward'):
                model=smplx.MANO(str(Path(intake).resolve()/'models'),is_rhand=hand=='right',
                    use_pca=True,num_pca_comps=6,flat_hand_mean=True,batch_size=24,dtype=torch.float32).to('cpu')
                model.eval();parents=model.parents.detach().cpu().numpy()
                if tuple(parents.tolist())!=RAW_PARENTS:raise ValueError('SDK native parent table differs from declared contract')
                phase=torch.linspace(0,2*np.pi,24);pose=torch.zeros(24,6);pose[:,1]=.8*(1-torch.cos(phase))/2
                with torch.no_grad():result=model(hand_pose=pose,return_verts=True,return_full_pose=True)
                vertices=result.vertices.detach().cpu().numpy();raw=result.joints.detach().cpu().numpy()
                full_pose=result.full_pose.detach().cpu().numpy();joints=canonicalize(vertices,raw,tips)
                faces=model.faces.astype(np.int32)
                if full_pose.shape!=(24,48) or faces.shape!=(1538,3) or faces.min()<0 or faces.max()>=778 or not np.isfinite(full_pose).all():
                    raise ValueError('Full native pose and surface topology required')
                np.savez_compressed(case/'native_sdk_output.private.npz',vertices=vertices,raw_joints=raw,
                    canonical_joints=joints,faces=faces,pose_coefficients=pose.numpy(),full_pose_axis_angle=full_pose,parents=parents)
                mesh_xy,joint_xy,depth,normal,cam=camera(vertices,joints)
                (case/'camera.private.json').write_bytes(canonical(cam))
            with journal.stage(hand+'_legacy_geometry_comparison'):
                pilot=legacy_root/(hand+'_pc1')/'supervised/worker_journal'
                old_report,old_reference,binding=load_bound_pilot(pilot)
                if old_report['hand']!=hand or old_report.get('flat_hand_mean') is not True or old_report['component']!=1:
                    raise ValueError('Explicit matching legacy flat/hand/component required')
                with np.load(pilot/'private_surface.npz',allow_pickle=False) as old:
                    equality={'vertices_equal':bool(np.array_equal(vertices,old['vertices'])),
                              'canonical_joints_equal':bool(np.array_equal(joints,old['joints'])),
                              'pose_coefficients_equal':bool(np.array_equal(pose.numpy(),old['pose']))}
                verify_pilot(pilot,old_report,binding)
            with journal.stage(hand+'_private_render_decode_and_features'):
                import cv2
                source=case/'source.private.avi';writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'FFV1'),12.,(512,420))
                try:
                    if not writer.isOpened():raise ValueError('Lossless writer unavailable')
                    for index in range(24):
                        journal.check_budget();image=np.full((420,512,3),(40,32,24),np.uint8)
                        triangles=vertices[index,faces].astype(float)
                        ns=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
                        shade=np.abs(ns@normal)/np.maximum(np.linalg.norm(ns,axis=1),1e-12)
                        for f in np.argsort(depth[index,faces].mean(axis=1)):
                            color=tuple(int(v*(.55+.45*shade[f])) for v in (170,205,225))
                            cv2.fillConvexPoly(image,np.rint(mesh_xy[index,faces[f]]).astype(np.int32),color,cv2.LINE_AA)
                        cv2.putText(image,'MANO / CONTROLLED REPLAY / RESEARCH ONLY',(12,22),cv2.FONT_HERSHEY_SIMPLEX,.40,(220,220,220),1,cv2.LINE_AA)
                        writer.write(image)
                        if index==12:
                            ok,png=cv2.imencode('.png',image)
                            if not ok:raise ValueError('Preview encoding failed')
                            (case/'preview.private.png').write_bytes(png.tobytes())
                finally:writer.release()
                cap=cv2.VideoCapture(str(source));frames=[];measured=0;errors=[]
                try:
                    for index in range(24):
                        ok,image=cap.read()
                        if not ok or image.shape[:2]!=(420,512):raise ValueError('Rendered sequence incomplete')
                        timestamp=float(cap.get(cv2.CAP_PROP_POS_MSEC))
                        if abs(timestamp-index*1000/12)>.01:raise ValueError('Rendered source timestamp mismatch')
                        frames.append({'frame_idx':index,'source_pts_ms':timestamp,'detected':True,
                            'detection_semantics':'model_reference_available_no_detector',
                            'authored_handedness':hand,'origin_type':'controlled_mano_sdk_output',
                            'landmarks_world':{n:dict(zip(('x','y','z'),p.tolist())) for n,p in zip(LANDMARK_NAMES,joints[index])},
                            'landmarks_px':{n:{'x':float(v[0]),'y':float(v[1]),'z':float(p[2])} for n,v,p in zip(LANDMARK_NAMES,joint_xy[index],joints[index])}})
                        try:extract(joints[index],handedness=hand);measured+=1
                        except GeometryError as error:errors.append(error.code)
                        journal.frame_completed(index+(0 if hand=='right' else 24),True)
                    if cap.read()[0]:raise ValueError('Extra source video frame')
                finally:cap.release()
                (case/'reference.private.json').write_bytes(canonical({'frames':frames,
                    'source_info':{'width':512,'height':420,'fps':12,'total_frames':24},
                    'length_unit':'model_native_units','landmarks_px_z_semantics':'unprojected model-native z, not pixel or metric camera depth'}))
                row={'producer_version':VERSION,'state':'PRIVATE_MODEL_NATIVE_REPLAY_NOT_BIO_APPROVED',
                    'hand':hand,'flat_hand_mean':True,'component':1,'amplitude':.8,
                    'parameter_scope':'legacy engineering replay, not a biological admissible range',
                    'random_motion_sampled':False,'frames_n':24,'native_sdk_joint_count':16,'canonical_point_count':21,
                    'raw_sdk_and_full_pose_saved':True,'source_video':snapshot_file(source),
                    'legacy_geometry_comparison':equality,'measurable_feature_frames_n':measured,'feature_errors':errors,
                    'model_source':sources['MANO_'+hand.upper()+'.pkl'],
                    'physical_unit_verified':False,'biological_validity_proven':False,'release_allowed':False,
                    'rendering':'orthographic triangle painter, not exact per-pixel visibility or calibrated camera'}
                (case/'report.private.json').write_bytes(canonical(row));cases.append(row)
            del model,result
        with journal.stage('recheck_source_inputs'):
            authorize_inputs(intake,research_record)
            for row in sources.values():
                if snapshot_file(row['path'])!=row:raise ValueError('Original input changed during generation')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');recovered=verify_bundle(output/'journal_bundle.private.zip')
    summary={'scope':'new_controlled_cpu_mano_replay_with_raw_sdk_point_contract_not_random_or_bio_validation',
        'producer_version':VERSION,'cases_n':len(cases),'new_model_forward_frames_n':48,
        'rendered_decoded_frames_n':sum(r['frames_n'] for r in cases),
        'raw_sdk_joint_count':16,'canonical_point_count':21,'raw_sdk_and_full_pose_saved_cases_n':len(cases),
        'exact_legacy_vertices_reproduced_cases_n':sum(r['legacy_geometry_comparison']['vertices_equal'] for r in cases),
        'exact_legacy_canonical_joints_reproduced_cases_n':sum(r['legacy_geometry_comparison']['canonical_joints_equal'] for r in cases),
        'exact_legacy_pose_coefficients_reproduced_cases_n':sum(r['legacy_geometry_comparison']['pose_coefficients_equal'] for r in cases),
        'measurable_feature_frames_n':sum(r['measurable_feature_frames_n'] for r in cases),
        'runtime_journal_status':recovered['status'],'runtime_journal_completed_frames_n':recovered['completed_frames'],
        'runtime_versions':{n:importlib.metadata.version(n) for n in ('torch','smplx','numpy','opencv-contrib-python')},
        'new_model_inference':True,'random_motion_sampled':False,'new_independent_families_n':0,
        'physical_unit_verified':False,'biological_validity_proven':False,'full_generator_ready':False,'release_allowed':False,
        'limitations':['Current producer is recorded; this does not recover historical worker source bytes.',
            'Native SDK index and named surface-tip contract is explicit, not independent human annotation.',
            'Model-native units and biological/static/temporal admissible limits remain unresolved.',
            'No anatomical mesh collision, object dynamics, human/attack study or operating clearance.',
            'Private research only; original intake/license snapshots and model files are preserved.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('intake','research-record','worker-root','legacy-root','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(execute(a.intake,a.research_record,a.worker_root,a.legacy_root,a.output)))
