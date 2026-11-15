import copy
import json
from types import SimpleNamespace
import unittest
import numpy as np

from analysis.runtime_benchmark.common_camera_mask import (
    common_camera, view_basis, project, surface_proxy, surface_weight_interval, neutral_registration, VIEWS, WIDTH, HEIGHT,
)


def reference():
    p = np.zeros((21, 3)); p[9] = [0., 2., 0.]; p[5] = [-1., 2., 0.]; p[17] = [1., 2., 0.]
    p[[4, 8, 16, 20]] = [[-2, 3, 0], [-1, 4, 0], [1, 4, 0], [2, 3, 0]]
    return p


def calibration():
    joints = np.tile(reference(), (2, 1, 1)); vertices = joints.copy()
    config = SimpleNamespace(condition2_min_visible_fingers=2, condition2_margin_frac=.1)
    return common_camera(reference(), [{'vertices': vertices, 'joints': joints}], config)


class CommonCameraMaskTests(unittest.TestCase):
    def test_neutral_registration_preserves_chirality_under_rotated_native_left_frame(self):
        right = reference(); reflection = np.diag([-1.,1.,1.])
        # Arbitrary proper native embedding, including an upside-down long axis.
        rotation = np.diag([-1.,-1.,1.]); offset = np.array([3.,-4.,2.])
        left = right@reflection@rotation.T+offset
        br = neutral_registration(right,'right'); bl = neutral_registration(left,'left')
        rr = (right-right[0])@br; ll = (left-left[0])@bl
        np.testing.assert_allclose(ll,rr*[-1.,1.,1.],atol=1e-14)
        self.assertGreater(rr[9,1],0); self.assertGreater(ll[9,1],0)
        self.assertAlmostEqual(np.linalg.det(bl),1.)

    def test_registration_is_rigid_and_uses_a_fixed_neutral_not_each_frame(self):
        neutral = reference(); basis = neutral_registration(neutral,'left')
        sequence = np.stack((neutral,neutral+[.2,.1,.3])); origin = sequence[0,0]
        registered = (sequence-origin)@basis
        np.testing.assert_allclose(np.linalg.norm(sequence-origin,axis=2),np.linalg.norm(registered,axis=2),atol=1e-14)
        self.assertGreater(np.linalg.norm(registered[1,0]-registered[0,0]),.1)

    def test_registration_rejects_unlabeled_or_degenerate_hand_references(self):
        with self.assertRaises(ValueError): neutral_registration(reference(),'unknown')
        with self.assertRaises(ValueError): neutral_registration(np.zeros((21,3)),'right')

    def test_two_views_are_proper_fixed_cameras_and_opposite_depth(self):
        camera = calibration(); points = np.array([[.2, 1., .3], [-.7, 2., -.4]])
        positive, zp = project(points, np.zeros(3), camera, VIEWS[0])
        negative, zn = project(points, np.zeros(3), camera, VIEWS[1])
        np.testing.assert_allclose(positive[:, 0]+negative[:, 0], WIDTH)
        np.testing.assert_allclose(positive[:, 1], negative[:, 1]); np.testing.assert_allclose(zp, -zn)
        for view in VIEWS:
            basis, _ = view_basis(camera, view); self.assertAlmostEqual(np.linalg.det(basis), 1.)

    def test_global_fit_contains_both_cases_instead_of_refitting_each_clip(self):
        joints = np.tile(reference(), (2, 1, 1)); a = joints.copy(); b = joints.copy(); b[:, :, 0] *= 2
        config = SimpleNamespace(condition2_min_visible_fingers=2, condition2_margin_frac=.1)
        camera = common_camera(reference(), [{'vertices': a, 'joints': joints}, {'vertices': b, 'joints': joints}], config)
        for points in (a, b):
            px, _ = project(points, joints[0, 0], camera, VIEWS[0])
            self.assertTrue((px[..., 0] >= 0).all() and (px[..., 0] < WIDTH).all())
            self.assertTrue((px[..., 1] >= 0).all() and (px[..., 1] < HEIGHT).all())
        pa, _ = project(a, np.zeros(3), camera, VIEWS[0]); pb, _ = project(b, np.zeros(3), camera, VIEWS[0])
        self.assertGreater(np.ptp(pb[..., 0]), np.ptp(pa[..., 0]))

    def test_only_first_wrist_translation_is_removed_later_motion_survives(self):
        camera = calibration(); points = np.tile(reference(), (2, 1, 1)); offset = np.array([8., -3., 5.])
        original, _ = project(points, points[0, 0], camera, VIEWS[0])
        translated, _ = project(points+offset, points[0, 0]+offset, camera, VIEWS[0])
        np.testing.assert_allclose(original, translated)
        points[1] += [.2, 0., 0.]
        moved, _ = project(points, points[0, 0], camera, VIEWS[0])
        self.assertGreater(moved[1, 0, 0], moved[0, 0, 0])

    def test_surface_proxy_includes_entire_incident_face_without_claiming_anatomy(self):
        p = np.zeros((21, 3))
        for finger, base in enumerate((1, 5, 9, 13, 17)):
            for j in range(4): p[base+j] = [finger*2., 0., 2.+j]
        vertices = np.array([[4., .02, 2.5], [4., -.02, 2.6], [2., .03, 2.5],
                             [2., .01, 2.2], [2., -.01, 2.3], [2., .02, 2.4]])
        proxy = surface_proxy(vertices, p, np.array([[0, 1, 2], [3, 4, 5]]))
        np.testing.assert_array_equal(proxy['protected_face_ids'], [0]); self.assertFalse(proxy['anatomical_coverage_proven'])

    def test_empty_target_frame_never_counts_as_hidden_success(self):
        points = np.zeros((2, 21, 2)); points[:, 0] = [256, 300]; points[:, 9] = [256, 200]
        masks = np.zeros((2, HEIGHT, WIDTH), bool); masks[0, 210, 256] = True
        result = surface_weight_interval({'minimum_w3': 1., 'maximum_w3': 4., 'feasible': True}, points, masks)
        self.assertFalse(result['feasible']); self.assertEqual(result['empty_proxy_frames_n'], 1)
        self.assertIsNone(result['proposed_w3'])

    def test_whole_surface_can_reject_a_feasible_landmark_interval(self):
        points = np.zeros((1, 21, 2)); points[:, 0] = [256, 300]; points[:, 9] = [256, 200]
        mask = np.zeros((1, HEIGHT, WIDTH), bool); mask[0, 0, 0] = True
        legacy = {'minimum_w3': 1., 'maximum_w3': 2., 'feasible': True}; before = copy.deepcopy(legacy)
        result = surface_weight_interval(legacy, points, mask)
        self.assertFalse(result['feasible']); self.assertGreater(result['minimum_w3'], result['maximum_w3'])
        self.assertEqual(legacy, before)

    def test_surface_radius_preserves_predeclared_two_pixel_buffer(self):
        points = np.zeros((1, 21, 2)); points[:, 0] = [256, 300]; points[:, 9] = [256, 200]
        mask = np.zeros((1, HEIGHT, WIDTH), bool); mask[0, 200, 256] = True
        result = surface_weight_interval({'minimum_w3': .5, 'maximum_w3': 2., 'feasible': True}, points, mask)
        self.assertTrue(result['feasible']); self.assertAlmostEqual(result['minimum_w3'], 1.04)
        # A feasible interval used to leak numpy.bool_ into the immutable
        # diagnostics receipt; rejection-only runs never exercised that path.
        self.assertIs(type(result['feasible']), bool)
        self.assertEqual(json.loads(json.dumps(result,allow_nan=False)), result)

    def test_malformed_reference_or_target_is_rejected(self):
        with self.assertRaises(ValueError): common_camera(np.zeros((21, 3)), [{'vertices': [], 'joints': []}], SimpleNamespace())
        with self.assertRaises(ValueError): view_basis(calibration(), 'unregistered')
        with self.assertRaises(ValueError): surface_proxy(np.zeros((3, 3)), np.zeros((21, 3)), np.array([[0, 1, 2]]))


if __name__ == '__main__': unittest.main()
