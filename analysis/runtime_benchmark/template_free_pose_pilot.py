"""TF-02 registered static PCA proposals and immutable A/B/U diagnostics."""
import argparse
from collections import Counter
import importlib.metadata
import json
from pathlib import Path
import sys
import time

import numpy as np

from analysis.runtime_benchmark.mano_recorded_producer import authorize_inputs,canonicalize,point_contract,RAW_PARENTS,TIP_NAMES
from analysis.runtime_benchmark.mano_anatomical_frame_probe import template_basis,compose_anatomical,extract_anatomical
from analysis.runtime_benchmark.mano_model_prior_audit import extract_profile,assess
from analysis.runtime_benchmark.mano_conditioned_generator import recipe,trajectory
from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from validation_v03.session_artifacts import canonical,_private

VERSION='template_free_static_pca_pilot_v1'
FRAME_INDICES=(0,3,6,9,12,15,18,24)


def proposal(hand,seed,attempt):
    if hand not in ('right','left') or type(seed) is not int or seed not in (7,19) or type(attempt) is not int or not 0<=attempt<8:
        raise ValueError('Registered hand/seed/attempt required')
    entropy=[20261116,seed,0 if hand=='right' else 1,attempt,2]
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(entropy)))
    return {'version':VERSION,'hand':hand,'seed':seed,'attempt':attempt,'rng':'numpy.PCG64/SeedSequence',
            'entropy':entropy,'coefficients':rng.normal(0.,.5,6).tolist(),
            'scale_status':'engineering_proposal_not_learned_density_or_human_limit',
            'prototype_id':None,'trajectory':None,'release_allowed':False}


def expand(coefficients,components):
    coefficients=np.asarray(coefficients);components=np.asarray(components)
    if coefficients.shape!=(6,) or components.shape!=(6,45) or not all(np.isfinite(x).all() for x in (coefficients,components)):
        raise ValueError('Finite six coefficients and6x45 model basis required')
    return (coefficients.astype(np.float32)@components.astype(np.float32)).reshape(1,45)


def decision(strict,effective,surface,bmc_error=None):
    strict=np.asarray(strict);effective=np.asarray(effective)
    if strict.shape!=(1,15,3) or effective.shape!=strict.shape or not all(np.isfinite(x).all() for x in (strict,effective)):
        raise ValueError('Finite complete model prior losses required')
    reasons=[]
    if effective.any():reasons.append('AUTHOR_MODEL_PRIOR_VIOLATION')
    if surface['state']=='UNMEASURABLE_DEGENERATE_TRIANGLES':reasons.append('UNMEASURABLE_SURFACE')
    elif not surface['sampled_surface_clear']:reasons.append('SAMPLED_SURFACE_INTERSECTION_INDICATOR')
    if bmc_error is not None:reasons.append('UNMEASURABLE_BMC_GEOMETRY')
    return {'strict_axis_excess_n':int(np.count_nonzero(strict)),
            'masked_axis_excess_n':int(np.count_nonzero(effective)),
            'max_masked_axis_excess_radians':float(effective.max()),
            'surface_indicator':bool(surface['pair_ids'].get('intersects')),
            'surface_state':surface['state'],'bmc_geometry_error':bmc_error,
            'model_surface_candidate':not reasons,'rejection_reasons':reasons,
            'pending_BMC_state':'UNRESOLVED_LIMITS',
            'temporal_rules':'NOT_APPLICABLE_STATIC_POSE_NO_TIMESTAMPS',
            'state':'MODEL_CONSTRAINED_RESEARCH_ONLY','release_allowed':False,'accepted_into_pool':False}


