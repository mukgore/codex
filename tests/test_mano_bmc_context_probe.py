import unittest
import numpy as np

from analysis.runtime_benchmark.mano_bmc_context_probe import contexts, world_rotations, compose_world_delta, design


class BMCContextTests(unittest.TestCase):
    def test_contexts_are_complete_crossed_factors_without_random_or_time(self):
        rows = contexts()
        self.assertEqual(len(rows), 12)
        self.assertEqual(len({(r['beta0'], r['pose_name'], r['root_name']) for r in rows}), 12)
        self.assertEqual({r['beta0'] for r in rows}, {-1., 0., 1.})
        self.assertTrue(all(np.count_nonzero(r['betas'][1:]) == 0 for r in rows))

    def test_world_delta_composes_with_rotated_parent_instead_of_adding_rotvecs(self):
        # Joint1 parent=root; root rotates local x to world y. Applying world z
        # on the left must rotate that outgoing world vector towards negative x.
        pose = np.zeros(45); pose[0] = .3
        root = np.array([0., 0., np.pi/2])
        changed = compose_world_delta(pose, root, 1, [0., 0., 1.], .05)
        before = world_rotations(pose, root)[1] @ np.array([1., 0., 0.])
        after = world_rotations(changed, root)[1] @ np.array([1., 0., 0.])
        expected = np.array([-np.sin(.05), np.cos(.05), 0.])
        np.testing.assert_allclose(before, [0., 1., 0.], atol=1e-14)
        np.testing.assert_allclose(after, expected, atol=1e-14)
        self.assertFalse(np.allclose(changed[:3], pose[:3]+[0., 0., .05]))
        np.testing.assert_array_equal(changed[3:], pose[3:])

    def test_compound_ancestor_frame_and_round_trip(self):
        row = contexts()[-1]; pose, root = row['pose'], row['root']
        before = world_rotations(pose, root)
        joint = 3; axis = np.array([1., 2., 3.])/np.sqrt(14)
        changed = compose_world_delta(pose, root, joint, axis, .02)
        after = world_rotations(changed, root)
        # Rodrigues independently computed for the requested world rotation.
        k = np.array([[0., -axis[2], axis[1]], [axis[2], 0., -axis[0]], [-axis[1], axis[0], 0.]])
        delta = np.eye(3)+np.sin(.02)*k+(1-np.cos(.02))*(k@k)
        np.testing.assert_allclose(after[joint], delta@before[joint], atol=1e-14)
        np.testing.assert_allclose(after[:joint], before[:joint], atol=1e-14)
        undone = compose_world_delta(changed, root, joint, axis, -.02)
        np.testing.assert_allclose(world_rotations(undone, root), before, atol=1e-14)

    def test_design_has_paired_methods_for_each_signed_direction(self):
        axes = np.tile(np.eye(3), (15, 1, 1))
        poses, rows = design(np.zeros(45), np.zeros(3), axes, axes, list(range(1, 16)))
        self.assertEqual(poses.shape, (180, 45))
        np.testing.assert_array_equal(poses[:90], poses[90:])
        self.assertEqual(sum(r['method'] == 'adaptive' for r in rows), 90)

    def test_invalid_axis_parent_pose_and_joint_are_rejected(self):
        for joint, axis in ((0, [1., 0., 0.]), (1, [2., 0., 0.]), (1, [np.nan, 0., 0.])):
            with self.assertRaises(ValueError):
                compose_world_delta(np.zeros(45), np.zeros(3), joint, axis, .02)
        with self.assertRaises(ValueError):
            world_rotations(np.zeros(44), np.zeros(3))
        with self.assertRaises(ValueError):
            world_rotations(np.zeros(45), np.zeros(3), tuple(range(16)))


if __name__ == '__main__':
    unittest.main()
