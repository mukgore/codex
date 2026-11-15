import unittest

import numpy as np

from analysis.runtime_benchmark.mano_bmc_direction_probe import geometric_axes,native_axial_axes,build_design


class BMCDirectionProbeTests(unittest.TestCase):
    def test_axes_include_nonzero_neutral_flexion_and_actual_outgoing_twist(self):
        frames=np.tile(np.eye(3),(15,1,1));angles=np.tile([.4,.2],(15,1))
        axes=geometric_axes(frames,angles)
        np.testing.assert_allclose(axes[0,0],[0,1,0])
        np.testing.assert_allclose(axes[0,1],[-np.cos(.4),0,np.sin(.4)])
        np.testing.assert_allclose(axes[0,2],[np.sin(.4)*np.cos(.2),np.sin(.2),np.cos(.4)*np.cos(.2)])

    def test_reflected_rotation_axes_are_axial_not_polar_vectors(self):
        axes=geometric_axes(np.tile(np.eye(3),(15,1,1)),np.zeros((15,2)))
        native=native_axial_axes(axes,'left');wrong=native_axial_axes(axes,'left',incorrect_polar_control=True)
        np.testing.assert_array_equal(native,-wrong)
        s=np.diag([-1.,1.,1.]);a=np.array([1.,2.,3.]);b=np.array([3.,1.,2.])
        np.testing.assert_allclose(np.cross(s@a,s@b),-s@np.cross(a,b))

    def test_design_counts_and_two_step_sizes_are_explicit(self):
        axes=geometric_axes(np.tile(np.eye(3),(15,1,1)),np.zeros((15,2)))
        right,rows=build_design(axes,list(range(1,16)),'right');left,control=build_design(axes,list(range(1,16)),'left')
        self.assertEqual(right.shape,(181,45));self.assertEqual(left.shape,(226,45))
        self.assertEqual(sum(r['kind']=='incorrect_polar_sign_control' for r in control),45)
        self.assertEqual({r['step_radians'] for r in rows[1:]},{.01,.03})

    def test_invalid_frame_and_control_hand_rejected(self):
        frames=np.tile(np.eye(3),(15,1,1));frames[0,0,0]=2.
        with self.assertRaises(ValueError):geometric_axes(frames,np.zeros((15,2)))
        axes=geometric_axes(np.tile(np.eye(3),(15,1,1)),np.zeros((15,2)))
        with self.assertRaises(ValueError):native_axial_axes(axes,'right',incorrect_polar_control=True)


if __name__=='__main__':unittest.main()
