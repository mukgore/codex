import copy
import unittest
from validation_v03.compare_scores import compare


def trials():
    result=[]
    for split in ('development','validation','test'):
        for label,score in (('human',.9),('attack',.1)):
            result.append(dict(trial_id=split+label,label=label,split=split,
                source_family_ids=split+'-source-a;'+split+'-source-b',
                participant_id=split+'-person' if label=='human' else '',
                capture_id=split+label+'-capture',outcome='scored',
                legacy_score=str(score),candidate_score=str(score)))
    return result


class CompareScoreTests(unittest.TestCase):
    def run_comparison(self,rows):
        return compare(rows,min_human_accept=1,max_attack_accept=0)

    def test_test_scores_cannot_tune_validation_threshold(self):
        rows=trials(); before=copy.deepcopy(rows)
        first=self.run_comparison(rows)
        self.assertEqual(rows,before)
        for row in rows:
            if row['split']=='test':row['candidate_score']='.99'
        second=self.run_comparison(rows)
        self.assertEqual(first['metrics']['candidate_score']['threshold'],second['metrics']['candidate_score']['threshold'])
        self.assertEqual(second['metrics']['candidate_score']['test']['attack']['score_accepted_n'],1)
        self.assertNotEqual(rows,before)

    def test_every_constituent_source_and_participant_and_capture_checked(self):
        for field,value in (('source_family_ids','test-source-a;validation-source-b'),
                            ('participant_id','validation-person'),
                            ('capture_id','validationhuman-capture')):
            rows=trials();rows[4][field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'leakage'):
                self.run_comparison(rows)

    def test_failures_and_aborts_stay_in_denominators(self):
        rows=trials()
        for label,outcome in (('human','technical_error'),('attack','aborted')):
            row=copy.deepcopy(rows[4 if label=='human' else 5])
            row.update(trial_id=label+'failed',outcome=outcome,legacy_score='',candidate_score='')
            rows.append(row)
        data=self.run_comparison(rows)['metrics']['candidate_score']['test']
        self.assertEqual(data['human']['attempted_n'],2)
        self.assertEqual(data['human']['score_accept_rate_among_scored'],1)
        self.assertEqual(data['human']['observed_score_accepts_per_attempt'],.5)
        self.assertEqual(data['attack']['aborted_n'],1)

    def test_missing_nonfinite_duplicate_and_unknown_records_rejected(self):
        for field,value in (('candidate_score','nan'),('participant_id',''),
                            ('source_family_ids','a;'),('outcome','unknown'),('trial_id','developmenthuman')):
            rows=trials();rows[4][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.run_comparison(rows)

    def test_infeasible_candidate_is_reported_without_selecting_on_test(self):
        rows=trials();rows[3]['candidate_score']='1.0'
        self.assertEqual(self.run_comparison(rows)['metrics']['candidate_score']['status'],'no_finite_feasible_threshold')

    def test_aggregate_contains_no_individual_identifiers(self):
        import json
        rows=trials();report=json.dumps(self.run_comparison(rows))
        for row in rows:
            self.assertNotIn(row['trial_id'],report)
            self.assertNotIn(row['capture_id'],report)

    def test_cli_writes_aggregate_and_refuses_existing_output(self):
        import csv,json,subprocess,sys,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'scores.csv';output=Path(directory)/'report.json'
            rows=trials()
            with source.open('w',encoding='utf8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
            args=[sys.executable,'-m','validation_v03.compare_scores','--input',str(source),
                '--output',str(output),'--min-human-accept','1','--max-attack-accept','0']
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(output.read_text(encoding='utf8'))
            self.assertEqual(report['endpoint'],'score_only')
            before=output.read_bytes()
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(output.read_bytes(),before)
