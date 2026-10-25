"""Synthetic mathematical checks only; no human or attack performance evidence."""
import itertools
import math
import unittest
import numpy as np
from validation_v03.standard_metrics import (
    constrained_dtw, time_derivatives, operating_point, threshold_table,
    select_validation_threshold, assert_disjoint_groups,
)


def exhaustive_cost(x, y, radius):
    # Independent tiny-path enumeration, not the dynamic-programming recurrence.
    costs = []
    def visit(i, j, cost):
        if i >= len(x) or j >= len(y) or abs(i-j) > radius:
            return
        cost += (x[i]-y[j])**2
        if (i, j) == (len(x)-1, len(y)-1):
            costs.append(cost)
            return
        for di, dj in ((1, 1), (1, 0), (0, 1)):
            visit(i+di, j+dj, cost)
    visit(0, 0, 0.)
    return min(costs)


class StandardMetricsTests(unittest.TestCase):
    def test_dtw_against_exhaustive_paths(self):
        for x, y in itertools.product(itertools.product((0., 1.), repeat=3), repeat=2):
            for radius in (0, 1, 2):
                r = constrained_dtw(x, y, radius=radius)
                self.assertAlmostEqual(r.distance**2, exhaustive_cost(x, y, radius))
                self.assertEqual(r.path[0], (0, 0))
                self.assertEqual(r.path[-1], (2, 2))

    def test_dtw_speed_change_and_wrong_motion(self):
        r = constrained_dtw([0, 1, 2], [0, 0, 1, 2], radius=1)
        self.assertEqual(r.distance, 0.)
        self.assertGreater(constrained_dtw([0, 1, 2], [2, 1, 0], radius=1).distance, 0)

    def test_dtw_path_summary(self):
        r = constrained_dtw([[0, 0], [0, 0]], [[1, 1], [1, 1]], radius=0)
        self.assertEqual(r.distance, 2.)
        self.assertEqual(r.path_rmse, 1.)

    def test_dtw_rejects_invalid(self):
        for x, y, radius in (([], [1], 1), ([0, math.nan], [0, 1], 1),
                             ([0], [0, 1, 2], 0), ([0], [0], -1)):
            with self.assertRaises(ValueError):
                constrained_dtw(x, y, radius=radius)

    def test_derivative_nonuniform_quadratic(self):
        t = np.array([0., .1, .3, .7, 1.])
        v, a = time_derivatives(t**2, t, max_gap_seconds=.5)
        np.testing.assert_allclose(v[:, 0], 2*t, atol=1e-12)
        np.testing.assert_allclose(a[:, 0], 2., atol=1e-12)

    def test_derivative_time_units(self):
        t = np.array([0., .1, .3, .7, 1.])
        v, a = time_derivatives(t**2, t*2, max_gap_seconds=1.)
        np.testing.assert_allclose(v[:, 0], t, atol=1e-12)
        np.testing.assert_allclose(a[:, 0], .5, atol=1e-12)

    def test_derivative_rejects_gaps_duplicates_and_null(self):
        for x, t in (([0, 1, 2], [0, 0, 1]), ([0, 1, 2], [0, 1, 10]),
                     ([0, None, 2], [0, 1, 2])):
            with self.assertRaises(ValueError):
                time_derivatives(x, t, max_gap_seconds=2.)

    def test_threshold_direction_and_ties(self):
        y, s = [1, 1, 0, 0], [.8, .5, .5, .1]
        p = operating_point(y, s, .5)
        self.assertEqual((p['human_accepted'], p['attack_accepted']), (2, 1))
        table = threshold_table(y, s)
        self.assertEqual(len(table), 4)
        self.assertEqual(table[0]['human_accepted'], 0)
        self.assertEqual(table[-1]['attack_accepted'], 2)

    def test_no_feasible_threshold(self):
        self.assertIsNone(select_validation_threshold([1, 0], [.2, .9],
                          split_name='validation', min_human_accept=1, max_attack_accept=0))

    def test_select_validation_and_reject_test_tuning(self):
        p = select_validation_threshold([1, 1, 0, 0], [.9, .8, .2, .1],
              split_name='validation', min_human_accept=1, max_attack_accept=0)
        self.assertEqual(p['threshold'], .8)
        with self.assertRaises(ValueError):
            select_validation_threshold([1, 0], [.9, .1], split_name='test',
                                        min_human_accept=1, max_attack_accept=0)

    def test_missing_or_single_class_scores_rejected(self):
        for y, s in (([1, 1], [.8, .9]), ([1, 0], [.8, math.nan])):
            with self.assertRaises(ValueError):
                threshold_table(y, s)

    def test_source_leakage(self):
        assert_disjoint_groups({'dev': ['a'], 'test': ['b']})
        with self.assertRaises(ValueError):
            assert_disjoint_groups({'dev': ['a'], 'test': ['a', 'b']})


if __name__ == '__main__':
    unittest.main()
