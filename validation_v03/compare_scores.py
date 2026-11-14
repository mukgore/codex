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

from validation_v03.standard_metrics import assert_disjoint_groups, select_validation_threshold, roc_det_summary

METRICS = ('legacy_score', 'candidate_score')
SPLITS = ('development', 'validation', 'test')
OUTCOMES = ('scored', 'technical_error', 'aborted')
# Explicit treatment codes, rather than arbitrary strings that might contain IDs.
ATTACK_FAMILIES = ('replay', 'static_image', 'stationary_hand', 'wrong_motion',
                  'partial_motion', 'interpolation', 'reverse', 'shuffle', 'random',
                  'invalid_geometry', 'coordinate_injection', 'other_specified')


def validate_rows(rows):
    if not rows:
        raise ValueError('No trial records')
    seen = set()
    groups = {kind: {split: set() for split in SPLITS}
              for kind in ('source_family_ids', 'participant_id', 'capture_id')}
    required = {'trial_id', 'label', 'split', 'source_family_ids', 'participant_id',
                'capture_id', 'outcome', *METRICS}
    has_attack_family = any('attack_family' in row for row in rows)
    for row in rows:
        if not isinstance(row,dict) or not required.issubset(row):
            raise ValueError('Missing input columns')
        if not all(isinstance(row[key],str) for key in required-set(METRICS)):
            raise ValueError('Trial metadata columns must be strings')
        if not row['trial_id'] or row['trial_id'] in seen:
            raise ValueError('Trial IDs must be nonempty and unique')
        seen.add(row['trial_id'])
        if row['split'] not in SPLITS or row['label'] not in ('human', 'attack') or row['outcome'] not in OUTCOMES:
            raise ValueError('Invalid split, label or outcome')
        if has_attack_family:
            if ('attack_family' not in row or
                    (row['label']=='attack' and row['attack_family'] not in ATTACK_FAMILIES) or
                    (row['label']=='human' and row['attack_family'] not in ('',None))):
                raise ValueError('Every attack needs a known attack_family code; human rows must be blank')
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


def _trial_endpoint(trials, metric, threshold):
    scored = [r for r in trials if r['outcome'] == 'scored']
    accepted = sum(float(r[metric]) >= threshold for r in scored)
    return {'attempted_n': len(trials), 'scored_n': len(scored),
            'technical_error_n': sum(r['outcome'] == 'technical_error' for r in trials),
            'aborted_n': sum(r['outcome'] == 'aborted' for r in trials),
            'score_accepted_n': accepted, 'score_rejected_n': len(scored)-accepted,
            'score_accept_rate_among_scored': accepted/len(scored) if scored else None,
            'observed_score_accepts_per_attempt': accepted/len(trials) if trials else None}


def endpoint(rows, metric, threshold):
    return {label: _trial_endpoint([r for r in rows if r['label']==label], metric, threshold)
            for label in ('human','attack')}


def attack_family_endpoints(rows, metric, threshold):
    if not any('attack_family' in row for row in rows):
        return {'status':'unavailable_no_attack_family_column'}
    groups = {family:_trial_endpoint([r for r in rows if r['label']=='attack' and
                                     r['attack_family']==family], metric, threshold)
              for family in ATTACK_FAMILIES
              if any(r['label']=='attack' and r['attack_family']==family for r in rows)}
    defined = {family:value['score_accept_rate_among_scored'] for family,value in groups.items()
               if value['scored_n']}
    worst = max(defined.values()) if defined else None
    return {'status':'evaluated_at_frozen_threshold','groups':groups,
            'worst_score_accept_rate_among_scored':worst,
            'worst_families_among_scored':[family for family,rate in defined.items() if rate==worst],
            'families_without_scored_trials':[family for family,value in groups.items() if not value['scored_n']],
            'selection_constraint':'pooled_attack_only_not_a_per_family_risk_guarantee'}


