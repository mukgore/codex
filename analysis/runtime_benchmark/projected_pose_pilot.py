"""TF-02P: deterministic model-box projection of saved PCA proposals, not humans."""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time

import numpy as np

from analysis.runtime_benchmark.mano_author_surface_audit import bound
from analysis.runtime_benchmark.mano_recorded_producer import authorize_inputs,canonicalize,RAW_PARENTS,TIP_NAMES
from analysis.runtime_benchmark.mano_anatomical_frame_probe import template_basis,compose_anatomical,extract_anatomical
from analysis.runtime_benchmark.mano_model_prior_audit import extract_profile,assess
from analysis.runtime_benchmark.template_free_pose import decide
from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,_private

VERSION='saved_pca_model_box_projected_static_pose_v1'


def project(angles,profile):
    value=np.asarray(angles,float)
    if value.shape!=(1,15,3) or not np.isfinite(value).all():raise ValueError('Complete finite static anatomical angles required')
    lower=np.empty((15,3));upper=lower.copy();covered=[]
    for group,ids in profile['native_joint_groups'].items():
        intervals=np.asarray(profile['intervals_degrees'][group],float)
        if intervals.shape!=(3,2) or not np.isfinite(intervals).all() or (intervals[:,0]>intervals[:,1]).any():
            raise ValueError('Finite ordered three-axis model intervals required')
        for joint in ids:
            if type(joint) is not int or not 1<=joint<=15:raise ValueError('Explicit nonroot joint required')
            covered.append(joint);lower[joint-1]=np.deg2rad(intervals[:,0]);upper[joint-1]=np.deg2rad(intervals[:,1])
    if sorted(covered)!=list(range(1,16)):raise ValueError('Each nonroot joint must be covered exactly once')
    corrected=np.clip(value,lower[None],upper[None]);delta=corrected-value
    return corrected,{'changed_axis_components_n':int(np.count_nonzero(delta)),
      'max_absolute_correction_degrees':float(np.rad2deg(np.abs(delta).max())),
      'l2_correction_degrees':float(np.linalg.norm(np.rad2deg(delta))),
      'lower_radians':lower.tolist(),'upper_radians':upper.tolist()}


