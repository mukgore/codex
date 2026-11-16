"""Aggregate-only export of new TF03 midpoint geometry and surface timings."""
import argparse
import csv
import json
from pathlib import Path

from analysis.audit_exact_shared_residuals import bound
from validation_v03.execution_record import verify


def export(root, record, report, timings):
    root, record, checked = bound(root, record)
    report, timings = Path(report).resolve(), Path(timings).resolve()
    if report == timings or report.exists() or timings.exists():
        raise FileExistsError('Distinct fresh outputs required')
    if any(p.is_relative_to(r) for p in (report, timings) for r in (root, record)):
        raise ValueError('Immutable sources cannot be export destinations')
    summary = json.loads((root/'summary.json').read_text())
    if (summary['new_midpoint_frames_n'], summary['SDK_pose_evaluations_n']) != (96, 98):
        raise ValueError('Complete registered midpoint denominator required')
    rows = []; exact = []; shared_counts = {}; narrow = 0
    for case in summary['cases']:
        frames = json.loads((root/case['case_id']/'surface_QA.private.json').read_text())
        for frame in frames:
            for key, value in frame['shared']['counts'].items():
                shared_counts[key] = shared_counts.get(key, 0)+value
            narrow += frame['nonshared']['tested_pairs_n']; exact.extend(frame['exact_residuals'])
            rows.append({'case_id': case['case_id'], 'hand': case['hand'], 'seed': case['seed'],
                         **{k: frame[k] for k in ('frame_idx', 'time_seconds', 'sampled_nonclear',
                                                 'unresolved_after_exact_n', 'exact_beyond_resolution_n',
                                                 'chord_max_native_error', 'chord_max_relative_to_endpoint_diagonal',
                                                 'surface_wall_ns', 'surface_own_cpu_ns')},
                         'nonshared_state': frame['nonshared']['state'],
                         'nonshared_narrow_phase_pair_instances_n': frame['nonshared']['tested_pairs_n'],
                         **frame['shared']['counts'], 'exact_residual_instances_n': len(frame['exact_residuals'])})
    if len(rows) != 96 or len(exact) != summary['exact_residual_instances_n']:
        raise ValueError('Frame/residual totals differ')
    manifest = json.loads((record/'provenance/manifest.json').read_text())
    summary.update(execution_record=checked, producer_code_commit=manifest['code_commit'],
                   recorded_input_files_n=len(manifest['inputs']), recorded_dependency_pins_n=len(manifest['pinned_versions']),
                   frame_timing_rows_n=len(rows), shared_pair_instance_counts=shared_counts,
                   nonshared_narrow_phase_pair_instances_n=narrow,
                   exact_off_shared_simplex_instances_n=sum(x.get('intersection_outside_shared_simplex_exactly', False) for x in exact),
                   exact_beyond_resolution_instances_n=sum(x.get('beyond_registered_resolution', False) for x in exact))
    with timings.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with report.open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, indent=2, allow_nan=False); stream.write('\n')
    if verify(record) != checked:
        raise ValueError('Source evidence changed during export')
    return {'execution_record': checked, 'frame_timing_rows_n': len(rows), 'new_inference_during_export': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'record', 'report', 'timings'):
        parser.add_argument('--'+name, type=Path, required=True)
    print(json.dumps(export(**vars(parser.parse_args()))))
