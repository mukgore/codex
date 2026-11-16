import unittest

import numpy as np

from analysis.template_free_temporal_path import evaluate, midpoint_chord_error
from analysis.runtime_benchmark.template_free_path_pilot import path


class TemporalPathTests(unittest.TestCase):
    def setUp(self):
        self.p = np.arange(135, dtype=float).reshape(3, 15, 3)/100

    def test_registered_old_sample_definition_and_exact_knots(self):
        times, original = path(self.p)
        np.testing.assert_array_equal(evaluate(self.p, times), original)
        np.testing.assert_array_equal(evaluate(self.p, [0, 1.5, 3]), self.p)

    def test_midpoints_are_new_times_and_convex_inside_each_segment(self):
        times = np.linspace(0, 3, 25); mid = (times[:-1]+times[1:])/2
        actual = evaluate(self.p, mid)
        self.assertFalse(np.isin(mid, times).any())
        for i, value in enumerate(actual):
            s = 0 if mid[i] < 1.5 else 1
            self.assertTrue((value >= self.p[s]).all())
            self.assertTrue((value <= self.p[s+1]).all())

    def test_nonlinear_parameter_interpolation_differs_from_endpoint_average(self):
        a = evaluate(self.p, [0, .125]); middle = evaluate(self.p, [.0625])[0]
        self.assertGreater(float(np.max(np.abs(middle-a.mean(axis=0)))), 0)

    def test_midpoint_chord_error_and_no_supremum_claim(self):
        t = np.linspace(0, 3, 25); p = np.zeros((25, 778, 3)); p[:, 1, 0] = 1
        m = (p[:-1]+p[1:])/2; m[:, 2, 2] = .01
        r = midpoint_chord_error(p, m, t, (t[:-1]+t[1:])/2)
        np.testing.assert_allclose(r['interval_max_native_error'], .01)
        np.testing.assert_allclose(r['interval_max_relative_to_endpoint_diagonal'], .01)
        self.assertFalse(r['observed_midpoint_errors_are_supremum_bounds'])
        self.assertFalse(r['continuous_collision_free_proven'])

    def test_endpoints_and_midpoint_can_all_be_disjoint_and_still_contact_in_between(self):
        # Congruent parallel triangles, one with z(t) below. At z=0 their
        # complete faces coincide; at every nonzero z they are disjoint.
        z = lambda t: 8*(t-.25)*(t-.75)
        self.assertTrue(all(z(t) != 0 for t in (0, .5, 1)))
        self.assertEqual(z(.25), 0); self.assertEqual(z(.75), 0)

    def test_invalid_time_geometry_and_missing_denominators_rejected(self):
        for times in ([-.01], [3.01], [1, 1], [1, 0], [], [np.nan]):
            with self.assertRaises(ValueError): evaluate(self.p, times)
        t = np.linspace(0, 3, 25); p = np.zeros((25, 778, 3)); m = np.zeros((24, 778, 3))
        with self.assertRaises(ValueError): midpoint_chord_error(p, m, t, (t[:-1]+t[1:])/2)
        p[:, 1, 0] = 1
        with self.assertRaises(ValueError): midpoint_chord_error(p, m[:23], t, (t[:-1]+t[1:])/2)


if __name__ == '__main__':
    unittest.main()
