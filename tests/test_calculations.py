"""Small analytical cases for high-risk interpretation errors; no participant data."""
import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from audit import boolean, sus_transform, score, longest_missing
class Calculations(unittest.TestCase):
    def test_sus_polarity_extremes(self):
        good=np.array([[5,1]*5]); bad=np.array([[1,5]*5])
        self.assertEqual(float(sus_transform(good).sum()*2.5),100)
        self.assertEqual(float(sus_transform(bad).sum()*2.5),0)
        with self.assertRaises(ValueError): sus_transform([[None]*10])
    def test_false_string(self):
        self.assertFalse(boolean('False')); self.assertTrue(boolean('True'))
        with self.assertRaises(ValueError): boolean('unknown')
    def test_detection_penalty_and_weighting(self):
        self.assertAlmostEqual(score(dict(angle=0,dtw_angle=0,accel=0),.5)[0],.5)
        self.assertAlmostEqual(.747*.44+.464*.31+.337*.25,.55677)
        self.assertEqual(longest_missing([{'lm':None},{'lm':None},{'lm':[[1,2]]},{'lm':None}]),2)
    def test_sus_range(self):
        with self.assertRaises(ValueError): sus_transform([[6]*10])
if __name__=='__main__': unittest.main()
