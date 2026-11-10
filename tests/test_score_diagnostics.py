import copy
import json
import math
import unittest

import numpy as np

from validation_v03.compare_scores import compare
from validation_v03.standard_metrics import operating_point, roc_det_summary, threshold_table


def examples():
    rows=[]
    for split in ('development','validation','test'):
        for index,(label,score,family) in enumerate([
                ('human',.9,''),('human',.8,''),('attack',.1,'replay'),
                ('attack',.7,'stationary_hand')]):
            rows.append({'trial_id':f'{split}-trial-{index}','label':label,'split':split,
                         'source_family_ids':f'{split}-family','capture_id':f'{split}-capture-{index}',
                         'participant_id':f'{split}-person-{index}' if label=='human' else '',
                         'outcome':'scored','legacy_score':score,'candidate_score':score,
                         'attack_family':family})
    return rows


class ScoreDiagnosticsTests(unittest.TestCase):
    def test_all_threshold_points_match_direct_boolean_counts(self):
        rng=np.random.default_rng(45)
        for _ in range(30):
            labels=[1]*8+[0]*7;scores=rng.integers(-3,4,size=15).tolist()
            table=threshold_table(labels,scores)
            self.assertEqual(len(table),len(set(scores))+1)
            for point in table:self.assertEqual(point,operating_point(labels,scores,point['threshold']))

    def test_auc_matches_independent_pairwise_ranks_with_ties(self):
        rng=np.random.default_rng(90)
        for _ in range(30):
            h=rng.integers(0,5,size=9).tolist();a=rng.integers(0,5,size=7).tolist()
            expected=sum(1 if x>y else .5 if x==y else 0 for x in h for y in a)/(len(h)*len(a))
            curve=roc_det_summary([1]*len(h)+[0]*len(a),h+a)
            self.assertAlmostEqual(curve['auc'],expected,places=14)
            json.dumps(curve,allow_nan=False)
            self.assertIsNone(curve['points'][0]['threshold'])
            self.assertEqual(curve['points'][0]['accept_rule'],'reject_all')

    def test_inverted_and_all_tied_scores(self):
        self.assertEqual(roc_det_summary([1,0],[0,1])['auc'],0)
        self.assertEqual(roc_det_summary([1,0],[1,1])['auc'],.5)
        self.assertEqual(roc_det_summary([1,0],[1,0])['auc'],1)
        self.assertEqual(roc_det_summary([1,0],[1,0])['eer_diagnostic']['rate'],0)
        self.assertEqual(roc_det_summary([1,0],[0,1])['eer_diagnostic']['rate'],1)
        self.assertEqual(roc_det_summary([1,0],[1,1])['eer_diagnostic']['rate'],.5)

    def test_test_curves_do_not_change_validation_selection(self):
        rows=examples();original=copy.deepcopy(rows)
        first=compare(rows,min_human_accept=1,max_attack_accept=0,include_curves=True)
        self.assertEqual(rows,original)
        for row in rows:
            if row['split']=='test' and row['label']=='attack':row['candidate_score']=.99
        second=compare(rows,min_human_accept=1,max_attack_accept=0,include_curves=True)
        one,two=first['metrics']['candidate_score'],second['metrics']['candidate_score']
        self.assertEqual(one['threshold'],two['threshold'])
        self.assertNotEqual(one['diagnostic_curves']['test']['auc'],two['diagnostic_curves']['test']['auc'])
        self.assertEqual(two['attack_families']['test']['worst_score_accept_rate_among_scored'],1)

    def test_failure_only_family_is_not_reported_as_successful_rejection(self):
        rows=examples();failed=copy.deepcopy(rows[-1])
        failed.update(trial_id='test-failure',capture_id='test-failed-capture',
                      attack_family='partial_motion',outcome='technical_error',legacy_score='',candidate_score='')
        rows.append(failed)
        result=compare(rows,min_human_accept=1,max_attack_accept=0,include_curves=True)['metrics']['candidate_score']
        group=result['attack_families']['test']['groups']['partial_motion']
        self.assertIsNone(group['score_accept_rate_among_scored'])
        self.assertEqual(group['score_rejected_n'],0)
        self.assertEqual(group['technical_error_n'],1)
        self.assertEqual(result['diagnostic_curves']['test']['attack_scored_n'],2)
        self.assertEqual(result['diagnostic_curves']['test']['attempts']['attack']['attempted_n'],3)

    def test_missing_family_column_is_explicit_and_mixed_or_arbitrary_codes_fail(self):
        rows=examples()
        for row in rows:row.pop('attack_family')
        result=compare(rows,min_human_accept=1,max_attack_accept=0)
        self.assertEqual(result['metrics']['legacy_score']['attack_families']['test']['status'],
                         'unavailable_no_attack_family_column')
        for mutate in [lambda r:r[0].pop('attack_family'),
                       lambda r:r[2].update(attack_family='participant-123'),
                       lambda r:r[0].update(attack_family='replay')]:
            rows=examples();mutate(rows)
            with self.assertRaises(ValueError):compare(rows,min_human_accept=1,max_attack_accept=0)

    def test_infeasible_threshold_still_has_curves_but_no_fallback(self):
        rows=examples()
        for row in rows:
            if row['split']=='validation' and row['label']=='attack':row['candidate_score']=1.
        result=compare(rows,min_human_accept=1,max_attack_accept=0,include_curves=True)['metrics']['candidate_score']
        self.assertEqual(result['status'],'no_finite_feasible_threshold')
        self.assertIsNone(result['test'])
        self.assertNotIn('threshold',result)
        self.assertIn('test',result['diagnostic_curves'])


if __name__=='__main__':unittest.main()
