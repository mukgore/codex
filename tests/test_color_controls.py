import unittest

from analysis.color_controls import disagreements


class ColorDenominatorTests(unittest.TestCase):
    def test_missing_detection_keeps_reference_points_without_zero_error(self):
        result=disagreements([{'lm':None}], [{'lm':[[0,0]]*21}],
                             [{'occlusion_levels':{'level3_DIP':{
                                 'mask_center':{'x':0,'y':0},'mask_radius':5}}}],100,100)
        self.assertEqual(result['hidden']['reference_points'],21)
        self.assertEqual(result['hidden']['compared_points'],0)
        self.assertIsNone(result['hidden']['mean_distance_pixels_on_compared_points'])

    def test_visible_hidden_grouping_uses_common_reference_positions(self):
        points=[[0,0]]+[[1,1]]*20
        result=disagreements([{'lm':points}], [{'lm':points}],
                             [{'occlusion_levels':{'level3_DIP':{
                                 'mask_center':{'x':0,'y':0},'mask_radius':5}}}],100,100)
        self.assertEqual(result['hidden']['compared_points'],1)
        self.assertEqual(result['visible']['compared_points'],20)
        self.assertEqual(result['visible']['mean_distance_pixels_on_compared_points'],0)
