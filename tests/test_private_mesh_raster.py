import unittest
import numpy as np
from analysis.runtime_benchmark.private_mesh_raster import rasterize, BACKGROUND_FACE


class PrivateRasterTests(unittest.TestCase):
    def test_near_surface_wins_independent_of_triangle_order(self):
        xy = np.tile([[1., 1.], [7., 1.], [1., 7.]], (2, 1)); faces = np.arange(6).reshape(2, 3)
        z = np.array([1., 1., 1., 2., 2., 2.]); colors = np.array([[0, 0, 255], [255, 0, 0]], np.uint8)
        image, ids, depth, _ = rasterize(xy, z, faces, colors, width=8, height=8)
        reverse, _, _, _ = rasterize(xy, z, faces[::-1], colors[::-1], width=8, height=8)
        np.testing.assert_array_equal(image, reverse); np.testing.assert_array_equal(image[2, 2], [255, 0, 0])
        self.assertEqual(ids[2, 2], 1); self.assertEqual(depth[2, 2], 2.)
        self.assertEqual(ids[7, 7], BACKGROUND_FACE); self.assertTrue(np.isnan(depth[7, 7]))

    def test_pixel_center_barycentric_depth_and_winding(self):
        xy = np.array([[0., 0.], [4., 0.], [0., 4.]])
        z = np.array([0., 4., 8.]); colors = np.array([[20, 30, 40]], np.uint8)
        a, _, depth, _ = rasterize(xy, z, np.array([[0, 1, 2]]), colors, width=5, height=5)
        b, _, _, _ = rasterize(xy, z, np.array([[2, 1, 0]]), colors, width=5, height=5)
        self.assertEqual(depth[0, 0], 1.5); np.testing.assert_array_equal(a, b)

    def test_frame_clipping_and_projected_degenerate_are_explicit(self):
        xy = np.array([[-2., -2.], [4., 0.], [0., 4.], [0., 0.], [1., 1.], [2., 2.]])
        image, ids, _, report = rasterize(xy, np.ones(6), np.array([[0, 1, 2], [3, 4, 5]]),
            np.array([[20, 30, 40], [50, 60, 70]], np.uint8), width=4, height=4)
        self.assertEqual(image.shape, (4, 4, 3)); self.assertGreater(report['visible_pixels_n'], 0)
        self.assertEqual(report['projected_degenerate_faces_n'], 1); self.assertFalse((ids == 1).any())

    def test_invalid_nonfinite_and_unbounded_inputs_are_rejected(self):
        xy = np.array([[0., 0.], [4., 0.], [0., 4.]])
        faces = np.array([[0, 1, 2]]); colors = np.array([[20, 30, 40]], np.uint8)
        for depth in ([0., 0.], [0., np.nan, 0.]):
            with self.assertRaises(ValueError): rasterize(xy, depth, faces, colors)
        with self.assertRaises(ValueError): rasterize(xy, np.zeros(3), faces, colors, width=2048)
        with self.assertRaises(ValueError): rasterize(xy, np.zeros(3), faces.astype(float), colors)


if __name__ == '__main__': unittest.main()
