"""Export measured diagnostic video times, retaining incomplete attempts.

Private raw model/mesh/visibility/source hashes are never copied to reports.
Both successful and failed recorded roots must match their execution receipt.
"""
import argparse
import csv
import json
from pathlib import Path
import statistics

import numpy as np

from analysis.runtime_benchmark.journal import recover_bytes
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def bound(root, record):
    root = _private(root); record = _private(record); status = verify(record)
    receipt = json.loads((record/'receipt.private.json').read_text(encoding='utf-8'))
    if receipt['artifact_roots'] != [str(root)]:
        raise ValueError('Export source root must match its execution evidence')
    manifest = json.loads((record/'provenance/manifest.json').read_text(encoding='utf-8'))
    return status, manifest


def timing_row(case, timing, run, render=None, metadata=None):
    render = render or {}; metadata = metadata or {}
    def seconds(name):
        value = timing['phases'].get(name)
        return '' if value is None else value['wall_ns']/1e9
    return {'run': run, 'case': case, 'state': timing['state'],
        'started_utc_epoch_ns': timing['started_utc_epoch_ns'], 'ended_utc_epoch_ns': timing['ended_utc_epoch_ns'],
        'hand': metadata.get('hand', ''), 'primitive': metadata.get('primitive', ''), 'policy': metadata.get('policy', ''),
        'motion_last_frame_seconds': render.get('motion_last_frame_time_seconds', ''),
        'encoded_clip_duration_seconds': render.get('encoded_clip_duration_seconds', ''),
        'decoded_frames': render.get('frames_n', ''), 'video_bytes': render.get('video_bytes', ''),
        'video_ready_seconds': '' if timing['video_ready_wall_ns'] is None else timing['video_ready_wall_ns']/1e9,
        'observed_pipeline_seconds': timing['validated_pipeline_wall_ns']/1e9,
        'process_cpu_seconds': timing['validated_pipeline_process_cpu_ns']/1e9,
        'proposal_compose_seconds': seconds('proposal_and_compose'), 'native_forward_seconds': seconds('native_forward'),
        'prior_BMC_QA_seconds': seconds('prior_and_pending_feature_QA'), 'surface_QA_seconds': seconds('sampled_triangle_surface_QA'),
        'rasterization_seconds': seconds('rasterization'), 'encoder_open_seconds': seconds('encoder_open'),
        'encoder_write_seconds': seconds('encoder_write'), 'encoder_finalize_seconds': seconds('encoder_finalize'),
        'visibility_store_seconds': seconds('visibility_artifact_store'), 'decode_QA_seconds': seconds('decode_qa'),
        'encoder_write_calls': timing['phases'].get('encoder_write', {}).get('calls_n', ''),
        'shared_model_setup_included': False}


def export(root, record, failed_root, failed_record, report, timings, generation_tests_passed):
    if type(generation_tests_passed) is not int or generation_tests_passed < 1:
        raise ValueError('Explicit generation-code test count required as caller-reported metadata')
    root = _private(root); failed_root = _private(failed_root)
    status, manifest = bound(root, record); failed_status, failed_manifest = bound(failed_root, failed_record)
    if status['state'] != 'EXITED_ZERO' or failed_status['state'] == 'EXITED_ZERO':
        raise ValueError('Successful run and distinct failed attempt required')
    report = Path(report).resolve(); timings = Path(timings).resolve()
    if any(p.is_relative_to(r) for p in (report, timings) for r in (root, failed_root, _private(record), _private(failed_record))):
        raise ValueError('Never add export files inside sealed sources')
    if report.exists() or timings.exists():
        raise FileExistsError('Fresh public export paths required')
    summary = json.loads((root/'summary.json').read_text(encoding='utf-8'))
    rows = []; failures = []
    for file in sorted(failed_root.glob('*/timing.private.json')):
        timing = json.loads(file.read_text(encoding='utf-8')); metadata = {}
        if (file.parent/'proposal.private.json').exists():
            proposal = json.loads((file.parent/'proposal.private.json').read_text(encoding='utf-8'))
            metadata = {'hand': proposal['hand'], 'policy': proposal['policy'], 'primitive': proposal['recipe']['primitive']}
        rows.append(timing_row(file.parent.name, timing, 'initial_failed', metadata=metadata))
        failures.append({'case': file.parent.name, 'timing': timing})
    rows.extend(timing_row(c['case'], c['timing'], 'successful_retry', c['render'], c) for c in summary['cases'])
    ready = [c['timing']['video_ready_wall_ns']/1e9 for c in summary['cases']]
    validated = [c['timing']['validated_pipeline_wall_ns']/1e9 for c in summary['cases']]
    statistics_ready = {'min': min(ready), 'median': statistics.median(ready), 'max': max(ready)}
    statistics_validated = {'min': min(validated), 'median': statistics.median(validated), 'max': max(validated)}
    camera_right = json.loads((root/'right_s7_synchronous_flex_spread_author_exact/camera.private.json').read_text())
    camera_left = json.loads((root/'left_s7_synchronous_flex_spread_author_exact/camera.private.json').read_text())
    dot = float(np.array(camera_left['normal'])@(np.array(camera_right['normal'])*[-1., 1., 1.]))
    summary.update(execution_record=status, producer_code_commit=manifest['code_commit'], generation_code_tests_passed=generation_tests_passed,
        test_count_scope='caller-reported suite result for generation code; exporter itself is checked by actual export and row validation, not a test-execution attestation',
        recorded_input_files_n=len(manifest['inputs']), recorded_dependency_pins_n=len(manifest['pinned_versions']),
        video_ready_seconds_summary=statistics_ready, validated_pipeline_seconds_summary=statistics_validated,
        failed_initial_attempt={'execution_record': failed_status, 'producer_code_commit': failed_manifest['code_commit'],
            'case_timings': failures, 'journal': recover_bytes((failed_root/'journal/events.jsonl').read_bytes()),
            'failure': 'Preview PNG filename API failed; original partial files retained; encode-to-bytes fix in retry.'},
        postrun_camera_metadata_review={'same_view_hand_comparison_ready': False,
            'normal_alignment_after_ideal_x_reflection_dot': dot,
            'scope': 'sample pair of recorded camera normals; not physical palm/back annotation',
            'interpretation': 'per-clip hand-relative fit is not a shared same-view camera; matched-camera rerender required'},
        timing_export_rows_n=len(rows), timing_scope='actual local fixed-order diagnostics; failed ready time is null, not zero; shared setup/receipt sealing excluded',
        public_exposure_scope='diagnostic recipe metadata only; no eligible operating challenges')
    if len(rows) != len(summary['cases'])+len(failures) or any(c['timing']['state'] != 'COMPLETED' for c in summary['cases']):
        raise ValueError('Complete and incomplete timing rows must remain distinguishable')
    with timings.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with report.open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, indent=2); stream.write('\n')
    # Evidence roots remain byte-for-byte intact after export.
    verify(record); verify(failed_record)
    return {'timing_rows_n': len(rows), 'completed_videos_n': len(summary['cases']),
            'incomplete_attempt_rows_n': len(failures), 'source_records_intact': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'record', 'failed-root', 'failed-record', 'report', 'timings'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--generation-tests-passed', type=int, required=True)
    a = parser.parse_args()
    print(json.dumps(export(a.root, a.record, a.failed_root, a.failed_record, a.report, a.timings, a.generation_tests_passed)))
