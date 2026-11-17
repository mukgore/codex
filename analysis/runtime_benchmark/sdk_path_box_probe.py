"""Recorded conditional interval candidates, checked against saved observations.

No SDK forwards are repeated. A passing sample check cannot validate backend
error assumptions or continuous collision absence.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np

from analysis.audit_exact_shared_residuals import bound
from analysis.runtime_benchmark.mano_recorded_producer import authorize_inputs, RAW_PARENTS
from analysis.runtime_benchmark.sdk_path_boxes import VERSION, ASSUMPTIONS, local_rotations, lbs_box, chord_remainder
from analysis.runtime_benchmark.interval_boxes import Unresolved
from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private, canonical


def execute(source, source_record, midpoint, midpoint_record, intake, research_record, output):
    source, source_record, before = bound(source, source_record)
    midpoint, midpoint_record, mid_before = bound(midpoint, midpoint_record)
    output = _private(output)
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (source, source_record, midpoint, midpoint_record)):
        raise ValueError('Fresh independent box probe output required')
    ss = json.loads((source/'summary.json').read_text()); ms = json.loads((midpoint/'summary.json').read_text())
    if ss['frames_n'] != 100 or ms['new_midpoint_frames_n'] != 96 or ms['release_allowed'] is not False:
        raise ValueError('Registered original and midpoint observations required')
    authorize_inputs(intake, research_record)
    journal = Journal(output/'journal', {
        'condition_id': 'TF03_SDK_PATH_CONDITIONAL_BOXES',
        'endpoint': '192 conditional half-interval boxes and saved observation containment',
        'input_exposure': 'private saved meshes/waypoints and licensed model buffers; not an attack',
        'cache_state': 'CPU interval arithmetic; module/model file cache uncontrolled',
        'planned_frames': 192, 'timeout_seconds': 900,
        'scope': 'journal frame means attempted time leaf, not model inference; no backend/CCD certification'})
    utc, wall, cpu = time.time_ns(), time.perf_counter_ns(), time.process_time_ns()
    cases = []; completed = 0
    try:
        import torch
        import smplx
        if str(torch.__version__) != '2.5.1+cpu' or importlib.metadata.version('smplx') != '0.1.28':
            raise ValueError('Existing pinned CPU buffer reader required')
        torch.set_num_threads(1)
        (output/'assumptions.private.json').write_bytes(canonical(ASSUMPTIONS))
        (output/'environment.private.json').write_bytes(canonical({
            'torch': str(torch.__version__), 'numpy': np.__version__,
            'scipy': importlib.metadata.version('scipy'), 'mpmath': importlib.metadata.version('mpmath'),
            'smplx': importlib.metadata.version('smplx'), 'SDK_forwards_n': 0, 'gpu_used': False}))
        for hand in ('right', 'left'):
            model = smplx.MANO(str(Path(intake).resolve()/'models'), is_rhand=hand == 'right', use_pca=False,
                               flat_hand_mean=True, batch_size=1, dtype=torch.float32).to('cpu').eval()
            if tuple(model.parents.tolist()) != RAW_PARENTS or model.pose_mean.any():
                raise ValueError('Bound model tree/zero mean contract differs')
            buffers = {key: getattr(model, attr).detach().cpu().numpy().copy() for key, attr in (
                ('template', 'v_template'), ('regressor', 'J_regressor'), ('posedirs', 'posedirs'), ('weights', 'lbs_weights'))}
            np.savez_compressed(output/(hand+'_buffers.private.npz'), **buffers, parents=model.parents.numpy())
            with np.load(source/(hand+'_setup.private.npz'), allow_pickle=False) as setup:
                basis = setup['basis'].copy()
                if not np.array_equal(setup['faces'], model.faces):
                    raise ValueError('Bound mesh indexing differs')
            for seed in (7, 19):
                name = f'{hand}_s{seed}'; rows = []; lower = np.zeros((48, 778, 3)); upper = lower.copy()
                remainder = np.zeros((24, 778)); valid = np.zeros(48, bool)
                with np.load(source/name/'native_output.private.npz', allow_pickle=False) as old:
                    vertices, times, waypoints = old['vertices'].copy(), old['times_seconds'].copy(), old['proposed_angles'][[0, 12, 24]].copy()
                with np.load(midpoint/name/'native_output.private.npz', allow_pickle=False) as new:
                    mid_vertices, mid_times = new['vertices'].copy(), new['times_seconds'].copy()
                if (vertices.shape != (25, 778, 3) or mid_vertices.shape != (24, 778, 3) or
                        not np.array_equal(times, np.linspace(0, 3, 25)) or not np.array_equal(mid_times, (times[:-1]+times[1:])/2)):
                    raise ValueError('Complete corresponding saved temporal grids required')
                with journal.stage(name+'_48_conditional_time_leaves'):
                    for interval in range(24):
                        for half in range(2):
                            journal.check_budget(); leaf = 2*interval+half; start, own = time.perf_counter_ns(), time.process_time_ns()
                            f0, f1 = half/2, (half+1)/2
                            t0, t1 = times[interval]+f0*.125, times[interval]+f1*.125
                            row = {'case_id': name, 'interval_idx': interval, 'half_idx': half,
                                   't0_seconds': float(t0), 't1_seconds': float(t1), 'status': 'UNRESOLVED',
                                   'checkpoint_comparisons_n': 0, 'outside_checkpoint_coordinates_n': 0,
                                   'backend_error_bounds_validated': False, 'CCD_clearance': False}
                            try:
                                rotations = local_rotations(waypoints, basis, float(t0), float(t1))
                                box = lbs_box(rotations, **buffers, parents=RAW_PARENTS)
                                error = chord_remainder(box, vertices[interval], vertices[interval+1], f0, f1)
                                lower[leaf], upper[leaf], valid[leaf] = box.lo, box.hi, True
                                remainder[interval] = np.maximum(remainder[interval], error)
                                checkpoints = (vertices[interval], mid_vertices[interval]) if half == 0 else (mid_vertices[interval], vertices[interval+1])
                                outside = sum(int(((p < box.lo) | (p > box.hi)).sum()) for p in checkpoints)
                                row.update(status='SAVED_OBSERVATION_OUTSIDE_CANDIDATE' if outside else 'CONDITIONAL_CANDIDATE',
                                           checkpoint_comparisons_n=2, outside_checkpoint_coordinates_n=outside,
                                           maximum_vertex_box_width_native=float((box.hi-box.lo).max()),
                                           maximum_chord_remainder_native=float(error.max()))
                            except Unresolved as error:
                                row['reason'] = str(error)
                            row.update(wall_ns=time.perf_counter_ns()-start, own_cpu_ns=time.process_time_ns()-own)
                            rows.append(row); completed += 1; journal.frame_completed(completed-1, row['status'] != 'UNRESOLVED')
                            print('Conditional time leaves '+str(completed)+'/192', flush=True)
                np.savez_compressed(output/(name+'.boxes.private.npz'), lower=lower, upper=upper, valid=valid,
                                    conditional_chord_remainder_upper=remainder,
                                    interval_remainder_valid=valid.reshape(24, 2).all(axis=1))
                (output/(name+'.leaves.private.json')).write_bytes(canonical(rows))
                finite = [r for r in rows if r['status'] != 'UNRESOLVED']
                cases.append({'case_id': name, 'hand': hand, 'seed': seed, 'leaves_n': len(rows),
                              'finite_candidate_leaves_n': len(finite), 'unresolved_leaves_n': len(rows)-len(finite),
                              'checkpoint_comparisons_n': sum(r['checkpoint_comparisons_n'] for r in rows),
                              'outside_checkpoint_coordinates_n': sum(r['outside_checkpoint_coordinates_n'] for r in rows),
                              'complete_original_intervals_n': int(valid.reshape(24, 2).all(axis=1).sum()),
                              'conditional_max_chord_remainder_native': max((r['maximum_chord_remainder_native'] for r in finite), default=None),
                              'backend_error_bounds_validated': False, 'CCD_clearance': False})
            del model
        if completed != 192 or verify(source_record) != before or verify(midpoint_record) != mid_before:
            raise ValueError('Registered denominator or saved evidence changed')
        authorize_inputs(intake, research_record); journal.finish('COMPLETED')
    finally:
        if not journal.closed:
            journal.close_without_terminal()
    export_bundle(output/'journal', output/'journal_bundle.private.zip'); checked = verify_bundle(output/'journal_bundle.private.zip')
    summary = {'version': VERSION, 'cases': cases, 'attempted_leaves_n': completed,
               'finite_candidate_leaves_n': sum(c['finite_candidate_leaves_n'] for c in cases),
               'unresolved_leaves_n': sum(c['unresolved_leaves_n'] for c in cases),
               'checkpoint_comparisons_n': sum(c['checkpoint_comparisons_n'] for c in cases),
               'outside_checkpoint_coordinates_n': sum(c['outside_checkpoint_coordinates_n'] for c in cases),
               'unique_saved_observation_frames_n': 196, 'model_buffer_loads_n': 2, 'SDK_forwards_n': 0,
               'assumptions': dict(ASSUMPTIONS), 'backend_error_bounds_validated': False,
               'continuous_collision_free_proven': False, 'CCD_clearance': False,
               'accepted_into_pool_n': 0, 'release_allowed': False, 'new_videos_n': 0, 'new_human_trials_n': 0,
               'journal_status': checked['status'],
               'timing': {'started_utc_epoch_ns': utc, 'ended_utc_epoch_ns': time.time_ns(),
                          'wall_ns': time.perf_counter_ns()-wall, 'own_cpu_ns': time.process_time_ns()-cpu,
                          'scope': 'model buffer loading, interval candidates, stored checks, store/journal and source rechecks; initial receipt verification/recorder excluded'},
               'limitations': ['Stored sample containment is a regression check, not proof of a target-backend error envelope.',
                               'Transcendental and producer-polynomial padding values are explicit unvalidated engineering assumptions.',
                               'No linear/nonlinear CCD narrow phase, whole-time shared-simplex proof, volume or biological admission.']}
    (output/'summary.json').write_bytes(canonical(summary)); return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'source-record', 'midpoint', 'midpoint-record', 'intake', 'research-record', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    result = execute(**vars(parser.parse_args()))
    print(json.dumps({k: result[k] for k in ('attempted_leaves_n', 'finite_candidate_leaves_n', 'unresolved_leaves_n', 'outside_checkpoint_coordinates_n')}))
