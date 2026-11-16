from fractions import Fraction
import unittest

import numpy as np

from analysis.exact_shared_simplex import pair, tolerance_squared


class ExactSharedSimplexTests(unittest.TestCase):
    def setUp(self):
        self.a = np.array([[0., 0., 0.], [2., 0., 0.], [0., 2., 0.]])
        self.tol = Fraction(1, 10**12)

    def test_near_parallel_shared_edge_resolves_without_epsilon_division(self):
        b = np.array([[0., 0., 0.], [2., 0., 0.], [0., 2., 1e-12]])
        r = pair(self.a, b, self.a[:2], self.tol)
        self.assertTrue(r['resolved']); self.assertFalse(r['intersection_outside_shared_simplex_exactly'])
        self.assertEqual(r['branch'], 'noncoplanar_shared_edge_identity')

    def test_coplanar_edge_overlap_and_contact(self):
        for third, outside in (([1., 1., 0.], True), ([0., -2., 0.], False)):
            b = np.array([[0., 0., 0.], [2., 0., 0.], third])
            r = pair(self.a, b, self.a[:2], self.tol)
            self.assertEqual(r['beyond_registered_resolution'], outside)
            self.assertEqual(pair(b, self.a, self.a[:2], self.tol)['state'], r['state'])

    def test_rational_sections_with_shared_vertex_same_and_opposite_rays(self):
        b = np.array([[0., 0., 0.], [1., 1., -1.], [1., 1., 1.]])
        self.assertTrue(pair(self.a, b, self.a[:1], self.tol)['beyond_registered_resolution'])
        self.assertFalse(pair(self.a, -b, self.a[:1], self.tol)['intersection_outside_shared_simplex_exactly'])

    def test_exact_nonzero_below_resolution_is_reported_separately(self):
        b = np.array([[0., 0., 0.], [1e-9, 1e-9, -1.], [1e-9, 1e-9, 1.]])
        r = pair(self.a, b, self.a[:1], self.tol)
        self.assertTrue(r['intersection_outside_shared_simplex_exactly'])
        self.assertFalse(r['beyond_registered_resolution'])

    def test_coplanar_vertex_containment_and_origin_only(self):
        b = np.array([[0., 0., 0.], [.5, .1, 0.], [.1, .5, 0.]])
        self.assertTrue(pair(self.a, b, self.a[:1], self.tol)['beyond_registered_resolution'])
        self.assertFalse(pair(self.a, -b, self.a[:1], self.tol)['intersection_outside_shared_simplex_exactly'])

    def test_diagonal_tolerance_uses_exact_binary_values_without_sqrt(self):
        self.assertEqual(tolerance_squared(self.a, .000001), Fraction(8)*Fraction.from_float(.000001)**2)

    def test_degenerate_geometry_and_invalid_common_points(self):
        b = [[0, 0, 0], [1, 0, 0], [2, 0, 0]]
        self.assertFalse(pair(self.a, b, self.a[:1], self.tol)['resolved'])
        with self.assertRaises(ValueError): pair(self.a, b, [[.1, .1, 0]], self.tol)
        with self.assertRaises(ValueError): tolerance_squared(self.a, True)


if __name__ == '__main__':
    unittest.main()
