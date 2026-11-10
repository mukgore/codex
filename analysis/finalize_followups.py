"""Whitelisted aggregate report; never copies coordinates, identifiers or input hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
from zipfile import ZipFile

from g4_lab.actual import ActualEvaluator


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['private-root','source-root','output']:
        p.add_argument('--'+name,required=True,type=Path)
    args=p.parse_args();private=args.private_root;source=args.source_root.resolve()
    if args.output.exists():p.error('New aggregate report path required')
    colors=read(private/'color_controls_20261110_v2/summary.json')
    sessions=read(private/'session_boundaries_20261110/summary.json')
    g4=read(private/'g4_bounds_summary_20261110.json')
    verification=read(private/'g4_bounds_20261110/independent_validation.json')
    with ZipFile(source/'left_1_experiment (2).zip') as archive:
        data=json.loads(archive.read('left_1_experiment/experiment_data.json'))
    rows=[]
    with ActualEvaluator(source) as evaluator:
        prepared=evaluator.call({'op':'prepare','data':data})
        for condition in ['unmasked','black','skin']:
            repeats=[r for r in colors['condition_runs'] if r['condition']==condition]
            frames=read(private/f'color_controls_20261110_v2/run_0_{condition}.private.json')['frames']
            raw=evaluator.call({'op':'evaluate','base':prepared['frames'],'frames':frames})['score']
            captcha=.25*raw['sA']+.38*raw['sDA']+.37*raw['sAc']
            if abs(captcha-raw['captcha'])>1e-12:raise ValueError('Weighted score mismatch')
            rows.append({'condition':condition,
                         'detected_frames_per_repeat':[r['legacy_and_candidate']['detected_frames'] for r in repeats],
                         'input_frames_per_repeat':113,
                         'legacy_score_per_repeat':[r['legacy_and_candidate']['legacy_score'] for r in repeats],
                         'offline_gate_per_repeat':[r['legacy_and_candidate']['offline_gate_pass'] for r in repeats],
                         'batch_seconds_median':statistics.median(r['batch_seconds_including_resource_worker'] for r in repeats),
                         'batch_seconds_range':[min(r['batch_seconds_including_resource_worker'] for r in repeats),
                                                max(r['batch_seconds_including_resource_worker'] for r in repeats)],
                         'archive_tracker_disagreement':repeats[0]['archive_mediapipe_disagreement'],
                         'legacy_internal_score_details':raw,
                         'candidate_features_first_repeat':repeats[0]['legacy_and_candidate']['complete_trial_candidate_features']})
    report={'scope':'available_material_only_no_new_human_observations',
            'prod_baseline':{'file':'handcaptcha/hand_captcha_prod.html',
                             'sha256':hashlib.sha256((source/'hand_captcha_prod.html').read_bytes()).hexdigest(),
                             'ui_modification_stage_entered':False},
            'sessions':sessions,'color_comparison':{'batches':colors['completed_batches'],
                                                    'versions':colors['versions'],'rows':rows,
                                                    'limitations':colors['limitations']},
            'g4_regression':{'attempts':g4['attempts'],'rows':g4['rows'],
                             'independent_formula_check':verification},
            'supply_bytes':{name:(private/f'stimulus_pair_final_20261110/{name}.private.mkv').stat().st_size
                            for name in ['unmasked','black','skin']},
            'not_completed':['new controlled filming','human screening and imitation',
                             'independent calibration/test','HaMeR inference','deployment','usability effectiveness']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'report_written':True,'color_batches':colors['completed_batches'],
                      'mapped_sessions':sessions['sessions_exactly_mapped'],'g4_attempts':g4['attempts']}))


if __name__=='__main__':main()
