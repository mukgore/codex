from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
import json
from types import SimpleNamespace
import threading
import unittest

from g4_lab.server import LabCapacityError, LabService, create_server


class LabCapacityTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.evaluator = SimpleNamespace(sources={'fixture': {}}, evaluate=lambda *args: {
            'gate_pass': True, 'score_pass': True, 'score': {'captcha': 1}})

    def service(self, **kwargs):
        return LabService(self.evaluator, clock=lambda: self.now, **kwargs)

    def test_invalid_capacity_and_lifetime(self):
        for kwargs in [{'max_events':0},{'max_sessions':True},{'ttl':float('nan')},
                       {'session_ttl':float('inf')},{'max_grants':100001}]:
            with self.assertRaises(ValueError):self.service(**kwargs)

    def test_session_limit_is_atomic_and_expired_slots_recover(self):
        service = self.service(max_sessions=2, session_ttl=5)
        def create(_):
            try:return service.session()
            except LabCapacityError:return None
        with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(create,range(8)))
        self.assertEqual(sum(x is not None for x in results),2)
        self.now=5
        service.session()
        self.assertEqual(len(service.sessions),1)

    def test_challenge_limit_recovers_after_expiry(self):
        service=self.service(max_challenges=1,ttl=5)
        session=service.session();service.issue(session)
        with self.assertRaises(LabCapacityError):service.issue(session)
        self.now=5;service.issue(session)
        self.assertEqual(len(service.challenges),1)

    def test_child_lifetime_cannot_outlive_session(self):
        service=self.service(session_ttl=3,ttl=60)
        session=service.session();challenge=service.issue(session)
        self.assertEqual(challenge['expires_in_s'],3)
        self.now=3
        with self.assertRaises(PermissionError):service.issue(session)
        self.assertEqual(service.challenges,{})

    def test_grant_limit_does_not_consume_next_challenge(self):
        service=self.service(max_grants=1)
        session=service.session()
        frames=[{'t_ms':i,'lm':[[0.1+j*.01,0.2+j*.01] for j in range(21)]} for i in range(3)]
        one=service.issue(session)
        result=service.submit(session,{'challenge_id':one['challenge_id'],'frames':frames})
        two=service.issue(session)
        with self.assertRaises(LabCapacityError):service.submit(session,{'challenge_id':two['challenge_id'],'frames':frames})
        self.assertFalse(service.challenges[two['challenge_id']]['used'])
        self.now=60
        self.assertFalse(service.consume(session,{'grant_id':result['grant_id']})['protected_action_allowed'])
        self.assertEqual(service.grants,{})

    def test_event_retention_preserves_monotonic_indices(self):
        service=self.service(max_events=2)
        for _ in range(5):service.consume(None,{'grant_id':'unknown'})
        self.assertEqual([x['event_index'] for x in service.events],[4,5])

    def test_http_capacity_returns_429_without_allocating_more_state(self):
        service=self.service(max_sessions=1)
        server=create_server(service)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for expected in (200,429):
                conn=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
                try:
                    conn.request('POST','/api/session',body=b'{}',headers={'Content-Type':'application/json'})
                    response=conn.getresponse();body=json.loads(response.read())
                    self.assertEqual(response.status,expected)
                    if expected==429:self.assertEqual(body['error'],'local_capacity_exceeded')
                finally:conn.close()
            self.assertEqual(len(service.sessions),1)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=5)


if __name__ == '__main__':unittest.main()