def execute(source,source_record,intake,research_record,loss_source,worker_root,output):
    source,source_record,before=bound(source,source_record);authorize_inputs(intake,research_record)
    output=_private(output)
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (source,source_record)):
        raise ValueError('Fresh independent output required')
    parent=json.loads((source/'summary.json').read_text());original=[r for r in parent['cases'] if r['arm']=='B']
    if len(original)!=32 or parent['version']!='tf02_static_pca6_sigma05_v1' or parent['release_allowed'] is not False:
        raise ValueError('Bound complete32 original PCA proposals required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from experiments.motion_fixture.mesh_intersections import topology,frame as surface_frame
    from experiments.motion_fixture.biomechanical_features import extract as bmc_extract,GeometryError
    prior=extract_profile(loss_source)
    journal=Journal(output/'journal',{'condition_id':'TF02P_SAVED_PCA_MODEL_BOX_PROJECTION',
      'endpoint':'static_corrected_poses_actual_model_surface_and_duplicate_audit',
      'input_exposure':'previously recorded private PCA proposals; no new random draw or action primitive',
      'cache_state':'shared CPU models; OS/module caches uncontrolled','planned_frames':34,'timeout_seconds':600,
      'scope':'model-space modification only; no human/clinical/motion/render/release validation'})
    count=0;cases=[];payloads={};private_groups={};setups=[]
    wall=time.perf_counter_ns();cpu=time.process_time_ns();utc=time.time_ns()
    try:
        import torch
        import smplx
        from smplx.vertex_ids import vertex_ids
        if str(torch.__version__)!='2.5.1+cpu' or importlib.metadata.version('smplx')!='0.1.28':
            raise ValueError('Existing exact CPU runtime required')
        torch.set_num_threads(1);torch.manual_seed(0)
        tips={n:vertex_ids['mano'][n] for n in TIP_NAMES}
        (output/'applied_model_prior.private.json').write_bytes(canonical(prior))
        (output/'environment.private.json').write_bytes(canonical({'torch':str(torch.__version__),
          'smplx':importlib.metadata.version('smplx'),'numpy':np.__version__,'python':sys.version,'gpu_used':False,'torch_threads':1}))

        def forward(model,pose):
            nonlocal count
            journal.check_budget()
            with torch.no_grad():
                value=model(hand_pose=torch.from_numpy(pose),betas=torch.zeros(1,10),global_orient=torch.zeros(1,3),
                  transl=torch.zeros(1,3),return_verts=True,return_full_pose=True)
            result={k:getattr(value,k).numpy().copy() for k in ('vertices','joints','full_pose')}
            if any(not np.isfinite(v).all() for v in result.values()):raise ValueError('Nonfinite actual SDK output')
            journal.frame_completed(count,True);count+=1
            return result

        with (output/'attempts.private.jsonl').open('xb',buffering=0) as log:
            for hand in ('right','left'):
                start=time.perf_counter_ns()
                with journal.stage(hand+'_setup_and_neutral_basis'):
                    model=smplx.MANO(str(Path(intake).resolve()/'models'),is_rhand=hand=='right',use_pca=False,
                      flat_hand_mean=True,batch_size=1,dtype=torch.float32).to('cpu').eval()
                    if tuple(model.parents.tolist())!=RAW_PARENTS:raise ValueError('Parent indices differ')
                    neutral=forward(model,np.zeros((1,45),np.float32))
                    with np.load(source/(hand+'_representation.private.npz'),allow_pickle=False) as saved:
                        basis=saved['basis'].copy();faces=saved['faces'].copy()
                    points=canonicalize(neutral['vertices'],neutral['joints'],tips)[0]
                    if np.max(np.abs(template_basis(points,hand)-basis))>1e-6 or not np.array_equal(model.faces,faces):
                        raise ValueError('Bound basis/topology differs')
                    mesh=topology(faces,778)
                    np.savez_compressed(output/(hand+'_setup.private.npz'),basis=basis,faces=faces,**neutral)
                setups.append({'hand':hand,'wall_ns':time.perf_counter_ns()-start})
                for parent_row in (r for r in original if r['hand']==hand):
                    case_id='P_'+parent_row['case_id'];directory=output/case_id;directory.mkdir()
                    start=time.perf_counter_ns();pcpu=time.process_time_ns();case_utc=time.time_ns()
                    with journal.stage(case_id+'_project_actual_forward_and_QA'):
                        with np.load(source/parent_row['case_id']/'native_output.private.npz',allow_pickle=False) as saved:
                            old_pose=saved['full_pose'].copy();coefficients=saved['coefficients'].copy()
                        original_angles=extract_anatomical(old_pose[:,3:],basis)
                        corrected,correction=project(original_angles,prior)
                        pose=compose_anatomical(corrected,basis).astype(np.float32)
                        log.write(canonical({'event':'PROJECTED','case_id':case_id,'source_case_id':parent_row['case_id'],
                          'correction':correction})+b'\n')
                        result=forward(model,pose)
                        if not np.array_equal(result['full_pose'][:,3:],pose) or result['full_pose'][:,:3].any():
                            raise ValueError('Actual root/nonroot pose differs')
                        recovered=extract_anatomical(result['full_pose'][:,3:],basis)
                        roundtrip=float(np.max(np.abs(compose_anatomical(recovered,basis)-pose)))
                        if roundtrip>1e-6:raise ValueError('Anatomical roundtrip differs')
                        strict,effective=assess(recovered,prior);surface=surface_frame(result['vertices'][0],mesh)
                        verdict=decide(effective,surface);canonical_points=canonicalize(result['vertices'],result['joints'],tips)
                        geometry_error=None
                        try:
                            features=bmc_extract(canonical_points[0],handedness=hand)
                            np.savez_compressed(directory/'bmc_features.private.npz',**{k:v for k,v in features.items() if isinstance(v,np.ndarray)})
                        except GeometryError as error:geometry_error=error.code
                        payload=result['vertices'].tobytes()+result['joints'].tobytes()
                        key=hashlib.sha256(payload).hexdigest()
                        if key in payloads and payloads[key]!=payload:raise ValueError('Hash bucket payload mismatch')
                        payloads.setdefault(key,payload);private_groups.setdefault(key,[]).append(case_id)
                        np.savez_compressed(directory/'native_output.private.npz',**result,canonical_points=canonical_points,
                          original_full_pose=old_pose,coefficients=coefficients,original_angles=original_angles,
                          projected_angles=corrected,recovered_angles=recovered,strict_excess_radians=strict,masked_excess_radians=effective)
                        (directory/'surface_QA.private.json').write_bytes(canonical(surface))
                    row={'case_id':case_id,'parent_case_id':parent_row['case_id'],'hand':hand,
                      'surface_state':surface['state'],
                      'seed':parent_row['seed'],'attempt':parent_row['attempt'],**correction,**verdict,
                      'strict_excess_components_n':int(np.count_nonzero(strict)),
                      'masked_excess_components_n':int(np.count_nonzero(effective)),
                      'bmc_geometry_error':geometry_error,'roundtrip_max_absolute_error':roundtrip,
                      'exact_neutral_geometry':np.array_equal(result['vertices'],neutral['vertices']) and np.array_equal(result['joints'],neutral['joints']),
                      'timing':{'started_utc_epoch_ns':case_utc,'ended_utc_epoch_ns':time.time_ns(),
                        'wall_ns':time.perf_counter_ns()-start,'own_cpu_ns':time.process_time_ns()-pcpu}}
                    (directory/'decision.private.json').write_bytes(canonical(row));cases.append(row)
                    log.write(canonical({'event':'ASSESSED','case_id':case_id,'decision':row})+b'\n')
                    print('Projected saved poses '+str(len(cases))+'/32',flush=True)
                del model
        authorize_inputs(intake,research_record)
        if verify(source_record)!=before or count!=34 or len(cases)!=32:raise ValueError('Parent evidence or denominator differs')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');checked=verify_bundle(output/'journal_bundle.private.zip')
    (output/'duplicate_groups.private.json').write_bytes(canonical({'groups':private_groups}))
    (output/'cases.private.json').write_bytes(canonical({'cases':cases}))
    summary={'version':VERSION,'actual_forward_poses_n':count,'projected_proposals_n':32,
      'original_unmodified_B_model_prior_zero_n':parent['by_arm']['B']['model_prior_zero_n'],
      'model_prior_zero_n':sum(r['masked_excess_components_n']==0 for r in cases),
      'sampled_surface_clear_n':sum(r['surface_state']=='NO_TESTED_PAIR_INTERSECTION' for r in cases),
      'model_surface_eligible_n':sum(r['model_surface_eligible'] for r in cases),
      'bmc_geometry_measurable_n':sum(r['bmc_geometry_error'] is None for r in cases),
      'changed_proposals_n':sum(r['changed_axis_components_n']>0 for r in cases),
      'changed_axis_components_n':sum(r['changed_axis_components_n'] for r in cases),
      'correction_max_degrees':max(r['max_absolute_correction_degrees'] for r in cases),
      'correction_l2_degrees_min':min(r['l2_correction_degrees'] for r in cases),
      'correction_l2_degrees_max':max(r['l2_correction_degrees'] for r in cases),
      'unique_actual_geometry_payloads_n':len(payloads),'exact_neutral_geometry_n':sum(r['exact_neutral_geometry'] for r in cases),
      'rejection_reason_counts':dict(Counter(x for r in cases for x in r['rejection_reasons'])),
      'shared_setups':setups,'journal_status':checked['status'],'release_allowed':False,'accepted_into_pool_n':0,
      'pending_BMC_state':'UNRESOLVED_LIMITS','new_random_draws_n':0,'new_motion_sequences_n':0,'new_videos_n':0,
      'human_trials_n':0,'new_independent_families_n':0,
      'timing':{'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),'wall_ns':time.perf_counter_ns()-wall,
        'own_cpu_ns':time.process_time_ns()-cpu,'scope':'setup through actual projection SDK/QA/store/parent recheck; recorder snapshot/seal excluded'}}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','intake','research-record','loss-source','worker-root','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(execute(a.source,a.source_record,a.intake,a.research_record,a.loss_source,a.worker_root,a.output)))
