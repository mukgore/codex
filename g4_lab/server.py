"""New loopback G4 server, using the owned HTML scorer on submitted replay data.

This is an experiment, not a historical endpoint or trusted camera SDK. A valid
stored-answer replay can pass. No client-supplied passed/score flag is trusted.
"""
from __future__ import annotations
import argparse
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import secrets
import socket
import threading
import time
from urllib.parse import urlsplit
import numpy as np
from .actual import ActualEvaluator
from .validation import validate_frames

MAX_BODY_BYTES=2_000_000  # local resource bound, not a performance target
CHALLENGE_TTL_SECONDS=60.0  # local test setting only


class LabCapacityError(RuntimeError):
    """Fail closed when the bounded in-memory lab cannot accept more state."""

PAGE='''<!doctype html><html lang="en"><meta charset="utf-8"><title>G4 local replay lab</title><h1>Owned CAPTCHA: local replay evaluation</h1><p>New experimental server. Offline landmarks only; no camera, CDN or external upload. Not a historical authentication service.</p><button id="issue">Issue local challenge</button><video id="video" controls width="480"></video><p>Paste an approved local replay array [{t_ms,lm}] below.</p><textarea id="frames" rows="10" cols="85"></textarea><p><button id="submit">Evaluate replay</button><button id="consume">Consume test action once</button></p><pre id="result"></pre><script src="/app.js"></script></html>'''
APP='''let challenge,grant; const out=x=>document.getElementById('result').textContent=JSON.stringify(x,null,2); async function post(path,body={}){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return r.json();} document.getElementById('issue').onclick=async()=>{await post('/api/session');challenge=await post('/api/challenge');document.getElementById('video').src=challenge.media_url;out(challenge);};document.getElementById('submit').onclick=async()=>{const r=await post('/api/submit',{challenge_id:challenge.challenge_id,frames:JSON.parse(document.getElementById('frames').value)});grant=r.grant_id;out(r);};document.getElementById('consume').onclick=async()=>out(await post('/api/protected_action',{grant_id:grant}));'''

