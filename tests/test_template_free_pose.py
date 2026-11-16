import unittest

import numpy as np

from analysis.runtime_benchmark.template_free_pose import propose, expand, representation_errors, decide


class TemplateFreePoseTests(unittest.TestCase):
    def test_streams_are_reproducible_and_do_not_share_draws(self):
        draws = []
        for hand in ('right', 'left'):
            for seed in (7, 19):
                for attempt in range(8):
                    c, p = propose(hand, seed, attempt)
                    np.testing.assert_array_equal(c, propose(hand, seed, attempt)[0])
                    self.assertIsNone(p['primitive']); self.assertIsNone(p['time_curve'])
                    draws.append(c.tobytes())
        self.assertEqual(len(set(draws)), 32)
        for bad in (True, -1, 8):
            with self.assertRaises(ValueError): propose('right', 7, bad)

    def test_expansion_preserves_signed_coupling_without_clipping(self):
        basis = np.zeros((6, 45)); basis[0, :3] = [1, -2, 3]; basis[1, :3] = [-2, 1, 0]
        actual = expand([2, -3, 0, 0, 0, 0], basis)
        np.testing.assert_array_equal(actual[0, :3], [8, -7, 6])
        with self.assertRaises(ValueError): expand([float('nan')]*6, basis)
        with self.assertRaises(ValueError): expand([0]*6, np.zeros((45, 6)))

    def test_representation_drift_and_missing_geometry_fail_closed(self):
        output = {'full_pose': np.zeros((1, 48)), 'joints': np.zeros((1, 16, 3)), 'vertices': np.zeros((1, 778, 3))}
        self.assertEqual(max(representation_errors(output, output).values()), 0)
        changed = {k: v.copy() for k, v in output.items()}; changed['vertices'][0, 0, 0] = 2e-6
        with self.assertRaises(ValueError): representation_errors(output, changed)
        changed['vertices'] = np.zeros((1, 21, 3))
        with self.assertRaises(ValueError): representation_errors(output, changed)

    def test_measurement_failures_and_model_excess_never_release(self):
        zero = np.zeros((1, 15, 3))
        clear = {'state': 'NO_TESTED_PAIR_INTERSECTION', 'pair_ids': {}}
        self.assertTrue(decide(zero, clear)['model_surface_eligible'])
        excess = zero.copy(); excess[0, 1, 0] = .001
        self.assertFalse(decide(excess, clear)['model_surface_eligible'])
        for surface in ({'state': 'UNMEASURABLE_DEGENERATE_TRIANGLES'},
                        {'state': 'SURFACE_INTERSECTION_INDICATORS', 'pair_ids': {'intersects': [[1, 2]]}}):
            self.assertFalse(decide(zero, surface)['model_surface_eligible'])
        self.assertFalse(decide(zero, clear)['release_allowed'])
        with self.assertRaises(ValueError): decide(zero, {'state': 'UNKNOWN'})
