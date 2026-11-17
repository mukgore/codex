import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from analysis.runtime_benchmark.arrival_replay import run, ScheduledFrame
from analysis.runtime_benchmark.arrival_record import verify_directory
from analysis.runtime_benchmark.stage_profile import JsonlSink


ENTRY='analysis.runtime_benchmark.replay_fixture:observe'


class ArrivalReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def execute(self,schedule,**kw):
        return run(schedule,kw.pop('entry',ENTRY),self.root/kw.pop('name','run'),
                   input_role='synthetic_fixture',**kw)

    def events(self,name='run'):
        return [json.loads(line) for line in (self.root/name/'queue/events.private.jsonl').read_bytes().splitlines()]

    def test_fifo_order_and_only_current_pixels_with_real_delivery_lateness(self):
        schedule=[ScheduledFrame(0,900000000,b'slow')]+[ScheduledFrame(i*10000000,i,bytes([i])) for i in range(1,4)]
        result=self.execute(schedule)
        self.assertEqual(result['status'],'COMPLETED',result)
        saved=verify_directory(self.root/'run/queue');self.assertEqual(saved,result['queue_recovery'])
        s=saved['recovery']['summary'];self.assertEqual(s['arrived_frames_n'],4)
        self.assertEqual(s['finished_frames_n']+s['dropped_frames_n'],4)
        events=self.events();waiting=[];started=[]
        for event in events:
            if event['kind']=='arrival':waiting.append(event['sequence'])
            elif event['kind']=='drop':waiting.remove(event['sequence'])
            elif event['kind']=='start':
                self.assertEqual(event['sequences'],[waiting.pop(0)])
                started.append(event['sequences'])
        self.assertEqual(started[0],[0])
        transport=[json.loads(line) for line in (self.root/'run/transport.private.jsonl').read_bytes().splitlines()]
        replies=[e['message'] for e in transport if e['kind']=='worker_message' and e['message']['kind']=='result']
        self.assertEqual([r['sequences'] for r in replies],started)
        for reply in replies:
            for seen in reply['result']['seen']:
                self.assertEqual(seen['keys'],['pixels','sequence','source_pts_ns'])
                self.assertEqual(seen['sha256'],hashlib.sha256(schedule[seen['sequence']].pixels).hexdigest())
        self.assertFalse(result['authentication_proven']);self.assertFalse(result['model_performance_proven'])

    def test_latest_replaces_pending_and_batch_flushes_on_eos(self):
        schedule=[ScheduledFrame(0,0,b'slow')]+[ScheduledFrame(i*10000000,i,b'x') for i in range(1,4)]
        result=self.execute(schedule,policy='latest')
        self.assertEqual(result['status'],'COMPLETED',result)
        # fsync/OS stalls can release multiple arrivals before the first take.
        # The first chosen sequence need not be0. Every take must choose the
        # latest actual arrival, and EOS must eventually settle the final one.
        latest=None;chosen=[]
        for event in self.events():
            if event['kind']=='arrival':latest=event['sequence']
            elif event['kind']=='start':
                self.assertEqual(event['sequences'],[latest]);chosen.append(latest)
        self.assertEqual(chosen[-1],3)
        self.assertEqual(chosen,sorted(set(chosen)))
        result=self.execute([ScheduledFrame(0,0,b'x')],name='partial',capacity=2,min_batch=2,max_batch=2,max_wait_ns=10**9,
                            entry='analysis.runtime_benchmark.replay_fixture:no_detection')
        self.assertEqual(result['status'],'COMPLETED',result)
        self.assertEqual(result['queue_recovery']['recovery']['summary']['outcomes'],{'no_detection':1})

    def test_delayed_ingress_logging_can_replace_first_frame_before_dispatch(self):
        original=JsonlSink.__call__
        def delayed(sink,event):
            original(sink,event)
            if event['kind']=='arrival' and event['sequence']==0:time.sleep(.06)
        schedule=[ScheduledFrame(i*10000000,i,b'x') for i in range(4)]
        with patch.object(JsonlSink,'__call__',delayed):
            result=self.execute(schedule,policy='latest')
        self.assertEqual(result['status'],'COMPLETED',result)
        self.assertEqual([e['sequences'] for e in self.events() if e['kind']=='start'],[[3]])
        self.assertEqual(verify_directory(self.root/'run/queue')['recovery']['summary']['dropped_frames_n'],3)

    def test_timeout_preserves_unknown_finish_and_not_arrived_frames(self):
        result=self.execute([ScheduledFrame(0,0,b'hang'),ScheduledFrame(10**9,1,b'x')],timeout_seconds=.08)
        self.assertEqual(result['status'],'TIMEOUT',result)
        s=result['queue_recovery']['recovery']['summary']
        self.assertEqual((s['unfinished_frames_n'],s['not_arrived_frames_n']),(1,1))
        self.assertFalse(any(e['kind']=='finish' for e in self.events()))
        self.assertIsNotNone(result['worker_returncode'])

    def test_handler_error_crash_and_setup_failure_remain_distinct(self):
        result=self.execute([ScheduledFrame(0,0,b'error')])
        self.assertEqual(result['status'],'ERROR')
        self.assertEqual(result['queue_recovery']['recovery']['summary']['outcomes'],{'error':1})
        result=self.execute([ScheduledFrame(0,0,b'crash')],name='crash')
        self.assertEqual(result['status'],'ERROR');self.assertEqual(result['worker_returncode'],7)
        self.assertEqual(result['queue_recovery']['recovery']['summary']['unfinished_frames_n'],1)
        result=self.execute([],name='setup',entry='missing_fixture_module:handler')
        self.assertEqual(result['phase'],'setup');self.assertEqual(result['status'],'ERROR')
        self.assertIsNone(result['queue_recovery'])

    def test_invalid_input_and_existing_output_rejected_without_new_execution(self):
        for schedule,kw in [([ScheduledFrame(-1,0,b'x')],{}),([ScheduledFrame(0,0,'file.mp4')],{}),
                            ([],{'timeout_seconds':True}),([],{'max_batch':'2'})]:
            with self.assertRaises(ValueError):self.execute(schedule,**kw)
            self.assertFalse((self.root/'run').exists())
        result=self.execute([]);self.assertEqual(result['status'],'COMPLETED')
        before=(self.root/'run/result.private.json').read_bytes()
        with self.assertRaises(FileExistsError):self.execute([])
        self.assertEqual((self.root/'run/result.private.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
