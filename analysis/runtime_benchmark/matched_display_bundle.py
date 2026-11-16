"""TF-04 matched A/B/C/U input bundle, preserving all upstream experiment states."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import time

import numpy as np

from analysis.runtime_benchmark.mano_author_surface_audit import bound
from analysis.runtime_benchmark.mano_recorded_producer import authorize_inputs,canonicalize,point_contract,RAW_PARENTS,TIP_NAMES
from analysis.runtime_benchmark.mano_anatomical_frame_probe import template_basis,compose_anatomical,extract_anatomical
from analysis.runtime_benchmark.mano_model_prior_audit import extract_profile,assess
from analysis.runtime_benchmark.mano_conditioned_generator import recipe,trajectory
from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,_private

VERSION='tf04_matched_ABC_U_native_bundle_v1'
COLOR=[170,205,225]


def repeat_static(value):
    value=np.asarray(value)
    if value.ndim<2 or value.shape[0]!=1 or not np.isfinite(value).all():
        raise ValueError('One complete finite static SDK result required')
    return np.repeat(value,25,axis=0)


def execute(paths,paths_record,projected,projected_record,audit,audit_record,raw,raw_record,guarded,guarded_record,
            intake,research_record,loss_source,worker_root,output):
    bindings=[bound(root,rec) for root,rec in ((paths,paths_record),(audit,audit_record),(raw,raw_record),(guarded,guarded_record))]
    (paths,paths_record,pbefore),(audit,audit_record,abefore),(raw,raw_record,rbefore),(guarded,guarded_record,gbefore)=bindings
    projected=_private(projected);projected_record=_private(projected_record);zbefore=verify(projected_record)
    zreceipt=json.loads((projected_record/'receipt.private.json').read_text())
    if (zbefore['state']!='PROCESS_ERROR' or zreceipt['artifact_roots']!=[str(projected)] or not zreceipt['postflight_snapshot_matched']):
        raise ValueError('Explicit audited producer-error source required')
    ps=json.loads((paths/'summary.json').read_text());gs=json.loads((guarded/'summary.json').read_text())
    checked=json.loads((audit/'cases.private.json').read_text())['cases']
    if (ps['model_surface_eligible_paths_n']!=4 or gs['protection_mode']!='author_region_union'
            or gs['camera_mode']!='hand_neutral_registered' or gs['release_allowed'] is not False):
        raise ValueError('Four recorded model paths and current union-guarded camera required')
    authorize_inputs(intake,research_record);output=_private(output)
    roots=[x for root,rec,_ in bindings for x in (root,rec)]+[projected,projected_record]
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in roots):
        raise ValueError('Fresh independent native bundle output required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from dataset_pipeline.common import LANDMARK_NAMES
    from experiments.motion_fixture.mesh_intersections import topology,frame as surface_frame
    prior=extract_profile(loss_source)
    journal=Journal(output/'journal',{'condition_id':'TF04_MATCHED_A_B_C_U_NATIVE_BUNDLE',
      'endpoint':'matched geometry and PTS grid before frozen-camera display',
      'input_exposure':'existing private licensed model and recorded generated A/B/C/U development sources',
      'cache_state':'shared CPU model per hand; cached recorded B/C/U; OS/module caches uncontrolled',
      'planned_frames':102,'timeout_seconds':600,'scope':'new A100/neutral2 SDK evaluations; B/C/U evidence reused, no video/human/pool approval'})
    completed=0;cases=[];utc=time.time_ns();wall=time.perf_counter_ns();cpu=time.process_time_ns()
    try:
        import torch
        import smplx
        from smplx.vertex_ids import vertex_ids
        if str(torch.__version__)!='2.5.1+cpu' or importlib.metadata.version('smplx')!='0.1.28':raise ValueError('Existing CPU runtime required')
        torch.set_num_threads(1);torch.manual_seed(0);tips={n:vertex_ids['mano'][n] for n in TIP_NAMES}
        (output/'point_contract.private.json').write_bytes(canonical(point_contract(LANDMARK_NAMES,tips)))
        (output/'frozen_camera.private.json').write_bytes((guarded/'shared_camera.private.json').read_bytes())
        (output/'applied_model_prior.private.json').write_bytes(canonical(prior))
        (output/'environment.private.json').write_bytes(canonical({'torch':str(torch.__version__),
          'smplx':importlib.metadata.version('smplx'),'numpy':np.__version__,'python':sys.version,'torch_threads':1,'gpu_used':False}))
        for hand in ('right','left'):
            with journal.stage(hand+'_fresh_neutral'):
                model=smplx.MANO(str(Path(intake).resolve()/'models'),is_rhand=hand=='right',use_pca=False,
                  flat_hand_mean=True,batch_size=1,dtype=torch.float32).to('cpu').eval()
                if tuple(model.parents.tolist())!=RAW_PARENTS:raise ValueError('Native parent indices differ')
                with torch.no_grad():neutral=model(hand_pose=torch.zeros(1,45),betas=torch.zeros(1,10),global_orient=torch.zeros(1,3),
                  transl=torch.zeros(1,3),return_verts=True)
                journal.frame_completed(completed,True);completed+=1
                neutral_points=canonicalize(neutral.vertices.numpy(),neutral.joints.numpy(),tips)[0]
                basis=template_basis(neutral_points,hand);faces=model.faces.copy();mesh=topology(faces,778)
                with np.load(paths/(hand+'_setup.private.npz'),allow_pickle=False) as saved:
                    if not np.array_equal(saved['neutral_points'],neutral_points) or np.max(np.abs(saved['basis']-basis))>1e-6:
                        raise ValueError('Neutral path reference differs')
                np.savez_compressed(output/(hand+'_fresh_neutral.private.npz'),vertices=neutral.vertices.numpy(),
                  points=neutral_points,faces=faces,basis=basis)
            for seed in (7,19):
                parent_path=paths/f'{hand}_s{seed}'
                path_proposal=json.loads((parent_path/'proposal.private.json').read_text())
                projected_id=path_proposal['waypoint_case_ids'][0];raw_id=projected_id.removeprefix('P_')
                eligible=next(r for r in checked if r['case_id']==projected_id)
                if not eligible['model_surface_eligible'] or eligible['bmc_geometry_error'] is not None:
                    raise ValueError('Selected static baseline not accepted by source audit')
                with np.load(parent_path/'native_output.private.npz',allow_pickle=False) as saved:
                    c={k:saved[k].copy() for k in saved.files};times=c['times_seconds']
                if not np.array_equal(times,np.linspace(0.,3.,25)):raise ValueError('Registered shared25-frame3-second PTS grid differs')
                for arm in ('A','B','C','U'):
                    name=f'{arm}_{hand}_s{seed}';directory=output/name;directory.mkdir();start=time.perf_counter_ns();pcpu=time.process_time_ns()
                    with journal.stage(name+'_native_prepare_and_model_QA'):
                        if arm=='A':
                            spec=recipe(seed,'middle_only_cues_open','preflex20');_,angles=trajectory(spec,hand,'author_exact')
                            poses=compose_anatomical(angles,basis).astype(np.float32)
                            with torch.no_grad():result=model(hand_pose=torch.from_numpy(poses),betas=torch.zeros(25,10),
                              global_orient=torch.zeros(25,3),transl=torch.zeros(25,3),return_verts=True,return_full_pose=True)
                            vertices=result.vertices.numpy();joints=result.joints.numpy();full=result.full_pose.numpy()
                            for _ in range(25):journal.frame_completed(completed,True);completed+=1
                            points=canonicalize(vertices,joints,tips);surface=[surface_frame(v,mesh) for v in vertices]
                            source_case='registered_preflex20_recipe_phase_grid_beta0_root0';fresh=True
                        elif arm=='C':
                            vertices=c['vertices'];joints=c['raw_joints'];points=c['canonical_points'];full=c['full_pose']
                            surface=json.loads((parent_path/'surface_QA.private.json').read_text());source_case=f'{hand}_s{seed}';fresh=False
                        else:
                            parent=projected/projected_id if arm=='B' else raw/raw_id
                            with np.load(parent/'native_output.private.npz',allow_pickle=False) as saved:
                                vertices=repeat_static(saved['vertices']);joints=repeat_static(saved['joints'])
                                points=repeat_static(saved['canonical_points']);full=repeat_static(saved['full_pose'])
                            s=json.loads((parent/('surface_QA.private.json' if arm=='B' else 'QA.private.json')).read_text())
                            surface=[s if arm=='B' else s['surface']]*25
                            source_case=projected_id if arm=='B' else raw_id;fresh=False
                        if (vertices.shape!=(25,778,3) or joints.shape!=(25,16,3) or points.shape!=(25,21,3) or full.shape!=(25,48)
                                or not all(np.isfinite(v).all() for v in (vertices,joints,points,full)) or full[:,:3].any()):
                            raise ValueError('Matched full pose/geometry/root contract differs')
                        actual_angles=extract_anatomical(full[:,3:],basis);strict,effective=assess(actual_angles,prior)
                        penalized=int(np.any(effective>0,axis=(1,2)).sum())
                        surface_bad=sum(s['state']!='NO_TESTED_PAIR_INTERSECTION' for s in surface)
                        np.savez_compressed(directory/'native_output.private.npz',vertices=vertices,raw_joints=joints,
                          canonical_joints=points,full_pose_axis_angle=full,betas=np.zeros((25,10),np.float32),times_seconds=times,faces=faces)
                        (directory/'proposal.private.json').write_bytes(canonical({'recipe':{'base_bgr':COLOR},
                          'source_case':source_case,'arm':arm,'actual_new_model_inference':fresh,'beta':0,'root':0,
                          'PTS_grid_seconds':times.tolist(),'A_timing':'existing phase curve re-timed to3sec' if arm=='A' else None,
                          'static_repetition':arm in ('B','U')}))
                        (directory/'native_QA.private.json').write_bytes(canonical({'strict_excess_radians':strict.tolist(),
                          'masked_excess_radians':effective.tolist(),'surfaces':surface,'surface_QA_reused':not fresh}))
                    row={'case':name,'arm':arm,'hand':hand,'seed':seed,'policy':'author_exact','frames_n':25,
                      'model_penalized_frames_n':penalized,'surface_indicator_frames_n':surface_bad,
                      'model_surface_eligible_for_display_comparison':not penalized and not surface_bad,
                      'fresh_native_inference':fresh,'source_case':source_case,'release_allowed':False,'accepted_into_pool':False,
                      'timing':{'wall_ns':time.perf_counter_ns()-start,'own_cpu_ns':time.process_time_ns()-pcpu}}
                    (directory/'decision.private.json').write_bytes(canonical(row));cases.append(row)
                    print('Matched native cases '+str(len(cases))+'/16',flush=True)
            del model
        if completed!=102 or len(cases)!=16:raise ValueError('Matched source/native denominator differs')
        for _,rec,status in bindings:
            if verify(rec)!=status:raise ValueError('Bound source evidence changed')
        if verify(projected_record)!=zbefore:raise ValueError('Audited process-error source changed')
        authorize_inputs(intake,research_record);journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');checked_journal=verify_bundle(output/'journal_bundle.private.zip')
    summary={'version':VERSION,'cases_n':16,'cases':cases,'native_forward_frames_n':completed,'SDK_calls_n':6,
      'reused_B_C_U_coordinate_frames_n':300,'time_grid_start_to_last_PTS_seconds':3.,'nominal_encoded_length_seconds':25/8,
      'shared_color_bgr':COLOR,'frozen_camera_from_bound_union_guard':True,'camera_recalibrated':False,
      'static_input_producer_state':'PROCESS_ERROR','static_raw_output_audit_state':'EXITED_ZERO',
      'journal_status':checked_journal['status'],'new_videos_n':0,'new_independent_families_n':0,
      'pending_BMC_state':'UNRESOLVED_LIMITS','accepted_into_pool_n':0,'release_allowed':False,
      'timing':{'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),'wall_ns':time.perf_counter_ns()-wall,
        'own_cpu_ns':time.process_time_ns()-cpu,'scope':'model/source prepare through QA/store/parent recheck; recorder excluded'}}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('paths','paths-record','projected','projected-record','audit','audit-record','raw','raw-record','guarded','guarded-record',
              'intake','research-record','loss-source','worker-root','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(execute(**{k.replace('-','_'):v for k,v in vars(a).items()})))
