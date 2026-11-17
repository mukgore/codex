"""Read-only source reconstruction in a fresh process; never run an inference."""
import argparse
from collections import defaultdict
import csv
import json
import math
import os
from pathlib import Path

from analysis.mediapipe_matched_metrics import evaluate
from g4_lab.actual import LANDMARK_NAMES
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private
from .journal import recover_bytes,verify_bundle


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def json_equal(a,b):
    canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
    if canonical(a)!=canonical(b):raise ValueError('Canonical JSON reconstruction differs')


def csv_equal(a,b):
    with Path(a).open(encoding='utf-8',newline='') as first,Path(b).open(encoding='utf-8',newline='') as second:
        left,right=list(csv.reader(first)),list(csv.reader(second))
    if left!=right:raise ValueError('CSV header/row reconstruction differs')
    return len(left)-1


def near(a,b):
    """Only reconstructed float metrics allow1e-12 absolute/relative error."""
    if type(a) is not type(b):raise ValueError('Metric type differs')
    if isinstance(a,float):
        if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError('Reconstructed numeric metric differs')
    elif isinstance(a,dict):
        if set(a)!=set(b):raise ValueError('Metric fields differ')
        for key in a:near(a[key],b[key])
    elif isinstance(a,list):
        if len(a)!=len(b):raise ValueError('Metric list length differs')
        for x,y in zip(a,b):near(x,y)
    elif a!=b:raise ValueError('Metric value differs')


def prediction_audit(root,display):
    """Recalculate saved prediction errors; reuse pure-math metric routine only."""
    root,display=_private(root),_private(display)
    summary=read(root/'summary.json');rows=read(root/'videos.private.json')['rows']
    identity=('case','arm','hand','seed','view')
    entries=read(display/'summary.json')['cases']
    references={tuple(c[k] for k in identity):c['directory_id'] for c in entries}
    if len(references)!=32 or len(rows)!=48:raise ValueError('Registered display/video roster differs')
    scores=[];groups=defaultdict(list);attempted=detected=0
    for i,row in enumerate(rows):
        directory=(display/references[tuple(row[k] for k in identity)]).resolve()
        if not directory.is_relative_to(display):raise ValueError('Reference path escapes display')
        reference=read(directory/'reference.private.json')
        folder=root/f'm{i:02d}';prediction=read(folder/'predictions.private.json')
        metrics=evaluate(reference['frames'],prediction['frames'],LANDMARK_NAMES)
        near(metrics,read(folder/'metrics.private.json'))
        for key,value in metrics.items():
            if key!='per_frame':near(value,row[key])
        json_equal(row,read(folder/'summary.private.json'))
        attempted+=metrics['attempted_frames_n'];detected+=metrics['detected_frames_n']
        groups[row['arm'],row['kind']].append(metrics)
        raw_scores=read(folder/'scores.private.json')['results']
        if len(raw_scores)!=2:raise ValueError('Two score modes required')
        for mode,values in zip(('full_interval','auto_keyframes'),raw_scores):
            scores.append({**{k:row[k] for k in (*identity,'kind')},'segmentation':mode,**values})
    json_equal(scores,read(root/'scores.private.json')['rows'])
    if (attempted,detected,len(scores))!=(1200,769,96):raise ValueError('Recorded frame/score denominators differ')
    aggregates=[]
    for (arm,kind),values in groups.items():
        points=sum(v['detected_point_comparisons_n'] for v in values)
        detected_n=sum(v['detected_frames_n'] for v in values)
        normalized_n=sum(v['normalized_point_comparisons_n'] for v in values)
        def weighted(key,denominator):
            count=sum(v[denominator] for v in values)
            return sum(v[key]*v[denominator] for v in values if v[key] is not None)/count if count else None
        aggregates.append(dict(arm=arm,kind=kind,videos_n=len(values),attempted_frames_n=25*len(values),
            detected_frames_n=detected_n,detected_point_comparisons_n=points,
            conditional_mean_point_error_pixels=weighted('conditional_mean_point_error_pixels','detected_point_comparisons_n'),
            conditional_middle_PIP_error_pixels=weighted('conditional_middle_PIP_error_pixels','detected_frames_n'),
            normalized_point_comparisons_n=normalized_n,
            conditional_mean_error_reference_hand_lengths=weighted('conditional_mean_error_reference_hand_lengths','normalized_point_comparisons_n')))
    near(aggregates,summary['aggregates'])
    grouped=defaultdict(list)
    for row in scores:grouped[row['arm'],row['kind'],row['segmentation']].append(row)
    score_summary=[]
    for (arm,kind,mode),values in grouped.items():
        angles=lambda v:all(x['below_threshold'] for x in v['keyframe_angles'])
        score_summary.append(dict(arm=arm,kind=kind,segmentation=mode,videos_n=len(values),
            score_threshold_met_n=sum(v['score_threshold_met'] for v in values),
            all_keyframe_angle_conditions_met_n=sum(angles(v) for v in values),
            score_and_keyframe_conditions_met_n=sum(v['score_threshold_met'] and angles(v) for v in values),
            score_min=min(v['score']['captcha'] for v in values),score_max=max(v['score']['captcha'] for v in values)))
    near(score_summary,summary['score_aggregates'])
    journal=recover_bytes((root/'journal/events.jsonl').read_bytes());bundle=verify_bundle(root/'journal_bundle.private.zip')
    if journal['status']!='COMPLETED' or bundle['status']!='COMPLETED' or journal['completed_frames']!=1200:
        raise ValueError('Stored journal/bundle incomplete')
    return dict(videos_n=48,stored_prediction_frames_n=1200,detected_frames_n=769,
                raw_prediction_metrics_match=True,score_rows_reaggregated_n=96,
                scoring_js_rerun=False,stored_journal_bundle_match=True)


