import copy
import json
from pathlib import Path
import unittest

from analysis.literature_constraint_comparison import compare


class LiteratureComparisonTests(unittest.TestCase):
    def setUp(self):
        p=Path(__file__).resolve().parents[1]/'references/cobos2008_constraint_extraction.json'
        self.source=json.loads(p.read_text())

    def test_preserves_both_reported_values_without_admission(self):
        result=compare(self.source)
        self.assertEqual(result['reported_cell_comparisons_n'],18)
        self.assertEqual(result['equal_reported_cells_n'],16)
        self.assertEqual([(r['finger'],r['joint'],r['reported_axis']) for r in result['different_reported_cells']],
            [('thumb','MCP','abduction_adduction'),('thumb','IP','abduction_adduction')])
        self.assertFalse(result['paper_error_proven']);self.assertFalse(result['profile_changed'])

    def test_malformed_or_applied_source_is_rejected(self):
        for change in ('applied','duplicate','reversed','wrong_units'):
            source=copy.deepcopy(self.source)
            if change=='applied':source['production_profile_applied']=True
            if change=='duplicate':source['selected_static_comparison']['rows'].append(source['selected_static_comparison']['rows'][0])
            if change=='reversed':source['selected_static_comparison']['rows'][0]['cobos']['flexion']=[90,50]
            if change=='wrong_units':source['selected_static_comparison']['units']='radian'
            with self.subTest(change=change),self.assertRaises(ValueError):compare(source)


if __name__=='__main__':unittest.main()
