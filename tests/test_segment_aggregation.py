import copy
import json
from pathlib import Path
import subprocess
import unittest

from analysis.segment_aggregation import combine,evaluate


class SegmentAggregationTests(unittest.TestCase):
    def test_short_low_segment_is_visible_without_relabeling_the_motion(self):
        result=combine({'captcha':.8,'tF':101},[{'captcha':1,'tF':100},{'captcha':0,'tF':1}],[100,1])
        self.assertEqual(result['segment_equal_mean'],.5)
        self.assertAlmostEqual(result['segment_frame_weighted_mean'],100/101)
        self.assertEqual(result['segment_minimum'],0)
        self.assertTrue(result['concat_at_or_above_with_low_segment'])
        self.assertEqual(result['segments_n'],2)
        self.assertNotIn('human_error',result)

    def test_zero_length_segment_is_retained_in_unweighted_and_minimum_views(self):
        result=combine({'captcha':1,'tF':10},[{'captcha':1,'tF':10},{'captcha':0,'tF':0}],[10,0])
        self.assertEqual(result['segment_equal_mean'],.5)
        self.assertEqual(result['segment_frame_weighted_mean'],1)
        self.assertEqual(result['zero_frame_segments_n'],1)
        self.assertFalse(result['all_segments_at_or_above'])

    def test_bad_denominators_scores_and_thresholds_rejected(self):
        for concat,parts,counts,threshold in (
            ({'captcha':1,'tF':2},[{'captcha':1,'tF':1}],[1],.25),
            ({'captcha':1,'tF':1},[{'captcha':1,'tF':2}],[1],.25),
            ({'captcha':1,'tF':1},[{'captcha':float('nan'),'tF':1}],[1],.25),
            ({'captcha':True,'tF':1},[{'captcha':1,'tF':1}],[1],.25),
            ({'captcha':1,'tF':1},[{'captcha':1,'tF':1}],[True],.25),
            ({'captcha':1,'tF':1},[{'captcha':1,'tF':1}],[1],0)):
            with self.subTest(counts=counts,threshold=threshold),self.assertRaises(ValueError):
                combine(concat,parts,counts,threshold=threshold)

    def fixture(self):
        points=[[j*.02,.1+(j%4)*.05] for j in range(21)]
        base=[copy.deepcopy(points) for _ in range(11)]
        keyframes=[{'clip':{'clip_id':'synthetic'},'frameIdx':i,'allBaseLm':base} for i in (0,9,10)]
        segments=[{'fromKf':0,'toKf':1,'frames':[{'t':i*40,'lm':frame} for i,frame in enumerate(base[:10])]},
                  {'fromKf':1,'toKf':2,'frames':[{'t':0,'lm':None},{'t':40,'lm':None}]}]
        return keyframes,segments

    def score(self,segments,keyframes):
        root=Path(__file__).resolve().parents[1]
        source=root.parent/'handcaptcha'/'hand_captcha_prod.html'
        if not source.exists():self.skipTest('Owned production source is not available')
        run=subprocess.run(['node',str(root/'g4_lab/js_bridge.cjs'),str(source)],
            input=json.dumps({'op':'score_saved','segments':segments,'keyframes':keyframes})+'\n',
            capture_output=True,text=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr)
        reply=json.loads(run.stdout);self.assertTrue(reply['ok'])
        return reply['result']

    def test_actual_html_retains_two_missing_frames_and_does_not_mutate_inputs(self):
        keyframes,segments=self.fixture();before=copy.deepcopy((keyframes,segments))
        baseline=self.score(segments,keyframes)
        self.assertAlmostEqual(baseline['captcha'],10/12,places=6)
        self.assertEqual((baseline['tF'],baseline['dC']),(12,10))
        data={'segments':segments,'scores':{'captcha':baseline['captcha']}}
        result=evaluate(data,keyframes,self.score)
        self.assertEqual(result['aggregations']['segment_minimum'],0)
        self.assertEqual(result['aggregations']['segments_with_fewer_than_three_detected_frames'],1)
        self.assertTrue(result['aggregations']['concat_at_or_above_with_low_segment'])
        self.assertEqual((keyframes,segments),before)

    def test_incomplete_or_out_of_range_transitions_rejected_without_scoring(self):
        keyframes,segments=self.fixture()
        def forbidden(*_):self.fail('Incomplete source must not be scored')
        with self.assertRaises(ValueError):evaluate({'segments':segments[:1]},keyframes,forbidden)
        keyframes[0]['frameIdx']=100
        with self.assertRaises(ValueError):evaluate({'segments':segments},keyframes,forbidden)

    def test_perfect_two_frame_reference_is_zero_because_all_metrics_are_unavailable(self):
        keyframes,_=self.fixture();base=keyframes[0]['allBaseLm'][:2]
        kfs=[{'clip':{'clip_id':'two-frame-fixture'},'frameIdx':i,'allBaseLm':base} for i in (0,1)]
        segment={'fromKf':0,'toKf':1,'frames':[{'t':i*40,'lm':base[0]} for i in range(4)]}
        result=self.score([segment],kfs)
        self.assertIsNone(result['rA']);self.assertIsNone(result['rDA']);self.assertIsNone(result['rAc'])
        self.assertEqual(result['captcha'],0)
        segment['frames'].append({'t':160,'lm':None})
        missing=self.score([segment],kfs)
        self.assertEqual(missing['captcha'],0)

    def test_candidate_aggregation_refused_if_stored_replay_does_not_match(self):
        keyframes,segments=self.fixture();calls=[]
        def score(*_):calls.append(1);return {'captcha':.5,'tF':12}
        with self.assertRaisesRegex(ValueError,'replay not established'):
            evaluate({'segments':segments,'scores':{'captcha':.9}},keyframes,score)
        self.assertEqual(len(calls),1)


if __name__=='__main__':unittest.main()
