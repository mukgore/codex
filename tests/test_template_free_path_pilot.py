import unittest
import numpy as np
from analysis.runtime_benchmark.template_free_path_pilot import path,derivatives


class TemplateFreePathTests(unittest.TestCase):
    def test_actual_distinct_waypoints_are_exact_and_segments_stay_in_convex_ranges(self):
        rng=np.random.default_rng(19);states=rng.normal(size=(3,15,3));before=states.copy()
        times,angles=path(states)
        np.testing.assert_array_equal(angles[[0,12,24]],states);np.testing.assert_array_equal(states,before)
        self.assertEqual(len(times),25);self.assertEqual(times[-1],3.)
        for index in (0,1):
            selected=angles[index*12:index*12+13]
            self.assertTrue(np.all(selected>=np.minimum(states[index],states[index+1])-1e-14))
            self.assertTrue(np.all(selected<=np.maximum(states[index],states[index+1])+1e-14))

    def test_derivatives_use_actual_seconds_and_midpoint_spacings(self):
        t=np.array([0.,.1,.4,.9]);angles=np.broadcast_to(t[:,None,None]**2,(4,15,3)).copy()
        v,a=derivatives(angles,t)
        np.testing.assert_allclose(v[:,0,0],[.1,.5,1.3]);np.testing.assert_allclose(a,2.)
        with self.assertRaises(ValueError):derivatives(angles,[0,0,.4,.9])

    def test_missing_or_nonfinite_waypoints_cannot_create_motion(self):
        for x in (np.zeros((2,15,3)),np.full((3,15,3),np.nan)):
            with self.assertRaises(ValueError):path(x)
