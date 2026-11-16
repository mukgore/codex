"""New SDK midpoint samples of the original TF03 Euler/LBS path, not CCD."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import time

import numpy as np

from analysis.audit_exact_shared_residuals import bound
from analysis.exact_shared_simplex import pair as exact_pair, tolerance_squared
from analysis.shared_simplex_intersections import topology as shared_topology, frame as shared_frame, EPSILON, OVERLAP, UNRESOLVED, DEGENERATE
from analysis.template_free_temporal_path import VERSION, evaluate, midpoint_chord_error
from analysis.runtime_benchmark.mano_recorded_producer import authorize_inputs, canonicalize, RAW_PARENTS, TIP_NAMES
from analysis.runtime_benchmark.mano_anatomical_frame_probe import compose_anatomical, extract_anatomical
from analysis.runtime_benchmark.mano_model_prior_audit import extract_profile, assess
from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical, _private


def execute(source, source_record, intake, research_record, loss_source, worker_root, output):
    source, source_record, before = bound(source, source_record)
    ss = json.loads((source/'summary.json').read_text())
    if ss['paths_n'] != 4 or ss['frames_n'] != 100 or ss['release_allowed'] is not False:
        raise ValueError('Complete quarantined TF03 four-path source required')
    output = _private(output)
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (source, source_record)):
        raise ValueError('Fresh independent midpoint output required')
    authorize_inputs(intake, research_record)
    sys.path.insert(0, str(Path(worker_root).resolve(strict=True)))
    from experiments.motion_fixture.mesh_intersections import topology, frame as nonshared_frame
    prior = extract_profile(loss_source)
    journal = Journal(output/'journal', {
        'condition_id': 'TF03_ORIGINAL_EULER_LBS_96_NEW_MIDPOINTS',
        'endpoint': 'new_model_midpoint_geometry_sampled_surface_and_chord_discrepancy_not_CCD',
        'input_exposure': 'saved private source waypoints and licensed CPU model; not pixel-only attack',
        'cache_state': 'shared model per hand; OS/import caches uncontrolled',
        'planned_frames': 98, 'timeout_seconds': 900,
        'scope': '96 new midpoint evaluations plus two fresh neutral checks; no continuous collision certificate'})
    started, wall, cpu = time.time_ns(), time.perf_counter_ns(), time.process_time_ns()
    completed = 0; rows = []; exact_instances = 0
    try:
        import torch
        import smplx
        from smplx.vertex_ids import vertex_ids
        if str(torch.__version__) != '2.5.1+cpu' or importlib.metadata.version('smplx') != '0.1.28':
            raise ValueError('Existing pinned CPU runtime required')
        torch.set_num_threads(1); torch.manual_seed(0)
        tips = {name: vertex_ids['mano'][name] for name in TIP_NAMES}
        (output/'environment.private.json').write_bytes(canonical({
            'python': sys.version, 'numpy': np.__version__, 'torch': str(torch.__version__),
            'smplx': importlib.metadata.version('smplx'), 'torch_threads': 1, 'gpu_used': False}))
        (output/'applied_model_prior.private.json').write_bytes(canonical(prior))
        for hand in ('right', 'left'):
            with journal.stage(hand+'_neutral_correspondence'):
                model = smplx.MANO(str(Path(intake).resolve()/'models'), is_rhand=hand == 'right', use_pca=False,
                                   flat_hand_mean=True, batch_size=1, dtype=torch.float32).to('cpu').eval()
                if tuple(model.parents.tolist()) != RAW_PARENTS:
                    raise ValueError('Model parent tree changed')
                with torch.no_grad():
                    neutral = model(hand_pose=torch.zeros(1, 45), betas=torch.zeros(1, 10),
                                    global_orient=torch.zeros(1, 3), transl=torch.zeros(1, 3), return_verts=True)
                neutral_points = canonicalize(neutral.vertices.numpy(), neutral.joints.numpy(), tips)[0]
                with np.load(source/(hand+'_setup.private.npz'), allow_pickle=False) as setup:
                    basis, faces = setup['basis'].copy(), setup['faces'].copy()
                    neutral_error = float(np.max(np.abs(neutral_points-setup['neutral_points'])))
                if neutral_error > 1e-7 or not np.array_equal(model.faces, faces):
                    raise ValueError('Bound neutral/topology correspondence failed')
                np.savez_compressed(output/(hand+'_neutral.private.npz'), vertices=neutral.vertices.numpy(),
                                    canonical_points=neutral_points, faces=faces, basis=basis)
                journal.frame_completed(completed, True); completed += 1
                mesh, shared_mesh = topology(faces, 778), shared_topology(faces, 778)
            for seed in (7, 19):
                name = f'{hand}_s{seed}'; folder = output/name; folder.mkdir()
                case_start, case_cpu, case_utc = time.perf_counter_ns(), time.process_time_ns(), time.time_ns()
                with np.load(source/name/'native_output.private.npz', allow_pickle=False) as saved:
                    parents, parent_times, proposed = saved['vertices'].copy(), saved['times_seconds'].copy(), saved['proposed_angles'].copy()
                waypoints = proposed[[0, 12, 24]]
                if np.max(np.abs(evaluate(waypoints, parent_times)-proposed)) > 1e-12:
                    raise ValueError('Original sampled Euler definition differs')
                times = (parent_times[:-1]+parent_times[1:])/2
                angles = evaluate(waypoints, times); poses = compose_anatomical(angles, basis).astype(np.float32)
                with journal.stage(name+'_24_new_SDK_midpoints'):
                    with torch.no_grad():
                        result = model(hand_pose=torch.from_numpy(poses), betas=torch.zeros(24, 10),
                                       global_orient=torch.zeros(24, 3), transl=torch.zeros(24, 3), return_verts=True, return_full_pose=True)
                    vertices, raw, full = result.vertices.numpy(), result.joints.numpy(), result.full_pose.numpy()
                    if (vertices.shape != (24, 778, 3) or not np.isfinite(vertices).all() or
                            not np.array_equal(full[:, 3:], poses) or full[:, :3].any()):
                        raise ValueError('Complete actual midpoint SDK contract failed')
                    actual = extract_anatomical(full[:, 3:], basis); strict, effective = assess(actual, prior)
                    chord = midpoint_chord_error(parents, vertices, parent_times, times)
                    np.savez_compressed(folder/'native_output.private.npz', vertices=vertices, raw_joints=raw,
                                        canonical_points=canonicalize(vertices, raw, tips), full_pose=full,
                                        proposed_angles=angles, actual_angles=actual, times_seconds=times,
                                        strict_excess_radians=strict, masked_excess_radians=effective,
                                        chord_vertex_errors_native=chord['per_vertex_native_error'])
                surface_rows = []
                with journal.stage(name+'_new_sample_surface_QA'):
                    for index, v in enumerate(vertices):
                        journal.check_budget(); fw, fc = time.perf_counter_ns(), time.process_time_ns()
                        old = nonshared_frame(v, mesh); shared = shared_frame(v, shared_mesh)
                        exact = []
                        if shared['unresolved_pair_ids']:
                            tol2 = tolerance_squared(v, EPSILON)
                            for i, j in shared['unresolved_pair_ids']:
                                exact_instances += 1
                                if exact_instances > 1024:
                                    raise ValueError('Registered exact fallback budget exceeded')
                                common = np.intersect1d(faces[i], faces[j])
                                exact.append({'face_pair_ids': [i, j], **exact_pair(v[faces[i]], v[faces[j]], v[common], tol2)})
                        unresolved_after = sum(not r['resolved'] for r in exact)
                        exact_overlap = sum(r.get('beyond_registered_resolution', False) for r in exact)
                        sampled_nonclear = (old['state'] != 'NO_TESTED_PAIR_INTERSECTION' or
                                            shared['counts'][OVERLAP] > 0 or shared['counts'][DEGENERATE] > 0 or
                                            unresolved_after > 0 or exact_overlap > 0)
                        surface_rows.append({'frame_idx': index, 'time_seconds': float(times[index]),
                                             'nonshared': old, 'shared': shared, 'exact_residuals': exact,
                                             'unresolved_after_exact_n': unresolved_after,
                                             'exact_beyond_resolution_n': exact_overlap,
                                             'sampled_nonclear': sampled_nonclear,
                                             'chord_max_native_error': float(chord['interval_max_native_error'][index]),
                                             'chord_max_relative_to_endpoint_diagonal': float(chord['interval_max_relative_to_endpoint_diagonal'][index]),
                                             'surface_wall_ns': time.perf_counter_ns()-fw, 'surface_own_cpu_ns': time.process_time_ns()-fc})
                        journal.frame_completed(completed, True); completed += 1
                        print('New midpoint frames '+str(completed-1-(hand == 'left'))+'/96', flush=True)
                (folder/'surface_QA.private.json').write_bytes(canonical(surface_rows))
                row = {'case_id': name, 'hand': hand, 'seed': seed, 'new_midpoint_frames_n': 24,
                       'neutral_correspondence_max_native_error': neutral_error,
                       'model_prior_penalized_frames_n': int(np.any(effective > 0, axis=(1, 2)).sum()),
                       'model_prior_max_excess_radians': float(effective.max()),
                       'nonshared_surface_nonclear_frames_n': sum(r['nonshared']['state'] != 'NO_TESTED_PAIR_INTERSECTION' for r in surface_rows),
                       'shared_overlap_indicator_instances_n': sum(r['shared']['counts'][OVERLAP] for r in surface_rows),
                       'shared_float_unresolved_instances_n': sum(r['shared']['counts'][UNRESOLVED] for r in surface_rows),
                       'exact_residual_instances_n': sum(len(r['exact_residuals']) for r in surface_rows),
                       'unresolved_after_exact_instances_n': sum(r['unresolved_after_exact_n'] for r in surface_rows),
                       'exact_beyond_resolution_instances_n': sum(r['exact_beyond_resolution_n'] for r in surface_rows),
                       'sampled_surface_nonclear_frames_n': sum(r['sampled_nonclear'] for r in surface_rows),
                       'chord_max_native_error': float(chord['interval_max_native_error'].max()),
                       'chord_max_relative_to_endpoint_diagonal': float(chord['interval_max_relative_to_endpoint_diagonal'].max()),
                       'intervals_above_relative_1e_minus_7_n': int((chord['interval_max_relative_to_endpoint_diagonal'] > EPSILON).sum()),
                       'timing': {'started_utc_epoch_ns': case_utc, 'ended_utc_epoch_ns': time.time_ns(),
                                  'wall_ns': time.perf_counter_ns()-case_start, 'own_cpu_ns': time.process_time_ns()-case_cpu},
                       'continuous_collision_free_proven': False, 'release_allowed': False}
                (folder/'summary.private.json').write_bytes(canonical(row)); rows.append(row)
            del model
        if completed != 98 or len(rows) != 4 or verify(source_record) != before:
            raise ValueError('Full denominator or source evidence changed')
        authorize_inputs(intake, research_record); journal.finish('COMPLETED')
    finally:
        if not journal.closed:
            journal.close_without_terminal()
    export_bundle(output/'journal', output/'journal_bundle.private.zip'); checked = verify_bundle(output/'journal_bundle.private.zip')
    summary = {'version': VERSION, 'cases': rows, 'paths_n': 4, 'new_midpoint_frames_n': 96,
               'fresh_neutral_frames_n': 2, 'SDK_pose_evaluations_n': 98, 'SDK_batch_calls_n': 6,
               'original_100_frames_reinferred_n': 0,
               'sampled_surface_nonclear_frames_n': sum(r['sampled_surface_nonclear_frames_n'] for r in rows),
               'model_prior_penalized_frames_n': sum(r['model_prior_penalized_frames_n'] for r in rows),
               'exact_residual_instances_n': exact_instances,
               'intervals_above_relative_1e_minus_7_n': sum(r['intervals_above_relative_1e_minus_7_n'] for r in rows),
               'continuous_collision_free_proven': False, 'chord_remainder_supremum_bound_available': False,
               'linear_vertex_CCD_applicable_to_original_model_path_without_remainder': False,
               'new_videos_n': 0, 'new_human_trials_n': 0, 'accepted_into_pool_n': 0, 'release_allowed': False,
               'journal_status': checked['status'],
               'timing': {'started_utc_epoch_ns': started, 'ended_utc_epoch_ns': time.time_ns(),
                          'wall_ns': time.perf_counter_ns()-wall, 'own_cpu_ns': time.process_time_ns()-cpu,
                          'scope': 'model import/setup, new neutral/midpoint SDK, sampled QA/chord/store and source recheck; initial receipt verification and recorder excluded'},
               'limitations': ['Midpoint sample errors are observations, not all-time chord-deviation upper bounds.',
                               'Endpoint and midpoint clearance cannot certify continuous collision absence.',
                               'Actual producer composes Euler rotations via axis-angle/float32 and SDK Rodrigues/LBS; no ideal-rotation numerical parity guarantee.',
                               'No closed-volume containment, hand-object physics, clinical limits or human comfort approval.']}
    (output/'summary.json').write_bytes(canonical(summary)); return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'source-record', 'intake', 'research-record', 'loss-source', 'worker-root', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    summary = execute(**vars(parser.parse_args()))
    print(json.dumps({k: summary[k] for k in ('new_midpoint_frames_n', 'sampled_surface_nonclear_frames_n', 'model_prior_penalized_frames_n')}))
