"""Recorded rational follow-up only on the eight unresolved float pair instances."""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from analysis.exact_shared_simplex import VERSION, pair, tolerance_squared
from analysis.shared_simplex_intersections import EPSILON
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private, canonical


def bound(root, record):
    root, record = _private(root), _private(record)
    checked = verify(record)
    receipt = json.loads((record/'receipt.private.json').read_text())
    if checked['state'] != 'EXITED_ZERO' or receipt['artifact_roots'] != [str(root)]:
        raise ValueError('Exact successful source/record binding required')
    return root, record, checked


def run(source, source_record, supplement, supplement_record, output):
    source, source_record, source_before = bound(source, source_record)
    supplement, supplement_record, supplement_before = bound(supplement, supplement_record)
    output = _private(output)
    if output.exists() or any(output.is_relative_to(r) or r.is_relative_to(output) for r in (source, source_record, supplement, supplement_record)):
        raise ValueError('Fresh independent output required')
    ss = json.loads((supplement/'summary.json').read_text())
    if ss['frames_n'] != 100 or ss['relative_epsilon'] != EPSILON or ss['counts']['NUMERICALLY_UNRESOLVED'] != 8:
        raise ValueError('Fixed completed 100-frame/eight-residual supplement required')
    output.mkdir(); rows = []; started, wall, cpu = time.time_ns(), time.perf_counter_ns(), time.process_time_ns()
    for case in ss['cases']:
        name, hand = case['case_id'], case['hand']
        if name not in {'left_s7', 'left_s19', 'right_s7', 'right_s19'} or hand not in ('left', 'right'):
            raise ValueError('Registered source cases required')
        stored = json.loads((supplement/(name+'.shared_surface.private.json')).read_text())
        with np.load(source/(hand+'_setup.private.npz'), allow_pickle=False) as setup:
            faces = setup['faces'].copy()
        with np.load(source/name/'native_output.private.npz', allow_pickle=False) as native:
            vertices = native['vertices'].copy()
        for frame in stored['frames']:
            for i, j in frame['unresolved_pair_ids']:
                start, own = time.perf_counter_ns(), time.process_time_ns()
                v = vertices[frame['frame_idx']]; common = np.intersect1d(faces[i], faces[j])
                if len(common) not in (1, 2):
                    raise ValueError('Shared simplex correspondence lost')
                result = pair(v[faces[i]], v[faces[j]], v[common], tolerance_squared(v, EPSILON))
                row = {'case_id': name, 'frame_idx': frame['frame_idx'], 'face_pair_ids': [i, j],
                       'shared_vertices_n': len(common), **result,
                       'wall_ns': time.perf_counter_ns()-start, 'own_cpu_ns': time.process_time_ns()-own}
                (output/(f'r{len(rows):02d}.private.json')).write_bytes(canonical(row)); rows.append(row)
                print('Exact residual pairs '+str(len(rows))+'/8', flush=True)
    if len(rows) != 8 or verify(source_record) != source_before or verify(supplement_record) != supplement_before:
        raise ValueError('Residual denominator or evidence changed')
    result = {'version': VERSION, 'scope': 'followup_of_eight_unresolved_pair_instances_only',
              'pairs_n': len(rows), 'unique_frames_n': len({(r['case_id'], r['frame_idx']) for r in rows}),
              'resolved_n': sum(r['resolved'] for r in rows),
              'exact_off_shared_simplex_n': sum(r.get('intersection_outside_shared_simplex_exactly', False) for r in rows),
              'beyond_registered_resolution_n': sum(r.get('beyond_registered_resolution', False) for r in rows),
              'branches': {key: sum(r.get('branch') == key for r in rows) for key in sorted({r.get('branch', 'degenerate') for r in rows})},
              'relative_epsilon': EPSILON, 'original_float_supplement_preserved': True,
              'all_pairs_rationally_checked': False, 'new_SDK_calls_n': 0, 'new_videos_n': 0,
              'new_human_trials_n': 0, 'accepted_into_pool_n': 0, 'release_allowed': False,
              'continuous_collision_free_proven': False, 'volume_penetration_free_proven': False,
              'biological_validity_proven': False,
              'timing': {'started_utc_epoch_ns': started, 'ended_utc_epoch_ns': time.time_ns(),
                         'wall_ns': time.perf_counter_ns()-wall, 'own_cpu_ns': time.process_time_ns()-cpu,
                         'scope': 'residual selection/load/exact geometry/store and both source rechecks; initial source verification and recorder excluded'},
              'limitations': ['Exact arithmetic applies to supplied binary64 coordinates, not unknown physical/anatomical truth.',
                              'Only the eight float-unresolved instances were refined; other float outcomes are not exact-predicate certified.',
                              'No continuous collision, volume containment, physical contact or human validity admission.']}
    (output/'summary.json').write_bytes(canonical(result)); return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'source-record', 'supplement', 'supplement-record', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    result = run(**vars(parser.parse_args()))
    print(json.dumps({k: result[k] for k in ('pairs_n', 'resolved_n', 'exact_off_shared_simplex_n', 'beyond_registered_resolution_n')}))
