import math
import unittest

from analysis.runtime_benchmark.bounded_interval_refinement import refine


class Unresolved(Exception):
    pass


class BoundedIntervalRefinementTests(unittest.TestCase):
    def run_refinement(self, evaluate, **kwargs):
        return refine(evaluate, 0., 1., max_depth=kwargs.get('depth', 3),
                      unresolved_type=Unresolved, retry_reason='ZERO')

    def test_finite_parent_is_not_recomputed_or_split(self):
        calls=[]
        result=self.run_refinement(lambda a,b: calls.append((a,b)) or (a,b))
        self.assertEqual(calls,[(0.,1.)]);self.assertTrue(result['complete'])
        self.assertEqual(result['values'],{'r':(0.,1.)})
        self.assertFalse(result['backend_error_bounds_validated']);self.assertFalse(result['CCD_clearance'])

    def test_interval_children_cover_parent_without_sampling(self):
        def evaluate(a,b):
            if b-a>.25:raise Unresolved('ZERO')
            return (a,b)
        result=self.run_refinement(evaluate)
        self.assertTrue(result['complete']);self.assertEqual(len(result['attempts']),7)
        self.assertEqual([(r['start'],r['end']) for r in result['terminals']],
                         [(0,.25),(.25,.5),(.5,.75),(.75,1)])

    def test_depth_budget_preserves_all_unresolved_children(self):
        def evaluate(a,b):raise Unresolved('ZERO')
        result=self.run_refinement(evaluate,depth=3)
        self.assertFalse(result['complete']);self.assertEqual(len(result['attempts']),15)
        self.assertEqual(len(result['terminals']),8);self.assertEqual(result['values'],{})
        self.assertTrue(all(r['stop_reason']=='DEPTH_LIMIT' for r in result['terminals']))

    def test_other_unresolved_reason_is_preserved_without_retry(self):
        def evaluate(a,b):raise Unresolved('DIFFERENT')
        result=self.run_refinement(evaluate)
        self.assertEqual(len(result['attempts']),1)
        self.assertEqual(result['terminals'][0]['stop_reason'],'NON_RETRYABLE_REASON')

    def test_unexpected_errors_are_not_converted_into_candidates(self):
        def evaluate(a,b):raise RuntimeError('failure')
        with self.assertRaises(RuntimeError):self.run_refinement(evaluate)

    def test_adjacent_floats_cannot_create_an_interior_split(self):
        def evaluate(a,b):raise Unresolved('ZERO')
        result=refine(evaluate,1.,math.nextafter(1.,math.inf),max_depth=8,
                      unresolved_type=Unresolved,retry_reason='ZERO')
        self.assertEqual(result['terminals'][0]['stop_reason'],'NO_INTERIOR_FLOAT')

    def test_invalid_interval_and_budget_are_rejected(self):
        for a,b,depth in [(0.,1.,True),(0.,1.,9),(0.,1.,-1),(1.,0.,3),(0.,math.inf,3)]:
            with self.assertRaises(ValueError):
                refine(lambda a,b:None,a,b,max_depth=depth,unresolved_type=Unresolved,retry_reason='ZERO')


if __name__=='__main__':unittest.main()
