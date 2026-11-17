"""Export scoped localhost observations without source IDs, raw clocks or hashes."""
import argparse
import csv
import json
from pathlib import Path

from analysis.runtime_benchmark.http_client_timing import reconcile
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def ms(value):return None if value is None else value/1e6


def aggregate(root):
    root=_private(root)
    summary=json.loads((root/'summary.private.json').read_text())
    attempts=json.loads((root/'attempts.private.json').read_text())
    if (summary['scope']!='new_loopback_known_reference_and_static_replay_timing' or summary['cases_n']!=3
            or summary['source_families_n']!=1 or summary['actual_models_executed_n']!=0 or attempts['error_type'] is not None):
        raise ValueError('Registered completed known-source probe required')
    if any(summary[k] is not False for k in ('independent_holdout','actual_camera_or_hold_observed','first_pixel_presented',
                                            'historical_or_deployed_authentication_proven','client_server_clock_subtraction_performed','release_allowed')):
        raise ValueError('Unexpected scientific/release scope')
    if any(summary[k]!=0 for k in ('past_model_runs_repeated_n','new_videos_n','new_human_trials_n')):
        raise ValueError('Probe may not claim new model/video/human trials')
    joined=reconcile((root/'client.private.jsonl').read_bytes(),(root/'server.private.jsonl').read_bytes())
    if joined!=json.loads((root/'joined.private.json').read_text()) or joined['unmatched_server_requests_n']:
        raise ValueError('Raw correspondence differs')
    requests=joined['requests'];by_id={r['client']['correlation']:r for r in requests}
    if any(r['server'] is None for r in requests) or len(by_id)!=len(requests):raise ValueError('Missing/duplicate request pairing')
    cases=attempts['cases']
    if [r['case'] for r in cases]!=['known_reference','static_first_detected','invalid_schema_claims']:
        raise ValueError('Registered ordered cases required')
    used=set();rows=[];request_case={}
    for row in cases:
        ids=row['correlations']
        if len(set(ids))!=len(ids) or used.intersection(ids):raise ValueError('Overlapping attempt requests')
        used.update(ids);group=[by_id[c] for c in ids]
        request_case.update({c:row['case'] for c in ids})
        expected=[('POST','/api/challenge'),('POST','/api/submit')] if row['case']=='invalid_schema_claims' else [
            ('POST','/api/challenge'),('GET','/media/:challenge'),('POST','/api/submit')]
        if row['server_grant_issued']:expected += [('POST','/api/protected_action')]*2
        if [(r['client']['method'],r['client']['route']) for r in group]!=expected:raise ValueError('Attempt endpoint order differs')
        submit=next(r for r in group if r['client']['route']=='/api/submit')
        if submit['client']['http_status']!=row['submit_http_status'] or submit['server']['http_status']!=row['submit_http_status']:
            raise ValueError('Submit status correspondence differs')
        evaluators=[p for p in submit['server']['phases'] if p['name']=='evaluator']
        if len(evaluators)>1:raise ValueError('Unexpected repeated evaluator')
        if row['case']=='invalid_schema_claims' and (row['submit_http_status']!=400 or evaluators or row['server_grant_issued']):
            raise ValueError('Invalid-schema control reached evaluator/grant')
        start=group[0]['client']['started_ns']
        media=next((r for r in group if r['client']['route']=='/media/:challenge'),None)
        actions=[r for r in group if r['client']['route']=='/api/protected_action']
        first_action_ms=None if not actions else ms(actions[0]['client']['body_received_ns']-start)
        if not actions and row['issue_to_action_body_received_ns'] is not None:raise ValueError('Unobserved action given a duration')
        if row['repeat_action_allowed'] is True:raise ValueError('Repeated action allowed')
        public=dict(case=row['case'],submitted_frames_n=row.get('planned_frames_n'),detected_frames_n=row.get('detected_frames_n'),
                    submit_http_status=row['submit_http_status'],validation_pass=row['validation_pass'],
                    score_captcha=row.get('evaluation',{}).get('score',{}).get('captcha'),score_pass=row['score_pass'],
                    offline_gate_pass=row['gate_pass'],server_grant_issued=row['server_grant_issued'],
                    new_local_test_action_allowed=row['protected_action_allowed'],repeat_action_allowed=row['repeat_action_allowed'],
                    issue_trace_start_to_media_body_ms=None if media is None else ms(media['client']['body_received_ns']-start),
                    issue_trace_start_to_first_action_body_ms=first_action_ms,
                    issue_trace_start_to_schema_submit_body_ms=ms(submit['client']['body_received_ns']-start) if row['case']=='invalid_schema_claims' else None,
                    procedure_entry_to_first_action_body_ms=ms(row['issue_to_action_body_received_ns']),
                    client_submit_elapsed_ms=ms(submit['client']['elapsed_ns']),server_submit_handler_ms=ms(submit['server']['elapsed_ns']),
                    server_evaluator_inclusive_ms=None if not evaluators else ms(evaluators[0]['elapsed_ns']),
                    evaluator_outcome=None if not evaluators else evaluators[0]['outcome'],first_pixel_observed=False)
        rows.append(public)
    setup=[r for r in requests if r['client']['correlation'] not in used]
    if len(setup)!=1 or (setup[0]['client']['method'],setup[0]['client']['route'])!=('POST','/api/session'):
        raise ValueError('Unexpected requests outside registered attempts')
    if summary['protected_test_actions_n']!=sum(r['new_local_test_action_allowed'] is True for r in rows):
        raise ValueError('Action counter differs')
    events=json.loads((root/'server_events.private.json').read_text())
    evaluated=[e for e in events if e['kind']=='evaluated']
    if len(evaluated)!=2 or any((e['score_pass'],e['gate_pass'])!=(r['score_pass'],r['offline_gate_pass']) for e,r in zip(evaluated,rows)):
        raise ValueError('Independent service event outcomes differ')
    observed=[e['protected_action_allowed'] for e in events if e['kind']=='protected_action']
    expected=[]
    for row in rows:
        if row['server_grant_issued']:expected.extend((row['new_local_test_action_allowed'],row['repeat_action_allowed']))
    if observed!=expected:raise ValueError('Service action events differ from client observations')
    request_rows=[]
    for i,r in enumerate(requests):
        client,server=r['client'],r['server']
        if client['http_status']!=server['http_status']:raise ValueError('Client/server HTTP status differs')
        request_rows.append(dict(request_index=i,case=request_case.get(client['correlation'],'session_setup'),
                                 method=client['method'],route=client['route'],http_status=client['http_status'],
                                 client_elapsed_ms=ms(client['elapsed_ns']),server_dispatch_elapsed_ms=ms(server['elapsed_ns']),
                                 server_response_write_completed=server['response_write_completed']))
    result=dict(scope=summary['scope'],cases_n=3,cases=rows,source_families_n=1,independent_holdout=False,
                knowledge='known fixed source with full stored coordinates/video before issue; not pixel inference',
                source_pool_prepared_n=summary['source_pool_prepared_n'],actual_models_executed_n=0,past_model_runs_repeated_n=0,
                new_videos_n=0,new_human_trials_n=0,actual_camera_or_hold_observed=False,first_pixel_observed=False,
                historical_or_deployed_authentication_proven=False,client_server_clock_subtraction_performed=False,
                protected_test_actions_n=summary['protected_test_actions_n'],matched_requests_n=len(requests),
                raw_reconstruction_match=True,release_allowed=False,
                core_wall_ms=ms(summary['core_wall_ns']),core_own_python_cpu_ms=ms(summary['core_own_cpu_ns']),
                setup_wall_ms=ms(summary['setup_wall_ns']),node_child_cpu_ms=None,
                timing_boundary='primary attempt elapsed reconstructed from client issue request trace start to body receipt; procedure entry is a separate earlier producer measurement',
                limitations=['n=1 per case on one known source; no latency distribution/generalization inference',
                             'G4 onRes gate uses supplied timestamps, not observed wall-clock camera hold',
                             'Server phases are inclusive and include tracing overhead; nested durations must not be summed',
                             'New protected action is an in-memory loopback test counter; original/deployed authentication not tested'])
    return result,request_rows


def export(root,record,report,requests_csv):
    root,record=_private(root),_private(record);report=Path(report).resolve();requests_csv=Path(requests_csv).resolve()
    if report==requests_csv or any(p.exists() or any(p.is_relative_to(s) for s in (root,record)) for p in (report,requests_csv)):
        raise ValueError('Distinct fresh reports outside immutable evidence required')
    checked=verify(record);receipt=json.loads((record/'receipt.private.json').read_text())
    if checked['state']!='EXITED_ZERO' or checked['artifact_files_n']!=8 or receipt['artifact_roots']!=[str(root)]:
        raise ValueError('Successful exact registered eight-file output binding required')
    result,rows=aggregate(root);manifest=json.loads((record/'provenance/manifest.json').read_text())
    result.update(execution_record=checked,producer_code_commit=manifest['code_commit'],
                  recorded_input_files_n=len(manifest['inputs']),recorded_dependency_pins_n=len(manifest['pinned_versions']))
    with report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    with requests_csv.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    if verify(record)!=checked:raise ValueError('Probe raw evidence changed during export')
    return dict(cases_n=3,matched_requests_n=len(rows),recorded_outputs_n=8)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','record','report','requests-csv'):parser.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(export(**vars(parser.parse_args()))))
