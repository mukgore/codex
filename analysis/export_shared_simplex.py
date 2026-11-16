"""Export aggregate shared-simplex diagnostics and frame compute times only."""
import argparse
import csv
import json
from pathlib import Path

from analysis.audit_exact_shared_residuals import bound
from validation_v03.execution_record import verify


def export(supplement, supplement_record, exact, exact_record, report, timings):
    supplement, supplement_record, float_status = bound(supplement, supplement_record)
    exact, exact_record, exact_status = bound(exact, exact_record)
    report, timings = Path(report).resolve(), Path(timings).resolve()
    if report == timings or report.exists() or timings.exists():
        raise FileExistsError('Distinct fresh public outputs required')
    if any(p.is_relative_to(root) for p in (report, timings) for root in (supplement, supplement_record, exact, exact_record)):
        raise ValueError('Immutable roots cannot be export destinations')
    fs = json.loads((supplement/'summary.json').read_text())
    es = json.loads((exact/'summary.json').read_text())
    if fs['frames_n'] != 100 or es['pairs_n'] != fs['counts']['NUMERICALLY_UNRESOLVED'] or es['pairs_n'] != 8:
        raise ValueError('Bound denominators differ from registered complete runs')
    rows = []
    for case in fs['cases']:
        frames = json.loads((supplement/(case['case_id']+'.shared_surface.private.json')).read_text())['frames']
        for frame in frames:
            rows.append({'case_id': case['case_id'], 'hand': case['hand'], 'seed': case['seed'],
                         'frame_idx': frame['frame_idx'], 'time_seconds': frame['time_seconds'],
                         'shared_pair_instances_n': frame['shared_pairs_n'],
                         **frame['counts'], 'float_supplement_clear': frame['supplement_clear'],
                         'wall_ns': frame['wall_ns'], 'own_cpu_ns': frame['own_cpu_ns']})
    if len(rows) != 100 or sum(r['shared_pair_instances_n'] for r in rows) != sum(fs['counts'].values()):
        raise ValueError('Per-frame aggregate denominator mismatch')
    # Source summaries contain only aggregate counts/times; raw coordinates,
    # face IDs, exact rational inputs, hashes and detailed records stay private.
    for root, record, summary, checked in ((supplement, supplement_record, fs, float_status), (exact, exact_record, es, exact_status)):
        manifest = json.loads((record/'provenance/manifest.json').read_text())
        summary.update(execution_record=checked, producer_code_commit=manifest['code_commit'],
                       recorded_input_files_n=len(manifest['inputs']),
                       recorded_dependency_pins_n=len(manifest['pinned_versions']))
    result = {'float_supplement': fs, 'exact_eight_residual_followup': es,
              'frame_timing_rows_n': len(rows), 'original_outputs_modified': False,
              'all_pairs_rationally_checked': False, 'release_allowed': False}
    report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    with timings.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    if verify(supplement_record) != float_status or verify(exact_record) != exact_status:
        raise ValueError('Bound output changed during export')
    return {'frame_rows_n': len(rows), 'float_outputs_n': float_status['artifact_files_n'],
            'exact_outputs_n': exact_status['artifact_files_n'], 'new_geometry_computation': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('supplement', 'supplement-record', 'exact', 'exact-record', 'report', 'timings'):
        parser.add_argument('--'+name, type=Path, required=True)
    print(json.dumps(export(**vars(parser.parse_args()))))
