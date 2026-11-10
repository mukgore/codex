"""Card D paired-camera analysis contract; no capture, invented trials or threshold tuning."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import statistics

CONDITIONS = ('normal_imitation','slow_imitation','small_imitation','hold_first',
              'hold_middle','hold_last','wrong_order','partial','wrist_only','static_photo')
OUTCOMES = ('recorded','tracking_failure','timeout','technical_error','aborted')
ORIGINS = ('offline_fixed_duration','issued_live')
PAIR_FIELDS = ('protocol_id','participant_id','target_id','source_family_id','camera_id',
               'recording_seconds','repeat','score_origin')
LEGACY_THRESHOLD = .25


def validate(rows):
    if not isinstance(rows,list) or not 0 < len(rows) <= 100000:
        raise ValueError('Nonempty list of at most 100000 analysis rows required')
    required = {'trial_id','capture_id','condition','outcome','legacy_score','gate_pass',
                'motion_completed',*PAIR_FIELDS}
    seen, captures, trial_contexts, targets = set(), {}, {}, {}
    for row in rows:
        if not isinstance(row,dict) or not required.issubset(row):
            raise ValueError('Missing paired-camera fields')
        for name in ('trial_id','capture_id','protocol_id','participant_id','target_id',
                     'source_family_id','camera_id'):
            value=row[name]
            if not isinstance(value,str) or not value or value.strip()!=value:
                raise ValueError('Explicit nonempty lineage and trial identifiers required')
        if row['condition'] not in CONDITIONS or row['outcome'] not in OUTCOMES or row['score_origin'] not in ORIGINS:
            raise ValueError('Unknown condition, outcome or score origin')
        if type(row['repeat']) is not int or not 1 <= row['repeat'] <= 1000:
            raise ValueError('Positive explicit repeat index required')
        duration=row['recording_seconds']
        if isinstance(duration,bool) or not isinstance(duration,(int,float)) or not math.isfinite(duration) or duration<=0:
            raise ValueError('Positive finite planned recording duration required')
        score=row['legacy_score']
        if score is not None and (isinstance(score,bool) or not isinstance(score,(int,float)) or
                                  not math.isfinite(score) or not 0<=score<=1):
            raise ValueError('Legacy score must be null or finite in [0,1]')
        if row['outcome'] in ('technical_error','aborted') and score is not None:
            raise ValueError('Technical/aborted attempts cannot masquerade as completed score evaluations')
        for name in ('gate_pass','motion_completed'):
            if row[name] is not None and type(row[name]) is not bool:
                raise ValueError('Independent judgments must be Boolean or null')
        key=tuple(row[name] for name in PAIR_FIELDS)+(row['condition'],)
        if key in seen:raise ValueError('Duplicate paired condition/repeat/origin')
        seen.add(key)
        context=tuple(row[name] for name in PAIR_FIELDS if name!='score_origin')+(row['condition'],)
        if row['capture_id'] in captures and captures[row['capture_id']]!=context:
            raise ValueError('Capture reused across incompatible controls')
        captures[row['capture_id']]=context
        trial_key=(row['trial_id'],row['score_origin'])
        if trial_key in trial_contexts:raise ValueError('Duplicate trial within score origin')
        trial_contexts[trial_key]=True
        if row['target_id'] in targets and targets[row['target_id']]!=row['source_family_id']:
            raise ValueError('Target assigned conflicting source family')
        targets[row['target_id']]=row['source_family_id']


def _endpoints(rows):
    scores=[r['legacy_score'] for r in rows if r['legacy_score'] is not None]
    accepted=sum(score>=LEGACY_THRESHOLD for score in scores)
    gates=[r['gate_pass'] for r in rows if r['gate_pass'] is not None]
    return {'attempted_n':len(rows),'scored_n':len(scores),'unscored_n':len(rows)-len(scores),
            'score_accepted_n':accepted,'score_rejected_n':len(scores)-accepted,
            'score_accept_rate_among_scored':accepted/len(scores) if scores else None,
            'observed_score_accepts_per_attempt':accepted/len(rows),
            'gate_observed_n':len(gates),'gate_passed_n':sum(gates),
            'score_and_gate_passed_n':sum(r['legacy_score'] is not None and
                r['legacy_score']>=LEGACY_THRESHOLD and r['gate_pass'] is True for r in rows),
            'motion_complete_n':sum(r['motion_completed'] is True for r in rows),
            'motion_incomplete_n':sum(r['motion_completed'] is False for r in rows),
            'motion_unjudged_n':sum(r['motion_completed'] is None for r in rows),
            'outcomes':dict(Counter(r['outcome'] for r in rows))}


def _mean_summary(groups):
    means=[statistics.mean(values) for values in groups.values()]
    return {'units_n':len(means),'mean':statistics.mean(means) if means else None,
            'median':statistics.median(means) if means else None,
            'min':min(means) if means else None,'max':max(means) if means else None}


def summarize(rows, *, data_scope):
    validate(rows)
    if data_scope not in ('observed','synthetic','unspecified'):
        raise ValueError('Explicit data scope required')
    report={'schema_version':1,'data_scope':data_scope,'legacy_threshold':LEGACY_THRESHOLD,
            'endpoint':'camera_control_score_gate_motion_diagnostic_not_authentication',
            'score_origins':{},'limitations':[
                'Caller-supplied lineage is not independently authenticated.',
                'Repeat index must identify prospectively paired controls; no nearest-score matching.',
                'Motion-completion judgments must be independent of scores.',
                'No population uncertainty or threshold calibration; no protected-action measurement.']}
    for origin in ORIGINS:
        subset=[r for r in rows if r['score_origin']==origin]
        if not subset:continue
        normal={tuple(r[field] for field in PAIR_FIELDS):r for r in subset if r['condition']=='normal_imitation'}
        origin_report={'conditions':{},'normal_matches_required_on':list(PAIR_FIELDS)}
        for condition in CONDITIONS:
            controls=[r for r in subset if r['condition']==condition]
            if not controls:continue
            result=_endpoints(controls)
            if condition!='normal_imitation':
                differences=[];missing_normal=missing_score=ties=reversals=0
                participant_values=defaultdict(list);target_values=defaultdict(list)
                for control in controls:
                    reference=normal.get(tuple(control[field] for field in PAIR_FIELDS))
                    if reference is None:missing_normal+=1;continue
                    if reference['legacy_score'] is None or control['legacy_score'] is None:
                        missing_score+=1;continue
                    difference=reference['legacy_score']-control['legacy_score']
                    differences.append(difference);ties+=difference==0;reversals+=difference<0
                    participant_values[control['participant_id']].append(difference)
                    target_values[control['target_id']].append(difference)
                result['paired']={'scored_pair_n':len(differences),'missing_normal_match_n':missing_normal,
                    'matched_but_unscored_pair_n':missing_score,'score_reversal_n':reversals,'score_tie_n':ties,
                    'normal_minus_control_mean':statistics.mean(differences) if differences else None,
                    'normal_minus_control_median':statistics.median(differences) if differences else None,
                    'participant_mean_summary':_mean_summary(participant_values),
                    'target_mean_summary':_mean_summary(target_values)}
            origin_report['conditions'][condition]=result
        report['score_origins'][origin]=origin_report
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    packet=json.loads(args.input.read_text(encoding='utf-8'))
    report=summarize(packet['trials'],data_scope=packet['data_scope'])
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,indent=2,allow_nan=False);stream.write('\n')


if __name__=='__main__':main()