def execute(intake,research_record,loss_source,worker_root,output):
    authorize_inputs(intake,research_record);output=_private(output)
    if output.exists():raise FileExistsError('Fresh private pilot output required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from dataset_pipeline.common import LANDMARK_NAMES
    from experiments.motion_fixture.mesh_intersections import topology,frame as surface_frame
    from experiments.motion_fixture.biomechanical_features import extract as bmc_extract,GeometryError
    prior=extract_profile(loss_source)
    journal=Journal(output/'journal',{'condition_id':'TF02_STATIC_PCA_A_B_U',
      'endpoint':'registered_static_proposals_model_prior_and_sampled_surface_rejection',
      'input_exposure':'existing licensed private models; generated development proposals',
      'cache_state':'shared CPU model per hand; OS/module caches uncontrolled',
      'planned_frames':70,'timeout_seconds':600,'scope':'static research only; no human/motion/render/pool approval'})
    completed=0;rows=[];probes=[];setups=[]
    started=time.time_ns();wall=time.perf_counter_ns();cpu=time.process_time_ns()
    try:
        with journal.stage('runtime_setup'):
            import torch
            import smplx
            from smplx.vertex_ids import vertex_ids
            if str(torch.__version__)!='2.5.1+cpu' or importlib.metadata.version('smplx')!='0.1.28':
                raise ValueError('Existing pinned CPU runtime required')
            torch.set_num_threads(1);torch.manual_seed(0)
            tips={name:vertex_ids['mano'][name] for name in TIP_NAMES}
            (output/'point_contract.private.json').write_bytes(canonical(point_contract(LANDMARK_NAMES,tips)))
            (output/'applied_model_prior.private.json').write_bytes(canonical(prior))
            (output/'design.private.json').write_bytes(canonical({'version':VERSION,'seeds':[7,19],'attempts_per_seed':8,
              'A_frame_indices':FRAME_INDICES,'B_pc_count':6,'B_coefficient_sd':.5,'geometry_beta':0.,'root':0.,
              'planned_forward_poses_n':70,'logical_arm_cases_n':96,'U_shares_B_actual_outputs':True,
              'corrections_enabled':False,'temporal_checks':'N/A_STATIC','release_allowed':False}))
            (output/'environment.private.json').write_bytes(canonical({'python':sys.version,'torch':str(torch.__version__),
              'smplx':importlib.metadata.version('smplx'),'numpy':np.__version__,'torch_threads':torch.get_num_threads(),'gpu_used':False}))

        def forward(model,pose):
            nonlocal completed
            journal.check_budget()
            with torch.no_grad():
                result=model(hand_pose=torch.from_numpy(pose),betas=torch.zeros(1,10),global_orient=torch.zeros(1,3),
                             transl=torch.zeros(1,3),return_verts=True,return_full_pose=True)
            journal.frame_completed(completed,True);completed+=1
            return {name:getattr(result,name).numpy() for name in ('vertices','joints','full_pose')}

        with (output/'attempts.private.jsonl').open('xb',buffering=0) as log:
            for hand in ('right','left'):
                setup_start=time.perf_counter_ns()
                with journal.stage(hand+'_model_neutral_and_representation_probes'):
                    authorize_inputs(intake,research_record)
                    options=dict(is_rhand=hand=='right',flat_hand_mean=True,batch_size=1,dtype=torch.float32)
                    model=smplx.MANO(str(Path(intake).resolve()/'models'),use_pca=False,**options).to('cpu');model.eval()
                    pcmodel=smplx.MANO(str(Path(intake).resolve()/'models'),use_pca=True,num_pca_comps=6,**options).to('cpu');pcmodel.eval()
                    if tuple(model.parents.tolist())!=RAW_PARENTS:raise ValueError('Native parent indices differ')
                    neutral=forward(model,np.zeros((1,45),np.float32))
                    points=canonicalize(neutral['vertices'],neutral['joints'],tips)[0]
                    basis=template_basis(points,hand);mesh=topology(model.faces,778)
                    components=pcmodel.hand_components.detach().cpu().numpy().copy()
                    coefficients=proposal(hand,7,0)['coefficients']
                    explicit=expand(coefficients,components)
                    native=forward(model,explicit);pca=forward(pcmodel,np.array(coefficients,np.float32).reshape(1,6))
                    diffs={k:float(np.max(np.abs(native[k]-pca[k]))) for k in native}
                    probe={'hand':hand,'max_absolute_differences':diffs,'tolerance':1e-6}
                    (output/(hand+'_representation_probe.private.json')).write_bytes(canonical(probe));probes.append(probe)
                    np.savez_compressed(output/(hand+'_setup.private.npz'),basis=basis,components=components,faces=model.faces,
                      neutral_vertices=neutral['vertices'],neutral_joints=neutral['joints'],
                      probe_input=explicit,probe_pca_full_pose=pca['full_pose'],probe_native_full_pose=native['full_pose'])
                    if max(diffs.values())>1e-6:raise ValueError('PCA/native representation mismatch')
                    del pcmodel
                setups.append({'hand':hand,'wall_ns':time.perf_counter_ns()-setup_start,'includes_neutral_and_two_probes':True})
                for seed in (7,19):
                    spec=recipe(seed,'middle_only_cues_open','preflex20')
                    _,a_angles=trajectory(spec,hand,'author_exact')
                    for attempt in range(8):
                        bspec=proposal(hand,seed,attempt)
                        for arm in ('A','B'):
                            name=f'{arm}_{hand}_s{seed}_a{attempt}';directory=output/name;directory.mkdir()
                            start=time.perf_counter_ns();pcpu=time.process_time_ns();utc=time.time_ns()
                            if arm=='A':
                                selected=a_angles[FRAME_INDICES[attempt]:FRAME_INDICES[attempt]+1]
                                pose=compose_anatomical(selected,basis).astype(np.float32)
                                proposal_data={'arm':'A','recipe':spec,'frame_index':FRAME_INDICES[attempt],
                                                'anatomical_euler_radians':selected.tolist(),'beta_override':0.,'root':0.}
                            else:
                                pose=expand(bspec['coefficients'],components);proposal_data=bspec
                            log.write(canonical({'event':'PROPOSED','case':name,'proposal':proposal_data})+b'\n')
                            with journal.stage(name+'_native_and_QA'):
                                actual=forward(model,pose)
                                if not np.array_equal(actual['full_pose'][:,3:],pose) or np.any(actual['full_pose'][:,:3]):
                                    raise ValueError('Actual full pose differs from prescribed nonroot/root')
                                joints=canonicalize(actual['vertices'],actual['joints'],tips)
                                angles=extract_anatomical(actual['full_pose'][:,3:],basis)
                                roundtrip=float(np.max(np.abs(compose_anatomical(angles,basis)-actual['full_pose'][:,3:])))
                                if roundtrip>1e-6:raise ValueError('Anatomical/native roundtrip mismatch')
                                strict,effective=assess(angles,prior)
                                surface=surface_frame(actual['vertices'][0],mesh)
                                bmc_error=None
                                try:
                                    features=bmc_extract(joints[0],handedness=hand)
                                    np.savez_compressed(directory/'bmc_features.private.npz',**{k:v for k,v in features.items() if isinstance(v,np.ndarray)})
                                except GeometryError as error:bmc_error=error.code
                                verdict=decision(strict,effective,surface,bmc_error)
                                np.savez_compressed(directory/'native_output.private.npz',vertices=actual['vertices'],
                                  raw_joints=actual['joints'],canonical_joints=joints,full_pose_axis_angle=actual['full_pose'],
                                  input_nonroot_pose=pose,betas=np.zeros((1,10),np.float32),anatomical_euler_radians=angles,
                                  strict_excess_radians=strict,masked_excess_radians=effective)
                                (directory/'proposal.private.json').write_bytes(canonical(proposal_data))
                                (directory/'surface_QA.private.json').write_bytes(canonical(surface))
                            row={'case_id':name,'arm':arm,'hand':hand,'seed':seed,'attempt':attempt,**verdict,
                              'anatomical_roundtrip_max_absolute_error':roundtrip,
                              'timing':{'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),
                                'wall_ns':time.perf_counter_ns()-start,'own_cpu_ns':time.process_time_ns()-pcpu}}
                            (directory/'decision.private.json').write_bytes(canonical(row));rows.append(row)
                            log.write(canonical({'event':'ASSESSED','case':name,'decision':row})+b'\n')
                            if arm=='B':
                                rows.append({**row,'case_id':name.replace('B_','U_',1),'arm':'U','shared_actual_output_case':name,
                                  'gate_applied':False,'model_surface_candidate':False,'ungated_proposal_retained':True,
                                  'timing':None,'timing_scope':'shares B native/QA time; no separate SDK forward'})
                        print('Static proposal pairs '+str(len(rows)//3)+'/32',flush=True)
                del model
        authorize_inputs(intake,research_record)
        if completed!=70 or len(rows)!=96:raise ValueError('Registered forward/logical case denominators differ')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip')
    checked=verify_bundle(output/'journal_bundle.private.zip')
    aggregates=[]
    for arm in ('A','B','U'):
        cases=[r for r in rows if r['arm']==arm]
        aggregates.append({'arm':arm,'cases_n':len(cases),
          'model_prior_zero_n':sum(r['masked_axis_excess_n']==0 for r in cases),
          'strict_excess_zero_n':sum(r['strict_axis_excess_n']==0 for r in cases),
          'sampled_surface_clear_n':sum(r['surface_state']=='NO_TESTED_PAIR_INTERSECTION' for r in cases),
          'bmc_geometry_measurable_n':sum(r['bmc_geometry_error'] is None for r in cases),
          'model_surface_candidate_n':sum(r['model_surface_candidate'] for r in cases),
          'rejection_reason_counts':dict(Counter(x for r in cases for x in r['rejection_reasons']))})
    (output/'cases.private.json').write_bytes(canonical({'cases':rows}))
    summary={'version':VERSION,'native_forward_poses_n':completed,'logical_arm_cases_n':96,'aggregates':aggregates,
      'representation_probes':probes,'shared_hand_setup':setups,'journal_status':checked['status'],
      'prototype_free_proposal_poses_n':32,'corrections_n':0,'new_videos_n':0,'human_trials_n':0,
      'accepted_into_pool_n':0,'release_allowed':False,'pending_BMC_state':'UNRESOLVED_LIMITS',
      'timing':{'started_utc_epoch_ns':started,'ended_utc_epoch_ns':time.time_ns(),'wall_ns':time.perf_counter_ns()-wall,
        'own_cpu_ns':time.process_time_ns()-cpu,'scope':'runtime setup through proposal SDK/QA/journal store; snapshot/receipt excluded'}}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('intake','research-record','loss-source','worker-root','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();s=execute(a.intake,a.research_record,a.loss_source,a.worker_root,a.output)
    print(json.dumps({'native_forward_poses_n':s['native_forward_poses_n'],'aggregates':s['aggregates']}))
