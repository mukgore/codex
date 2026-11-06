import unittest

import numpy as np

from analysis.camera_controls import angular_activity, diagnostics
from validation_v03.adapters import InputSpec


class CameraControlTests(unittest.TestCase):
    def test_activity_does_not_bridge_missing_intervals(self):
        def block(times, angles):
            return {'times_seconds': times, 'angles_degrees': [[x] * 15 for x in angles]}

        self.assertAlmostEqual(
            angular_activity([block([0, 1], [5, 5]), block([10, 12], [100, 106])]), 2.0)
        self.assertIsNone(angular_activity([]))

    def test_undetected_frames_are_not_a_zero_motion_measurement(self):
        class Scorer:
            def call(self, request):
                self.request = request
                return {'score': {'captcha': 0}, 'score_pass': False, 'gate_pass': False}

        spec = InputSpec(640, 480, 'normalized_xy', 'ms', False, 0.2)
        frames = [{'t_ms': t, 'lm': None} for t in (0, 40, 80)]
        report = diagnostics(Scorer(), np.zeros((3, 21, 2)).tolist(),
                             {'analyzed_frames': 0, 'blocks': []}, frames, spec)
        self.assertEqual(report['attempted_frames'], 3)
        self.assertEqual(report['detected_frames'], 0)
        self.assertIsNone(report['angular_activity_degrees_per_second'])
        self.assertIsNone(report['complete_trial_candidate_features'])
