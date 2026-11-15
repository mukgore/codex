import copy
import unittest

import numpy as np

from analysis.runtime_benchmark.mano_random_diagnostic import (
    FRAMES,envelope,proposal,rejection_reasons,stream_seed,trajectory,
)


class RandomDiagnosticTests(unittest.TestCase):
    def test_keyed_streams_reproduce_independently_of_order(self):
        a=proposal(7,0,'right');proposal(19,1,'left')
        self.assertEqual(a,proposal(7,0,'right'))
        self.assertEqual(len(set(a['child_seeds'].values())),3)
        self.assertNotEqual(a,proposal(7,1,'right'))
        self.assertNotEqual(a['child_seeds'],proposal(7,0,'left')['child_seeds'])

    def test_bounded_coupled_trajectory_and_real_seconds(self):
        for seed in (7,19,42):
            for hand in ('right','left'):
                spec=proposal(seed,0,hand);times,pose=trajectory(spec)
                self.assertEqual(pose.shape,(FRAMES,6));self.assertEqual(pose.dtype,np.float32)
                self.assertTrue((np.diff(times)>0).all());self.assertEqual(times[-1],spec['duration_seconds'])
                np.testing.assert_array_equal(pose[[0,-1]],0)
                np.testing.assert_array_equal(pose[:,[0,3,4,5]],0)
                self.assertLessEqual(float(pose[:,1].max()),.8)
                np.testing.assert_allclose(pose[:,2],pose[:,1]*spec['secondary_pc2_amplitude']/spec['primary_pc1_amplitude'],atol=1e-8)
                np.testing.assert_array_equal(trajectory(proposal(seed,0,hand))[1],pose)
                self.assertFalse(spec['release_allowed'])

    def test_piecewise_quintic_endpoints_and_plateau(self):
        values=envelope([0.,.175,.35,.45,.55,1.],.35,.2)
        np.testing.assert_allclose(values,[0.,.5,1.,1.,1.,0.],atol=1e-12)
        w=envelope(np.linspace(0,1,1001),.35,.2)
        self.assertTrue(((w>=0)&(w<=1)).all())

    def test_tampered_recipe_and_invalid_keys_rejected(self):
        spec=copy.deepcopy(proposal(7,0,'right'));spec['primary_pc1_amplitude']=2.
        with self.assertRaises(ValueError):trajectory(spec)
        for args in ((True,0,'right','trajectory'),(7,16,'right','trajectory'),(7,0,'other','trajectory'),(7,0,'right','other')):
            with self.assertRaises(ValueError):stream_seed(*args)
        for phases in ([np.nan],[1.1],[-.1]):
            with self.assertRaises(ValueError):envelope(phases,.35,.2)

    def test_no_implicit_admission_even_with_rule_pass(self):
        result={'unresolved_rules':[],'geometry_errors':[],'violations':[],'evidence_backed_rule_checks_pass':True}
        self.assertIn('ENGINEERING_DIAGNOSTIC_NOT_ELIGIBLE_FOR_POOL',rejection_reasons(result))
        result['unresolved_rules']=['bone_lengths']
        self.assertIn('UNRESOLVED_BONE_LENGTHS',rejection_reasons(result))


if __name__=='__main__':unittest.main()
