import unittest
from analysis.runtime_benchmark.arrival_queue import ArrivalQueue


class Clock:
    now = 0
    def __call__(self): return self.now


class ArrivalQueueTests(unittest.TestCase):
    def make(self, **kw):
        clock = Clock()
        return clock, ArrivalQueue(clock=clock, policy='fifo', capacity=3, **kw)

    def test_unarrived_frames_have_no_consumer_lookup_and_pts_is_not_wall_time(self):
        clock, queue = self.make(); worker = queue.consumer()
        self.assertIsNone(worker.take())
        with self.assertRaises(AttributeError): worker.read(99)
        with self.assertRaises(AttributeError): worker.frames
        clock.now=5; queue.arrive(0, 900000000, b'pixels0')
        clock.now=7; batch=worker.take()
        self.assertEqual([f.sequence for f in batch.frames], [0])
        self.assertEqual(batch.frames[0].pixels,b'pixels0')
        clock.now=12; result=worker.finish(batch,outcome='response_ready')
        self.assertEqual(result['arrival_to_finish_ns'],[7])
        self.assertEqual(result['service_ns'],5)
        self.assertEqual(queue.events[2]['queue_wait_ns'],[2])

    def test_batch_wait_and_eos_partial_flush(self):
        clock,queue=self.make(min_batch=2,max_batch=3,max_wait_ns=10); worker=queue.consumer()
        queue.arrive(0,0,b'a'); clock.now=9; self.assertIsNone(worker.take())
        clock.now=10; batch=worker.take(); self.assertEqual(len(batch.frames),1)
        worker.finish(batch,outcome='no_detection')
        queue.arrive(1,1,b'b'); queue.end_input()
        batch=worker.take(); self.assertEqual(len(batch.frames),1)
        worker.finish(batch,outcome='response_ready'); queue.close(reason='completed')

    def test_fifo_overflow_during_inflight_includes_drop_denominator(self):
        clock,queue=self.make(); worker=queue.consumer()
        queue.arrive(0,0,b'a'); batch=worker.take()
        for i in range(1,4): queue.arrive(i,i,b'a')
        self.assertFalse(queue.arrive(4,4,b'a'))
        with self.assertRaises(RuntimeError): worker.take()
        worker.finish(batch,outcome='error')
        self.assertEqual(worker.take().frames[0].sequence,1)
        self.assertEqual([e['sequence'] for e in queue.events if e['kind']=='drop'],[4])

    def test_latest_replaces_waiting_but_never_active(self):
        c=Clock(); q=ArrivalQueue(policy='latest',capacity=1,clock=c); w=q.consumer()
        q.arrive(0,0,b'a'); active=w.take()
        q.arrive(1,1,b'b'); q.arrive(2,2,b'c')
        w.finish(active,outcome='response_ready')
        self.assertEqual(w.take().frames[0].sequence,2)
        self.assertEqual([e['sequence'] for e in q.events if e['kind']=='drop'],[1])

    def test_deadline_includes_queue_batch_and_compute_wait_and_is_exclusive(self):
        c,q=self.make(deadline_ns=10); w=q.consumer()
        q.arrive(0,0,b'a'); batch=w.take(); q.arrive(1,1,b'b')
        c.now=10; self.assertFalse(w.finish(batch,outcome='response_ready')['deadline_met'])
        self.assertIsNone(w.take()); self.assertFalse(q.arrive(2,2,b'c'))
        self.assertEqual([e['reason'] for e in q.events if e['kind']=='drop'],['deadline','deadline'])

    def test_no_fake_finish_after_interruption_or_premature_completion(self):
        c,q=self.make(); w=q.consumer(); q.arrive(0,0,b'a'); batch=w.take()
        with self.assertRaises(ValueError): q.close(reason='completed')
        q.close(reason='aborted')
        self.assertEqual(q.events[-1]['unfinished_token'],batch.token)
        self.assertFalse(any(e['kind']=='finish' for e in q.events))
        with self.assertRaises(ValueError): w.finish(batch,outcome='response_ready')

    def test_validation_prevents_replayed_ids_paths_and_clock_regression(self):
        c,q=self.make(); q.arrive(0,0,b'a')
        for args in ((0,1,b'b'),(1,-1,b'b'),(1,1,'file.mp4'),(1,1,b'')):
            with self.assertRaises(ValueError): q.arrive(*args)
        c.now=5; q.arrive(1,1,b'a'); c.now=4
        with self.assertRaises(ValueError): q.consumer().take()
        c.now=6; q.end_input()
        with self.assertRaises(RuntimeError): q.arrive(2,2,b'a')

    def test_recording_failure_prohibits_continuation(self):
        def bad_sink(event):
            if event['kind'] != 'queue_started': raise OSError('disk full')
        q=ArrivalQueue(policy='fifo',capacity=1,sink=bad_sink)
        with self.assertRaises(OSError): q.arrive(0,0,b'a')
        with self.assertRaises(RuntimeError): q.consumer().take()


if __name__=='__main__': unittest.main()
