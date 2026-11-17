import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from analysis.runtime_benchmark.http_timing import ServerTiming,TimedEvaluator,recover
from analysis.runtime_benchmark.http_client_timing import TimedLocalClient,measure_attempt,reconcile,recover as recover_client
from g4_lab.server import LabService,create_server


def encoded(events):return b''.join(json.dumps(e).encode()+b'\n' for e in events)


class Clock:
    now=0
    def __call__(self):return self.now


class HTTPTimingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    def test_nested_inclusive_clock_accounting_and_all_prefixes(self):
        c=Clock();t=ServerTiming(self.root/'server.jsonl',clock=c)
        with t.request('client_1','POST','/api/submit') as r:
            def outer():
                c.now+=2
                def inner():c.now+=3;return 7
                value=r.call('evaluator',inner);c.now+=2;return value
            self.assertEqual(r.call('submit',outer),7)
            r.http_status=200;r.call('response_write',lambda:None);r.response_write_completed=True
        t.close();result=recover(encoded(t.events));self.assertEqual(result['state'],'COMPLETED')
        row=result['requests'][0];self.assertEqual(row['elapsed_ns'],7)
        self.assertEqual([p['elapsed_ns'] for p in row['phases']],[7,3,0])
        self.assertEqual(row['phases'][1]['parent_id'],0)
        for n in range(1,len(t.events)):
            self.assertEqual(recover(encoded(t.events[:n]))['state'],'INTERRUPTED')
        self.assertEqual(recover(b'')['state'],'LOG_LOST')
        self.assertEqual(recover(encoded(t.events)+b'{')['state'],'LOG_CORRUPT')

    def test_error_abort_live_close_and_scope_restoration(self):
        t=ServerTiming(self.root/'server.jsonl')
        with self.assertRaises(KeyboardInterrupt):
            with t.request('bad secret string!','POST','/api/submit') as r:
                with self.assertRaises(RuntimeError):t.close()
                r.call('evaluator',lambda:(_ for _ in ()).throw(KeyboardInterrupt()))
        t.close();r=recover(encoded(t.events))['requests'][0]
        self.assertEqual(r['outcome'],'ABORTED');self.assertIsNone(r['correlation']);self.assertIsNone(r['http_status'])
        self.assertFalse(r['response_write_completed'])
        with self.assertRaises(RuntimeError):
            with t.request('x','POST','/api/submit'):pass

    def test_corruption_duration_parent_response_and_extra_metadata_rejected(self):
        t=ServerTiming(self.root/'server.jsonl')
        with t.request('c','POST','/api/submit') as r:r.call('submit',lambda:None)
        t.close()
        for kind,key,value in [('phase_finished','elapsed_ns',-1),('phase_started','parent_id',0),
                               ('request_finished','response_write_completed',True),('request_started','body','private'),
                               ('timing_started','schema_version',True)]:
            events=copy.deepcopy(t.events);next(e for e in events if e['kind']==kind)[key]=value
            self.assertEqual(recover(encoded(events))['state'],'LOG_CORRUPT',(kind,key))

    def test_concurrent_request_contexts_do_not_cross_evaluator_phases(self):
        t=ServerTiming(self.root/'server.jsonl');e=TimedEvaluator(SimpleNamespace(evaluate=lambda x:x*x),t)
        def work(i):
            with t.request(str(i),'POST','/api/submit'):return e.evaluate(i)
        with ThreadPoolExecutor(max_workers=4) as executor:self.assertEqual(list(executor.map(work,range(8))),[i*i for i in range(8)])
        self.assertTrue(t.wait_idle());t.close();r=recover(encoded(t.events))
        self.assertEqual(r['state'],'COMPLETED');self.assertEqual(len(r['requests']),8)
        self.assertTrue(all(len(row['phases'])==1 and row['phases'][0]['name']=='evaluator' for row in r['requests']))

    def test_client_storage_failure_stops_before_network_and_cannot_continue(self):
        client=TimedLocalClient(9,self.root/'client.jsonl')
        with patch('analysis.runtime_benchmark.http_client_timing.JsonlSink.__call__',side_effect=OSError('disk full')):
            with patch('analysis.runtime_benchmark.http_client_timing.HTTPConnection') as connection:
                with self.assertRaises(OSError):client.post('/api/session',{})
                with self.assertRaises(RuntimeError):client.post('/api/session',{})
                connection.assert_not_called()
        client.close()
        self.assertEqual(recover_client((self.root/'client.jsonl').read_bytes())['state'],'INTERRUPTED')

    def loopback(self,result,*,name='run'):
        root=self.root/name;root.mkdir();(root/'fixture.mp4').write_bytes(b'synthetic bytes; no decoded video')
        def evaluate(*args):
            if isinstance(result,Exception):raise result
            return dict(result)
        evaluator=SimpleNamespace(sources={'fixture':{}},clips={'fixture':{'video_file':'fixture.mp4'}},source_root=root,evaluate=evaluate)
        timing=ServerTiming(root/'server.jsonl');service=LabService(TimedEvaluator(evaluator,timing),source_order=['fixture'])
        server=create_server(service,timing=timing);thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.01),daemon=True);thread.start()
        client=TimedLocalClient(server.server_port,root/'client.jsonl')
        frames=[dict(t_ms=i,lm=[[.1+j*.01,.2+j*.01] for j in range(21)]) for i in range(3)]
        try:
            self.assertEqual(client.post('/api/session',{})[0],200)
            attempt=measure_attempt(client,lambda media:frames)
        finally:
            client.close();server.shutdown();server.server_close();thread.join(timeout=3)
            self.assertTrue(timing.wait_idle());timing.close()
        server_raw=(root/'server.jsonl').read_bytes();client_raw=(root/'client.jsonl').read_bytes()
        joined=reconcile(client_raw,server_raw)
        self.assertEqual(joined['unmatched_server_requests_n'],0)
        self.assertTrue(all(row['server'] is not None for row in joined['requests']))
        self.assertNotIn(client.cookie.encode(),server_raw+client_raw)
        self.assertNotIn(b'"lm"',server_raw+client_raw)
        self.assertEqual(recover_client(client_raw)['state'],'COMPLETED')
        return attempt,joined,service,server_raw,client_raw

    def test_http_score_gate_grant_action_and_repeat_are_separate(self):
        result,joined,service,server_raw,client_raw=self.loopback(dict(gate_pass=True,score_pass=True,score={'captcha':1}))
        self.assertTrue(result['server_grant_issued']);self.assertTrue(result['protected_action_allowed'])
        self.assertFalse(result['repeat_action_allowed']);self.assertEqual(service.protected_actions,1)
        self.assertIsNone(result['first_pixel_presented_ns'])
        self.assertGreaterEqual(result['issue_to_action_body_received_ns'],result['media_body_received_elapsed_ns'])
        self.assertFalse(joined['server_clock_subtraction_performed'])
        submit=next(row for row in joined['requests'] if row['client']['route']=='/api/submit')
        names=[p['name'] for p in submit['server']['phases']]
        self.assertIn('submit',names);self.assertIn('evaluator',names);self.assertIn('response_write',names)
        events=[json.loads(line) for line in client_raw.splitlines()]
        for n in range(1,len(events)):self.assertEqual(recover_client(encoded(events[:n]))['state'],'INTERRUPTED')
        next(e for e in events if e['kind']=='request_finished')['elapsed_ns']=-1
        self.assertEqual(recover_client(encoded(events))['state'],'LOG_CORRUPT')

    def test_http_score_reject_and_gate_reject_never_become_server_allow(self):
        for i,(gate,score) in enumerate(((True,False),(False,True))):
            result,_,service,_,_=self.loopback(dict(gate_pass=gate,score_pass=score,score={'captcha':.8}),name=str(i))
            self.assertEqual((result['gate_pass'],result['score_pass']),(gate,score))
            self.assertFalse(result['server_grant_issued']);self.assertIsNone(result['protected_action_allowed'])
            self.assertIsNone(result['issue_to_action_body_received_ns']);self.assertEqual(service.protected_actions,0)

    def test_http_evaluation_error_is_503_with_failed_evaluator_stage(self):
        result,joined,service,_,_=self.loopback(TimeoutError('private error details'))
        self.assertEqual(result['submit_http_status'],503);self.assertFalse(result['server_grant_issued'])
        self.assertEqual(service.protected_actions,0)
        row=next(r for r in joined['requests'] if r['client']['route']=='/api/submit')
        phase=next(p for p in row['server']['phases'] if p['name']=='evaluator')
        self.assertEqual(phase['outcome'],'ERROR');self.assertEqual(row['server']['http_status'],503)


if __name__=='__main__':unittest.main()
