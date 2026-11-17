"""Export fixture correctness, excluding synthetic durations/model-like metrics."""
import argparse
import json
from pathlib import Path

from analysis.runtime_benchmark.stage_profile import rebuild_summary, recover_events
from analysis.runtime_benchmark.stage_profile_fixture import CASES
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def export(root, record, report):
    root, record = _private(root), _private(record); report = Path(report).resolve()
    if report.exists() or any(report.is_relative_to(p) for p in (root, record)):
        raise ValueError('Fresh export outside immutable sources required')
    checked = verify(record); receipt = json.loads((record/'receipt.private.json').read_text())
    if checked['state'] != 'EXITED_ZERO' or receipt['artifact_roots'] != [str(root)]:
        raise ValueError('Successful exact fixture output binding required')
    summary = json.loads((root/'summary.json').read_text())
    if summary['scope'] != 'synthetic_instrumentation_fixture_only' or summary['actual_models_executed_n'] != 0:
        raise ValueError('Only registered synthetic instrumentation fixture exports supported')
    cases = []
    for case in summary['cases']:
        name = case['case']
        if name not in CASES: raise ValueError('Unexpected fixture case')
        raw = (root/(name+'.trace.private.jsonl')).read_bytes()
        stored = json.loads((root/(name+'.summary.private.json')).read_text())
        if rebuild_summary(raw) != stored or stored['workload_role'] != 'synthetic_instrumentation_fixture_not_mediapipe':
            raise ValueError('Fixture raw/summary scope or correspondence differs')
        cases.append({k: case[k] for k in ('case', 'legacy_exception_type', 'semantics_match',
                                           'namespace_restored', 'state', 'profile_status',
                                           'profile_recovery_status', 'actual_model_executed')})
        if recover_events(raw)['state'] != case['profile_status']:
            raise ValueError('Actual error/complete state recovery differs')
    if len(cases) != 5 or {c['case'] for c in cases} != set(CASES):
        raise ValueError('All five planned cases required')
    manifest = json.loads((record/'provenance/manifest.json').read_text())
    result = {'scope': summary['scope'], 'cases_n': 5, 'cases': cases,
              'actual_models_executed_n': 0, 'actual_model_stage_times_measured': False,
              'past_model_runs_repeated_n': 0, 'new_human_trials_n': 0, 'new_videos_n': 0,
              'profile_raw_summary_roundtrip_all': True, 'release_allowed': False,
              'execution_record': checked, 'producer_code_commit': manifest['code_commit'],
              'recorded_input_files_n': len(manifest['inputs']), 'recorded_dependency_pins_n': len(manifest['pinned_versions']),
              'limitations': summary['limitations'],
              'duration_export_policy': 'fixture durations stay private; no MediaPipe/HaMeR performance inference'}
    with report.open('x', encoding='utf-8') as stream: json.dump(result, stream, indent=2); stream.write('\n')
    if verify(record) != checked: raise ValueError('Raw fixture evidence changed')
    return {'source_record_intact': True, 'fixture_cases_n': 5, 'actual_models_executed_n': 0}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'record', 'report'): p.add_argument('--'+name, type=Path, required=True)
    print(json.dumps(export(**vars(p.parse_args()))))
