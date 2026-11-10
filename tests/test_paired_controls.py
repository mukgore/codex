import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from validation_v03.paired_controls import summarize


def trial(condition, participant='private-person-101', repeat=1, score=.8,
          origin='offline_fixed_duration', camera='private-camera-a', outcome='recorded'):
    return {'trial_id':f'private-trial-{participant}-{condition}-{repeat}',
            'capture_id':f'private-capture-{participant}-{condition}-{repeat}',
            'protocol_id':'private-protocol','participant_id':participant,
            'target_id':'private-target-a','source_family_id':'private-family-a',
            'camera_id':camera,'recording_seconds':8.,'repeat':repeat,'score_origin':origin,
            'condition':condition,'outcome':outcome,'legacy_score':score,
            'gate_pass':None,'motion_completed':None}


class PairedControlTests(unittest.TestCase):
    def run_report(self,rows):return summarize(rows,data_scope='synthetic')

    def test_pair_gaps_reversals_and_independent_judgments(self):
        rows=[trial('normal_imitation',score=.8),trial('hold_first',score=.6),
              trial('normal_imitation',participant='private-person-202',score=.4),
              trial('hold_first',participant='private-person-202',score=.5)]
        rows[1]['gate_pass']=False;rows[1]['motion_completed']=False
        result=self.run_report(rows)['score_origins']['offline_fixed_duration']['conditions']['hold_first']
        self.assertEqual(result['score_accepted_n'],2)
        self.assertEqual(result['score_and_gate_passed_n'],0)
        self.assertEqual(result['motion_incomplete_n'],1)
        self.assertEqual(result['motion_unjudged_n'],1)
        self.assertEqual(result['paired']['score_reversal_n'],1)
        self.assertAlmostEqual(result['paired']['normal_minus_control_mean'],.05)
        self.assertEqual(result['paired']['participant_mean_summary']['units_n'],2)

    def test_unmatched_camera_duration_or_repeat_never_silently_pairs(self):
        for field,value in [('camera_id','different-camera'),('recording_seconds',7.5),('repeat',2)]:
            rows=[trial('normal_imitation'),trial('hold_first')];rows[1][field]=value
            paired=self.run_report(rows)['score_origins']['offline_fixed_duration']['conditions']['hold_first']['paired']
            self.assertEqual(paired['missing_normal_match_n'],1)
            self.assertEqual(paired['scored_pair_n'],0)
            self.assertIsNone(paired['normal_minus_control_mean'])

    def test_live_and_offline_endpoints_cannot_be_pooled(self):
        rows=[trial('normal_imitation'),trial('hold_first'),
              trial('hold_first',origin='issued_live')]
        result=self.run_report(rows)['score_origins']
        self.assertEqual(result['offline_fixed_duration']['conditions']['hold_first']['paired']['scored_pair_n'],1)
        self.assertEqual(result['issued_live']['conditions']['hold_first']['paired']['missing_normal_match_n'],1)

    def test_photo_and_stationary_hand_remain_distinct(self):
        rows=[trial('normal_imitation'),trial('hold_first',score=.1),trial('static_photo',score=.9)]
        result=self.run_report(rows)['score_origins']['offline_fixed_duration']['conditions']
        self.assertEqual(result['hold_first']['score_accepted_n'],0)
        self.assertEqual(result['static_photo']['score_accepted_n'],1)

    def test_timeouts_tracking_and_unscored_errors_stay_in_denominators(self):
        rows=[trial('normal_imitation',score=.8),trial('hold_middle',score=None,outcome='technical_error'),
              trial('hold_middle',repeat=2,score=.3,outcome='tracking_failure'),
              trial('hold_middle',repeat=3,score=.3,outcome='timeout')]
        result=self.run_report(rows)['score_origins']['offline_fixed_duration']['conditions']['hold_middle']
        self.assertEqual(result['attempted_n'],3)
        self.assertEqual(result['scored_n'],2)
        self.assertEqual(result['score_rejected_n'],0)
        self.assertEqual(result['outcomes'],{'technical_error':1,'tracking_failure':1,'timeout':1})
        self.assertEqual(result['paired']['matched_but_unscored_pair_n'],1)

    def test_duplicate_capture_malformed_score_or_boolean_string_rejected(self):
        for change in [lambda r:r.append(copy.deepcopy(r[0])),
                       lambda r:r[1].update(capture_id=r[0]['capture_id']),
                       lambda r:r[1].update(legacy_score=float('nan')),
                       lambda r:r[1].update(gate_pass='False'),
                       lambda r:r[1].update(outcome='aborted'),
                       lambda r:r[1].update(recording_seconds=True)]:
            rows=[trial('normal_imitation'),trial('hold_first')];change(rows)
            with self.assertRaises(ValueError):self.run_report(rows)

    def test_aggregate_does_not_expose_identifiers_or_mutate_inputs(self):
        rows=[trial('normal_imitation'),trial('hold_first')];before=copy.deepcopy(rows)
        report=json.dumps(self.run_report(rows),allow_nan=False)
        self.assertEqual(rows,before)
        for field in ('trial_id','capture_id','participant_id','camera_id','target_id','source_family_id','protocol_id'):
            for row in rows:self.assertNotIn(row[field],report)

    def test_real_cli_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'input.json';output=Path(folder)/'report.json'
            source.write_text(json.dumps({'data_scope':'synthetic','trials':[
                trial('normal_imitation'),trial('hold_first')]}),encoding='utf-8')
            command=[sys.executable,'-m','validation_v03.paired_controls','--input',str(source),'--output',str(output)]
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);before=output.read_bytes()
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
            self.assertEqual(output.read_bytes(),before)


if __name__=='__main__':unittest.main()
