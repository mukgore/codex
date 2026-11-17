import copy
import csv
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analysis.runtime_benchmark import reconstruction_worker as worker
from analysis.runtime_benchmark import reconstruction_audit as audit
from analysis.runtime_benchmark.journal import _private as fixture_path


class ReconstructionAuditTests(unittest.TestCase):
    def test_json_comparison_ignores_format_but_rejects_types_missing_and_order(self):
        worker.json_equal({'x':[1,None],'y':True},{'y':True,'x':[1,None]})
        for left,right in [({'x':1},{'x':True}),({'x':1},{'x':1.0}),([1,2],[2,1]),({'x':None},{})]:
            with self.assertRaises(ValueError):worker.json_equal(left,right)
        with self.assertRaises(ValueError):worker.json_equal(float('nan'),float('nan'))

    def test_metric_tolerance_is_bounded_and_preserves_null_and_integer_denominators(self):
        worker.near({'mean':.25,'n':25,'missing':None},{'mean':.25+1e-13,'n':25,'missing':None})
        for left,right in [(.25,.250001),(None,0),({'n':25},{'n':25.0}),([1],[1,2]),(float('inf'),float('inf'))]:
            with self.assertRaises(ValueError):worker.near(left,right)

    def test_csv_requires_exact_headers_rows_and_denominators(self):
        with tempfile.TemporaryDirectory() as temp:
            a,b=Path(temp)/'a.csv',Path(temp)/'b.csv'
            a.write_bytes(b'n,error\n25,\n');b.write_bytes(b'n,error\r\n25,\r\n')
            self.assertEqual(worker.csv_equal(a,b),1)
            b.write_text('error,n\n,25\n')
            with self.assertRaises(ValueError):worker.csv_equal(a,b)
            b.write_text('n,error\n25,0\n')
            with self.assertRaises(ValueError):worker.csv_equal(a,b)

    def test_roster_paths_and_existing_output_rejected_before_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);plan=root/'plan.json'
            jobs=[dict(id=k,kind=k,root=str(root/k),record=str(root/(k+'_record')))
                  for k in ('mediapipe','stage_profile','process_replay','local_http')]
            with patch.object(audit,'_private',side_effect=fixture_path),patch.object(audit.subprocess,'run') as launch:
                for mutation in ('kind','traversal','overlap','existing'):
                    values=copy.deepcopy(jobs);output=root/'output'
                    if mutation=='kind':values[0]['kind']='execute_model'
                    elif mutation=='traversal':values[0]['id']='../other'
                    elif mutation=='overlap':output=root/'mediapipe'/'nested'
                    else:output.mkdir()
                    plan.write_text(json.dumps(dict(jobs=values)))
                    with self.assertRaises((ValueError,FileExistsError)):audit.run(plan,output)
                launch.assert_not_called()

    def test_failure_statuses_are_preserved_and_later_jobs_still_attempted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);plan=root/'plan.json'
            jobs=[dict(id=k,kind=k,root=str(root/k),record=str(root/(k+'_record')))
                  for k in ('mediapipe','stage_profile','process_replay','local_http')]
            plan.write_text(json.dumps(dict(jobs=jobs)))
            with patch.object(audit,'_private',side_effect=fixture_path),patch.object(audit.subprocess,'run') as launch:
                launch.side_effect=[audit.subprocess.CompletedProcess([],2),audit.subprocess.TimeoutExpired([],60),
                                    audit.subprocess.CompletedProcess([],3),audit.subprocess.CompletedProcess([],4)]
                result=audit.run(plan,root/'output')
            self.assertFalse(result['all_reconstructions_match']);self.assertEqual(launch.call_count,4)
            self.assertEqual([r['status'] for r in result['jobs']],['ERROR','TIMEOUT','ERROR','ERROR'])
            self.assertIsNone(result['jobs'][1]['returncode'])
            self.assertTrue((root/'output/summary.private.json').exists())

    def test_empty_old_logs_require_presence_and_unchanged_zero_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'old.log';path.write_bytes(b'')
            plan=dict(expected_empty_files=[dict(path=str(path),bytes=0,sha256=hashlib.sha256(b'').hexdigest())])
            with patch.object(audit,'_private',side_effect=fixture_path):
                audit.check_empty_files(plan);path.write_bytes(b'new output')
                with self.assertRaises(ValueError):audit.check_empty_files(plan)
                path.unlink()
                with self.assertRaises(ValueError):audit.check_empty_files(plan)


if __name__=='__main__':unittest.main()
