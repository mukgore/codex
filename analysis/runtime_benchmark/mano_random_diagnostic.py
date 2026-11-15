"""Bounded private random MANO diagnostic; no admissible biological pool output.

Only the existing engineering PCA neighbourhood is sampled. Every proposal,
native model output and failed/pending assessment is retained. No renderer,
collision, human comfort or anatomical admissibility is claimed.
"""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np

from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from analysis.runtime_benchmark.mano_recorded_producer import (
    RAW_PARENTS,TIP_NAMES,authorize_inputs,canonicalize,point_contract,
)
from validation_v03.run_manifest import snapshot_file
from validation_v03.session_artifacts import canonical,_private

VERSION='mano_bounded_pca_engineering_diagnostic_v1'
FRAMES=24


def stream_seed(seed,attempt,hand,stream):
    if type(seed) is not int or not 0<=seed<2**64 or type(attempt) is not int or not 0<=attempt<16:
        raise ValueError('Bounded integer master seed and attempt required')
    if hand not in ('right','left') or stream not in ('geometry','trajectory','appearance'):
        raise ValueError('Explicit hand and named RNG stream required')
    digest=hashlib.sha256(f'{VERSION}|{seed}|{attempt}|{hand}|{stream}'.encode()).digest()
    return int.from_bytes(digest[:16],'big')


def proposal(seed,attempt,hand):
    children={name:stream_seed(seed,attempt,hand,name) for name in ('geometry','trajectory','appearance')}
    rng=np.random.Generator(np.random.PCG64(children['trajectory']))
    return {'version':VERSION,'master_seed':seed,'attempt':attempt,'hand':hand,
        'rng':'numpy.PCG64','child_seeds':children,
        'active_rng_streams':['trajectory'],'unused_rng_streams':['geometry','appearance'],
        'primary_pc1_amplitude':float(rng.uniform(.4,.8)),
        'secondary_pc2_amplitude':float(rng.uniform(-.08,.08)),
        'duration_seconds':float(rng.uniform(1.5,2.5)),
        'rise_fraction':float(rng.uniform(.3,.4)),'hold_fraction':float(rng.uniform(.1,.2)),
        'frames_n':FRAMES,'shape':'fixed_model_mean','flat_hand_mean':True,
        'parameter_scope':'engineering_diagnostic_bounds_not_biological_admissible_limits',
        'parent_recipe':'recorded_flat_pc1_neighbourhood_not_new_independent_family',
        'random_motion_sampled':True,'release_allowed':False}


def envelope(phase,rise,hold):
    phase=np.asarray(phase,float)
    if (not np.isfinite(phase).all() or (phase<0).any() or (phase>1).any()
            or not np.isfinite([rise,hold]).all() or not 0<rise<rise+hold<1):
        raise ValueError('Finite unit phase and ordered positive motion phases required')
    def smooth(x):return x*x*x*(10+x*(-15+6*x))
    return np.where(phase<rise,smooth(np.clip(phase/rise,0,1)),
        np.where(phase<=rise+hold,1.,1-smooth(np.clip((phase-rise-hold)/(1-rise-hold),0,1))))


def trajectory(spec):
    # The complete recipe must be the deterministic output of this version.
    if spec!=proposal(spec['master_seed'],spec['attempt'],spec['hand']):
        raise ValueError('Modified or unsupported sampled recipe')
    times=np.linspace(0.,spec['duration_seconds'],FRAMES)
    weight=envelope(times/spec['duration_seconds'],spec['rise_fraction'],spec['hold_fraction'])
    pose=np.zeros((FRAMES,6),np.float32)
    pose[:,1]=spec['primary_pc1_amplitude']*weight
    pose[:,2]=spec['secondary_pc2_amplitude']*weight
    return times,pose


def rejection_reasons(assessment):
    reasons=['ENGINEERING_DIAGNOSTIC_NOT_ELIGIBLE_FOR_POOL']
    reasons += ['UNRESOLVED_'+name.upper() for name in assessment['unresolved_rules']]
    if assessment['geometry_errors']:reasons.append('UNMEASURABLE_GEOMETRY')
    if assessment['violations']:reasons.append('DECLARED_RULE_VIOLATIONS')
    if not assessment['evidence_backed_rule_checks_pass']:reasons.append('NO_EVIDENCE_BACKED_ADMISSION')
    reasons += ['SELF_COLLISION_NOT_CHECKED','CONTACT_PHYSICS_NOT_CHECKED',
        'FINAL_MASKED_RENDER_NOT_CHECKED','HUMAN_FEASIBILITY_NOT_OBSERVED']
    return reasons


