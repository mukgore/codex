"""Private TF-02 actual static MANO pilot; no action template for B/U."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import time

import numpy as np

from analysis.runtime_benchmark.template_free_pose import (
    A_INDICES, HANDS, SEEDS, VERSION, propose, expand, representation_errors, decide,
)
from analysis.runtime_benchmark.mano_recorded_producer import authorize_inputs, canonicalize, RAW_PARENTS, TIP_NAMES
from analysis.runtime_benchmark.mano_anatomical_frame_probe import template_basis, compose_anatomical, extract_anatomical
from analysis.runtime_benchmark.mano_model_prior_audit import extract_profile, assess
from analysis.runtime_benchmark.mano_conditioned_generator import recipe, trajectory, Timings
from analysis.runtime_benchmark.mano_author_surface_audit import bound
from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical, _private


def execute(source, source_record, intake, research_record, loss_source, worker_root, output):
    source, source_record, before = bound(source, source_record)
    authorize_inputs(intake, research_record)
    output = _private(output)
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (source, source_record)):
        raise ValueError('Fresh independent output required')
    prior = extract_profile(loss_source)
    source_summary = json.loads((source/'summary.json').read_text())
    if source_summary.get('primitive_profile') != 'non_target_cues_open_preflex20' or source_summary['release_allowed'] is not False:
        raise ValueError('Bound preflex baseline required')
    sys.path.insert(0, str(Path(worker_root).resolve(strict=True)))
    from experiments.motion_fixture.mesh_intersections import topology, frame as surface_frame
    journal = Journal(output/'journal', {'condition_id': 'TF02_STATIC_POSE_PILOT_V1',
        'endpoint': 'PCA_full_pose_representation_then_static_model_and_sampled_surface_QA',
        'input_exposure': 'existing private scientific MANO and source-bound baseline recipes',
        'cache_state': 'sequential CPU models; OS/module caches uncontrolled',
        'planned_frames': 70, 'timeout_seconds': 600,
        'scope': 'static engineering proposals, no motion/clinical/human/render/authentication proof'})
    cases = []; controls = []; setups = []; count = 0
    core_wall = time.perf_counter_ns(); core_cpu = time.process_time_ns()
    try:
        import torch
        import smplx
        from smplx.vertex_ids import vertex_ids
        if str(torch.__version__) != '2.5.1+cpu' or importlib.metadata.version('smplx') != '0.1.28':
            raise ValueError('Pinned existing CPU SDK required')
        torch.set_num_threads(1); torch.manual_seed(0)
        tip_ids = {name: vertex_ids['mano'][name] for name in TIP_NAMES}
        (output/'environment.private.json').write_bytes(canonical({'torch': str(torch.__version__),
            'smplx': importlib.metadata.version('smplx'), 'numpy': np.__version__, 'python': sys.version,
            'torch_threads': torch.get_num_threads(), 'gpu_used': False}))
        (output/'prior.private.json').write_bytes(canonical(prior))
        (output/'point_contract.private.json').write_bytes((source/'point_contract.private.json').read_bytes())

        def forward(model, pose):
            nonlocal count
            journal.check_budget()
            with torch.no_grad():
                r = model(hand_pose=torch.from_numpy(np.asarray(pose, np.float32)),
                    betas=torch.zeros(1, 10), global_orient=torch.zeros(1, 3), transl=torch.zeros(1, 3),
                    return_verts=True, return_full_pose=True)
            values = {name: getattr(r, name).numpy().copy() for name in ('full_pose', 'vertices', 'joints')}
            if any(not np.isfinite(v).all() for v in values.values()): raise ValueError('Nonfinite actual SDK output')
            journal.frame_completed(count, True); count += 1
            return values

        # All representation checks precede the64 experimental proposals.
        models = {}; bases = {}; meshes = {}; components = {}
        for hand in HANDS:
            start = time.perf_counter_ns()
            with journal.stage(hand+'_setup_neutral_and_representation_controls'):
                kwargs = {'is_rhand': hand == 'right', 'flat_hand_mean': True, 'batch_size': 1, 'dtype': torch.float32}
                full_model = smplx.MANO(str(Path(intake).resolve()/'models'), use_pca=False, **kwargs).to('cpu').eval()
                pca_model = smplx.MANO(str(Path(intake).resolve()/'models'), use_pca=True, num_pca_comps=6, **kwargs).to('cpu').eval()
                if tuple(full_model.parents.tolist()) != RAW_PARENTS or not np.array_equal(full_model.faces, pca_model.faces):
                    raise ValueError('Model topology differs')
                comp = pca_model.hand_components.numpy().copy()
                if not np.array_equal(full_model.hand_mean.numpy(), np.zeros(45, np.float32)):
                    raise ValueError('Flat hand mean must be zero')
                neutral = forward(full_model, np.zeros((1, 45), np.float32))
                points = canonicalize(neutral['vertices'], neutral['joints'], tip_ids)[0]
                basis = template_basis(points, hand)
                with np.load(source/(hand+'_fresh_neutral.private.npz'), allow_pickle=False) as previous:
                    if not np.array_equal(previous['vertices'], neutral['vertices']): raise ValueError('Neutral source replay differs')
                    if np.abs(previous['basis']-basis).max() > 1e-6: raise ValueError('Neutral anatomical basis differs')
                coeff, _ = propose(hand, 7, 0)
                a = forward(pca_model, coeff.astype(np.float32).reshape(1, 6))
                b = forward(full_model, expand(coeff, comp))
                errors = representation_errors(a, b)
                controls.append({'hand': hand, 'max_absolute_errors': errors, 'tolerance': 1e-6})
                np.savez_compressed(output/(hand+'_representation.private.npz'), components=comp,
                    coefficients=coeff, basis=basis, faces=full_model.faces,
                    **{'pca_'+k: v for k, v in a.items()}, **{'full_'+k: v for k, v in b.items()})
                models[hand] = full_model; bases[hand] = basis; meshes[hand] = topology(full_model.faces, 778); components[hand] = comp
                del pca_model
            setups.append({'hand': hand, 'wall_ns': time.perf_counter_ns()-start, 'native_forwards_n': 3})
        for hand in HANDS:
            for seed in SEEDS:
                parent = f'{hand}_s{seed}_middle_only_cues_open_author_exact'
                if not any(c['case'] == parent for c in source_summary['cases']): raise ValueError('Missing baseline recipe parent')
                old = json.loads((source/parent/'proposal.private.json').read_text())
                spec = recipe(seed, 'middle_only_cues_open', 'preflex20')
                if old['recipe'] != spec: raise ValueError('Existing authored recipe drift')
                _, angles_a = trajectory(spec, hand, 'author_exact')
                for attempt in range(8):
                    for arm in ('A', 'B'):
                        journal.check_budget(); case_id = f'{arm}_{hand}_s{seed}_a{attempt}'
                        directory = output/case_id; directory.mkdir(); timer = Timings(); state = 'INCOMPLETE'
                        try:
                            with journal.stage(case_id):
                                with timer.phase('proposal_and_expand'):
                                    if arm == 'A':
                                        index = A_INDICES[attempt]; coeff = np.empty(0)
                                        pose = compose_anatomical(angles_a[index:index+1], bases[hand]).astype(np.float32)
                                        proposal = {'primitive': 'middle_only_cues_open', 'entry': 'preflex20',
                                            'source_frame_index': index, 'parent_case': parent, 'corrections': []}
                                    else:
                                        coeff, proposal = propose(hand, seed, attempt); pose = expand(coeff, components[hand])
                                    (directory/'proposal.private.json').write_bytes(canonical({**proposal,
                                        'hand': hand, 'seed': seed, 'attempt': attempt, 'coefficients_drawn_float64': coeff.tolist(),
                                        'coefficients_sdk_float32': coeff.astype(np.float32).tolist(), 'beta_zero': True, 'root_zero': True}))
                                with timer.phase('native_forward'):
                                    result = forward(models[hand], pose)
                                    if np.abs(result['full_pose'][:, 3:]-pose).max() > 1e-6 or result['full_pose'][:, :3].any():
                                        raise ValueError('Actual SDK pose/root differs from proposal')
                                with timer.phase('anatomical_model_and_surface_QA'):
                                    angles = extract_anatomical(result['full_pose'][:, 3:], bases[hand])
                                    strict, effective = assess(angles, prior)
                                    surface = surface_frame(result['vertices'][0], meshes[hand])
                                    decision = decide(effective, surface)
                                    points = canonicalize(result['vertices'], result['joints'], tip_ids)
                                    (directory/'QA.private.json').write_bytes(canonical({'surface': surface,
                                        'strict_excess_radians': strict.tolist(), 'effective_excess_radians': effective.tolist(),
                                        'anatomical_euler_radians': angles.tolist(), 'decision': decision}))
                                with timer.phase('native_store'):
                                    np.savez_compressed(directory/'native_output.private.npz', **result,
                                        canonical_points=points, input_nonroot_axis_angle=pose,
                                        betas=np.zeros((1, 10), np.float32), coefficients=coeff)
                                state = 'COMPLETED'
                        finally:
                            timing = timer.snapshot(None, state)
                            timing.update(kind='static_pose_generation_and_QA',
                                boundary='proposal/SDK/model-surface QA/store; no video, shared setup excluded')
                            (directory/'timing.private.json').write_bytes(canonical(timing))
                        row = {'case_id': case_id, 'arm': arm, 'hand': hand, 'seed': seed, 'attempt': attempt,
                            'strict_model_excess_components_n': int(np.count_nonzero(strict)),
                            'effective_model_excess_components_n': int(np.count_nonzero(effective)),
                            'effective_model_excess_max_radians': float(effective.max()),
                            'surface_pairs_n': len(surface['pair_ids'].get('intersects', [])),
                            'surface_state': surface['state'], 'timing': timing, **decision}
                        (directory/'decision.private.json').write_bytes(canonical(row)); cases.append(row)
                    print('TF02 paired proposals '+str(len(cases)//2)+'/32', flush=True)
        if count != 70 or len(cases) != 64: raise ValueError('Registered denominator differs')
        authorize_inputs(intake, research_record)
        if verify(source_record) != before: raise ValueError('Parent receipt changed')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed: journal.close_without_terminal()
    export_bundle(output/'journal', output/'journal_bundle.private.zip')
    checked = verify_bundle(output/'journal_bundle.private.zip')
    by_arm = {}
    for arm in ('A', 'B', 'U'):
        rows = [r for r in cases if r['arm'] == ('B' if arm == 'U' else arm)]
        by_arm[arm] = {'proposals_n': len(rows), 'model_prior_zero_n': sum(r['effective_model_excess_components_n'] == 0 for r in rows),
            'sampled_surface_clear_n': sum(r['surface_state'] == 'NO_TESTED_PAIR_INTERSECTION' for r in rows),
            'model_surface_eligible_measured_n': sum(r['model_surface_eligible'] for r in rows),
            'gate_applied': arm != 'U', 'shared_geometry_with': 'B' if arm == 'U' else None,
            'new_sdk_forwards_n': 0 if arm == 'U' else 32, 'accepted_into_pool_n': 0}
    summary = {'version': VERSION, 'cases': cases, 'by_arm': by_arm, 'representation_controls': controls,
        'shared_setups': setups, 'native_forward_poses_n': count, 'unique_experimental_proposals_n': 64,
        'nominal_arm_rows_n': 96, 'U_reuses_B_geometry_and_measurements': True,
        'core_wall_ns': time.perf_counter_ns()-core_wall, 'core_process_cpu_ns': time.process_time_ns()-core_cpu,
        'journal_status': checked['status'], 'pending_BMC_state': 'UNRESOLVED_LIMITS',
        'new_motion_sequences_n': 0, 'new_videos_n': 0, 'human_validity_proven': False,
        'new_independent_families_n': 0, 'accepted_into_pool_n': 0, 'release_allowed': False}
    (output/'summary.json').write_bytes(canonical(summary))
    return {k: v for k, v in summary.items() if k != 'cases'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'source-record', 'intake', 'research-record', 'loss-source', 'worker-root', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    a = parser.parse_args()
    print(json.dumps(execute(a.source, a.source_record, a.intake, a.research_record, a.loss_source, a.worker_root, a.output)))
