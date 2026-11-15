"""Private actual MANO relative-joint counterfactuals; not human-valid answers."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import time

import numpy as np

from analysis.runtime_benchmark.hidden_motion_counterfactual import perturb,DELTAS_DEGREES,MIDDLE_CANONICAL
from analysis.runtime_benchmark.mano_recorded_producer import authorize_inputs,canonicalize,RAW_PARENTS,TIP_NAMES
from analysis.runtime_benchmark.mano_anatomical_frame_probe import compose_anatomical,extract_anatomical
from analysis.runtime_benchmark.mano_model_prior_audit import extract_profile,assess
from analysis.runtime_benchmark.mano_conditioned_generator import Timings,policy_profile
from analysis.runtime_benchmark.mano_author_surface_audit import bound
from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,_private


def execute(source,source_record,guarded,guarded_record,intake,research_record,loss_source,worker_root,output):
    source,source_record,sbefore=bound(source,source_record);guarded,guarded_record,gbefore=bound(guarded,guarded_record)
    authorize_inputs(intake,research_record);output=_private(output)
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (source,source_record,guarded,guarded_record)):
        raise ValueError('Fresh output outside immutable parent/evidence roots required')
    ss=json.loads((source/'summary.json').read_text());gs=json.loads((guarded/'summary.json').read_text())
    parents=list(dict.fromkeys(c['case'] for c in gs['cases'] if c['H264_rendition_created']))
    if (ss.get('primitive_profile')!='non_target_cues_open_preflex20' or gs['protection_mode']!='author_region_union'
            or len(parents)!=8 or gs['H264_rendition_videos_n']!=16 or gs['release_allowed'] is not False):
        raise ValueError('Exactly eight current technical parent motions/sixteen views required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from experiments.motion_fixture.mesh_intersections import topology,frame as surface_frame
    from experiments.motion_fixture.biomechanical_profile import pending_profile,assess as assess_pending
    prior=extract_profile(loss_source);contract=json.loads((source/'point_contract.private.json').read_text())
    kinds=[r['point_kind'] for r in contract['canonical_points']]
    pending=pending_profile();pending.update(length_unit='model_native_units',profile_version='counterfactual_pending_limits_v1')
    journal=Journal(output/'journal',{'condition_id':'MIDDLE_RELATIVE_MOTION_COUNTERFACTUAL_SDK',
        'endpoint':'actual_native_model_alternatives_with_parent_replay_and_model_surface_QA',
        'input_exposure':'existing private research model and recorded paired-preflex parents',
        'cache_state':'sequential hand-shared model; OS/module caches uncontrolled','planned_frames':802,'timeout_seconds':900,
        'scope':'engineering relative-joint alternatives, not human-valid answers or a successful attack'})
    completed=0;cases=[];setups=[]
    try:
        import torch
        import smplx
        from smplx.vertex_ids import vertex_ids
        if str(torch.__version__)!='2.5.1+cpu' or importlib.metadata.version('smplx')!='0.1.28':
            raise ValueError('Existing exact CPU model runtime required')
        torch.set_num_threads(1);torch.manual_seed(0)
        tips={name:vertex_ids['mano'][name] for name in TIP_NAMES}
        (output/'design.private.json').write_bytes(canonical({'parent_cases':parents,'deltas_degrees':DELTAS_DEGREES,
            'changed_anatomical_components':'middle MCP/PIP/DIP bend, ratios1/.85/.55',
            'pulse':'quintic rise/fall from max(T/3,1 second) to2T/3; first second unchanged',
            'camera_mask_shape_appearance_times_and_nonmiddle_inputs_frozen':True,
            'engineering_values_not_clinical_limits':True,'new_independent_families_n':0}))
        (output/'environment.private.json').write_bytes(canonical({'torch':str(torch.__version__),
            'smplx':importlib.metadata.version('smplx'),'numpy':np.__version__,'torch_threads':torch.get_num_threads(),
            'gpu_used':False,'python':sys.version}))
        for hand in ('right','left'):
            start=time.perf_counter_ns()
            with journal.stage(hand+'_model_setup_and_parent_neutral_replay'):
                model=smplx.MANO(str(Path(intake).resolve()/'models'),is_rhand=hand=='right',use_pca=False,
                    flat_hand_mean=True,batch_size=1,dtype=torch.float32).to('cpu');model.eval()
                if tuple(model.parents.tolist())!=RAW_PARENTS:raise ValueError('Native parent contract differs')
                with np.load(source/(hand+'_fresh_neutral.private.npz'),allow_pickle=False) as old:
                    basis=old['basis'].copy();faces=old['faces'].copy();old_vertices=old['vertices'].copy();old_points=old['points'].copy()
                if not np.array_equal(model.faces,faces):raise ValueError('Native face index contract differs')
                with torch.no_grad():
                    neutral=model(hand_pose=torch.zeros(1,45),betas=torch.zeros(1,10),global_orient=torch.zeros(1,3),
                                  transl=torch.zeros(1,3),return_verts=True)
                points=canonicalize(neutral.vertices.numpy(),neutral.joints.numpy(),tips)[0]
                if not np.array_equal(neutral.vertices.numpy(),old_vertices) or not np.array_equal(points,old_points):
                    raise ValueError('Actual SDK neutral replay differs from bound parent')
                journal.frame_completed(completed,True);completed+=1;mesh=topology(faces,778)
            setups.append({'hand':hand,'wall_ns':time.perf_counter_ns()-start,'neutral_replay_exact':True})
            for parent_index,parent in enumerate(parents):
                parent_row=next(c for c in ss['cases'] if c['case']==parent)
                if parent_row['hand']!=hand:continue
                with np.load(source/parent/'native_output.private.npz',allow_pickle=False) as old:
                    old_v=old['vertices'].copy();old_raw=old['raw_joints'].copy();old_j=old['canonical_joints'].copy()
                    old_pose=old['full_pose_axis_angle'].copy();betas=old['betas'].copy();times=old['times_seconds'].copy()
                proposal=json.loads((source/parent/'proposal.private.json').read_text());angles=np.array(proposal['anatomical_euler_radians'])
                if not np.array_equal(compose_anatomical(angles,basis).astype(np.float32),old_pose[:,3:]):
                    raise ValueError('Recorded anatomical proposal no longer composes to exact native parent pose')
                applied=policy_profile(prior,hand,parent_row['policy'])
                for variant_index,delta in enumerate(DELTAS_DEGREES):
                    journal.check_budget();case_id=f'p{parent_index:02d}d{variant_index}';directory=output/case_id;directory.mkdir()
                    timer=Timings();state='INCOMPLETE'
                    try:
                        with journal.stage(case_id+'_native_counterfactual_and_QA'):
                            with timer.phase('proposal_and_compose'):
                                changed,pulse=perturb(angles,times,delta)
                                poses=old_pose[:,3:].copy() if delta==0 else compose_anatomical(changed,basis).astype(np.float32)
                                (directory/'proposal.private.json').write_bytes(canonical({'parent_case':parent,'delta_degrees':delta,
                                    'base_bgr':proposal['recipe']['base_bgr'],
                                    'times_seconds':times.tolist(),'pulse':pulse.tolist(),'anatomical_euler_radians':changed.tolist(),
                                    'corrections':[],'human_valid_answer_proven':False}))
                            with timer.phase('native_forward'):
                                with torch.no_grad():
                                    result=model(hand_pose=torch.from_numpy(poses),betas=torch.from_numpy(betas),
                                        global_orient=torch.from_numpy(old_pose[:,:3]),transl=torch.zeros(25,3),
                                        return_verts=True,return_full_pose=True)
                                vertices=result.vertices.numpy();raw=result.joints.numpy();full=result.full_pose.numpy()
                                joints=canonicalize(vertices,raw,tips)
                                if not np.array_equal(full[:,3:],poses) or not np.array_equal(full[:,:3],old_pose[:,:3]):
                                    raise ValueError('Native pose/root input changed')
                                if delta==0 and (not np.array_equal(vertices,old_v) or not np.array_equal(raw,old_raw)):
                                    raise ValueError('Zero perturbation actual SDK control does not replay parent exactly')
                                if not np.array_equal(vertices[times<=1.],old_v[times<=1.]) or not np.array_equal(raw[times<=1.],old_raw[times<=1.]):
                                    raise ValueError('Initial source motion interval changed')
                            for _ in range(25):journal.frame_completed(completed,True);completed+=1
                            with timer.phase('model_prior_pending_and_surface_QA'):
                                recovered=extract_anatomical(full[:,3:],basis);loss=assess(recovered,applied)[1]
                                source_loss=assess(recovered,prior)[1]
                                surfaces=[surface_frame(v,mesh) for v in vertices]
                                pending_result=assess_pending(joints,times,pending,handedness=hand,
                                    length_unit='model_native_units',point_kinds=kinds)
                                (directory/'surface_QA.private.json').write_bytes(canonical(surfaces))
                                (directory/'pending_assessment.private.json').write_bytes(canonical(pending_result))
                            with timer.phase('native_output_store'):
                                np.savez_compressed(directory/'native_output.private.npz',vertices=vertices,raw_joints=raw,
                                    canonical_joints=joints,full_pose_axis_angle=full,betas=betas,times_seconds=times,faces=faces)
                            state='COMPLETED'
                    finally:
                        timing=timer.snapshot(None,state)
                        timing.update(boundary='counterfactual proposal/SDK/model-surface-pending QA/store; no video produced',
                                      kind='native_coordinate_generation',shared_model_setup_included=False)
                        (directory/'timing.private.json').write_bytes(canonical(timing))
                    surface_n=sum(bool(r['pair_ids'].get('intersects')) for r in surfaces)
                    bad_surface=sum(r['state']=='UNMEASURABLE_DEGENERATE_TRIANGLES' for r in surfaces)
                    row={'case_id':case_id,'parent_case':parent,'hand':hand,'policy':parent_row['policy'],'delta_degrees':delta,
                        'frames_n':25,'control_parent_native_replay_exact':True if delta==0 else None,
                        'policy_penalized_frames_n':int(np.any(loss>0,axis=(1,2)).sum()),
                        'original_author_penalized_frames_n':int(np.any(source_loss>0,axis=(1,2)).sum()),
                        'surface_indicator_frames_n':surface_n,'surface_unmeasurable_frames_n':bad_surface,
                        'hidden_middle_point_max_displacement_native_units':float(np.linalg.norm(joints[:,MIDDLE_CANONICAL]-old_j[:,MIDDLE_CANONICAL],axis=2).max()),
                        'anatomical_bend_input_max_difference_degrees':float(np.rad2deg(np.abs(changed-angles).max())),
                        'native_root_joint_max_displacement_native_units':float(np.linalg.norm(raw[:,0]-old_raw[:,0],axis=1).max()),
                        'nonmiddle_anatomical_inputs_changed':False,'global_root_pose_changed':False,'shape_and_times_changed':False,
                        'initial_second_native_replay_exact':True,
                        'model_surface_eligible_for_display_comparison':not loss.any() and not surface_n and not bad_surface,
                        'pending_BMC_state':pending_result['state'],'human_valid_answer_proven':False,
                        'timing':timing,'decision':'QUARANTINED_GENERATOR_SIDE_COUNTERFACTUAL','accepted_into_pool':False,'release_allowed':False}
                    row['model_surface_eligible_for_display_comparison']=bool(row['model_surface_eligible_for_display_comparison'])
                    (directory/'decision.private.json').write_bytes(canonical(row));cases.append(row)
                    print('Native counterfactuals '+str(len(cases))+'/32',flush=True)
            del model
        authorize_inputs(intake,research_record)
        if verify(source_record)!=sbefore or verify(guarded_record)!=gbefore:raise ValueError('Parent evidence changed')
        if completed!=802 or len(cases)!=32:raise ValueError('Counterfactual sample denominator differs')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');checked=verify_bundle(output/'journal_bundle.private.zip')
    summary={'version':'relative_middle_counterfactual_native_v1','cases':cases,'cases_n':len(cases),
        'parent_motions_n':8,'deltas_degrees':DELTAS_DEGREES,'native_forward_frames_n':completed,'shared_hand_setup':setups,
        'journal_status':checked['status'],'new_model_inference':True,'new_video_created':False,
        'new_independent_families_n':0,'human_valid_answers_proven':False,'accepted_into_pool_n':0,'release_allowed':False}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','guarded','guarded-record','intake','research-record','loss-source','worker-root','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(execute(a.source,a.source_record,a.guarded,a.guarded_record,a.intake,a.research_record,a.loss_source,a.worker_root,a.output)))
