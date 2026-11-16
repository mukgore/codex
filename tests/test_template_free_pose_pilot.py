import unittest
import numpy as np
from analysis.runtime_benchmark.template_free_pose_pilot import proposal,expand,decision


class StaticPosePilotTests(unittest.TestCase):
    def test_reproducible_separate_registered_streams_without_prototype_or_path(self):
        values=[]
        for hand in ('right','left'):
            for seed in (7,19):
                for attempt in range(8):
                    a=proposal(hand,seed,attempt);self.assertEqual(a,proposal(hand,seed,attempt))
                    self.assertIsNone(a['prototype_id']);self.assertIsNone(a['trajectory'])
                    self.assertEqual(len(a['coefficients']),6);values.append(tuple(a['coefficients']))
        self.assertEqual(len(set(values)),32)
        for args in [('right',True,0),('right',7,8),('left',8,0),('x',7,0)]:
            with self.assertRaises(ValueError):proposal(*args)

    def test_pca_expansion_combines_correlated_basis_and_preserves_inputs(self):
        components=np.zeros((6,45),np.float32);components[0,:]=1;components[1,:]=2
        coefficients=np.array([.4,-.1,0,0,0,0]);before=components.copy()
        np.testing.assert_allclose(expand(coefficients,components),.2,atol=1e-7)
        np.testing.assert_array_equal(before,components)
        with self.assertRaises(ValueError):expand([0]*5,components)
        components[0,0]=np.nan
        with self.assertRaises(ValueError):expand(coefficients,components)

    def test_model_surface_or_geometry_failures_cannot_be_admitted(self):
        losses=np.zeros((1,15,3));clear={'state':'NO_TESTED_PAIR_INTERSECTION','sampled_surface_clear':True,'pair_ids':{}}
        accepted=decision(losses,losses,clear)
        self.assertTrue(accepted['model_surface_candidate']);self.assertFalse(accepted['release_allowed'])
        self.assertEqual(accepted['pending_BMC_state'],'UNRESOLVED_LIMITS')
        bad=losses.copy();bad[0,0,0]=.1
        self.assertFalse(decision(bad,bad,clear)['model_surface_candidate'])
        crossing={'state':'SURFACE_INTERSECTION_INDICATORS','sampled_surface_clear':False,'pair_ids':{'intersects':[[1,2]]}}
        self.assertFalse(decision(losses,losses,crossing)['model_surface_candidate'])
        self.assertFalse(decision(losses,losses,clear,'DEGENERATE_BONE')['model_surface_candidate'])

    def test_zero_mask_and_strict_loss_remain_distinct(self):
        strict=np.zeros((1,15,3));strict[0,0,0]=.5e-6
        r=decision(strict,np.zeros_like(strict),{'state':'NO_TESTED_PAIR_INTERSECTION','sampled_surface_clear':True,'pair_ids':{}})
        self.assertEqual(r['strict_axis_excess_n'],1);self.assertEqual(r['masked_axis_excess_n'],0)
        self.assertTrue(r['model_surface_candidate']);self.assertIn('NO_TIMESTAMPS',r['temporal_rules'])
