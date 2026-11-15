import json
import math
from pathlib import Path
import unittest

from analysis.literature_velocity_consistency import audit,predicted_peak


class LiteratureVelocityTests(unittest.TestCase):
    def test_units_and_half_cycle_are_explicit(self):
        self.assertAlmostEqual(predicted_peak(180,1,t1_fraction_of_cycle=1),math.pi**2/2)
        self.assertAlmostEqual(predicted_peak(180,1,t1_fraction_of_cycle=.5),math.pi**2)
        with self.assertRaises(ValueError):predicted_peak(90,0,t1_fraction_of_cycle=.5)

    def test_published_rounding_does_not_resolve_author_intent_or_admit_motion(self):
        path=Path(__file__).resolve().parents[1]/'references/chen2013_constraint_extraction.json'
        source=json.loads(path.read_text());result=audit(source)
        self.assertEqual(result['rows_n'],6)
        self.assertLess(result['max_half_cycle_residual_rad_s'],.001)
        for row in result['rows']:self.assertAlmostEqual(row['reported_to_literal_ratio'],2.,places=3)
        for key in ('phase_intent_resolved','paper_error_proven','human_speed_limit_established','biomechanical_profile_changed'):
            self.assertFalse(result[key])
        source['production_profile_applied']=True
        with self.assertRaises(ValueError):audit(source)


if __name__=='__main__':unittest.main()
