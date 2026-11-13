from http.client import HTTPConnection
import json
import threading
import time
from types import SimpleNamespace
import unittest

from g4_lab.server import LabService,LabCapacityError,LabEvaluationError,create_server


class LabEvaluationFailureTests(unittest.TestCase):
    def service(self,**kwargs):
        self.now=0
        evaluator=SimpleNamespace(sources={'fixture':{}},evaluate=lambda *_: {
            'gate_pass':True,'score_pass':True,'score':{'captcha':1}})
        return LabService(evaluator,clock=lambda:self.now,**kwargs)

    def submission(self,service):
        session=service.session();challenge=service.issue(session)
        frames=[{'t_ms':i,'lm':[[.1+j*.01,.2+j*.01] for j in range(21)]} for i in range(3)]
        return session,{'challenge_id':challenge['challenge_id'],'frames':frames}

    def test_all_state_operations_stop_waiting_without_mutating_state(self):
        service=self.service(state_wait_timeout=.04)
        session,payload=self.submission(service)
        held=threading.Event();release=threading.Event()
        def occupy():
            with service.lock:held.set();release.wait(3)
        thread=threading.Thread(target=occupy);thread.start();self.assertTrue(held.wait(1))
        try:
            operations=(service.session,lambda:service.issue(session),lambda:service.submit(session,payload),
                        lambda:service.consume(session,{'grant_id':'missing'}),
                        lambda:service.media(session,payload['challenge_id']))
            for operation in operations:
                before=time.monotonic()
                with self.assertRaises(LabCapacityError):operation()
                self.assertLess(time.monotonic()-before,1)
            self.assertFalse(service.challenges[payload['challenge_id']]['used'])
            self.assertEqual(len(service.sessions),1);self.assertEqual(service.grants,{})
        finally:release.set();thread.join(timeout=2)
        self.assertIsNotNone(service.session())

    def test_evaluation_error_consumes_attempt_without_grant(self):
        for error in (TimeoutError('private detail'),RuntimeError('private detail')):
            service=self.service();session,payload=self.submission(service)
            def fail(*_):raise error
            service.evaluator.evaluate=fail
            with self.assertRaisesRegex(LabEvaluationError,'evaluator_unavailable'):
                service.submit(session,payload)
            self.assertEqual(service.grants,{})
            self.assertTrue(service.challenges[payload['challenge_id']]['used'])
            self.assertNotIn('private detail',json.dumps(service.events))
            self.assertIsNone(service.events[-1]['score_pass'])
            with self.assertRaises(PermissionError):service.submit(session,payload)

    def test_result_arriving_after_expiry_cannot_create_a_grant(self):
        service=self.service(ttl=1);session,payload=self.submission(service)
        original=service.evaluator.evaluate
        def late(*args):self.now=1;return original(*args)
        service.evaluator.evaluate=late
        with self.assertRaisesRegex(PermissionError,'expired_during'):service.submit(session,payload)
        self.assertEqual(service.grants,{})
        self.assertFalse(service.events[-1]['grant_issued'])

    def test_http_returns_sanitized_unavailability(self):
        service=self.service();session,payload=self.submission(service)
        def fail(*_):raise TimeoutError('private detail')
        service.evaluator.evaluate=fail
        server=create_server(service);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            conn=HTTPConnection(*server.server_address,timeout=3)
            try:
                conn.request('POST','/api/submit',json.dumps(payload),
                             {'Content-Type':'application/json','Cookie':'g4_session='+session})
                response=conn.getresponse();body=response.read()
                self.assertEqual(response.status,503)
                self.assertEqual(json.loads(body),{'error':'evaluator_unavailable'})
            finally:conn.close()
        finally:server.shutdown();server.server_close();thread.join(timeout=3)

    def test_invalid_state_wait_budget(self):
        for value in (True,0,float('nan'),float('inf'),21,'1'):
            with self.subTest(value=value),self.assertRaises(ValueError):self.service(state_wait_timeout=value)


if __name__=='__main__':unittest.main()
