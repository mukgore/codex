from http.client import HTTPConnection
import socket
import threading
import time
from types import SimpleNamespace
import unittest

from g4_lab.server import LabService,create_server


class LabConnectionTests(unittest.TestCase):
    def assert_socket_closed(self,connection):
        try:self.assertEqual(connection.recv(1024),b'')
        except (ConnectionResetError,ConnectionAbortedError):pass  # Windows shutdown forms.

    def start_server(self,**kwargs):
        service=LabService(SimpleNamespace(sources={'synthetic':{}}))
        server=create_server(service,**kwargs)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def cleanup():
            server.shutdown();server.server_close();thread.join(timeout=5)
        self.addCleanup(cleanup)
        return service,server

    def wait_for(self,predicate):
        end=time.monotonic()+3
        while time.monotonic()<end:
            if predicate():return
            time.sleep(.01)
        self.fail('Connection state did not reach the expected bound')

    def test_invalid_connection_budgets(self):
        for kwargs in ({'max_connections':0},{'max_connections':True},{'max_connections':257},
                       {'request_timeout':True},{'request_timeout':float('nan')},
                       {'request_timeout':0},{'request_timeout':61}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                create_server(None,**kwargs)

    def test_slow_body_saturates_bound_without_creating_session_then_recovers(self):
        service,server=self.start_server(max_connections=1,request_timeout=2)
        entered=threading.Event();original=server.finish_request
        def entered_handler(*args):entered.set();return original(*args)
        server.finish_request=entered_handler
        slow=socket.create_connection(server.server_address,timeout=3);self.addCleanup(slow.close)
        slow.sendall((f'POST /api/session HTTP/1.0\r\nHost: 127.0.0.1:{server.server_port}\r\n'
                      'Content-Type: application/json\r\nContent-Length: 2\r\n\r\n{').encode())
        self.assertTrue(entered.wait(2))
        conn=socket.create_connection(server.server_address,timeout=3)
        try:
            # A saturated listener may close before a client finishes sending.
            # On Windows that produces a reset rather than a readable 503.
            try:
                conn.sendall((f'POST /api/session HTTP/1.0\r\nHost: 127.0.0.1:{server.server_port}\r\n'
                              'Content-Type: application/json\r\nContent-Length: 2\r\n\r\n{}').encode())
                reply=conn.recv(1024)
                self.assertTrue(not reply or reply.startswith(b'HTTP/1.0 503'))
            except ConnectionError:pass
            self.assertEqual(service.sessions,{})
        finally:conn.close()
        # A hard deadline closes the incomplete body and releases the only slot.
        self.assert_socket_closed(slow)
        def recovered():
            if not server.connection_slots.acquire(False):return False
            server.connection_slots.release();return True
        self.wait_for(recovered)
        conn=HTTPConnection(*server.server_address,timeout=3)
        try:
            conn.request('POST','/api/session',body=b'{}',headers={'Content-Type':'application/json'})
            response=conn.getresponse();response.read();self.assertEqual(response.status,200)
            self.assertEqual(len(service.sessions),1)
        finally:conn.close()

    def test_total_deadline_expires_even_with_continuous_header_bytes(self):
        _,server=self.start_server(max_connections=1,request_timeout=.3)
        expired=threading.Event();original=server.expire_connection
        def expire(request):original(request);expired.set()
        server.expire_connection=expire
        slow=socket.create_connection(server.server_address,timeout=2);self.addCleanup(slow.close)
        slow.sendall(b'POST /api/session HTTP/1.0\r\nX-Slow: ')
        stopped=threading.Event()
        def trickle():
            while not stopped.wait(.03):
                try:slow.sendall(b'a')
                except OSError:return
        thread=threading.Thread(target=trickle,daemon=True);thread.start()
        try:self.assertTrue(expired.wait(2))
        finally:stopped.set();thread.join(timeout=2)
        self.assert_socket_closed(slow)


if __name__=='__main__':unittest.main()
