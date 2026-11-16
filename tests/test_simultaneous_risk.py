import csv
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from validation_v03.simultaneous_risk import DECLARATIONS, evaluate, exact_upper


def fixture():
    rows = []
    for split in ('development', 'validation', 'test'):
        for label in ('human', 'attack'):
            for i in range(4):
                key = f'{split}-{label}-{i}'
                rows.append(dict(trial_id=key, label=label, split=split,
                                 source_family_ids=key, participant_id=key, capture_id=key,
                                 outcome='scored', legacy_score='0', candidate_score='0',
                                 attack_family='replay' if label == 'attack' else ''))
    plan = dict(schema_version=1, confidence=.95,
                thresholds={'legacy_score': .5, 'candidate_score': .5},
                families={'replay': {'clusters_n': 4, 'attempts_per_cluster': 1}},
                **{k: True for k in DECLARATIONS})
    return rows, plan


class SimultaneousRiskTests(unittest.TestCase):
    def test_zero_events_exact_and_multiplicity_includes_both_metrics(self):
        rows, plan = fixture(); result = evaluate(rows, plan)
        self.assertEqual(result['statements_n'], 2)
        upper = result['worst_declared_type_upper']['legacy_score']
        self.assertAlmostEqual(upper, 1-.025**.25)
        self.assertGreater(upper, 0)
        self.assertNotIn('test-attack-0', json.dumps(result))

    def test_general_exact_tail_equation_and_boundaries(self):
        for n, k in ((5, 1), (10, 3), (100, 40)):
            p = exact_upper(k, n, .0125)
            cdf = sum(math.comb(n, j)*p**j*(1-p)**(n-j) for j in range(k+1))
            self.assertAlmostEqual(cdf, .0125, places=11)
        self.assertEqual(exact_upper(0, 0, .05), 1)
        self.assertEqual(exact_upper(5, 5, .05), 1)

    def test_finite_sample_marginal_coverage_is_at_least_nominal(self):
        n = 12; alpha = .0125
        for p in (.001, .02, .1, .5, .9, .999):
            noncoverage = sum(math.comb(n, k)*p**k*(1-p)**(n-k)
                              for k in range(n+1) if exact_upper(k, n, alpha) < p)
            self.assertLessEqual(noncoverage, alpha+1e-12)

    def test_missing_declared_type_has_vacuous_upper_and_counts_in_correction(self):
        rows, plan = fixture()
        plan['families']['stationary_hand'] = {'clusters_n': 4, 'attempts_per_cluster': 1}
        result = evaluate(rows, plan)
        self.assertEqual(result['statements_n'], 4)
        self.assertEqual(result['worst_declared_type_upper']['candidate_score'], 1)
        self.assertEqual(result['families']['stationary_hand']['observed_clusters_n'], 0)

    def test_errors_aborts_and_missing_within_budget_cannot_lower_upper(self):
        for outcome in ('technical_error', 'aborted'):
            rows, plan = fixture(); before = evaluate(rows, plan)
            rows[-1].update(outcome=outcome, legacy_score='', candidate_score='')
            after = evaluate(rows, plan)
            metric = after['families']['replay']['metrics']['legacy_score']
            self.assertEqual(metric['unresolved_clusters_n'], 1)
            self.assertEqual(metric['possible_accepting_clusters_n'], 1)
            self.assertGreater(metric['upper'], before['worst_declared_type_upper']['legacy_score'])
        rows, plan = fixture(); plan['families']['replay']['attempts_per_cluster'] = 2
        self.assertEqual(evaluate(rows, plan)['worst_declared_type_upper']['legacy_score'], 1)

    def test_repeated_trials_are_one_any_accept_event(self):
        rows, plan = fixture()
        for i in range(4):
            row = next(r for r in rows if r['trial_id'] == f'test-attack-{i}')
            repeat = dict(row, trial_id=row['trial_id']+'-repeat', candidate_score='1')
            rows.append(repeat)
        plan['families']['replay']['attempts_per_cluster'] = 2
        result = evaluate(rows, plan)['families']['replay']
        self.assertEqual(result['observed_clusters_n'], 4)
        self.assertEqual(result['attempted_n'], 8)
        self.assertEqual(result['metrics']['candidate_score']['observed_accepting_clusters_n'], 4)

    def test_other_treatment_connects_clusters_before_type_filter(self):
        rows, plan = fixture()
        rows[-4]['source_family_ids'] = 'a'
        rows[-3]['source_family_ids'] = 'b'
        rows[-2]['source_family_ids'] = 'a;b'
        rows[-2]['attack_family'] = 'stationary_hand'
        plan['families']['stationary_hand'] = {'clusters_n': 1, 'attempts_per_cluster': 1}
        plan['families']['replay'] = {'clusters_n': 2, 'attempts_per_cluster': 2}
        self.assertEqual(evaluate(rows, plan)['families']['replay']['observed_clusters_n'], 2)

    def test_undeclared_assumptions_return_no_inferential_bounds(self):
        for key in DECLARATIONS:
            rows, plan = fixture(); plan[key] = False
            result = evaluate(rows, plan)
            self.assertIsNone(result['worst_declared_type_upper']['legacy_score'])
            self.assertIsNone(result['families']['replay']['metrics']['legacy_score']['upper'])

    def test_unplanned_types_overbudget_and_split_leakage_rejected(self):
        rows, plan = fixture(); rows[-1]['attack_family'] = 'stationary_hand'
        with self.assertRaises(ValueError): evaluate(rows, plan)
        rows, plan = fixture(); plan['families']['replay']['clusters_n'] = 3
        with self.assertRaises(ValueError): evaluate(rows, plan)
        rows, plan = fixture(); rows[-1]['source_family_ids'] = rows[0]['source_family_ids']
        with self.assertRaises(ValueError): evaluate(rows, plan)

    def test_invalid_numerics_and_implicit_declarations_rejected(self):
        for value in (True, float('nan'), float('inf'), 1, .5):
            rows, plan = fixture(); plan['confidence'] = value
            with self.assertRaises(ValueError): evaluate(rows, plan)
        for args in ((True, 4, .05), (2, 1, .05), (0, 4, float('nan'))):
            with self.assertRaises(ValueError): exact_upper(*args)
        rows, plan = fixture(); del plan[DECLARATIONS[0]]
        with self.assertRaises(ValueError): evaluate(rows, plan)

    def test_cli_preserves_output_and_keeps_plan_hashes_private(self):
        rows, plan = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root/'rows.csv'; spec = root/'plan.json'; target = root/'out.json'
            with source.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
            spec.write_text(json.dumps(plan))
            command = [sys.executable, '-m', 'validation_v03.simultaneous_risk', '--input', str(source),
                       '--plan', str(spec), '--output', str(target), '--data-scope', 'synthetic']
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(target.read_text()); original = target.read_bytes()
            self.assertEqual(report['data_scope'], 'synthetic')
            self.assertEqual(len(report['plan_sha256']), 64)
            self.assertNotIn('test-attack-0', target.read_text())
            self.assertNotEqual(subprocess.run(command, capture_output=True, timeout=15).returncode, 0)
            self.assertEqual(target.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
