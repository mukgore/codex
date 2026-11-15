import unittest
import numpy as np
from analysis.runtime_benchmark.hidden_motion_counterfactual import perturb,frame_difference,aggregate_differences


class HiddenMotionCounterfactualTests(unittest.TestCase):
    def test_two_second_parent_preserves_initial_source_motion_interval(self):
        parent=np.zeros((25,15,3));times=np.linspace(0,2,25)
        result,pulse=perturb(parent,times,10.)
        np.testing.assert_array_equal(result[times<=1.],parent[times<=1.])
        self.assertGreater(pulse[14],.999999)
        self.assertTrue(np.any(result[times>1.]!=0))

    def test_only_middle_bend_changes_and_entry_exit_and_pulse_support_remain_fixed(self):
        parent=np.arange(25*15*3,dtype=float).reshape(25,15,3)/1000
        original=parent.copy();times=np.linspace(0,3,25)
        result,pulse=perturb(parent,times,10.)
        np.testing.assert_array_equal(parent,original)
        unchanged=np.ones((15,3),bool);unchanged[[3,4,5],2]=False
        np.testing.assert_array_equal(result[:,unchanged],parent[:,unchanged])
        np.testing.assert_array_equal(result[:9],parent[:9]);np.testing.assert_allclose(result[16:],parent[16:],atol=1e-14)
        np.testing.assert_allclose(np.rad2deg(result[12,[3,4,5],2]-parent[12,[3,4,5],2]),[10,8.5,5.5])
        self.assertAlmostEqual(pulse[12],1.)

    def test_exact_zero_control_and_rejected_unregistered_perturbations(self):
        parent=np.zeros((25,15,3));times=np.linspace(0,2,25)
        result,_=perturb(parent,times,0.);np.testing.assert_array_equal(result,parent)
        for delta in (True,20.,float('nan')):
            with self.assertRaises(ValueError):perturb(parent,times,delta)

    def test_pixel_metrics_count_pixels_not_channels_and_keep_outside_changes(self):
        a=np.zeros((2,3,3),np.uint8);b=a.copy();b[0,0]=[1,2,3];b[1,2]=[0,0,5]
        mask=np.zeros((2,3),bool);mask[0,0]=True
        row=frame_difference(a,b,mask)
        self.assertEqual(row['all_changed_pixels_n'],2);self.assertEqual(row['inside_mask_changed_pixels_n'],1)
        self.assertEqual(row['outside_mask_changed_pixels_n'],1);self.assertEqual(row['absolute_channel_difference_sum'],11)
        summary=aggregate_differences([row,frame_difference(a,a,mask)])
        self.assertFalse(summary['exact_decoded_pixels_equal']);self.assertEqual(summary['changed_frames_n'],1)
        self.assertEqual(summary['frames_n'],2)

    def test_missing_frames_or_invalid_pixel_denominators_are_not_equal_success(self):
        with self.assertRaises(ValueError):aggregate_differences([])
        a=np.zeros((2,3,3),np.uint8)
        with self.assertRaises(ValueError):frame_difference(a,a,np.zeros((2,3),np.uint8))


if __name__=='__main__':unittest.main()
