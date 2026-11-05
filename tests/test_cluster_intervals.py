import copy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from validation_v03.cluster_intervals import test_intervals as intervals


def fixture():
    result = []
    for split in ('development', 'validation', 'test'):
        for label in ('human', 'attack'):
            for index in range(4):
                result.append(dict(trial_id=f'{split}-{label}-{index}', label=label, split=split,
                                   participant_id=f'{split}-{label}-{index}', capture_id=f'{split}-{label}-{index}',
                                   source_family_ids=f'{split}-{label}-{index}', outcome='scored',
                                   legacy_score=str(index/3), candidate_score=str((3-index)/3)))
    return result


class ClusterIntervalsTests(unittest.TestCase):
    def evaluate(self, rows, **kwargs):
        return intervals(rows, {'legacy_score': .5, 'candidate_score': .5}, repetitions=500, seed=7, confidence=.95, **kwargs)

    def test_deterministic_paired_intervals_and_no_ids(self):
        rows = fixture(); a = self.evaluate(rows); b = self.evaluate(rows)
        self.assertEqual(a, b)
        self.assertEqual(a['labels']['human']['cluster_n'], 4)
        self.assertEqual(a['labels']['human']['paired_candidate_minus_legacy'], 0)
        low, high = a['labels']['human']['intervals']['paired_difference']['bounds']
        self.assertLess(low, 0); self.assertGreater(high, 0)
        self.assertNotIn('test-human-0', str(a))

    def test_multi_source_transitive_linkage_is_one_cluster(self):
        rows = fixture(); test = [row for row in rows if row['split']=='test' and row['label']=='human']
        test[0]['source_family_ids']='a;b'; test[1]['source_family_ids']='b;c'
        test[2]['source_family_ids']='c;d'; test[3]['source_family_ids']='d;e'
        result = self.evaluate(rows)['labels']['human']
        self.assertEqual(result['cluster_n'], 1)
        self.assertEqual(result['status'], 'INSUFFICIENT_CLUSTERS'); self.assertIsNone(result['intervals'])

    def test_failures_remain_in_attempt_denominator(self):
        rows = fixture()
        failed = next(row for row in rows if row['trial_id']=='test-human-3')
        failed.update(outcome='technical_error', legacy_score='', candidate_score='')
        result = self.evaluate(rows)['labels']['human']
        self.assertEqual(result['attempted_n'], 4)
        self.assertEqual(result['legacy_accepts_per_attempt'], .25)

    def test_zero_events_do_not_produce_false_zero_risk_bounds(self):
        rows = fixture()
        for row in rows:
            if row['split']=='test': row.update(legacy_score='0', candidate_score='0')
        result = self.evaluate(rows)['labels']['attack']['intervals']['candidate']
        self.assertEqual(result['status'], 'DEGENERATE_RESAMPLING'); self.assertIsNone(result['bounds'])

    def test_test_scores_never_modify_frozen_thresholds_and_lineage_leakage_fails(self):
        rows = fixture(); result = self.evaluate(rows)
        self.assertEqual(result['thresholds'], {'legacy_score': .5, 'candidate_score': .5})
        rows[-1]['source_family_ids'] = rows[0]['source_family_ids']
        with self.assertRaises(ValueError): self.evaluate(rows)

    def test_csv_cli_connects_validation_thresholds_to_cluster_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)/'trials.csv';target=Path(temporary)/'report.json';rows=fixture()
            with source.open('w',newline='',encoding='utf8') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            result=subprocess.run([sys.executable,'-m','validation_v03.compare_scores','--input',str(source),'--output',str(target),
                '--min-human-accept','0','--max-attack-accept','1','--cluster-repetitions','500','--cluster-seed','7','--cluster-confidence','.95'],
                capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(target.read_text(encoding='utf8'))
            self.assertEqual(report['cluster_intervals']['split'],'test')
            for metric in ('legacy_score','candidate_score'):
                self.assertEqual(report['cluster_intervals']['thresholds'][metric],report['metrics'][metric]['threshold'])
