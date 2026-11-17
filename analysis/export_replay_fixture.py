"""Allowlist synthetic transport correctness; never export fixture durations."""
import argparse
import json
from pathlib import Path

from analysis.runtime_benchmark.arrival_record import verify_directory
from analysis.runtime_benchmark.replay_fixture import registered_cases
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def export(root,record,report):
    root,record=_private(root),_private(record);report=Path(report).resolve()
    if report.exists() or any(report.is_relative_to(p) for p in (root,record)):
        raise ValueError('Fresh report outside immutable evidence required')
    checked=verify(record);receipt=json.loads((record/'receipt.private.json').read_text())
    if checked['state']!='EXITED_ZERO' or receipt['artifact_roots']!=[str(root)] or checked['artifact_files_n']!=41:
        raise ValueError('Successful exact registered artifact root required')
    summary=json.loads((root/'summary.private.json').read_text())
    if summary['scope']!='synthetic_preloaded_timed_release_transport_fixture' or summary['actual_models_executed_n']!=0:
        raise ValueError('Registered synthetic transport fixture only')
    planned={case[0]:case for case in registered_cases()};rows=[]
    if len(summary['cases'])!=7 or {r['case'] for r in summary['cases']}!=set(planned):
        raise ValueError('All seven registered cases required')
    for row in summary['cases']:
        name=row['case'];recovery=row['queue_recovery'];expected=planned[name]
        result=json.loads((root/name/'result.private.json').read_text())
        if result['input_role']!='synthetic_fixture' or row['status']!=expected[3] or result['status']!=row['status']:
            raise ValueError('Case status/scope differs')
        public=dict(case=name,status=row['status'],queue_created=recovery is not None,
                    exposure_correspondence_match=row['exposure_correspondence_match'])
        if recovery is not None:
            if verify_directory(root/name/'queue')['recovery']!=recovery:
                raise ValueError('Raw reconstruction differs')
            s=recovery['summary']
            keys=('planned_frames_n','arrived_frames_n','finished_frames_n','dropped_frames_n',
                  'unfinished_frames_n','unsettled_frames_n','not_arrived_frames_n','outcomes','drop_reasons')
            public.update({k:s[k] for k in keys});public['queue_state']=recovery['state']
            public['raw_reconstruction_match']=True
        rows.append(public)
    manifest=json.loads((record/'provenance/manifest.json').read_text())
    result=dict(scope=summary['scope'],cases_n=7,cases=rows,actual_models_executed_n=0,
                past_model_runs_repeated_n=0,new_videos_n=0,new_human_trials_n=0,
                model_performance_proven=False,authentication_proven=False,release_allowed=False,
                duration_export_policy='Synthetic sleep/IPC/clock values stay private; no model performance inference',
                producer_code_commit=manifest['code_commit'],execution_record=checked,
                recorded_input_files_n=len(manifest['inputs']),recorded_dependency_pins_n=len(manifest['pinned_versions']))
    with report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    if verify(record)!=checked:raise ValueError('Source evidence changed during export')
    return dict(cases_n=7,actual_models_executed_n=0,recorded_outputs_n=41)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','record','report'):parser.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(export(**vars(parser.parse_args()))))