def reconstruct(job,output):
    root,record=_private(job['root']),_private(job['record']);output=_private(output)
    if output.exists():raise FileExistsError('Fresh reconstructed output required')
    for source in (root,record):
        if output.is_relative_to(source) or source.is_relative_to(output):raise ValueError('Reconstruction overlaps evidence')
    before=verify(record)
    if before['state']!='EXITED_ZERO':raise ValueError('Registered completed source execution required')
    output.mkdir(parents=True,exist_ok=False);kind=job['kind'];details={};extra_checks=[]
    if kind=='mediapipe':
        from analysis.export_mediapipe_matched import export
        display_record=_private(job['display_record']);display_before=verify(display_record)
        if display_before['state']!='EXITED_ZERO':raise ValueError('Bound reference display execution required')
        details=prediction_audit(root,job['display'])
        export(root,record,output/'report.json',output/'rows.csv')
        extra_checks.append((display_record,display_before))
    elif kind=='stage_profile':
        from analysis.export_stage_profile_fixture import export
        export(root,record,output/'report.json');details=dict(synthetic_cases_n=5,raw_summary_roundtrip=True)
    elif kind=='process_replay':
        from analysis.export_replay_fixture import export
        export(root,record,output/'report.json');details=dict(synthetic_cases_n=7,raw_summary_roundtrip=True)
    elif kind=='local_http':
        from analysis.export_local_http_probe import export
        export(root,record,output/'report.json',output/'rows.csv');details=dict(known_source_cases_n=3,matched_http_requests_n=11,raw_summary_roundtrip=True)
    else:raise ValueError('Allowlisted reconstruction kind required')
    json_equal(read(output/'report.json'),read(job['published_report']))
    csv_rows_n=None
    if 'published_csv' in job:csv_rows_n=csv_equal(output/'rows.csv',job['published_csv'])
    for path,expected in [(record,before),*extra_checks]:
        if verify(path)!=expected:raise ValueError('Source execution evidence changed')
    result=dict(kind=kind,worker_pid=os.getpid(),source_record=before,details=details,
                published_json_match=True,published_csv_rows_n=csv_rows_n,
                actual_models_executed_n=0,prior_model_or_service_runs_repeated_n=0,
                fresh_measurement_session=False,independent_implementation=False)
    with (output/'worker_result.private.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--job',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();plan=read(_private(args.plan))
    matching=[job for job in plan['jobs'] if job['id']==args.job]
    if len(matching)!=1:raise ValueError('Unique job required')
    result=reconstruct(matching[0],args.output)
    print(json.dumps(dict(kind=result['kind'],published_json_match=result['published_json_match'],actual_models_executed_n=0)))
