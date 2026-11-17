"""Allowlisted reconstruction evidence, without private paths/PIDs/raw hashes."""
import argparse
import json
from pathlib import Path

from analysis.runtime_benchmark.reconstruction_audit import check_empty_files
from analysis.runtime_benchmark.reconstruction_worker import read,json_equal,csv_equal
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private

DETAILS={
    'mediapipe':('videos_n','stored_prediction_frames_n','detected_frames_n','raw_prediction_metrics_match',
                 'score_rows_reaggregated_n','scoring_js_rerun','stored_journal_bundle_match'),
    'stage_profile':('synthetic_cases_n','raw_summary_roundtrip'),
    'process_replay':('synthetic_cases_n','raw_summary_roundtrip'),
    'local_http':('known_source_cases_n','matched_http_requests_n','raw_summary_roundtrip'),
}


def export(root,record,report):
    root,record=_private(root),_private(record);report=Path(report).resolve()
    if report.exists() or any(report.is_relative_to(p) for p in (root,record)):
        raise ValueError('Fresh report outside immutable evidence required')
    checked=verify(record);receipt=read(record/'receipt.private.json')
    if checked['state']!='EXITED_ZERO' or checked['artifact_files_n']!=24 or receipt['artifact_roots']!=[str(root)]:
        raise ValueError('Successful exact24-file audit binding required')
    summary=read(root/'summary.private.json');plan=read(root/'plan.private.json')
    if (summary['scope']!='fresh_process_readonly_reconstruction_not_measurement_reexecution'
            or summary['all_reconstructions_match'] is not True or summary['jobs_n']!=4):
        raise ValueError('All four registered reconstructions required')
    if any(summary[k] is not False for k in ('independent_implementation','new_measurement_session',
                                            'third_party_authentication_proven','runtime_R9_fully_complete','release_allowed')):
        raise ValueError('Unexpected claim scope')
    rows=[];source_files=0
    if [r['kind'] for r in summary['jobs']]!=list(DETAILS):raise ValueError('Ordered job roster differs')
    for job,result in zip(plan['jobs'],summary['jobs']):
        kind=job['kind'];directory=root/job['id'];worker=read(directory/'reconstructed/worker_result.private.json')
        json_equal(result,read(directory/'process_result.private.json'));json_equal(result['worker'],worker)
        if result['status']!='EXITED_ZERO' or result['returncode']!=0 or worker['worker_pid']==summary['parent_pid']:
            raise ValueError('Separate worker completion differs')
        if verify(_private(job['record']))!=worker['source_record']:raise ValueError('Original source record changed')
        json_equal(read(directory/'reconstructed/report.json'),read(job['published_report']))
        if job.get('published_csv'):
            if csv_equal(directory/'reconstructed/rows.csv',job['published_csv'])!=worker['published_csv_rows_n']:
                raise ValueError('Reconstructed CSV row count differs')
        source_files+=worker['source_record']['artifact_files_n']
        rows.append(dict(kind=kind,status='MATCH',source_recorded_outputs_n=worker['source_record']['artifact_files_n'],
                         published_json_match=True,published_csv_rows_n=worker['published_csv_rows_n'],
                         details={k:worker['details'][k] for k in DETAILS[kind]}))
    display=verify(_private(plan['jobs'][0]['display_record']))
    if display['state']!='EXITED_ZERO':raise ValueError('Reference display evidence changed')
    source_files+=display['artifact_files_n'];check_empty_files(plan)
    if source_files!=812 or len(plan['expected_empty_files'])!=60:raise ValueError('Registered original-file coverage differs')
    manifest=read(record/'provenance/manifest.json')
    result=dict(scope=summary['scope'],jobs_n=4,jobs=rows,all_reconstructions_match=True,
                source_execution_records_n=5,source_artifact_files_verified_n=812,
                reference_display_recorded_outputs_n=display['artifact_files_n'],
                source_empty_logs_bound_by_plan_and_old_receipts_n=60,
                actual_models_executed_n=0,prior_model_or_service_runs_repeated_n=0,new_videos_n=0,new_human_trials_n=0,
                independent_implementation=False,new_measurement_session=False,third_party_authentication_proven=False,
                runtime_R9_fully_complete=False,release_allowed=False,
                producer_code_commit=manifest['code_commit'],execution_record=checked,
                recorded_input_files_n=len(manifest['inputs']),recorded_dependency_pins_n=len(manifest['pinned_versions']),
                limitations=['Fresh processes reuse existing implementation; not a third-party or independent algorithm validation',
                             'No original model/video/Node/HTTP measurement run was repeated',
                             'R9 actual independent measurement and R5-R8 missing real-input conditions remain incomplete'])
    with report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    if verify(record)!=checked:raise ValueError('Reconstruction source evidence changed')
    return dict(jobs_n=4,all_reconstructions_match=True,source_artifact_files_verified_n=812)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','record','report'):parser.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(export(**vars(parser.parse_args()))))