class LabService:
    def __init__(self,evaluator:ActualEvaluator,*,clock=time.monotonic,ttl=CHALLENGE_TTL_SECONDS,stationary_filter=False,source_order=None,
                 session_ttl=300,max_sessions=1024,max_challenges=4096,max_grants=4096,max_events=10000, max_issues_per_session=None):
        for value in (ttl,session_ttl):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<value<=3600:
                raise ValueError('Bounded positive finite lifetime required')
        for value in (max_sessions,max_challenges,max_grants,max_events):
            if type(value) is not int or not 1<=value<=100000:
                raise ValueError('Bounded positive integer capacity required')
        if max_issues_per_session is not None and (
                type(max_issues_per_session) is not int or not 1 <= max_issues_per_session <= 100000):
            raise ValueError('Bounded positive integer session issue budget required')
        self.max_issues_per_session = max_issues_per_session
        self.evaluator=evaluator
        self.clock=clock;self.ttl=ttl;self.stationary_filter=stationary_filter
        self.session_ttl=session_ttl
        self.max_sessions=max_sessions;self.max_challenges=max_challenges;self.max_grants=max_grants;self.max_events=max_events
        self.lock=threading.RLock();self.sessions={};self.challenges={};self.grants={};self.events=[];self.event_index=0
        self.source_order=list(source_order) if source_order else None;self.issued=0;self.protected_actions=0

    def log(self,kind,**fields):
        self.event_index+=1
        self.events.append({'event_index':self.event_index,'kind':kind,**fields})
        del self.events[:-self.max_events]

    def _purge(self):
        # Called while holding the service lock. Event retention is separately bounded.
        now=self.clock()
        for token,session in list(self.sessions.items()):
            if now>=session['expires']:del self.sessions[token]
        for records in (self.challenges,self.grants):
            for token,record in list(records.items()):
                if now>=record['expires'] or record['session'] not in self.sessions:del records[token]

    def session(self):
        with self.lock:
            self._purge()
            if len(self.sessions)>=self.max_sessions:raise LabCapacityError('session_capacity')
            session = secrets.token_urlsafe(24)
            self.sessions[session] = {'expires': self.clock() + self.session_ttl, 'issued': 0}
            return session

    def issue(self,session):
        with self.lock:
            self._purge()
            if session not in self.sessions: raise PermissionError('session_required')
            state = self.sessions[session]
            if self.max_issues_per_session is not None and state['issued'] >= self.max_issues_per_session:
                raise LabCapacityError('session_issue_budget')
            if len(self.challenges)>=self.max_challenges:raise LabCapacityError('challenge_capacity')
            keys=list(self.evaluator.sources)
            key=self.source_order[self.issued%len(self.source_order)] if self.source_order else secrets.choice(keys)
            self.issued+=1
            token=secrets.token_urlsafe(24)
            self.challenges[token]={'session':session,'key':key,'expires':min(self.clock()+self.ttl,state['expires']),'used':False}
            state['issued'] += 1
            self.log('issued',source_family=key)
            return {'challenge_id':token,'media_url':'/media/'+token,'expires_in_s':self.challenges[token]['expires']-self.clock(),'input_channel':'offline_landmark_replay'}

    def submit(self,session,payload):
        with self.lock:
            self._purge()
            if not isinstance(payload,dict) or set(payload)!={'challenge_id','frames'}: raise ValueError('unexpected_submission_schema')
            token=payload['challenge_id']
            if not isinstance(token,str) or len(token)>128: raise ValueError('invalid_challenge_id')
            record=self.challenges.get(token)
            if session not in self.sessions or record is None or record['session']!=session: raise PermissionError('challenge_session_mismatch')
            if record['used'] or self.clock()>=record['expires']: raise PermissionError('challenge_used_or_expired')
            if len(self.grants)>=self.max_grants:raise LabCapacityError('grant_capacity')
            record['used']=True
            try:
                frames=validate_frames(payload['frames'])
            except ValueError:
                self.log('evaluated',source_family=record['key'],validation_pass=False,gate_pass=None,score_pass=None,protected_action_allowed=False)
                raise
            result=self.evaluator.evaluate(record['key'],frames)
            stationary=False
            detected=[f['lm'] for f in frames if f['lm'] is not None]
            if detected:
                arr=np.asarray(detected)
                stationary=bool(np.all(arr==arr[0]))
            passed=result['gate_pass'] and result['score_pass'] and not(self.stationary_filter and stationary)
            reply={**result,'validation_pass':True,'stationary_filter_reject':bool(self.stationary_filter and stationary),'grant_id':None,'protected_action_allowed':False}
            if passed:
                grant=secrets.token_urlsafe(24)
                self.grants[grant]={'session':session,'expires':record['expires'],'used':False,'key':record['key']}
                reply['grant_id']=grant
            self.log('evaluated',source_family=record['key'],validation_pass=True,gate_pass=result['gate_pass'],score_pass=result['score_pass'],score=result['score']['captcha'],grant_issued=passed,protected_action_allowed=False)
            return reply

    def consume(self,session,payload):
        with self.lock:
            self._purge()
            if not isinstance(payload,dict) or set(payload)!={'grant_id'} or not isinstance(payload['grant_id'],str): raise ValueError('invalid_grant')
            grant=self.grants.get(payload['grant_id'])
            allowed=bool(grant and session in self.sessions and grant['session']==session and not grant['used'] and self.clock()<grant['expires'])
            if allowed:
                grant['used']=True;self.protected_actions+=1
            self.log('protected_action',protected_action_allowed=allowed)
            return {'protected_action_allowed':allowed,'protected_action_counter':self.protected_actions}

    def media(self,session,token):
        with self.lock:
            self._purge()
            record=self.challenges.get(token)
            if not record or record['session']!=session or self.clock()>=record['expires']: raise PermissionError('media_denied')
            clip=self.evaluator.clips[record['key']]
            path=(self.evaluator.source_root/clip['video_file']).resolve()
            if not path.is_relative_to(self.evaluator.source_root) or path.suffix.lower()!='.mp4': raise PermissionError('unsafe_media')
            return path

