from fractions import Fraction
import unittest

import numpy as np
from scipy.spatial.transform import Rotation

from analysis.runtime_benchmark.interval_boxes import Box, Unresolved, elementary, norm
from analysis.runtime_benchmark.sdk_path_boxes import (
    euler_matrix, matrix_quaternion, quaternion_rotvec, sdk_rodrigues,
    local_rotations, lbs_box, chord_remainder, euler_range,
)
from analysis.template_free_temporal_path import evaluate


def contained(box, value):
    a = np.asarray(value, float)
    return bool(((a >= box.lo) & (a <= box.hi)).all())


class SDKPathBoxTests(unittest.TestCase):
    def test_outward_arithmetic_contains_exact_rational_values(self):
        a, b = Box(.1), Box(.3)
        for candidate, exact in ((a+b, Fraction.from_float(.1)+Fraction.from_float(.3)),
                                 (a*b, Fraction.from_float(.1)*Fraction.from_float(.3)),
                                 (a/b, Fraction.from_float(.1)/Fraction.from_float(.3))):
            self.assertLessEqual(Fraction.from_float(float(candidate.lo)), exact)
            self.assertGreaterEqual(Fraction.from_float(float(candidate.hi)), exact)

    def test_zero_crossing_squares_and_divisor_fail_closed(self):
        self.assertEqual(float(Box(-2, 3).square().lo), 0)
        self.assertTrue(contained(Box(-2, 3).square(), 9))
        with self.assertRaises(Unresolved): Box(1)/Box(-1, 1)
        with self.assertRaises(Unresolved): Box(-1, 2).sqrt()
        with self.assertRaises(Unresolved): Box(np.inf)

    def test_float32_cast_and_matmul_contain_actual_reductions(self):
        rng = np.random.default_rng(7)
        a = rng.normal(size=(4, 17)).astype(np.float32)
        b = rng.normal(size=(17, 3)).astype(np.float32)
        self.assertTrue(contained(Box(a).cast32(), a))
        self.assertTrue(contained(Box(a, bits=32)@Box(b, bits=32), a@b))

    def test_interval_real_trig_tracks_internal_extremum(self):
        candidate = elementary('sin', Box(1., 2.), 0)
        self.assertTrue(contained(candidate, 1))
        self.assertTrue(contained(candidate, [np.sin(1), np.sin(2)]))

    def test_registered_euler_range_contains_all_interior_parameter_samples(self):
        p = np.arange(135, dtype=float).reshape(3, 15, 3)/100
        for t0, t1 in ((0, .125), (1.375, 1.5), (1.5, 1.625), (2.875, 3)):
            candidate = euler_range(p, t0, t1)
            self.assertTrue(contained(candidate, evaluate(p, np.linspace(t0, t1, 17))))
        with self.assertRaises(Unresolved): euler_range(p, 1.4, 1.6)

    def test_scipy_conversion_chain_includes_native_axis_angles(self):
        for angles in ([.1, .2, .3], [-.4, .1, .2], [2., .1, -.2], [0, 0, 0]):
            q = Box(angles)
            m = euler_matrix(q)
            true_matrix = Rotation.from_euler('XYZ', angles).as_matrix()
            self.assertTrue(contained(m, true_matrix))
            r = quaternion_rotvec(matrix_quaternion(m))
            self.assertTrue(contained(r, Rotation.from_matrix(true_matrix).as_rotvec()))

    def test_sdk_shifted_norm_and_small_input_singularity(self):
        import torch
        from smplx.lbs import batch_rodrigues
        for pose in ([.1, .2, .3], [.0001, -.0002, .0003], [0, 0, 0]):
            box = sdk_rodrigues(Box(pose))
            actual = batch_rodrigues(torch.tensor([pose], dtype=torch.float32)).numpy()[0]
            self.assertTrue(contained(box, actual))
        with self.assertRaises(Unresolved): sdk_rodrigues(Box(np.full(3, -float(np.float32(1e-8)))))

    def test_local_basis_conjugation_and_real_float32_path(self):
        p = np.zeros((3, 15, 3)); p[:, :, 0] = np.array([.1, .2, .3])[:, None]
        b = np.tile(np.eye(3), (16, 1, 1))
        r = local_rotations(p, b, .5, .625)
        self.assertEqual(len(r), 16)
        self.assertTrue(contained(r[0], np.eye(3)))

    def test_lbs_rigid_root_fixture_and_chord_box(self):
        template = np.zeros((778, 3), np.float32); template[:, 0] = np.linspace(0, 1, 778)
        regressor = np.zeros((16, 778), np.float32); regressor[:, 0] = 1
        posedirs = np.zeros((135, 2334), np.float32)
        weights = np.zeros((778, 16), np.float32); weights[:, 0] = 1
        parents = [-1]+[0]*15
        b = lbs_box([Box(np.eye(3), bits=32) for _ in range(16)], template, regressor, posedirs, weights, parents)
        self.assertTrue(contained(b, template))
        distance = chord_remainder(Box(template), template, template, 0, 1)
        self.assertTrue((distance >= 0).all())
        self.assertLess(float(distance.max()), 1e-12)


if __name__ == '__main__':
    unittest.main()
