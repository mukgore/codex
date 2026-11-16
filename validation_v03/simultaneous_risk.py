"""Conditional simultaneous upper bounds for preplanned cluster-level events.

This endpoint is any score acceptance within a fixed cluster/type budget, not
per-attempt FAR or authentication success. Caller declarations are not verified.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from scipy.special import betainccinv

from .cluster_intervals import _clusters
from .compare_scores import ATTACK_FAMILIES, METRICS, validate_rows

DECLARATIONS = ('thresholds_locked_before_test', 'iid_clusters_within_family',
                'fixed_attempt_budget_before_test', 'complete_test_roster')


def exact_upper(events, units, alpha):
    """One-sided Clopper-Pearson; zero observations have vacuous upper 1."""
    if (type(events) is not int or type(units) is not int or
            not 0 <= events <= units <= 1_000_000 or
            isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or
            not math.isfinite(alpha) or not 0 < alpha < 1):
        raise ValueError('Valid integer counts and finite tail probability required')
    if units == 0 or events == units:
        return 1.0
    if events == 0:
        return -math.expm1(math.log(alpha)/units)
    return float(betainccinv(events+1, units-events, alpha))


def evaluate(rows, plan):
    validate_rows(rows)
    if plan.get('schema_version') != 1:
        raise ValueError('Versioned risk plan required')
    confidence = plan.get('confidence')
    if (isinstance(confidence, bool) or not isinstance(confidence, (float, int)) or
            not math.isfinite(confidence) or not .5 < confidence < 1):
        raise ValueError('Finite confidence strictly between .5 and 1 required')
    thresholds = plan.get('thresholds', {})
    if (set(thresholds) != set(METRICS) or any(isinstance(t, bool) or
            not isinstance(t, (float, int)) or not math.isfinite(t) for t in thresholds.values())):
        raise ValueError('Both finite pre-test frozen thresholds required')
    families = plan.get('families')
    if (not isinstance(families, dict) or not families or
            not set(families).issubset(ATTACK_FAMILIES)):
        raise ValueError('Explicit preplanned attack types required')
    for spec in families.values():
        if (not isinstance(spec, dict) or set(spec) != {'clusters_n', 'attempts_per_cluster'} or
                any(type(spec[k]) is not int or not 1 <= spec[k] <= 1_000_000 for k in spec)):
            raise ValueError('Positive fixed cluster counts and attempt budgets required')
    if any(type(plan.get(k)) is not bool for k in DECLARATIONS):
        raise ValueError('All assumption declarations must be explicit booleans')
    if any('attack_family' not in r for r in rows):
        raise ValueError('Attack type column required')
    if any(r['label'] == 'attack' and r['attack_family'] not in families for r in rows):
        raise ValueError('Observed type outside preplanned scope; do not silently omit it')
    # Link ALL test treatments before filtering; even human/other type rows may
    # connect two apparently separate repeats transitively.
    groups = _clusters([r for r in rows if r['split'] == 'test'])
    assumptions = all(plan[k] for k in DECLARATIONS)
    statements = len(METRICS)*len(families)
    tail = (1-confidence)/statements
    output = {'schema_version': 1, 'method': 'one_sided_clopper_pearson_bonferroni',
              'endpoint': 'any_score_acceptance_within_fixed_cluster_type_budget',
              'split': 'test', 'confidence': confidence, 'statements_n': statements,
              'per_statement_alpha': tail, 'thresholds': dict(thresholds),
              'assumptions_declared': {k: plan[k] for k in DECLARATIONS},
              'assumptions_independently_verified': False, 'families': {},
              'limitations': ['Conditional on iid clusters within each type and the declared fixed protocol.',
                             'Lineage components cannot establish independence or a complete roster.',
                             'Unscored or missing within-budget trials are conservative possible acceptances.',
                             'No per-attempt FAR, unseen-type bound, human comparison or authentication guarantee.',
                             'Threshold/model/type/budget selection using test data invalidates this plan.']}
    for family in sorted(families):
        spec = families[family]
        subsets = [[r for r in g if r['label'] == 'attack' and r['attack_family'] == family] for g in groups]
        subsets = [s for s in subsets if s]
        if len(subsets) > spec['clusters_n'] or any(len(s) > spec['attempts_per_cluster'] for s in subsets):
            raise ValueError('Observed cluster roster/budget exceeds plan')
        family_result = {'planned_clusters_n': spec['clusters_n'],
                         'observed_clusters_n': len(subsets),
                         'planned_attempts_per_cluster': spec['attempts_per_cluster'],
                         'attempted_n': sum(map(len, subsets)), 'metrics': {}}
        incomplete = len(subsets) != spec['clusters_n']
        for metric in METRICS:
            hits = possible = unresolved = 0
            for subset in subsets:
                accepted = any(r['outcome'] == 'scored' and float(r[metric]) >= thresholds[metric] for r in subset)
                unknown = len(subset) < spec['attempts_per_cluster'] or any(r['outcome'] != 'scored' for r in subset)
                hits += int(accepted); possible += int(accepted or unknown); unresolved += int(unknown)
            status = ('ASSUMPTIONS_NOT_DECLARED' if not assumptions else
                      'INCOMPLETE_CLUSTER_ROSTER' if incomplete else 'CONDITIONAL_BOUND')
            upper = (None if not assumptions else 1.0 if incomplete else exact_upper(possible, len(subsets), tail))
            family_result['metrics'][metric] = {'status': status, 'observed_accepting_clusters_n': hits,
                                                'possible_accepting_clusters_n': possible,
                                                'unresolved_clusters_n': unresolved, 'upper': upper}
        output['families'][family] = family_result
    output['worst_declared_type_upper'] = {metric: max(f['metrics'][metric]['upper'] for f in output['families'].values())
                                           if assumptions else None for metric in METRICS}
    output['scope'] = 'simultaneous_across_both_metrics_and_all_predeclared_types_only'
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('input', 'plan', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--data-scope', choices=('synthetic', 'observed', 'unspecified'), required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Fresh output required; prior evidence is preserved')
    source = args.input.read_bytes(); plan_bytes = args.plan.read_bytes()
    with args.input.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    result = evaluate(rows, json.loads(plan_bytes))
    result.update(data_scope=args.data_scope, input_sha256=hashlib.sha256(source).hexdigest(),
                  plan_sha256=hashlib.sha256(plan_bytes).hexdigest())
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')


if __name__ == '__main__':
    main()
