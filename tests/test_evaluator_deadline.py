"""Use real local child pipes to exercise blocked writes and stalled replies."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from g4_lab.actual import ActualEvaluator


ECHO="""import sys,json
for line in sys.stdin:
 request=json.loads(line)
 print(json.dumps({'ok':False,'error':'fixture_rejection'} if request.get('reject') else
                  {'ok':True,'result':request}),flush=True)
"""


class EvaluatorDeadlineTests(unittest.TestCase):
    def evaluator(self,script=ECHO,timeout=.5):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        root=Path(directory.name);(root/'pool_manifest.json').write_text('{"clips":[]}',encoding='utf8')
        popen=subprocess.Popen
        def child(_args,**kwargs):return popen([sys.executable,'-u','-c',script],**kwargs)
        with patch('g4_lab.actual.subprocess.Popen',side_effect=child):
            evaluator=ActualEvaluator(root,call_timeout=timeout)
        self.addCleanup(evaluator.close)
        return evaluator

    def test_healthy_child_preserves_results_and_logical_rejections(self):
        evaluator=self.evaluator()
        self.assertEqual(evaluator.call({'number':7}),{'number':7})
        with self.assertRaisesRegex(ValueError,'fixture_rejection'):evaluator.call({'reject':True})
        with self.assertRaises(ValueError):evaluator.call({'bad':float('nan')})
        self.assertFalse(evaluator.failed)
        self.assertEqual(evaluator.call({'number':8}),{'number':8})

    def test_queue_timeout_does_not_kill_a_healthy_child(self):
        evaluator=self.evaluator(timeout=.15);evaluator.lock.acquire()
        errors=[]
        def queued():
            try:evaluator.call({'number':1})
            except Exception as error:errors.append(error)
        thread=threading.Thread(target=queued);thread.start();thread.join(timeout=2)
        evaluator.lock.release()
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors),1);self.assertIsInstance(errors[0],TimeoutError)
        self.assertFalse(evaluator.failed);self.assertIsNone(evaluator.process.poll())
        self.assertEqual(evaluator.call({'number':2}),{'number':2})

    def test_concurrent_calls_receive_their_own_response(self):
        evaluator=self.evaluator("import sys,json,time\nfor line in sys.stdin:\n request=json.loads(line);time.sleep(.01);print(json.dumps({'ok':True,'result':request}),flush=True)",timeout=2)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda number:evaluator.call({'number':number}),range(16)))
        self.assertEqual(results,[{'number':number} for number in range(16)])
        self.assertFalse(evaluator.failed)

    def assert_aborted(self,evaluator,request):
        started=time.monotonic()
        with self.assertRaises(TimeoutError):evaluator.call(request)
        self.assertLess(time.monotonic()-started,3)
        self.assertTrue(evaluator.failed)
        self.assertIsNotNone(evaluator.process.poll())
        self.assertTrue(evaluator.writer is None or not evaluator.writer.is_alive())
        with self.assertRaisesRegex(RuntimeError,'unavailable'):evaluator.call({'new':True})

    def test_child_that_never_reads_cannot_block_pipe_write_forever(self):
        evaluator=self.evaluator('import time;time.sleep(60)',timeout=.4)
        self.assert_aborted(evaluator,{'payload':'x'*(4*1024*1024)})

    def test_child_that_reads_but_never_replies_is_killed(self):
        evaluator=self.evaluator('import sys,time;sys.stdin.readline();time.sleep(60)',timeout=.3)
        self.assert_aborted(evaluator,{'small':True})

    def test_queue_time_is_deducted_from_the_same_deadline(self):
        evaluator=self.evaluator('import sys,time;sys.stdin.readline();time.sleep(60)',timeout=.5)
        evaluator.lock.acquire()
        errors=[];elapsed=[];started=threading.Event()
        def queued():
            before=time.monotonic();started.set()
            try:evaluator.call({'small':True})
            except Exception as error:errors.append(error)
            elapsed.append(time.monotonic()-before)
        thread=threading.Thread(target=queued);thread.start();self.assertTrue(started.wait(1))
        time.sleep(.3);evaluator.lock.release();thread.join(timeout=3)
        self.assertFalse(thread.is_alive());self.assertIsInstance(errors[0],TimeoutError)
        self.assertLess(elapsed[0],.75)
        self.assertTrue(evaluator.failed)

    def test_malformed_or_truncated_reply_poisons_stream(self):
        for script in ("import sys;sys.stdin.readline();print('bad json',flush=True)",
                       "import sys;sys.stdin.readline();print('{}',flush=True)",
                       "import sys;sys.stdin.readline();print('{\"ok\":1,\"result\":0}',flush=True)",
                       'import sys;sys.stdin.readline()'):
            with self.subTest(script=script):
                evaluator=self.evaluator(script)
                with self.assertRaises(RuntimeError):evaluator.call({'small':True})
                self.assertTrue(evaluator.failed)

    def test_invalid_deadlines_rejected_before_launch(self):
        for value in (True,0,-1,float('nan'),float('inf'),61,'1'):
            with self.subTest(value=value),patch('g4_lab.actual.subprocess.Popen') as launch:
                with self.assertRaises(ValueError):ActualEvaluator(Path('.'),call_timeout=value)
                launch.assert_not_called()


if __name__=='__main__':unittest.main()
