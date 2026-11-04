import unittest

from analysis.reproducibility.reconcile_initial_scores import (
    dtw_path, estimate, summarize, table7_path, weighted,
)


class InitialScoreReconciliationTests(unittest.TestCase):
    def test_dtw_warp_and_tie_priority(self):
        left, right = dtw_path([0, 1, 2], [0, 0, 1, 2])
        self.assertEqual(left.tolist(), [0, 0, 1, 2])
        self.assertEqual(right.tolist(), [0, 1, 2, 3])
        left, right = dtw_path([0, 0], [0, 0])
        self.assertEqual(left.tolist(), [0, 1])
        self.assertEqual(right.tolist(), [0, 1])

    def test_signed_correlation_and_detection_rule_are_distinct(self):
        self.assertEqual(estimate(-.39, 'tendency', .8), 0)
        self.assertAlmostEqual(estimate(-.39, 'tendency', .8, clipped=False), -.4)
        self.assertEqual(estimate(None, 'angle', 1), 0)
        self.assertAlmostEqual(estimate(0, 'angle', .5), .5)

    def test_balance_and_hand_action_reweighting(self):
        # One left and three right sessions. All have three actions and levels.
        # Equal hand/action means give the one left session half of the weight.
        rows = []
        for session in range(4):
            for action in range(1, 4):
                score = .8 if session == 0 else .2
                rows.append(dict(session=str(session), action=('l' if session == 0 else 'r')+str(action),
                    total_frames=50 if session == 0 else 100, detection_rate=1,
                    raw=dict(angle=(1-score)*39.1673, dtw_angle=(1-score)*32.6513,
                        tendency=score*.78, tendency21=score*.78,
                        distance=0, dtw_distance=0, accel=0, trajectory=0)))
        trial = summarize(rows, 21)
        cell = table7_path(rows)
        self.assertAlmostEqual(trial['trial_equal_score'], .35)
        self.assertAlmostEqual(trial['session_equal_score'], .35)
        self.assertAlmostEqual(cell['score'], .5)
        self.assertAlmostEqual(trial['frame_weighted_score'], 300/1050)
        self.assertAlmostEqual(trial['mean_weighted_minus_weighted_mean'], 0)
        self.assertAlmostEqual(cell['mean_weighted_minus_weighted_mean'], 0)
        self.assertAlmostEqual(weighted(trial['metric_means']), .35)


if __name__ == '__main__':
    unittest.main()
