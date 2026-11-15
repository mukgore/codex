import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

from analysis.runtime_benchmark.mano_model_prior_audit import parse_interval, assess, ideal_mirror_control, execute


def profile():
    return {'native_joint_groups': {'free': [13], 'hinge': list(range(1, 13))+[14, 15]},
            'intervals_degrees': {'free': [[-45., 45.], [-15., 45.], [0., 45.]],
                                 'hinge': [[0., 0.], [0., 0.], [0., 90.]]},
            'zero_mask_radians': 1e-6}


class ModelPriorAuditTests(unittest.TestCase):
    def test_ideal_mirror_exposes_asymmetric_default_without_changing_it(self):
        config = profile(); before = copy.deepcopy(config)
        control = ideal_mirror_control(config)
        self.assertEqual(control['right_max_axis_loss_radians'], 0.)
        self.assertAlmostEqual(control['mirrored_max_axis_loss_radians'], 15*np.pi/180)
        self.assertEqual(config, before)
        self.assertFalse(control['clinical_asymmetry_proven'])

    def test_valid_receipt_cannot_be_swapped_to_unbound_data_or_mutated_by_output(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()/'private_artifacts'; base.mkdir()
            random = base/'random'; anatomy = base/'anatomy'
            r1 = base/'record1'; r2 = base/'record2'
            for path in (random, anatomy, r1, r2): path.mkdir()
            (r2/'receipt.private.json').write_text(json.dumps({'artifact_roots': [str(anatomy)]}))
            for linked, output, error in ((base/'other_data', base/'audit', 'source root'),
                                           (random, random/'audit', 'separate')):
                (r1/'receipt.private.json').write_text(json.dumps({'artifact_roots': [str(linked)]}))
                with patch('analysis.runtime_benchmark.mano_model_prior_audit.verify', return_value={'state': 'EXITED_ZERO'}):
                    with self.assertRaisesRegex(ValueError, error):
                        execute(random, r1, anatomy, r2, base/'unused_source.py', output)
                self.assertFalse(output.exists())

    def test_symmetric_asymmetric_and_zero_author_notations(self):
        self.assertEqual(parse_interval('+-:45'), [-45., 45.])
        self.assertEqual(parse_interval('+:45,-:15'), [-15., 45.])
        self.assertEqual(parse_interval('+-:0'), [0., 0.])
        for spec in ('+-:-1', '+:nan,-:0', '+:2,-:-1', '0..90', '+-:181'):
            with self.assertRaises(ValueError): parse_interval(spec)

    def test_zero_mask_is_on_absolute_angle_not_excess(self):
        angles = np.zeros((1, 15, 3)); angles[0, 0, 0] = .5e-6
        raw, effective = assess(angles, profile())
        self.assertEqual(raw[0, 0, 0], .5e-6); self.assertEqual(effective[0, 0, 0], 0.)
        angles[0, 0, 0] = 2e-6
        _, effective = assess(angles, profile()); self.assertEqual(effective[0, 0, 0], 2e-6)
        # A tiny excess at a large angle is NOT suppressed by the author's mask.
        angles[0, 0, 2] = np.pi/2+1e-8
        _, effective = assess(angles, profile()); self.assertGreater(effective[0, 0, 2], 0.)

    def test_mask_boundary_is_strict_and_zero_is_not_penalized(self):
        angles = np.zeros((3, 15, 3)); angles[1, 0, 0] = 1e-6; angles[2, 0, 0] = -1.0001e-6
        _, effective = assess(angles, profile())
        self.assertEqual(effective[0].sum(), 0.); self.assertEqual(effective[1].sum(), 0.)
        self.assertAlmostEqual(effective[2].sum(), 1.0001e-6)

    def test_native_joint_mapping_and_asymmetric_negative_side(self):
        angles = np.zeros((1, 15, 3)); angles[0, 12, 1] = -20*np.pi/180
        angles[0, 0, 2] = 95*np.pi/180
        raw, effective = assess(angles, profile())
        self.assertAlmostEqual(raw[0, 12, 1], 5*np.pi/180)
        self.assertAlmostEqual(effective[0, 0, 2], 5*np.pi/180)
        self.assertEqual(np.count_nonzero(raw), 2)

    def test_all_bounds_include_their_endpoints(self):
        angles = np.zeros((2, 15, 3)); angles[:, :, 2] = [[0.]*15, [90*np.pi/180]*15]
        angles[0, 12] = [-45., -15., 0.]; angles[1, 12] = [45., 45., 45.]
        angles[:, 12] *= np.pi/180
        raw, effective = assess(angles, profile())
        np.testing.assert_array_equal(raw, 0.); np.testing.assert_array_equal(effective, 0.)

    def test_missing_duplicate_nonfinite_and_root_inputs_fail_closed(self):
        for shape in ((0, 15, 3), (1, 16, 3), (1, 15, 2)):
            with self.assertRaises(ValueError): assess(np.zeros(shape), profile())
        angles = np.zeros((1, 15, 3)); angles[0, 0, 0] = np.nan
        with self.assertRaises(ValueError): assess(angles, profile())
        for edit in ('duplicate', 'missing', 'backwards'):
            config = copy.deepcopy(profile())
            if edit == 'duplicate': config['native_joint_groups']['free'].append(1)
            if edit == 'missing': config['native_joint_groups']['free'] = []
            if edit == 'backwards': config['intervals_degrees']['free'][0] = [2., 1.]
            with self.assertRaises(ValueError): assess(np.zeros((1, 15, 3)), config)


if __name__ == '__main__': unittest.main()