def handler_for(service):
    class Handler(BaseHTTPRequestHandler):
        server_version='G4LocalLab/1'
        def handle(self):
            try:super().handle()
            except (OSError,TimeoutError):pass  # deadline/client disconnect; no tokens in logs
        def log_message(self,*args): pass  # no request bodies/tokens in console logs
        def session_cookie(self):
            jar=cookies.SimpleCookie()
            try: jar.load(self.headers.get('Cookie',''))
            except cookies.CookieError: return None
            return jar['g4_session'].value if 'g4_session' in jar else None
        def allowed_host(self):
            return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
        def send(self,status,data,ctype='application/json',cookie=None):
            raw=data if isinstance(data,bytes) else (data.encode('utf-8') if isinstance(data,str) else json.dumps(data,allow_nan=False).encode('utf-8'))
            self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; media-src 'self'; connect-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if cookie:self.send_header('Set-Cookie',f'g4_session={cookie}; HttpOnly; SameSite=Strict; Path=/')
            self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if not self.allowed_host(): return self.send(403,{'error':'host_denied'})
            try:
                path=urlsplit(self.path).path
                if path=='/': return self.send(200,PAGE,'text/html; charset=utf-8')
                if path=='/app.js': return self.send(200,APP,'text/javascript; charset=utf-8')
                if path.startswith('/media/'):
                    media=service.media(self.session_cookie(),path[len('/media/'):])
                    return self.send(200,media.read_bytes(),'video/mp4')
                return self.send(404,{'error':'not_found'})
            except PermissionError as exc:return self.send(403,{'error':str(exc)})
        def do_POST(self):
            if not self.allowed_host(): return self.send(403,{'error':'host_denied'})
            origin=self.headers.get('Origin')
            if origin and origin!=f'http://{self.headers.get("Host")}':return self.send(403,{'error':'origin_denied'})
            try:
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('json_required')
                length=int(self.headers.get('Content-Length','-1'))
                if not 0<=length<=MAX_BODY_BYTES:raise ValueError('body_limit')
                payload=json.loads(self.rfile.read(length),parse_constant=lambda s:(_ for _ in ()).throw(ValueError('nonfinite_json')))
                path=urlsplit(self.path).path;session=self.session_cookie()
                if path=='/api/session':
                    if payload!={}:raise ValueError('session_schema')
                    session=service.session();return self.send(200,{'session_created':True},cookie=session)
                if path=='/api/challenge':
                    if payload!={}:raise ValueError('challenge_schema')
                    return self.send(200,service.issue(session))
                if path=='/api/submit':return self.send(200,service.submit(session,payload))
                if path=='/api/protected_action':return self.send(200,service.consume(session,payload))
                return self.send(404,{'error':'not_found'})
            except (ValueError,TypeError,UnicodeError,RecursionError):return self.send(400,{'error':'invalid_request'})
            except PermissionError as exc:return self.send(403,{'error':str(exc)})
            except LabCapacityError:return self.send(429,{'error':'local_capacity_exceeded'})
    return Handler

class BoundedLabHTTPServer(ThreadingHTTPServer):
    """Local connection budget; does not interrupt CPU work or authenticate callers."""
    daemon_threads=True

    def __init__(self,address,handler,*,max_connections,request_timeout):
        if type(max_connections) is not int or not 1<=max_connections<=256:
            raise ValueError('Connection budget must be an integer from 1 to 256')
        if (type(request_timeout) not in (int,float) or not math.isfinite(request_timeout) or
                not 0<request_timeout<=60):
            raise ValueError('Connection deadline must be finite and at most 60 seconds')
        self.connection_slots=threading.BoundedSemaphore(max_connections)
        self.request_timeout=request_timeout
        super().__init__(address,handler)

    def process_request(self,request,client_address):
        request.settimeout(self.request_timeout)
        if not self.connection_slots.acquire(blocking=False):
            try:
                request.settimeout(.05)
                request.sendall(b'HTTP/1.0 503 Service Unavailable\r\nConnection: close\r\nContent-Length: 0\r\nCache-Control: no-store\r\n\r\n')
            except OSError:pass
            finally:self.shutdown_request(request)
            return
        try:super().process_request(request,client_address)
        except BaseException:
            self.connection_slots.release()
            raise

    @staticmethod
    def expire_connection(request):
        try:request.shutdown(socket.SHUT_RDWR)
        except OSError:pass

    def process_request_thread(self,request,client_address):
        deadline=threading.Timer(self.request_timeout,self.expire_connection,args=(request,))
        deadline.daemon=True
        try:
            deadline.start()
            super().process_request_thread(request,client_address)
        finally:
            deadline.cancel()
            self.connection_slots.release()


def create_server(service,*,max_connections=16,request_timeout=20):
    return BoundedLabHTTPServer(('127.0.0.1',0),handler_for(service),
                               max_connections=max_connections,request_timeout=request_timeout)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--max-issues-per-session', type=int, default=64)
    parser.add_argument('--max-connections',type=int,default=16)
    parser.add_argument('--request-timeout',type=float,default=20)
    args = parser.parse_args()
    with ActualEvaluator(args.source_root) as evaluator:
        service = LabService(evaluator, max_issues_per_session=args.max_issues_per_session)
        server = create_server(service,max_connections=args.max_connections,request_timeout=args.request_timeout)
        print(f'Local replay UI: http://127.0.0.1:{server.server_port}',flush=True)
        try:server.serve_forever()
        finally:server.server_close()
if __name__=='__main__':main()
