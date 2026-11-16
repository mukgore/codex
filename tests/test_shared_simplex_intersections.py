import itertools
import unittest

import numpy as np

from analysis.shared_simplex_intersections import (
    DEGENERATE, EXPECTED, OVERLAP, UNRESOLVED, frame, pair, topology,
)


class SharedSimplexTests(unittest.TestCase):
    def setUp(self):
        self.a = np.array([[0., 0., 0.], [2., 0., 0.], [0., 2., 0.]])

    def test_coplanar_shared_edge_normal_contact_and_fold_overlap(self):
        clear = np.array([[0., 0., 0.], [2., 0., 0.], [0., -2., 0.]])
        overlap = np.array([[0., 0., 0.], [2., 0., 0.], [1., 1., 0.]])
        shared = self.a[:2]
        self.assertEqual(pair(self.a, clear, shared), EXPECTED)
        self.assertEqual(pair(self.a, overlap, shared), OVERLAP)

    def test_noncoplanar_shared_edge_is_only_common_segment(self):
        b = np.array([[0., 0., 0.], [2., 0., 0.], [.5, .5, 1.]])
        self.assertEqual(pair(self.a, b, self.a[:2]), EXPECTED)

    def test_coplanar_shared_vertex_containment_and_opposite_quadrant(self):
        b = np.array([[0., 0., 0.], [.5, .1, 0.], [.1, .5, 0.]])
        self.assertEqual(pair(self.a, b, self.a[:1]), OVERLAP)
        self.assertEqual(pair(self.a, -b, self.a[:1]), EXPECTED)

    def test_noncoplanar_shared_vertex_overlapping_and_opposite_sections(self):
        b = np.array([[0., 0., 0.], [1., 1., -1.], [1., 1., 1.]])
        self.assertEqual(pair(self.a, b, self.a[:1]), OVERLAP)
        self.assertEqual(pair(self.a, -b, self.a[:1]), EXPECTED)

    def test_strict_one_sided_triangles_have_only_shared_vertex(self):
        b = np.array([[0., 0., 0.], [1., 1., 1.], [1., 0., 2.]])
        self.assertEqual(pair(self.a, b, self.a[:1]), EXPECTED)

    def test_coplanar_nonlocal_edge_contact_is_an_indicator(self):
        b = np.array([[0., 0., 0.], [1., 0., 0.], [0., -1., 0.]])
        self.assertEqual(pair(self.a, b, self.a[:1]), OVERLAP)

    def test_pair_symmetry_all_vertex_orders_and_shared_edge_order(self):
        variants = [
            (np.array([[0., 0., 0.], [1., 1., -1.], [1., 1., 1.]]), self.a[:1], OVERLAP),
            (np.array([[0., 0., 0.], [2., 0., 0.], [0., -2., 0.]]), self.a[:2], EXPECTED),
            (np.array([[0., 0., 0.], [.5, .1, 0.], [.1, .5, 0.]]), self.a[:1], OVERLAP),
        ]
        for b, common, expected in variants:
            for ia in itertools.permutations(range(3)):
                for ib in itertools.permutations(range(3)):
                    for shared in (common, common[::-1]):
                        a_ordered, b_ordered = self.a[list(ia)], b[list(ib)]
                        self.assertEqual(pair(a_ordered, b_ordered, shared), expected)
                        self.assertEqual(pair(b_ordered, a_ordered, shared), expected)

    def test_frame_translation_scale_rotation_and_left_reflection(self):
        b = np.array([[1., 1., -1.], [1., 1., 1.]])
        v = np.concatenate((self.a, b)); mesh = topology([[0, 1, 2], [0, 3, 4]], 5)
        original = frame(v, mesh)
        q, _ = np.linalg.qr(np.array([[1., 2., 3.], [-2., 1., 1.], [1., 0., -3.]]))
        for variant in (v+100., v*1000., v@q, v*np.array([-1, 1, 1])):
            result = frame(variant, mesh)
            self.assertEqual(result['counts'], original['counts'])
            self.assertEqual(result['indicator_pair_ids'], [[0, 1]])
            self.assertFalse(result['volume_penetration_free_proven'])
            self.assertFalse(result['release_allowed'])

    def test_near_parallel_ill_conditioning_is_unresolved_not_clear(self):
        b = np.array([[0., 0., 0.], [2., 0., 0.], [0., 2., 1e-8]])
        self.assertEqual(pair(self.a, b, self.a[:2]), UNRESOLVED)

    def test_degenerate_faces_are_unmeasurable(self):
        b = np.array([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]])
        self.assertEqual(pair(self.a, b, self.a[:1]), DEGENERATE)
        v = np.concatenate((self.a, b[1:]))
        result = frame(v, topology([[0, 1, 2], [0, 3, 4]], 5))
        self.assertFalse(result['supplement_clear'])
        self.assertEqual(result['counts'][DEGENERATE], 1)

    def test_topology_partitions_shared_vertex_edge_and_unshared_pairs(self):
        mesh = topology([[0, 1, 2], [0, 3, 4], [0, 1, 5], [6, 7, 8]], 9)
        self.assertEqual(mesh['shared_pairs_n'], 3)
        self.assertEqual(sorted(mesh['shared_n']), [1, 1, 2])
        self.assertEqual(mesh['all_face_pairs_n'], 6)

    def test_invalid_topology_geometry_and_false_shared_simplex_rejected(self):
        for faces in ([[0, 0, 1]], [[0, 1, 2], [2, 0, 1]], [[0, 1, 3]]):
            with self.assertRaises(ValueError): topology(faces, 3)
        with self.assertRaises(ValueError): pair(self.a, self.a, [[.1, .1, 0]])
        with self.assertRaises(ValueError): pair(self.a, self.a, [[0, 0, 0], [0, 0, 0]])
        with self.assertRaises(ValueError): frame(np.full((3, 3), np.nan), topology([[0, 1, 2]], 3))
        with self.assertRaises(ValueError): pair(self.a, self.a, self.a[:1], epsilon=True)


if __name__ == '__main__':
    unittest.main()
