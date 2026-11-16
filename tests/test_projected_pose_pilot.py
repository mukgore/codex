import copy
import unittest
import numpy as np
from analysis.runtime_benchmark.projected_pose_pilot import project
from analysis.audit_projected_pose_outputs import summary_from_cases


class ProjectedPoseTests(unittest.TestCase):
    def profile(self):
        return {'native_joint_groups':{'hinge':list(range(1,16))},
          'intervals_degrees':{'hinge':[[0,0],[-5,5],[0,90]]}}

    def test_projection_preserves_interior_and_reports_every_changed_axis(self):
        angles=np.zeros((1,15,3));angles[:,:,2]=.2
        angles[0,0]=np.deg2rad([10,-7,100]);before=angles.copy();p=self.profile();pb=copy.deepcopy(p)
        result,change=project(angles,p)
        np.testing.assert_allclose(np.rad2deg(result[0,0]),[0,-5,90])
        np.testing.assert_array_equal(result[0,1:],angles[0,1:])
        np.testing.assert_array_equal(angles,before);self.assertEqual(p,pb)
        self.assertEqual(change['changed_axis_components_n'],3)
        self.assertAlmostEqual(change['max_absolute_correction_degrees'],10)

    def test_projection_is_idempotent_and_does_not_expand_fixed_bounds(self):
        rng=np.random.default_rng(7);first,_=project(rng.normal(size=(1,15,3)),self.profile())
        second,change=project(first,self.profile());np.testing.assert_array_equal(first,second)
        self.assertEqual(change['changed_axis_components_n'],0)
        self.assertTrue(np.all(first[:,:,0]==0))

    def test_missing_duplicate_nonfinite_and_unordered_profiles_rejected(self):
        for ids in ([1],list(range(1,16))+[1]):
            p=self.profile();p['native_joint_groups']['hinge']=ids
            with self.assertRaises(ValueError):project(np.zeros((1,15,3)),p)
        p=self.profile();p['intervals_degrees']['hinge'][1]=[5,-5]
        with self.assertRaises(ValueError):project(np.zeros((1,15,3)),p)
        with self.assertRaises(ValueError):project(np.full((1,15,3),np.nan),self.profile())

    def test_summary_requires_all_measured_surface_states_and_exact_denominator(self):
        case={'masked_excess_components_n':0,'surface_state':'NO_TESTED_PAIR_INTERSECTION',
          'model_surface_eligible':True,'bmc_geometry_error':None,'changed_axis_components_n':2,
          'max_absolute_correction_degrees':10.,'l2_correction_degrees':12.,'exact_neutral_geometry':False,
          'rejection_reasons':[]}
        rows=[{'case_id':str(i),**case} for i in range(32)]
        s=summary_from_cases(rows,32);self.assertEqual(s['model_surface_eligible_n'],32)
        self.assertEqual(s['changed_axis_components_n'],64)
        with self.assertRaises(ValueError):summary_from_cases(rows[:-1],31)
        del rows[0]['surface_state']
        with self.assertRaises(KeyError):summary_from_cases(rows,32)
