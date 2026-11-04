import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from analysis.runtime_benchmark.journal import Journal, recover_bytes, export_bundle, verify_bundle


class RuntimeJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.manifest=dict(condition_id='synthetic-journal-check',endpoint='logging_only',
                           input_exposure='synthetic',cache_state='no_model',planned_frames=2,timeout_seconds=30)

    def recovered(self, folder):
        return recover_bytes((folder/'events.jsonl').read_bytes())

    def test_complete_drop_denominator_and_portable_bundle_recovery(self):
        folder=self.root/'run';journal=Journal(folder,self.manifest)
        with journal.stage('synthetic_processing'):
            journal.frame_completed(0,True);journal.frame_dropped(1,'explicit_synthetic_drop')
        journal.finish('COMPLETED')
        result=self.recovered(folder)
        self.assertEqual(result['status'],'COMPLETED');self.assertEqual(result['completed_frames'],1)
        self.assertEqual(result['dropped_frames'],1)
        target=self.root/'bundle.zip';export_bundle(folder,target)
        self.assertEqual(verify_bundle(target),result)
        external=subprocess.run([sys.executable,'-c',
            'import json,sys;from analysis.runtime_benchmark.journal import verify_bundle;print(json.dumps(verify_bundle(sys.argv[1])))',str(target)],capture_output=True,text=True)
        self.assertEqual(external.returncode,0,external.stderr);self.assertEqual(json.loads(external.stdout),result)

    def test_missing_or_duplicate_frame_cannot_be_completed(self):
        folder=self.root/'run';journal=Journal(folder,self.manifest)
        journal.frame_completed(0,False)
        with self.assertRaises(ValueError):journal.frame_completed(0,True)
        with self.assertRaises(ValueError):journal.finish('COMPLETED')
        journal.close_without_terminal();self.assertEqual(self.recovered(folder)['status'],'INTERRUPTED')

    def test_real_worker_exit_is_interrupted_not_completed(self):
        folder=self.root/'crashed'
        worker='import json,os,sys;from analysis.runtime_benchmark.journal import Journal;j=Journal(sys.argv[1],json.loads(sys.argv[2]));j.frame_completed(0,True);os._exit(17)'
        process=subprocess.run([sys.executable,'-c',worker,str(folder),json.dumps(self.manifest)],capture_output=True)
        self.assertEqual(process.returncode,17);self.assertEqual(self.recovered(folder)['status'],'INTERRUPTED')

    def test_exception_and_keyboard_abort_keep_distinct_terminal_status(self):
        for exception,status in ((ValueError,'ERROR'),(KeyboardInterrupt,'ABORTED')):
            folder=self.root/status;journal=Journal(folder,self.manifest)
            with self.assertRaises(exception):
                with journal.stage('synthetic_failure'):raise exception('private message must not be logged')
            self.assertEqual(self.recovered(folder)['status'],status)
            self.assertNotIn(b'private message',(folder/'events.jsonl').read_bytes())

    def test_timeout_preserves_nonzero_elapsed_and_marks_injected_clock(self):
        now=[0];folder=self.root/'timeout';journal=Journal(folder,{**self.manifest,'timeout_seconds':1},clock=lambda:now[0])
        now[0]=2_000_000_000
        with self.assertRaises(TimeoutError):journal.frame_completed(0,True)
        result=self.recovered(folder);self.assertEqual(result['status'],'TIMED_OUT');self.assertEqual(result['elapsed_ns'],2_000_000_000)
        self.assertIn(b'injected_clock_not_runtime_evidence',(folder/'events.jsonl').read_bytes())

    def test_partial_tail_and_modified_complete_record_are_distinguished(self):
        folder=self.root/'run';journal=Journal(folder,self.manifest);journal.close_without_terminal()
        raw=(folder/'events.jsonl').read_bytes()
        self.assertEqual(recover_bytes(raw+b'{"partial":')['status'],'INTERRUPTED')
        self.assertEqual(recover_bytes(raw.replace(b'run_started',b'run_altered'))['status'],'LOG_CORRUPT')

    def test_bundle_member_tampering_is_detected(self):
        folder=self.root/'run';journal=Journal(folder,self.manifest);journal.finish('UNAVAILABLE',reason='model_missing')
        original=self.root/'original.zip';export_bundle(folder,original)
        altered=self.root/'altered.zip'
        with zipfile.ZipFile(original) as source,zipfile.ZipFile(altered,'w') as target:
            for name in source.namelist():
                target.writestr(name,source.read(name)+(b' ' if name=='events.jsonl' else b''))
        with self.assertRaises(ValueError):verify_bundle(altered)

    def test_existing_run_and_repository_output_are_not_overwritten(self):
        folder=self.root/'run';journal=Journal(folder,self.manifest);journal.finish('UNAVAILABLE')
        with self.assertRaises(FileExistsError):Journal(folder,self.manifest)
        with self.assertRaises(ValueError):Journal(Path(__file__).resolve().parents[1]/'runtime_private_test',self.manifest)
