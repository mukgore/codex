"""Export aggregate diagnostics and per-video timing without private model data."""
import argparse
import csv
import json
from pathlib import Path

from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def export(root, record, report, timings):
    root, record = _private(root), _private(record)
    report, timings = Path(report).resolve(), Path(timings).resolve()
    if report == timings or report.exists() or timings.exists():
        raise FileExistsError('Distinct fresh export files required')
    if any(p.is_relative_to(r) for p in (report, timings) for r in (root, record)):
        raise ValueError('Immutable evidence cannot be an export destination')
    checked = verify(record)
    receipt = json.loads((record/'receipt.private.json').read_text())
    if checked['state'] != 'EXITED_ZERO' or receipt['artifact_roots'] != [str(root)]:
        raise ValueError('Completed bound inference required')
    summary = json.loads((root/'summary.json').read_text())
    rows = json.loads((root/'videos.private.json').read_text())['rows']
    scores = json.loads((root/'scores.private.json').read_text())['rows']
    if (len(rows), sum(r['attempted_frames_n'] for r in rows), len(scores)) != (48, 1200, 96):
        raise ValueError('Registered denominators differ')
    if sum(r['detected_frames_n'] for r in rows) != summary['detected_frames_n']:
        raise ValueError('Detection total mismatch')
    # Explicit allowlists: no frame coordinates, asset paths, hashes or commands.
    keys = ('version', 'videos_n', 'actual_model_frames_n', 'detected_frames_n',
            'score_diagnostics_n', 'aggregates', 'score_aggregates', 'parameters',
            'versions', 'source_info_to_video_info_adapter', 'mirror',
            'new_model_or_asset_downloads_n', 'new_video_generation_n',
            'new_human_trials_n', 'new_independent_families_n', 'accepted_into_pool_n',
            'release_allowed', 'browser_prod_detector_equivalence_proven',
            'hold_or_authentication_validated', 'journal_status', 'frame_event_scope',
            'timing', 'limitations')
    result = {k: summary[k] for k in keys}
    manifest = json.loads((record/'provenance/manifest.json').read_text())
    result.update(execution_record=checked, producer_code_commit=manifest['code_commit'],
                  recorded_input_files_n=len(manifest['inputs']),
                  recorded_dependency_pins_n=len(manifest['pinned_versions']))
    fields = ('case', 'arm', 'hand', 'seed', 'view', 'kind', 'attempted_frames_n',
              'detected_frames_n', 'missing_frames_n', 'detected_fraction',
              'detected_point_comparisons_n', 'conditional_mean_point_error_pixels',
              'conditional_middle_PIP_error_pixels',
              'conditional_mean_error_reference_hand_lengths',
              'reference_scale_invalid_detected_frames_n',
              'started_utc_epoch_ns', 'ended_utc_epoch_ns', 'worker_subprocess_wall_ns',
              'worker_own_cpu_ns', 'worker_batch_extract_wall_ns',
              'worker_batch_extract_own_cpu_ns', 'validated_video_diagnostic_wall_ns',
              'graph_reset_per_video', 'frame_events_scope')
    with timings.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows({k: row[k] for k in fields} for row in rows)
    report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    if verify(record) != checked:
        raise ValueError('Source evidence changed during export')
    return {'source_record': checked, 'timing_rows_n': len(rows), 'new_inference': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'record', 'report', 'timings'):
        parser.add_argument('--'+name, type=Path, required=True)
    print(json.dumps(export(**vars(parser.parse_args()))))
