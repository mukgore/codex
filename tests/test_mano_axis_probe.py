import math
import unittest

import numpy as np

from analysis.runtime_benchmark.mano_axis_probe import design,descendants,expected_native_rotation,pair_delta


class NativeAxisProbeTests(unittest.TestCase):
    def test_design_has_one_neutral_and_all_native_signed_axis_probes(self):
        poses,rows=design();self.assertEqual(poses.shape,(91,45));np.testing.assert_array_equal(poses[0],0)
        keys=set()
        for row in rows[1:]:
            keys.add((row['native_joint_index'],row['native_axis_index'],row['sign']))
            nonzero=np.flatnonzero(poses[row['frame_idx']]);self.assertEqual(nonzero.tolist(),[(row['native_joint_index']-1)*3+row['native_axis_index']])
        self.assertEqual(len(keys),90)
        with self.assertRaises(ValueError):design(.2)

    def test_known_rotation_changes_only_descendant_positions(self):
        neutral=np.zeros((16,3));neutral[1]=[1,0,0];neutral[2]=[2,0,0];neutral[3]=[3,0,0];neutral[4]=[0,1,0]
        result=expected_native_rotation(neutral,1,2,math.pi/2)
        np.testing.assert_allclose(result[1:4],[[1,0,0],[1,1,0],[1,2,0]],atol=1e-12)
        np.testing.assert_array_equal(result[4],neutral[4]);self.assertEqual(descendants(1),[1,2,3])

    def test_thumb_chain_indices_are_not_assumed_to_be_first(self):
        self.assertEqual(descendants(13),[13,14,15]);self.assertEqual(descendants(15),[15])
        with self.assertRaises(ValueError):descendants(0)

    def test_flexion_difference_wraps_but_abduction_remains_linear(self):
        a=np.zeros((15,2));b=a.copy();a[0]=[-math.pi+.01,.03];b[0]=[math.pi-.01,-.02]
        result=pair_delta(a,b);self.assertAlmostEqual(result[0,0],.02);self.assertAlmostEqual(result[0,1],.05)
        with self.assertRaises(ValueError):pair_delta(np.zeros((14,2)),b)


if __name__=='__main__':unittest.main()
