import unittest
import numpy as np

from analysis.derivative_sensitivity import kinematics, vector_rms


class DerivativeSensitivityTests(unittest.TestCase):
    def test_sg_preserves_quadratic_and_time_scaling(self):
        t=np.arange(25)/24
        points=np.zeros((len(t),21,2));points[:,:,0]=t[:,None]**2
        _,v,a=kinematics(points,t,window=5,max_gap=.1)
        np.testing.assert_allclose(v[:,:,0],np.repeat((2*t)[:,None],21,axis=1),atol=1e-12)
        np.testing.assert_allclose(a[:,:,0],2,atol=2e-11)
        _,slow_v,slow_a=kinematics(points,t*2,window=5,max_gap=.2)
        np.testing.assert_allclose(slow_v,v/2,atol=1e-12)
        np.testing.assert_allclose(slow_a,a/4,atol=1e-12)

    def test_alternating_noise_creates_derivatives_and_filter_changes_them(self):
        t=np.arange(25)/24
        points=np.zeros((len(t),21,2));points[:,:,0]=np.where(np.arange(25)%2, .01,-.01)[:,None]
        _,_,raw=kinematics(points,t,window=0,max_gap=.1)
        _,_,filtered=kinematics(points,t,window=5,max_gap=.1)
        self.assertGreater(vector_rms(raw),0)
        self.assertLess(vector_rms(filtered),vector_rms(raw))

    def test_filter_rejects_nonuniform_time_and_unapproved_window(self):
        points=np.zeros((5,21,2))
        with self.assertRaises(ValueError):kinematics(points,[0,.1,.2,.3,.5],window=5,max_gap=1)
        with self.assertRaises(ValueError):kinematics(points,np.arange(5)/24,window=3,max_gap=.1)


if __name__=='__main__':unittest.main()
