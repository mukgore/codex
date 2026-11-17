"""Publish aggregate conditional candidates, never private model/vertex boxes."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

from analysis.audit_exact_shared_residuals import bound
from validation_v03.execution_record import verify


def export(first, first_record, refined, refined_record, report, timings):
    first, first_record, first_checked = bound(first, first_record)
    refined, refined_record, refined_checked = bound(refined, refined_record)
    report, timings = Path(report).resolve(), Path(timings).resolve()
    if report == timings or report.exists() or timings.exists():
        raise FileExistsError('Distinct fresh public outputs required')
    if any(p.is_relative_to(r) for p in (report, timings) for r in (first, first_record, refined, refined_record)):
        raise ValueError('Immutable private evidence cannot be export destinations')
    runs = {}; rows = []; comparisons = []
    for label, root, record, status, expected in (
            ('v1', first, first_record, first_checked, 192), ('v2', refined, refined_record, refined_checked, 768)):
        summary = json.loads((root/'summary.json').read_text())
        if (summary['attempted_leaves_n'] != expected or summary['SDK_forwards_n'] != 0 or
                summary['backend_error_bounds_validated'] is not False or summary['CCD_clearance'] is not False):
            raise ValueError('Complete explicitly conditional runs required')
        checked_points = set(); reasons = {}; run_rows = []
        for case in summary['cases']:
            leaves = json.loads((root/(case['case_id']+'.leaves.private.json')).read_text())
            for leaf in leaves:
                if leaf['status'] == 'UNRESOLVED':
                    reasons[leaf['reason']] = reasons.get(leaf['reason'], 0)+1
                elif label == 'v1':
                    checked_points.update((case['case_id'], leaf[k]) for k in ('t0_seconds', 't1_seconds'))
                run_rows.append({'run': label, 'case_id': case['case_id'], 'interval_idx': leaf['interval_idx'],
                                 'subdivision_idx': leaf.get('subdivision_idx', leaf.get('half_idx')),
                                 **{k: leaf[k] for k in ('t0_seconds', 't1_seconds', 'status', 'checkpoint_comparisons_n',
                                                       'outside_checkpoint_coordinates_n', 'wall_ns', 'own_cpu_ns')},
                                 'reason': leaf.get('reason'),
                                 'maximum_vertex_box_width_native': leaf.get('maximum_vertex_box_width_native'),
                                 'maximum_chord_remainder_native': leaf.get('maximum_chord_remainder_native'),
                                 'backend_error_bounds_validated': False, 'CCD_clearance': False})
        if len(run_rows) != expected:
            raise ValueError('Complete leaf accounting required')
        manifest = json.loads((record/'provenance/manifest.json').read_text())
        summary.update(execution_record=status, producer_code_commit=manifest['code_commit'],
                       recorded_input_files_n=len(manifest['inputs']), recorded_dependency_pins_n=len(manifest['pinned_versions']),
                       unresolved_reasons=reasons,
                       unique_checked_observation_frames_n=len(checked_points) if label == 'v1' else summary['unique_checked_observation_frames_n'])
        runs[label] = summary; rows.extend(run_rows)
    if runs['v1']['assumptions'] != runs['v2']['assumptions']:
        raise ValueError('Refinement must preserve backend assumptions')
    for hand in ('right', 'left'):
        with np.load(first/(hand+'_buffers.private.npz'), allow_pickle=False) as a, np.load(refined/(hand+'_buffers.private.npz'), allow_pickle=False) as b:
            if set(a.files) != set(b.files) or any(not np.array_equal(a[k], b[k]) for k in a.files):
                raise ValueError('Model buffer correspondence changed')
    for case in runs['v1']['cases']:
        name = case['case_id']
        with np.load(first/(name+'.boxes.private.npz'), allow_pickle=False) as a, np.load(refined/(name+'.boxes.private.npz'), allow_pickle=False) as b:
            common = a['interval_remainder_valid'] & b['interval_remainder_valid']
            old, new = a['conditional_chord_remainder_upper'][common], b['conditional_chord_remainder_upper'][common]
        ratios = new[old > 0]/old[old > 0]
        comparisons.append({'case_id': name, 'common_complete_original_intervals_n': int(common.sum()),
                            'vertex_interval_entries_compared_n': int(old.size),
                            'strictly_smaller_candidate_entries_n': int((new < old).sum()),
                            'new_over_old_ratio_median': float(np.median(ratios)) if len(ratios) else None,
                            'new_over_old_ratio_max': float(ratios.max()) if len(ratios) else None})
    result = {'scope': 'conditional_path_envelope_candidates_not_validated_backend_or_CCD',
              'runs': runs, 'comparisons': comparisons, 'leaf_timing_rows_n': len(rows),
              'model_buffers_bitwise_correspond': True, 'assumptions_unchanged': True,
              'backend_error_bounds_validated': False, 'continuous_collision_free_proven': False,
              'CCD_clearance': False, 'release_allowed': False}
    with timings.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    if verify(first_record) != first_checked or verify(refined_record) != refined_checked:
        raise ValueError('Private evidence changed during export')
    return {'source_records_intact': True, 'leaf_timing_rows_n': len(rows), 'CCD_clearance': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('first', 'first-record', 'refined', 'refined-record', 'report', 'timings'):
        parser.add_argument('--'+name, type=Path, required=True)
    print(json.dumps(export(**vars(parser.parse_args()))))
