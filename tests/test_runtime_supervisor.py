import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from analysis.runtime_benchmark.supervisor import run


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cwd = Path(__file__).resolve().parents[1]

    def execute(self, source, *, timeout=10, name='run'):
        return run([sys.executable, '-c', source], self.root / name,
                   cwd=self.cwd, timeout_seconds=timeout)

    def test_success_requires_complete_journal_not_just_zero_exit(self):
        empty = self.execute('pass', name='no_journal')
        self.assertEqual(empty['supervisor_status'], 'EXITED')
        self.assertFalse(empty['completed'])
        source = ('import os;from analysis.runtime_benchmark.journal import Journal;'
                  'j=Journal(os.environ["RUNTIME_JOURNAL_DIRECTORY"],dict(condition_id="fixture",'
                  'endpoint="logging_only",input_exposure="synthetic",cache_state="no_model",'
                  'planned_frames=1,timeout_seconds=5));j.frame_completed(0,True);j.finish("COMPLETED")')
        result = self.execute(source, name='complete')
        self.assertTrue(result['completed'], result)

    def test_blocked_worker_and_descendant_are_killed(self):
        heartbeat = self.root / 'heartbeat'
        child = 'import pathlib,time; p=pathlib.Path(' + repr(str(heartbeat)) + ');\nwhile True:p.write_text(str(time.time_ns()));time.sleep(.02)'
        source = ('import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",' + repr(child) + ']);time.sleep(60)')
        result = self.execute(source, timeout=1.5)
        self.assertEqual(result['supervisor_status'], 'TIMED_OUT', result)
        self.assertFalse(result['completed']); self.assertLess(result['elapsed_ns'], 8e9)
        self.assertTrue(heartbeat.exists(), 'Descendant must actually start before the deadline')
        before = heartbeat.read_bytes(); time.sleep(.15)
        self.assertEqual(before, heartbeat.read_bytes(), 'Owned descendant survived timeout')

    def test_leader_success_does_not_leave_background_descendant(self):
        heartbeat = self.root / 'background'
        child = 'import pathlib,time;p=pathlib.Path(' + repr(str(heartbeat)) + ');\nwhile True:p.write_text(str(time.time_ns()));time.sleep(.02)'
        source = ('import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",' + repr(child) + ']);time.sleep(.4)')
        result = self.execute(source)
        self.assertEqual(result['supervisor_status'], 'EXITED', result)
        self.assertTrue(heartbeat.exists()); before = heartbeat.read_bytes(); time.sleep(.15)
        self.assertEqual(before, heartbeat.read_bytes())

    def test_nonzero_exit_and_overwrite_are_not_success(self):
        result = self.execute('import sys;sys.exit(17)')
        self.assertEqual(result['supervisor_status'], 'ERROR')
        self.assertFalse(result['completed'])
        with self.assertRaises(FileExistsError): self.execute('pass')

    def test_timeout_does_not_fabricate_worker_terminal_event(self):
        source = ('import os,time;from analysis.runtime_benchmark.journal import Journal;'
                  'j=Journal(os.environ["RUNTIME_JOURNAL_DIRECTORY"],dict(condition_id="fixture",'
                  'endpoint="logging_only",input_exposure="synthetic",cache_state="no_model",'
                  'planned_frames=2,timeout_seconds=60));j.frame_completed(0,True);time.sleep(60)')
        result = self.execute(source, timeout=1.5)
        self.assertEqual(result['supervisor_status'], 'TIMED_OUT')
        self.assertEqual(result['worker_journal']['status'], 'INTERRUPTED')
        self.assertEqual(result['worker_journal']['completed_frames'], 1)

    def test_invalid_deadlines_and_shell_string_rejected(self):
        for value in (True, 0, -1, float('inf'), float('nan')):
            with self.assertRaises(ValueError): self.execute('pass', timeout=value)
        with self.assertRaises(ValueError):
            run('echo unsafe', self.root / 'string', cwd=self.cwd, timeout_seconds=1)
