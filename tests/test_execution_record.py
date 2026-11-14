import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from validation_v03.execution_record import inventory_existing, run, verify
from validation_v03.run_manifest import TEXT_FIELDS


class ExecutionRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.repo = self.root/'repo'; self.repo.mkdir()
        self.private = self.root/'private_artifacts'; self.private.mkdir()
        def git(*args):
            return subprocess.run(['git', '-c', 'safe.directory='+self.repo.as_posix(), '-C', str(self.repo), *args],
                                  check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.git = git
        git('init'); git('config', 'user.email', 'fixture@example.invalid'); git('config', 'user.name', 'Fixture')
        git('config', 'commit.gpgsign', 'false')
        self.worker = self.repo/'worker.py'
        self.worker.write_text("from pathlib import Path\nimport sys\np=Path(sys.argv[1]);p.mkdir();(p/'result.json').write_text('{\"fixture\":true}')\nprint('actual subprocess output')\n")
        git('add', 'worker.py'); git('commit', '-m', 'fixture')
        self.input = self.private/'input.json'; self.input.write_text('{}')
        (self.private/'requirements.lock').write_text('numpy=='+importlib.metadata.version('numpy')+'\n')
        self.config = self.private/'config.json'
        self.spec = {**{key:'fixture-'+key for key in TEXT_FIELDS}, 'schema_version':1,
                     'execution_scope':'offline_coordinate', 'split':'diagnostic', 'seed':7,
                     'timeout_seconds':15, 'parameters':{'fixture_only':True}, 'code_files':['worker.py'],
                     'input_files':[{'id':'input','role':'synthetic_input','path':'input.json'}],
                     'dependency_lock':'requirements.lock', 'browser':'not_applicable_offline'}
        self.config.write_text(json.dumps(self.spec))
        self.output = self.private/'result'; self.record = self.private/'record'

    def execute(self, code=None):
        command = [sys.executable, str(self.worker), str(self.output)] if code is None else [sys.executable, '-c', code]
        return run(self.config, self.repo, self.record, command, [self.output])

    def test_actual_command_is_bound_and_survives_later_repository_changes(self):
        result = self.execute()
        self.assertEqual(result['state'], 'EXITED_ZERO'); self.assertEqual(result['process_exit_code'], 0)
        self.assertIn('actual subprocess output', (self.record/'stdout.private.log').read_text())
        self.worker.write_text('later code\n'); self.git('add', 'worker.py'); self.git('commit', '-m', 'later')
        self.assertEqual(verify(self.record)['integrity'], 'RECORDED_FILES_MATCH')
        self.assertFalse(verify(self.record)['scientific_result_or_source_authentication_proven'])

    def test_nonzero_and_missing_outputs_remain_inspectable_failure(self):
        result = self.execute("print('failed attempt');raise SystemExit(3)")
        self.assertEqual(result['state'], 'PROCESS_ERROR'); self.assertEqual(result['process_exit_code'], 3)
        self.assertEqual(verify(self.record)['state'], 'PROCESS_ERROR')
        self.assertEqual(verify(self.record)['artifact_files_n'], 0)

    def test_zero_exit_without_output_is_rejected(self):
        result = self.execute('pass')
        self.assertEqual(result['state'], 'OUTPUT_REJECTED')
        self.assertEqual(verify(self.record)['state'], 'OUTPUT_REJECTED')

    def test_timeout_has_real_terminal_process_outcome_and_keeps_logs(self):
        self.spec['timeout_seconds'] = .3; self.config.write_text(json.dumps(self.spec))
        result = self.execute('import time;time.sleep(10)')
        self.assertEqual(result['state'], 'TIMED_OUT'); self.assertIsNotNone(result['process_exit_code'])
        self.assertEqual(verify(self.record)['state'], 'TIMED_OUT')

    def test_input_change_during_execution_rejects_snapshot(self):
        result = self.execute('from pathlib import Path;Path('+repr(str(self.input))+').write_text("changed")')
        self.assertEqual(result['state'], 'POSTFLIGHT_REJECTED')
        self.assertFalse(result['postflight_snapshot_matched'])
        self.assertEqual(verify(self.record)['state'], 'POSTFLIGHT_REJECTED')

    def test_any_result_addition_or_byte_change_is_detected(self):
        self.execute(); p = self.output/'result.json'; original = p.read_bytes()
        p.write_bytes(original+b' ')
        with self.assertRaises(ValueError): verify(self.record)
        p.write_bytes(original); extra = self.output/'extra.json'; extra.write_text('{}')
        with self.assertRaises(ValueError): verify(self.record)
        extra.unlink(); self.assertEqual(verify(self.record)['integrity'], 'RECORDED_FILES_MATCH')

    def test_receipt_log_and_provenance_tampering_are_detected(self):
        self.execute()
        for relative in ('receipt.private.json', 'stdout.private.log', 'provenance/manifest.json', 'postflight.private.json'):
            p = self.record/relative; before = p.read_bytes(); p.write_bytes(before+b' ')
            with self.subTest(relative=relative), self.assertRaises(ValueError): verify(self.record)
            p.write_bytes(before)

    def test_existing_output_and_evidence_are_never_overwritten(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError): self.execute()
        self.assertFalse(self.record.exists())
        self.output.rmdir(); self.execute()
        with self.assertRaises(FileExistsError): self.execute()

    def test_retrospective_inventory_does_not_manufacture_execution(self):
        self.output.mkdir(); (self.output/'old.txt').write_text('old fixture')
        result = inventory_existing(self.record, [self.output], run_id='old-fixture')
        self.assertIsNone(result['command']); self.assertIsNone(result['started_utc_epoch_ns'])
        self.assertIsNone(result['process_exit_code'])
        self.assertEqual(verify(self.record)['mode'], 'RETROSPECTIVE_ARTIFACT_INVENTORY')


if __name__ == '__main__': unittest.main()
