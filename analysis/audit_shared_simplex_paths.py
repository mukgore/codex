"""Recorded shared-simplex supplement on saved TF03 meshes; no new SDK calls."""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from analysis.shared_simplex_intersections import VERSION, EPSILON, EXPECTED, OVERLAP, UNRESOLVED, DEGENERATE, topology, frame
from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private, canonical


def run(source, source_record, output):
    source, source_record, output = map(_private, (source, source_record, output))
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (source, source_record)):
        raise ValueError('Fresh independent supplement root required')
    before = verify(source_record)
    receipt = json.loads((source_record/'receipt.private.json').read_text())
    if before['state'] != 'EXITED_ZERO' or receipt['artifact_roots'] != [str(source)]:
        raise ValueError('Exact completed source binding required')
    summary = json.loads((source/'summary.json').read_text())
    if (summary['paths_n'], summary['frames_n'], summary['release_allowed']) != (4, 100, False):
        raise ValueError('Registered TF03 four-path source required')
    cases = sorted(summary['paths'], key=lambda p: p['case_id'])
    if {p['case_id'] for p in cases} != {'left_s7', 'left_s19', 'right_s7', 'right_s19'}:
        raise ValueError('Fixed hand/seed denominator required')
    journal = Journal(output/'journal', {
        'condition_id': 'TF03_SHARED_SIMPLEX_SUPPLEMENT_V1',
        'endpoint': 'saved_mesh_shared_face_pairs_outside_common_simplex',
        'input_exposure': 'private saved model vertices/topology; not a pixel-only attack',
        'cache_state': 'sequential saved arrays; uncontrolled OS/module caches',
        'planned_frames': 100, 'timeout_seconds': 1800,
        'scope': 'sampled floating-point supplement; not volume, CCD, physics or human admission'})
    started, wall, cpu = time.time_ns(), time.perf_counter_ns(), time.process_time_ns()
    rows = []; completed = 0
    try:
        for case in cases:
            name = case['case_id']; hand = case['hand']; frames = []
            with np.load(source/(hand+'_setup.private.npz'), allow_pickle=False) as setup:
                mesh = topology(setup['faces'], 778)
            if mesh['shared_pairs_n'] > 200000:
                raise ValueError('Shared pair budget exceeded')
            with np.load(source/name/'native_output.private.npz', allow_pickle=False) as saved:
                vertices, times = saved['vertices'], saved['times_seconds']
                if (vertices.shape != (25, 778, 3) or times.shape != (25,) or
                        not np.isfinite(times).all() or not np.allclose(times, np.linspace(0, 3, 25), atol=1e-12, rtol=0)):
                    raise ValueError('Complete fixed saved frame/time contract required')
                with journal.stage(name+'_shared_pairs'):
                    for index, v in enumerate(vertices):
                        journal.check_budget(); fw, fc = time.perf_counter_ns(), time.process_time_ns()
                        result = frame(v, mesh)
                        if sum(result['counts'].values()) != mesh['shared_pairs_n']:
                            raise ValueError('Complete pair denominator lost')
                        frames.append({'frame_idx': index, 'time_seconds': float(times[index]), **result,
                                       'wall_ns': time.perf_counter_ns()-fw, 'own_cpu_ns': time.process_time_ns()-fc})
                        journal.frame_completed(completed, True); completed += 1
                        print('Shared supplement frames '+str(completed)+'/100', flush=True)
            row = {'case_id': name, 'hand': hand, 'seed': case['seed'], 'frames_n': len(frames),
                   'shared_pairs_per_frame_n': mesh['shared_pairs_n'],
                   'shared_vertex_only_pairs_per_frame_n': int((mesh['shared_n'] == 1).sum()),
                   'shared_edge_pairs_per_frame_n': int((mesh['shared_n'] == 2).sum()),
                   'counts': {key: sum(f['counts'][key] for f in frames) for key in (EXPECTED, OVERLAP, UNRESOLVED, DEGENERATE)},
                   'indicator_frames_n': sum(f['counts'][OVERLAP] > 0 for f in frames),
                   'unresolved_frames_n': sum(f['counts'][UNRESOLVED] > 0 for f in frames),
                   'degenerate_frames_n': sum(f['counts'][DEGENERATE] > 0 for f in frames),
                   'supplement_clear_frames_n': sum(f['supplement_clear'] for f in frames),
                   'source_nonshared_nonclear_frames_n': case['surface_nonclear_frames_n'],
                   'frame_compute_wall_ns': sum(f['wall_ns'] for f in frames),
                   'frame_compute_own_cpu_ns': sum(f['own_cpu_ns'] for f in frames)}
            (output/(name+'.shared_surface.private.json')).write_bytes(canonical({'summary': row, 'frames': frames}))
            rows.append(row)
        if completed != 100 or verify(source_record) != before:
            raise ValueError('Source evidence or complete frame denominator changed')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:
            journal.close_without_terminal()
    export_bundle(output/'journal', output/'journal_bundle.private.zip')
    checked = verify_bundle(output/'journal_bundle.private.zip')
    result = {'version': VERSION, 'scope': 'TF03_saved_mesh_shared_simplex_supplement',
              'paths_n': len(rows), 'frames_n': completed, 'cases': rows,
              'relative_epsilon': EPSILON, 'counts': {key: sum(r['counts'][key] for r in rows) for key in (EXPECTED, OVERLAP, UNRESOLVED, DEGENERATE)},
              **{key: sum(r[key] for r in rows) for key in ('indicator_frames_n', 'unresolved_frames_n', 'degenerate_frames_n', 'supplement_clear_frames_n')},
              'new_SDK_calls_n': 0, 'new_videos_n': 0, 'new_human_trials_n': 0,
              'accepted_into_pool_n': 0, 'release_allowed': False,
              'continuous_collision_free_proven': False, 'volume_penetration_free_proven': False,
              'biological_validity_proven': False, 'source_quarantine_preserved': True,
              'journal_status': checked['status'],
              'timing': {'started_utc_epoch_ns': started, 'ended_utc_epoch_ns': time.time_ns(),
                         'wall_ns': time.perf_counter_ns()-wall, 'own_cpu_ns': time.process_time_ns()-cpu,
                         'scope': 'source loading, topology, per-frame supplement, store/journal and source receipt recheck; recorder excluded'},
              'limitations': ['Existing non-shared-pair SAT not rerun or replaced.',
                              'Floating-point tolerance and ill-conditioned pairs can remain unresolved.',
                              'Off-simplex contact is an indicator, not measured penetration volume/depth.',
                              'No continuous collision, closed-surface containment, hand-object physics or human comfort approval.']}
    (output/'summary.json').write_bytes(canonical(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'source-record', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    result = run(**vars(parser.parse_args()))
    print(json.dumps({k: result[k] for k in ('paths_n', 'frames_n', 'counts', 'supplement_clear_frames_n')}))
