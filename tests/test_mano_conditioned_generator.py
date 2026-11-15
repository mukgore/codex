import copy
import json
from pathlib import Path
import unittest
import numpy as np

from analysis.runtime_benchmark.mano_conditioned_generator import (
    Timings, recipe, trajectory, policy_profile, SEEDS, PRIMITIVES, CUE_PRIMITIVES, POLICIES, FRAMES,
)
from analysis.runtime_benchmark.mano_model_prior_audit import assess


class ConditionedGeneratorTests(unittest.TestCase):
    def test_cue_proposals_keep_index_pinky_and_thumb_neutral_across_hands_and_policies(self):
        source = self.source()
        for seed in SEEDS:
            for primitive in CUE_PRIMITIVES:
                spec = recipe(seed, primitive)
                self.assertFalse(spec['visibility_verified'])
                self.assertFalse(spec['human_independent_finger_control_verified'])
                for hand in ('right', 'left'):
                    for policy in POLICIES:
                        times, angles = trajectory(spec, hand, policy)
                        np.testing.assert_array_equal(angles[:, list(range(3))+list(range(6,9))+list(range(12,15))], 0.)
                        self.assertGreater(np.max(angles[:,3:6,2]), 0.)
                        if primitive == CUE_PRIMITIVES[0]: np.testing.assert_array_equal(angles[:,9:12], 0.)
                        else: self.assertGreater(np.max(angles[:,9:12,2]), 0.)
                        self.assertFalse(assess(angles, policy_profile(source,hand,policy))[1].any())
                        np.testing.assert_allclose(angles[[0,-1]], 0., atol=1e-14)
                        replay_t, replay = trajectory(recipe(seed,primitive),hand,policy)
                        np.testing.assert_array_equal(replay,angles)
                        np.testing.assert_array_equal(replay_t,times)

    def source(self):
        return json.loads((Path(__file__).resolve().parents[1]/'references/manotorch_default_constraint_extraction.json').read_text())

    def test_seed_replay_and_semantic_substreams_do_not_depend_on_hand_or_policy(self):
        first = recipe(7, PRIMITIVES[0]); second = recipe(7, PRIMITIVES[0])
        self.assertEqual(first, second); self.assertNotEqual(first, recipe(19, PRIMITIVES[0]))
        self.assertEqual(len({tuple(v) for v in first['substreams_entropy'].values()}), 3)
        _, a = trajectory(first, 'right', 'author_exact')
        _, b = trajectory(first, 'right', 'ideal_mirror_comparator')
        np.testing.assert_array_equal(a, b)
        self.assertFalse(first['independent_joint_uniform_sampling'])

    def test_time_endpoints_and_finger_synergy_are_preserved(self):
        for seed in SEEDS:
            for primitive in PRIMITIVES:
                spec = recipe(seed, primitive); times, angles = trajectory(spec, 'right', 'author_exact')
                self.assertEqual(angles.shape, (FRAMES, 15, 3)); self.assertTrue((np.diff(times) > 0).all())
                self.assertEqual(times[0], 0.); self.assertEqual(times[-1], spec['duration_seconds'])
                np.testing.assert_allclose(angles[[0, -1]], 0., atol=1e-14)
                for start in (0, 3, 6, 9):
                    np.testing.assert_allclose(angles[:, start+1, 2], .85*angles[:, start, 2], atol=1e-14)
                    np.testing.assert_allclose(angles[:, start+2, 2], .55*angles[:, start, 2], atol=1e-14)

    def test_original_and_derived_policy_bounds_stay_distinct_without_source_mutation(self):
        source = self.source(); before = copy.deepcopy(source)
        for seed in SEEDS:
            for primitive in PRIMITIVES:
                for hand in ('right', 'left'):
                    for policy in POLICIES:
                        _, angles = trajectory(recipe(seed, primitive), hand, policy)
                        applied = policy_profile(source, hand, policy)
                        self.assertFalse(assess(angles, applied)[1].any())
        self.assertEqual(source, before)
        mirrored = policy_profile(source, 'left', 'ideal_mirror_comparator')
        self.assertEqual(mirrored['intervals_degrees']['thumb_cmc'][1], [-45., 15.])
        self.assertFalse(mirrored['profile_admission_enabled'])

    def test_mirrored_candidate_keeps_original_default_violation_visible(self):
        source = self.source(); spec = recipe(7, PRIMITIVES[0])
        _, right = trajectory(spec, 'right', 'author_exact')
        _, left = trajectory(spec, 'left', 'ideal_mirror_comparator')
        np.testing.assert_allclose(left, right*[-1., -1., 1.], atol=0.)
        self.assertFalse(assess(right, source)[1].any())
        self.assertTrue(assess(left, source)[1].any())

    def test_timing_accumulates_actual_disjoint_phases_and_preserves_failed_video_marker(self):
        timer = Timings()
        for _ in range(2):
            with timer.phase('work'): sum(range(1000))
        with self.assertRaises(RuntimeError):
            with timer.phase('failed'): raise RuntimeError('fixture')
        timer.video_ready_ns = timer.start_wall+1
        report = timer.snapshot(None, 'INCOMPLETE')
        self.assertEqual(report['video_ready_wall_ns'], 1)
        self.assertEqual(report['phases']['work']['calls_n'], 2)
        self.assertEqual(report['phases']['failed']['calls_n'], 1)
        self.assertGreaterEqual(report['validated_pipeline_wall_ns'], sum(r['wall_ns'] for r in report['phases'].values()))
        self.assertFalse(report['shared_hand_model_setup_included']); self.assertFalse(report['gpu_used'])
        with timer.phase('outer'):
            with self.assertRaises(ValueError):
                with timer.phase('nested'): pass

    def test_unregistered_sampling_or_ambiguous_handedness_is_rejected(self):
        for seed, primitive in ((True, PRIMITIVES[0]), (0, PRIMITIVES[0]), (7, 'unknown')):
            with self.assertRaises(ValueError): recipe(seed, primitive)
        with self.assertRaises(ValueError): trajectory(recipe(7, PRIMITIVES[0]), 'unknown', 'author_exact')
        with self.assertRaises(ValueError): policy_profile(self.source(), 'left', 'unknown')


if __name__ == '__main__': unittest.main()