def execute(intake,research_record,worker_root,output,seeds):
    if (not isinstance(seeds,list) or not 1<=len(seeds)<=4 or len(set(seeds))!=len(seeds)
            or any(type(s) is not int or not 0<=s<2**64 for s in seeds)):
        raise ValueError('One to four distinct bounded master seeds required')
    sources=authorize_inputs(intake,research_record)
    output=_private(output)
    if output.exists():raise FileExistsError('Fresh private diagnostic root required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from dataset_pipeline.common import LANDMARK_NAMES
    from experiments.motion_fixture.biomechanical_profile import pending_profile,assess
    profile=pending_profile();profile.update(length_unit='model_native_units',profile_version='mano_native_pending_limits_v1')
    planned=len(seeds)*4*FRAMES
    journal=Journal(output/'journal',{'condition_id':'G02_RANDOM_ENGINEERING_DIAGNOSTIC_20261115',
        'endpoint':'bounded_native_forward_and_pending_profile_rejection',
        'input_exposure':'existing private research model; authored diagnostic PCA proposal',
        'cache_state':'CPU OS/module cache uncontrolled','planned_frames':planned,'timeout_seconds':300,
        'scope':'native_model_output_not_camera_or_human_measurement'})
    attempts=[];count=0
    try:
        with journal.stage('runtime_and_scope_before_model_load'):
            import torch
            import smplx
            from smplx.vertex_ids import vertex_ids
            if str(torch.__version__)!='2.5.1+cpu' or importlib.metadata.version('smplx')!='0.1.28':
                raise ValueError('Existing explicit CPU runtime required')
            torch.set_num_threads(1);torch.manual_seed(0)
            tips={n:vertex_ids['mano'][n] for n in TIP_NAMES}
            contract=point_contract(LANDMARK_NAMES,tips)
            kinds=[r['point_kind'] for r in contract['canonical_points']]
            (output/'point_contract.private.json').write_bytes(canonical(contract))
            (output/'applied_profile.private.json').write_bytes(canonical(profile))
        with (output/'attempts.private.jsonl').open('xb',buffering=0) as log:
            for hand in ('right','left'):
                with journal.stage(hand+'_model_load'):
                    authorize_inputs(intake,research_record)
                    model=smplx.MANO(str(Path(intake).resolve()/'models'),is_rhand=hand=='right',
                        use_pca=True,num_pca_comps=6,flat_hand_mean=True,batch_size=FRAMES,dtype=torch.float32).to('cpu')
                    model.eval()
                    if tuple(model.parents.tolist())!=RAW_PARENTS:raise ValueError('Native parent contract changed')
                for seed in seeds:
                    for index in range(2):
                        journal.check_budget();label=f'{hand}_s{seed}_a{index}';case=output/label;case.mkdir()
                        spec=proposal(seed,index,hand);times,pose=trajectory(spec)
                        (case/'proposal.private.json').write_bytes(canonical(spec))
                        log.write(canonical({'event':'PROPOSED','case':label,'recipe':spec})+b'\n')
                        with journal.stage(label+'_native_forward'):
                            with torch.no_grad():result=model(hand_pose=torch.from_numpy(pose),return_verts=True,return_full_pose=True)
                            vertices=result.vertices.numpy();raw=result.joints.numpy();full=result.full_pose.numpy()
                            points=canonicalize(vertices,raw,tips)
                            if full.shape!=(FRAMES,48) or not np.isfinite(full).all():raise ValueError('Finite native full pose required')
                            np.savez_compressed(case/'native_output.private.npz',vertices=vertices,raw_joints=raw,
                                canonical_joints=points,full_pose_axis_angle=full,pose_coefficients=pose,times_seconds=times,
                                faces=model.faces,parents=model.parents.numpy())
                            for frame in range(FRAMES):journal.frame_completed(count*FRAMES+frame,True)
                        with journal.stage(label+'_assess_and_quarantine'):
                            assessment=assess(points,times,profile,handedness=hand,
                                length_unit='model_native_units',point_kinds=kinds)
                            (case/'assessment.private.json').write_bytes(canonical(assessment))
                            # This diagnostic cannot promote to a pool, even if caller-supplied rules pass.
                            row={'case':label,'state':'QUARANTINED_DIAGNOSTIC','frames_n':FRAMES,
                                'measurable_frames_n':assessment['measurable_frames_n'],
                                'assessment_state':assessment['state'],'rejection_reasons':rejection_reasons(assessment),
                                'rig_violation':any(v['rule']=='fixed_generated_rig_bone_lengths' for v in assessment['violations']),
                                'recipe_replay_exact':bool(np.array_equal(trajectory(proposal(seed,index,hand))[1],pose)),
                                'accepted_into_pool':False,'release_allowed':False}
                            (case/'decision.private.json').write_bytes(canonical(row))
                            log.write(canonical({'event':'DECIDED',**row})+b'\n');attempts.append(row);count+=1
                del model,result
        with journal.stage('source_scope_recheck'):
            authorize_inputs(intake,research_record)
            for source in sources.values():
                if snapshot_file(source['path'])!=source:raise ValueError('Model source changed during run')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');verified=verify_bundle(output/'journal_bundle.private.zip')
    reasons=Counter(r for row in attempts for r in row['rejection_reasons'])
    summary={'scope':'bounded_random_native_mano_engineering_diagnostic_all_outputs_quarantined',
        'version':VERSION,'seeds':seeds,'attempts_n':len(attempts),'native_forward_frames_n':count*FRAMES,
        'measurable_frames_n':sum(r['measurable_frames_n'] for r in attempts),
        'rig_violation_attempts_n':sum(r['rig_violation'] for r in attempts),
        'exact_recipe_replays_n':sum(r['recipe_replay_exact'] for r in attempts),
        'assessment_states':dict(Counter(r['assessment_state'] for r in attempts)),
        'rejection_reason_counts':dict(reasons),'accepted_into_pool_n':0,'quarantined_attempts_n':len(attempts),
        'runtime_journal_status':verified['status'],'runtime_journal_completed_frames_n':verified['completed_frames'],
        'new_model_inference':True,'random_motion_sampled':True,'rendered_videos_n':0,
        'new_independent_families_n':0,'biological_validity_proven':False,'physical_unit_verified':False,
        'full_generator_ready':False,'release_allowed':False,
        'limitations':['Engineering PCA bounds and smooth curve are not admissible anatomical or safety limits.',
            'No object, collision, full scene, final masked raster, independent family or human study.',
            'Rejected native arrays remain private diagnostic records; no delivery/pool promotion.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('intake','research-record','worker-root','output'):parser.add_argument('--'+n,type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',required=True)
    a=parser.parse_args();print(json.dumps(execute(a.intake,a.research_record,a.worker_root,a.output,a.seeds)))