def compare(rows, *, min_human_accept, max_attack_accept, include_curves=False):
    validate_rows(rows)
    validation = [r for r in rows if r['split'] == 'validation' and r['outcome'] == 'scored']
    labels = [int(r['label'] == 'human') for r in validation]
    report = {'schema_version': 2, 'endpoint': 'score_only',
        'limitations': ['caller-supplied lineage; no independent provenance verification',
                       'no camera, gate or protected-action measurement',
                       'no population confidence bounds; repeated trials may be dependent'],
        'selection': {'split': 'validation', 'min_human_accept': min_human_accept,
                      'max_attack_accept': max_attack_accept}, 'metrics': {}}
    for metric in METRICS:
        curves = None
        if include_curves:
            curves = {}
            for split in SPLITS:
                subset = [r for r in rows if r['split']==split and r['outcome']=='scored']
                curves[split] = roc_det_summary([int(r['label']=='human') for r in subset],
                                               [float(r[metric]) for r in subset])
                curves[split]['attempts'] = {label:{
                    'attempted_n':sum(r['split']==split and r['label']==label for r in rows),
                    'technical_error_n':sum(r['split']==split and r['label']==label and r['outcome']=='technical_error' for r in rows),
                    'aborted_n':sum(r['split']==split and r['label']==label and r['outcome']=='aborted' for r in rows)}
                    for label in ('human','attack')}
        point = select_validation_threshold(labels, [float(r[metric]) for r in validation],
            split_name='validation', min_human_accept=min_human_accept, max_attack_accept=max_attack_accept)
        if point is None or not math.isfinite(point['threshold']):
            report['metrics'][metric] = {'status': 'no_finite_feasible_threshold', 'test': None}
            if curves is not None: report['metrics'][metric]['diagnostic_curves'] = curves
            continue
        threshold = point['threshold']
        report['metrics'][metric] = {'status': 'evaluated', 'threshold': threshold,
            'validation': endpoint([r for r in rows if r['split']=='validation'],metric,threshold),
            'test': endpoint([r for r in rows if r['split']=='test'],metric,threshold),
            'attack_families': {split:attack_family_endpoints(
                [r for r in rows if r['split']==split],metric,threshold)
                for split in ('validation','test')}}
        if curves is not None: report['metrics'][metric]['diagnostic_curves'] = curves
    if include_curves:
        report['curve_policy'] = {'denominator':'scored_trials_only; all-attempt counts provided separately',
                                  'test_curves':'descriptive_only_no_test_threshold_selection',
                                  'det_axes':'linear_probabilities_no_probit_clipping',
                                  'auc':'rank_diagnostic_not_a_low_attack_risk_guarantee'}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--min-human-accept', type=float, required=True)
    parser.add_argument('--max-attack-accept', type=float, required=True)
    parser.add_argument('--curves', action='store_true', help='Include all diagnostic ROC/DET points by split')
    parser.add_argument('--curve-plot', type=Path, help='Write a standalone PNG/SVG/PDF using matplotlib')
    parser.add_argument('--data-scope', choices=('unspecified','observed','synthetic'),default='unspecified',
                        help='Caller-declared provenance label; does not verify data origin')
    parser.add_argument('--cluster-repetitions', type=int)
    parser.add_argument('--cluster-seed', type=int)
    parser.add_argument('--cluster-confidence', type=float)
    provenance=parser.add_mutually_exclusive_group()
    provenance.add_argument('--lineage-manifest',type=Path,
                        help='Require file-backed lineage preflight before selecting any threshold')
    provenance.add_argument('--generated-scene-manifest',type=Path,
                        help='Require generated-scene family axes and file lineage before selecting thresholds')
    args = parser.parse_args()
    with args.input.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if args.output.exists() or (args.curve_plot and args.curve_plot.exists()):
        parser.error('Choose new report and plot paths; existing outputs are preserved')
    if args.curve_plot and args.curve_plot.resolve()==args.output.resolve():
        parser.error('Report and plot paths must differ')
    lineage=None
    if args.lineage_manifest or args.generated_scene_manifest:
        from validation_v03.lineage_manifest import audit,validate_score_rows
        from validation_v03.session_artifacts import decode,_read
        try:
            validate_rows(rows)
            manifest_path=(args.lineage_manifest or args.generated_scene_manifest).resolve(strict=True)
            manifest_bytes=_read(manifest_path)
            if args.generated_scene_manifest:
                from validation_v03.generated_scene_manifest import audit as scene_audit
                lineage=scene_audit(decode(manifest_bytes),base=manifest_path.parent)
            else:
                lineage=audit(decode(manifest_bytes),base=manifest_path.parent)
            validate_score_rows(rows,lineage)
        except (OSError,ValueError,TypeError,KeyError,RecursionError):
            parser.error('Lineage preflight rejected input; no thresholds selected')
    report = compare(rows, min_human_accept=args.min_human_accept, max_attack_accept=args.max_attack_accept,
                     include_curves=args.curves or args.curve_plot is not None)
    report['data_scope'] = args.data_scope
    report['lineage_preflight']=lineage['summary'] if lineage else {'status':'not_supplied','independence_proven':False}
    if lineage:report['lineage_manifest_sha256']=hashlib.sha256(manifest_bytes).hexdigest()
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
    if args.curve_plot:
        from validation_v03.score_plots import plot_curves
        plot_curves(report,args.curve_plot)
    # This private integrity fingerprint is not consent to publish a data manifest.
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
