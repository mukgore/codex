import copy
import json
from pathlib import Path
import tempfile
import unittest

from analysis.runtime_benchmark.arrival_queue import ArrivalQueue
from analysis.runtime_benchmark.arrival_recovery import recover
from analysis.runtime_benchmark.arrival_record import RecordedQueue, verify_directory
from tests.test_arrival_queue import Clock


def raw(events):
    return b''.join(json.dumps(e).encode()+b'\n' for e in events)


class ArrivalRecoveryTests(unittest.TestCase):
    def completed(self,policy='fifo'):
        c=Clock(); q=ArrivalQueue(policy=policy,capacity=1,clock=c,planned_frames=3)
        q.arrive(0,2000,b'abc'); batch=q.consumer().take()
        c.now=2; q.arrive(1,100,b'a'); c.now=3; q.arrive(2,0,b'a')
        c.now=4; q.consumer().finish(batch,outcome='response_ready')
        q.end_input(); c.now=5; batch=q.consumer().take()
        c.now=7; q.consumer().finish(batch,outcome='no_detection'); q.close(reason='completed')
        return q

    def test_roundtrip_conserves_frames_and_times_with_fifo_and_latest(self):
        for policy in ('fifo','latest'):
            q=self.completed(policy); result=recover(raw(q.events))
            self.assertEqual(result['state'],'COMPLETED'); s=result['summary']
            self.assertEqual((s['arrived_frames_n'],s['finished_frames_n'],s['dropped_frames_n']),(3,2,1))
            self.assertEqual(s['not_arrived_frames_n'],0)
            self.assertEqual(s['arrival_to_finish_ns_by_sequence'][0],4)
            self.assertEqual(s['queue_wait_ns_by_sequence'][1 if policy=='fifo' else 2],3 if policy=='fifo' else 2)
            self.assertEqual(s['outcomes'],{'response_ready':1,'no_detection':1})

    def test_all_durable_prefixes_recover_without_invented_completion(self):
        q=self.completed('latest')
        for n in range(1,len(q.events)):
            r=recover(raw(q.events[:n])); self.assertEqual(r['state'],'INTERRUPTED',(n,r))
            self.assertIsNone(r['summary']['elapsed_ns'])
            s=r['summary']; self.assertEqual(s['arrived_frames_n'],sum(s[k] for k in ('finished_frames_n','dropped_frames_n','unfinished_frames_n','unsettled_frames_n')))
        self.assertEqual(recover(b'')['state'],'LOG_LOST')
        self.assertEqual(recover(b'{')['state'],'INTERRUPTED')

    def test_deadline_drop_close_and_unfinished_active_are_preserved(self):
        c=Clock(); q=ArrivalQueue(policy='fifo',capacity=2,clock=c,deadline_ns=5,planned_frames=4)
        q.arrive(0,0,b'x'); batch=q.consumer().take(); q.arrive(1,1,b'x')
        c.now=5; result=q.consumer().finish(batch,outcome='response_ready')
        self.assertFalse(result['deadline_met']); q.consumer().take(); q.arrive(2,2,b'x')
        q.close(reason='timeout'); r=recover(raw(q.events))
        self.assertEqual(r['state'],'TIMEOUT'); self.assertEqual(r['summary']['not_arrived_frames_n'],1)
        c=Clock(); q=ArrivalQueue(policy='fifo',capacity=2,clock=c)
        q.arrive(0,0,b'x'); q.consumer().take(); q.arrive(1,1,b'x'); q.close(reason='aborted')
        r=recover(raw(q.events)); self.assertEqual(r['state'],'ABORTED')
        self.assertEqual(r['summary']['unfinished_frames_n'],1)
        self.assertEqual(r['summary']['arrival_to_finish_ns_by_sequence'],{})

    def test_semantic_corruption_and_types_are_rejected(self):
        q=self.completed()
        edits=[(0,'schema_version',True),(0,'capacity',2),
               (1,'pixel_bytes_n',0),(1,'sequence',True),
               (2,'queue_wait_ns',[1]),(7,'outcome','success')]
        for i,key,value in edits:
            events=copy.deepcopy(q.events);events[i][key]=value
            self.assertEqual(recover(raw(events))['state'],'LOG_CORRUPT',(i,key))
        for kind,key,value in [('finish','service_ns',90),('finish','deadline_met',False),('close','unfinished_token',4),('start','sequences',[2])]:
            events=copy.deepcopy(q.events);next(e for e in events if e['kind']==kind)[key]=value
            self.assertEqual(recover(raw(events))['state'],'LOG_CORRUPT',(kind,key))

    def test_truncated_terminal_extra_events_and_bad_lines(self):
        q=self.completed(); data=raw(q.events)
        self.assertEqual(recover(data[:-1])['state'],'INTERRUPTED')
        self.assertEqual(recover(data+b'{')['state'],'LOG_CORRUPT')
        self.assertEqual(recover(data+raw([q.events[-1]]))['state'],'LOG_CORRUPT')
        self.assertEqual(recover(raw(q.events[:2])+b'no json\n')['state'],'LOG_CORRUPT')

    def test_early_batch_start_missing_overflow_and_reordered_frames_rejected(self):
        c=Clock();q=ArrivalQueue(policy='fifo',capacity=2,min_batch=2,max_batch=2,max_wait_ns=10,clock=c)
        q.arrive(0,0,b'x');c.now=10;q.consumer().take()
        events=copy.deepcopy(q.events);events[-1]['at_ns']=9;events[-1]['queue_wait_ns']=[9]
        self.assertEqual(recover(raw(events))['state'],'LOG_CORRUPT')
        events=self.completed().events;events=[e for e in events if e['kind']!='drop']
        for i,e in enumerate(events):e['event_id']=i
        self.assertEqual(recover(raw(events))['state'],'LOG_CORRUPT')

    def test_planned_missing_frames_cannot_be_completed(self):
        c=Clock();q=ArrivalQueue(policy='fifo',capacity=1,clock=c,planned_frames=2)
        q.arrive(0,0,b'x');b=q.consumer().take();q.consumer().finish(b,outcome='error');q.end_input()
        with self.assertRaises(ValueError):q.close(reason='completed')
        q.close(reason='error');r=recover(raw(q.events))
        self.assertEqual(r['summary']['not_arrived_frames_n'],1)
        self.assertEqual(r['state'],'ERROR')

    def test_private_record_readback_no_overwrite_and_raw_bytes_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'run';record=RecordedQueue(path,policy='fifo',capacity=1,planned_frames=1)
            q=record.queue;q.arrive(0,0,b'pixels');b=q.consumer().take()
            q.consumer().finish(b,outcome='response_ready');q.end_input();q.close(reason='completed')
            result=record.finish_recording();self.assertEqual(verify_directory(path),result)
            self.assertEqual(result['recovery']['state'],'COMPLETED')
            with self.assertRaises(FileExistsError):RecordedQueue(path,policy='fifo',capacity=1)
            with self.assertRaises(RuntimeError):record.finish_recording()
            raw_path=path/'events.private.jsonl';data=raw_path.read_bytes()
            # Coherent PTS changes leave latency unchanged, but must fail byte binding.
            raw_path.write_bytes(data.replace(b'"source_pts_ns": 0',b'"source_pts_ns": 1'))
            with self.assertRaises(ValueError):verify_directory(path)

    def test_storage_finalize_does_not_fabricate_queue_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            record=RecordedQueue(Path(temp)/'run',policy='fifo',capacity=1,planned_frames=2)
            q=record.queue;q.arrive(0,0,b'pixels');q.consumer().take()
            result=record.finish_recording()['recovery']
            self.assertEqual(result['state'],'INTERRUPTED')
            self.assertEqual(result['summary']['unfinished_frames_n'],1)
            self.assertEqual(result['summary']['not_arrived_frames_n'],1)
            self.assertIsNone(result['summary']['elapsed_ns'])


if __name__=='__main__':unittest.main()
