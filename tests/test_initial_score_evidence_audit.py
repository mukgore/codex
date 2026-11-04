import unittest
from analysis.reproducibility.audit_score_numeric_formats import candidates


class SavedNumericFormatsTests(unittest.TestCase):
    def test_numeric_equivalence(self):
        values=[r['value'] for r in candidates('4.93e-1; 0,493; 49.3%; .493e0')]
        self.assertEqual(values,[.493,.493,.493,.493])

    def test_rounding_interval_boundaries(self):
        self.assertEqual([r['value'] for r in candidates('4.925e-1 4.93499e-1 4.935e-1')],
                         [.4925,.493499])

    def test_other_units_and_integer_not_promoted(self):
        self.assertEqual(list(candidates('493 4.93e1 0.493e2 49.35%')),[])


if __name__=='__main__':unittest.main()
