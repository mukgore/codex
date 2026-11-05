"""Offline legacy/candidate score comparison; no camera, server or raw-log adapter.

CSV input stays private. Output contains aggregate score-only endpoints. Failed or
aborted attempts remain in denominators and are reported separately from rejection.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from validation_v03.standard_metrics import assert_disjoint_groups, select_validation_threshold

METRICS = ('legacy_score', 'candidate_score')
SPLITS = ('development', 'validation', 'test')
OUTCOMES = ('scored', 'technical_error', 'aborted')


def validate_rows(rows):
    if not rows:
        raise ValueError('No trial records')
    seen = set()
    groups = {kind: {split: set() for split in SPLITS}
              for kind in ('source_family_ids', 'participant_id', 'capture_id')}
    required = {'trial_id', 'label', 'split', 'source_family_ids', 'participant_id',
                'capture_id', 'outcome', *METRICS}
    for row in rows:
        if not required.issubset(row):
            raise ValueError('Missing input columns')
        if not row['trial_id'] or row['trial_id'] in seen:
            raise ValueError('Trial IDs must be nonempty and unique')
        seen.add(row['trial_id'])
        if row['split'] not in SPLITS or row['label'] not in ('human', 'attack') or row['outcome'] not in OUTCOMES:
            raise ValueError('Invalid split, label or outcome')
        families = [s.strip() for s in row['source_family_ids'].split(';')]
        if not all(families) or len(families) != len(set(families)) or not row['capture_id'].strip():
            raise ValueError('Every constituent source family and capture ID is required')
        if row['label'] == 'human' and not row['participant_id'].strip():
            raise ValueError('Human participant ID is required for split checking')
        for kind, values in (('source_family_ids', families),
                             ('participant_id', [row['participant_id'].strip()]),
                             ('capture_id', [row['capture_id'].strip()])):
            groups[kind][row['split']].update(v for v in values if v)
        for metric in METRICS:
            if row['outcome'] == 'scored':
                try:
                    value = float(row[metric])
                except (TypeError, ValueError):
                    raise ValueError('Both scored metrics must be finite') from None
                if not math.isfinite(value):
                    raise ValueError('Both scored metrics must be finite')
            elif row[metric] not in ('', None):
                raise ValueError('Unscored outcomes must not contain score values')
    for kind, splits in groups.items():
        # Participant groups can be empty for an attack-only split.
        populated = {name: values for name, values in splits.items() if values}
        assert_disjoint_groups(populated)
    for split in SPLITS:
        for label in ('human', 'attack'):
            if not any(r['split'] == split and r['label'] == label and r['outcome'] == 'scored' for r in rows):
                raise ValueError('Each split needs scored human and attack trials')


def endpoint(rows, metric, threshold):
    result = {}
    for label in ('human', 'attack'):
        trials = [r for r in rows if r['label'] == label]
        scored = [r for r in trials if r['outcome'] == 'scored']
        accepted = sum(float(r[metric]) >= threshold for r in scored)
        result[label] = {'attempted_n': len(trials), 'scored_n': len(scored),
            'technical_error_n': sum(r['outcome'] == 'technical_error' for r in trials),
            'aborted_n': sum(r['outcome'] == 'aborted' for r in trials),
            'score_accepted_n': accepted, 'score_rejected_n': len(scored)-accepted,
            'score_accept_rate_among_scored': accepted/len(scored),
            'observed_score_accepts_per_attempt': accepted/len(trials)}
    return result


def compare(rows, *, min_human_accept, max_attack_accept):
    validate_rows(rows)
    validation = [r for r in rows if r['split'] == 'validation' and r['outcome'] == 'scored']
    labels = [int(r['label'] == 'human') for r in validation]
    report = {'schema_version': 1, 'endpoint': 'score_only',
        'limitations': ['caller-supplied lineage; no independent provenance verification',
                       'no camera, gate or protected-action measurement',
                       'no population confidence bounds; repeated trials may be dependent'],
        'selection': {'split': 'validation', 'min_human_accept': min_human_accept,
                      'max_attack_accept': max_attack_accept}, 'metrics': {}}
    for metric in METRICS:
        point = select_validation_threshold(labels, [float(r[metric]) for r in validation],
            split_name='validation', min_human_accept=min_human_accept, max_attack_accept=max_attack_accept)
        if point is None or not math.isfinite(point['threshold']):
            report['metrics'][metric] = {'status': 'no_finite_feasible_threshold', 'test': None}
            continue
        threshold = point['threshold']
        report['metrics'][metric] = {'status': 'evaluated', 'threshold': threshold,
            'validation': endpoint([r for r in rows if r['split']=='validation'],metric,threshold),
            'test': endpoint([r for r in rows if r['split']=='test'],metric,threshold)}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--min-human-accept', type=float, required=True)
    parser.add_argument('--max-attack-accept', type=float, required=True)
    parser.add_argument('--cluster-repetitions', type=int)
    parser.add_argument('--cluster-seed', type=int)
    parser.add_argument('--cluster-confidence', type=float)
    args = parser.parse_args()
    with args.input.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    report = compare(rows, min_human_accept=args.min_human_accept, max_attack_accept=args.max_attack_accept)
    cluster_options=(args.cluster_repetitions,args.cluster_seed,args.cluster_confidence)
    if any(value is not None for value in cluster_options):
        if any(value is None for value in cluster_options):
            parser.error('Cluster intervals require repetitions, seed and confidence together')
        if all(report['metrics'][metric]['status']=='evaluated' for metric in METRICS):
            from validation_v03.cluster_intervals import test_intervals
            report['cluster_intervals']=test_intervals(rows,
                {metric:report['metrics'][metric]['threshold'] for metric in METRICS},
                repetitions=args.cluster_repetitions,seed=args.cluster_seed,confidence=args.cluster_confidence)
        else:
            report['cluster_intervals']={'status':'UNAVAILABLE_NO_TWO_FINITE_VALIDATION_THRESHOLDS'}
    report['input_sha256'] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    # This private integrity fingerprint is not consent to publish a data manifest.
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
