import unittest
import numpy as np
from scipy.spatial.transform import Rotation

from analysis.runtime_benchmark.mano_anatomical_frame_probe import template_basis, compose_anatomical, extract_anatomical, design


def fixture_points():
    p = np.zeros((21, 3))
    for f, base in enumerate((1, 5, 9, 13, 17)):
        for j in range(4):
            p[base+j] = [f-2., .1*j, 2.+.1*f+j]
    return p


class AnatomicalFrameTests(unittest.TestCase):
    def test_incoming_link_and_thumb_specific_up_reference(self):
        p = fixture_points(); basis = template_basis(p, 'right')
        # Native joint1 is canonical index MCP5, and uses incoming wrist->MCP.
        incoming = -p[5]/np.linalg.norm(p[5])
        np.testing.assert_allclose(basis[1, :, 0], incoming)
        self.assertFalse(np.allclose(basis[1, :, 0], (p[5]-p[6])/np.linalg.norm(p[5]-p[6])))
        thumb_incoming = -p[1]
        thumb_bend = np.cross(thumb_incoming, [1., 1., 1.])
        np.testing.assert_allclose(basis[13, :, 2], thumb_bend/np.linalg.norm(thumb_bend))
        np.testing.assert_allclose(basis.swapaxes(-1, -2)@basis, np.tile(np.eye(3), (16, 1, 1)), atol=1e-14)
        np.testing.assert_allclose(np.linalg.det(basis), 1.)

    def test_column_basis_conjugation_rotates_about_anatomical_axis(self):
        basis = np.tile(np.eye(3), (16, 1, 1))
        basis[1] = [[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]]
        angles = np.zeros((1, 15, 3)); angles[0, 0, 0] = .2
        pose = compose_anatomical(angles, basis)
        # Anatomical x maps to native y. Active +y rotation moves z towards x.
        moved = Rotation.from_rotvec(pose[0, :3]).apply([0., 0., 1.])
        np.testing.assert_allclose(moved, [np.sin(.2), 0., np.cos(.2)], atol=1e-14)
        np.testing.assert_array_equal(pose[0, 3:], 0.)

    def test_intrinsic_xyz_is_explicit_rx_ry_rz_and_not_extrinsic_xyz(self):
        angles = np.zeros((1, 15, 3)); x, y, z = .13, -.21, .32; angles[0, 0] = [x, y, z]
        basis = np.tile(np.eye(3), (16, 1, 1))
        pose = compose_anatomical(angles, basis)
        rx = np.array([[1, 0, 0], [0, np.cos(x), -np.sin(x)], [0, np.sin(x), np.cos(x)]])
        ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
        rz = np.array([[np.cos(z), -np.sin(z), 0], [np.sin(z), np.cos(z), 0], [0, 0, 1]])
        np.testing.assert_allclose(Rotation.from_rotvec(pose[0, :3]).as_matrix(), rx@ry@rz, atol=1e-14)
        self.assertGreater(np.abs(rx@ry@rz-rz@ry@rx).max(), .01)

    def test_left_basis_and_signed_angles_preserve_mirrored_rotation(self):
        p = fixture_points(); reflection = np.diag([-1., 1., 1.])
        right = template_basis(p, 'right'); left = template_basis(p@reflection, 'left')
        np.testing.assert_allclose(left, reflection@right@np.diag([1., 1., -1.]), atol=1e-14)
        angles = np.tile([.12, -.08, .17], (1, 15, 1))
        rp = compose_anatomical(angles, right); lp = compose_anatomical(angles*[-1., -1., 1.], left)
        r = Rotation.from_rotvec(rp.reshape(-1, 3)).as_matrix()
        l = Rotation.from_rotvec(lp.reshape(-1, 3)).as_matrix()
        np.testing.assert_allclose(l, reflection@r@reflection, atol=1e-14)

    def test_compound_roundtrip_and_complete_axis_design(self):
        angles, rows = design(); self.assertEqual(angles.shape, (94, 15, 3))
        self.assertEqual(sum(r['kind'] == 'single_axis' for r in rows), 90)
        basis = template_basis(fixture_points(), 'right')
        np.testing.assert_allclose(extract_anatomical(compose_anatomical(angles, basis), basis), angles, atol=1e-14)

    def test_degenerate_basis_gimbal_and_root_in_pose_are_rejected(self):
        with self.assertRaises(ValueError): template_basis(np.zeros((21, 3)), 'right')
        basis = np.tile(np.eye(3), (16, 1, 1)); bad = basis.copy(); bad[0, 0, 0] = -1
        with self.assertRaises(ValueError): compose_anatomical(np.zeros((1, 15, 3)), bad)
        with self.assertRaises(ValueError): extract_anatomical(np.zeros((1, 48)), basis)
        angles = np.zeros((1, 15, 3)); angles[0, 0, 1] = np.pi/2
        with self.assertRaises(ValueError): extract_anatomical(compose_anatomical(angles, basis), basis)


if __name__ == '__main__': unittest.main()
