"""TF-03 three-state paths in fixed model coordinates, not validated human motion."""
import argparse
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
from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,_private

VERSION='template_free_three_waypoint_model_path_v1'
EXPECTED={('right',7):(0,1,4),('right',19):(2,4,5),('left',7):(1,4,5),('left',19):(0,1,3)}


def path(waypoints):
    points=np.asarray(waypoints,float)
    if points.shape!=(3,15,3) or not np.isfinite(points).all():raise ValueError('Three complete finite static anatomical states required')
    times=np.linspace(0.,3.,25);result=[]
    for i,t in enumerate(times):
        if i in (0,12,24):result.append(points[i//12].copy());continue
        segment=0 if t<1.5 else 1;u=(t-1.5*segment)/1.5
        weight=6*u**5-15*u**4+10*u**3
        result.append(points[segment]+(points[segment+1]-points[segment])*weight)
    return times,np.array(result)


def derivatives(angles,times):
    value=np.asarray(angles,float);t=np.asarray(times,float)
    if value.ndim!=3 or len(value)<3 or value.shape[1:]!=(15,3) or t.shape!=(len(value),) or not np.isfinite(value).all() or not np.isfinite(t).all() or not (np.diff(t)>0).all():
        raise ValueError('Complete unwrapped Euler series with actual increasing seconds required')
    continuous=np.unwrap(value,axis=0);dt=np.diff(t)
    v=np.diff(continuous,axis=0)/dt[:,None,None]
    mid=(t[1:]+t[:-1])/2
    a=np.diff(v,axis=0)/np.diff(mid)[:,None,None]
    return v,a


def execute(source,source_record,audit,audit_record,intake,research_record,loss_source,worker_root,output):
    source=_private(source);source_record=_private(source_record)
    producer_status=verify(source_record);receipt=json.loads((source_record/'receipt.private.json').read_text())
    audit,audit_record,audit_status=bound(audit,audit_record)
    if (producer_status['state']!='PROCESS_ERROR' or receipt['artifact_roots']!=[str(source)]
            or receipt['postflight_snapshot_matched'] is not True):raise ValueError('Explicit audited failed producer required')
    original_journal=verify_bundle(source/'journal_bundle.private.zip')
    if original_journal['status']!='COMPLETED' or original_journal['completed_frames']!=34:
        raise ValueError('All static SDK outputs required before separate audit')
    audit_summary=json.loads((audit/'summary.json').read_text())
    if audit_summary['model_surface_eligible_n']!=18 or audit_summary['original_producer_state']!='PROCESS_ERROR':
        raise ValueError('Registered18 audited static candidates required')
    candidates=json.loads((audit/'cases.private.json').read_text())['cases']
    authorize_inputs(intake,research_record);output=_private(output)
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (source,source_record,audit,audit_record)):
        raise ValueError('Fresh output outside immutable parent roots required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from experiments.motion_fixture.mesh_intersections import topology,frame as surface_frame
    from experiments.motion_fixture.biomechanical_features import extract as bmc_extract,angular_derivatives,GeometryError
    prior=extract_profile(loss_source)
    journal=Journal(output/'journal',{'condition_id':'TF03_THREE_AUDITED_STATE_PATHS',
      'endpoint':'actual_native_path_model_surface_and_physical_time_parameter_derivatives',
      'input_exposure':'audited saved model poses; no action primitive or new random draw',
      'cache_state':'shared hand CPU model; module/OS caches uncontrolled','planned_frames':102,'timeout_seconds':600,
      'scope':'sampled model motion diagnostic; unresolved clinical/coupling/continuous/physics/human limits'})
    completed=0;rows=[];utc=time.time_ns();wall=time.perf_counter_ns();cpu=time.process_time_ns()
    try:
        import torch
        import smplx
        from smplx.vertex_ids import vertex_ids
        if str(torch.__version__)!='2.5.1+cpu' or importlib.metadata.version('smplx')!='0.1.28':raise ValueError('Pinned CPU runtime required')
        torch.set_num_threads(1);torch.manual_seed(0)
        tips={n:vertex_ids['mano'][n] for n in TIP_NAMES}
        (output/'applied_model_prior.private.json').write_bytes(canonical(prior))
        (output/'environment.private.json').write_bytes(canonical({'torch':str(torch.__version__),
          'numpy':np.__version__,'smplx':importlib.metadata.version('smplx'),'python':sys.version,'gpu_used':False,'torch_threads':1}))
        for hand in ('right','left'):
            with journal.stage(hand+'_setup_and_neutral'):
                model=smplx.MANO(str(Path(intake).resolve()/'models'),is_rhand=hand=='right',use_pca=False,
                  flat_hand_mean=True,batch_size=1,dtype=torch.float32).to('cpu').eval()
                if tuple(model.parents.tolist())!=RAW_PARENTS:raise ValueError('Native parent indices differ')
                with torch.no_grad():neutral=model(hand_pose=torch.zeros(1,45),betas=torch.zeros(1,10),
                  global_orient=torch.zeros(1,3),transl=torch.zeros(1,3),return_verts=True)
                journal.frame_completed(completed,True);completed+=1
                points=canonicalize(neutral.vertices.numpy(),neutral.joints.numpy(),tips)[0]
                with np.load(source/(hand+'_setup.private.npz'),allow_pickle=False) as saved:
                    basis=saved['basis'].copy();faces=saved['faces'].copy()
                    if not np.array_equal(neutral.vertices.numpy(),saved['vertices']):raise ValueError('Actual neutral differs from audited parent')
                if not np.array_equal(model.faces,faces) or np.max(np.abs(template_basis(points,hand)-basis))>1e-6:
                    raise ValueError('Bound basis/topology differs')
                mesh=topology(faces,778)
                np.savez_compressed(output/(hand+'_setup.private.npz'),basis=basis,faces=faces,neutral_points=points)
            for seed in (7,19):
                selected=sorted((r for r in candidates if r['hand']==hand and r['seed']==seed and r['model_surface_eligible']
                  and r['bmc_geometry_error'] is None),key=lambda r:r['attempt'])[:3]
                if tuple(r['attempt'] for r in selected)!=EXPECTED[hand,seed]:raise ValueError('Registered waypoint selection differs')
                states=[];actual_parents=[]
                for row in selected:
                    with np.load(source/row['case_id']/'native_output.private.npz',allow_pickle=False) as saved:
                        states.append(saved['projected_angles'][0]);actual_parents.append(saved['full_pose'][0])
                case_id=f'{hand}_s{seed}';directory=output/case_id;directory.mkdir()
                start=time.perf_counter_ns();pcpu=time.process_time_ns();case_utc=time.time_ns()
                with journal.stage(case_id+'_path_sdk_and_sampled_QA'):
                    times,angles=path(np.array(states));pose=compose_anatomical(angles,basis).astype(np.float32)
                    if not np.array_equal(pose[[0,12,24]],np.array(actual_parents)[:,3:]):
                        raise ValueError('Waypoint input poses do not reproduce actual static parents')
                    (directory/'proposal.private.json').write_bytes(canonical({'version':VERSION,'hand':hand,'seed':seed,
                      'waypoint_case_ids':[r['case_id'] for r in selected],'times_seconds':times.tolist(),
                      'waypoint_times_seconds':[0.,1.5,3.],'interpolation':'quintic convex per-segment Euler interpolation',
                      'action_primitive':None,'new_random_draws_n':0,'corrections':[]}))
                    with torch.no_grad():result=model(hand_pose=torch.from_numpy(pose),betas=torch.zeros(25,10),
                      global_orient=torch.zeros(25,3),transl=torch.zeros(25,3),return_verts=True,return_full_pose=True)
                    vertices=result.vertices.numpy();raw=result.joints.numpy();full=result.full_pose.numpy()
                    if not np.isfinite(vertices).all() or not np.array_equal(full[:,3:],pose) or full[:,:3].any():
                        raise ValueError('Nonfinite or changed actual model output')
                    for _ in range(25):journal.frame_completed(completed,True);completed+=1
                    points=canonicalize(vertices,raw,tips);recovered=extract_anatomical(full[:,3:],basis)
                    roundtrip=float(np.max(np.abs(compose_anatomical(recovered,basis)-pose)))
                    if roundtrip>1e-6:raise ValueError('Actual Euler/native roundtrip differs')
                    strict,effective=assess(recovered,prior);surfaces=[surface_frame(v,mesh) for v in vertices]
                    features=[];errors=[]
                    for index,p in enumerate(points):
                        try:features.append(bmc_extract(p,handedness=hand)['joint_angles_radians'])
                        except GeometryError as error:errors.append({'frame_index':index,'code':error.code})
                    v,a=derivatives(recovered,times)
                    if not errors:
                        bv,ba=angular_derivatives(np.array(features),times)
                        np.savez_compressed(directory/'bmc_temporal.private.npz',joint_angles_radians=features,
                          velocity_rad_s=bv,acceleration_rad_s2=ba)
                    np.savez_compressed(directory/'native_output.private.npz',vertices=vertices,raw_joints=raw,
                      canonical_points=points,full_pose=full,times_seconds=times,proposed_angles=angles,
                      actual_angles=recovered,strict_excess_radians=strict,masked_excess_radians=effective,
                      euler_parameter_velocity_rad_s=v,euler_parameter_acceleration_rad_s2=a,betas=np.zeros((25,10),np.float32))
                    (directory/'surface_QA.private.json').write_bytes(canonical(surfaces))
                penalized=int(np.any(effective>0,axis=(1,2)).sum())
                surface_bad=sum(s['state']!='NO_TESTED_PAIR_INTERSECTION' for s in surfaces)
                row={'case_id':case_id,'hand':hand,'seed':seed,'frames_n':25,'model_prior_penalized_frames_n':penalized,
                  'model_prior_max_excess_radians':float(effective.max()),'surface_nonclear_frames_n':surface_bad,
                  'bmc_feature_errors':errors,'roundtrip_max_absolute_error':roundtrip,
                  'euler_parameter_speed_max_abs_rad_s':float(np.abs(v).max()),
                  'euler_parameter_acceleration_max_abs_rad_s2':float(np.abs(a).max()),
                  'model_surface_path_eligible':not penalized and not surface_bad and not errors,
                  'pending_BMC_state':'UNRESOLVED_LIMITS','clinical_coupling_validated':False,
                  'continuous_collision_validated':False,'human_validated':False,'release_allowed':False,
                  'timing':{'started_utc_epoch_ns':case_utc,'ended_utc_epoch_ns':time.time_ns(),
                    'wall_ns':time.perf_counter_ns()-start,'own_cpu_ns':time.process_time_ns()-pcpu}}
                (directory/'decision.private.json').write_bytes(canonical(row));rows.append(row)
                print('Three-waypoint paths '+str(len(rows))+'/4',flush=True)
            del model
        if completed!=102 or len(rows)!=4 or verify(source_record)!=producer_status or verify(audit_record)!=audit_status:
            raise ValueError('Input evidence or registered denominator changed')
        authorize_inputs(intake,research_record);journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');checked=verify_bundle(output/'journal_bundle.private.zip')
    summary={'version':VERSION,'paths':rows,'paths_n':4,'frames_n':100,'native_forward_frames_n':102,
      'model_surface_eligible_paths_n':sum(r['model_surface_path_eligible'] for r in rows),
      'journal_status':checked['status'],'pending_BMC_state':'UNRESOLVED_LIMITS','new_random_draws_n':0,
      'new_videos_n':0,'human_trials_n':0,'new_independent_families_n':0,'accepted_into_pool_n':0,'release_allowed':False,
      'original_static_producer_state':'PROCESS_ERROR','static_raw_output_audit_state':'EXITED_ZERO',
      'timing':{'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),'wall_ns':time.perf_counter_ns()-wall,
        'own_cpu_ns':time.process_time_ns()-cpu,'scope':'shared setup through native/sample QA/temporal metrics/store/parent recheck; recorder excluded'}}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','audit','audit-record','intake','research-record','loss-source','worker-root','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(execute(a.source,a.source_record,a.audit,a.audit_record,a.intake,a.research_record,a.loss_source,a.worker_root,a.output)))
