"""Sequential loopback client with its own monotonic timing domain."""
from http.client import HTTPConnection
from http.cookies import SimpleCookie
import json
import re
import secrets
import time

from .http_timing import ROUTES
from .http_timing import recover as recover_server
from .journal import _private
from .stage_profile import JsonlSink


class TimedLocalClient:
    def __init__(self,port,path,*,timeout_seconds=5):
        if type(port) is not int or not 1<=port<=65535:raise ValueError('Loopback port required')
        if type(timeout_seconds) not in (int,float) or not 0<timeout_seconds<=20:raise ValueError('Bounded request timeout required')
        self.port=port;self.timeout=timeout_seconds;self.cookie=None;self.events=[];self.closed=False;self.broken=False
        self.last_body_received_ns=None;self.sink=JsonlSink(_private(path))
        try:self.emit('client_timing_started',schema_version=1,clock_domain='client_monotonic')
        except BaseException:self.sink.close();raise

    def emit(self,kind,**fields):
        if self.closed or self.broken:raise RuntimeError('Client timing closed/failed')
        event=dict(event_id=len(self.events),at_ns=time.perf_counter_ns(),kind=kind,**fields)
        try:self.sink(event)
        except BaseException:self.broken=True;raise
        self.events.append(event);return event

    def request(self,method,path,payload=None):
        media=bool(re.fullmatch(r'/media/[A-Za-z0-9_-]{1,128}',path))
        route='/media/:challenge' if media else path
        if method not in ('GET','POST') or route not in ROUTES or route=='other':raise ValueError('Allowlisted local request required')
        if method=='GET' and payload is not None:raise ValueError('GET body unsupported')
        correlation=secrets.token_hex(16)
        started=self.emit('request_started',correlation=correlation,method=method,route=route)['at_ns']
        status=None;body_received=None;size=None;outcome='OK';error_type=None
        connection=HTTPConnection('127.0.0.1',self.port,timeout=self.timeout)
        try:
            body=None if method=='GET' else json.dumps(payload,allow_nan=False).encode('utf-8')
            headers={'Host':f'127.0.0.1:{self.port}','X-Lab-Correlation':correlation}
            if body is not None:headers['Content-Type']='application/json'
            if self.cookie is not None:headers['Cookie']=self.cookie
            connection.request(method,path,body=body,headers=headers)
            response=connection.getresponse();status=response.status;raw=response.read()
            body_received=time.perf_counter_ns();self.last_body_received_ns=body_received;size=len(raw)
            if response.getheader('Set-Cookie'):
                jar=SimpleCookie();jar.load(response.getheader('Set-Cookie'))
                if 'g4_session' in jar:self.cookie='g4_session='+jar['g4_session'].value
            result=raw if media else json.loads(raw)
            return status,result
        except BaseException as error:
            outcome='ABORTED' if isinstance(error,KeyboardInterrupt) else 'ERROR';error_type=type(error).__name__
            raise
        finally:
            connection.close()
            now=time.perf_counter_ns()
            self.emit('request_finished',correlation=correlation,elapsed_ns=now-started,
                      measured_end_ns=now,http_status=status,body_received_ns=body_received,
                      response_bytes_n=size,outcome=outcome,error_type=error_type)

    def post(self,path,payload):return self.request('POST',path,payload)
    def media(self,path):return self.request('GET',path)

    def close(self):
        if self.closed:raise RuntimeError('Client timing already closed')
        try:
            if not self.broken:self.emit('client_timing_finished')
        finally:self.closed=True;self.sink.close()


def measure_attempt(client,frame_provider):
    """Issue→media receipt→provided replay→submit→one action; no rendered UI.

    Provider sees received media bytes only. Its own prior knowledge is an
    experiment input declaration, not something this API can authenticate.
    Caller creates a session before this attempt. Repeat consumption is timed
    separately from the first action response.
    """
    start=time.perf_counter_ns()
    result=dict(score_pass=None,gate_pass=None,validation_pass=None,server_grant_issued=False,
                protected_action_allowed=None,repeat_action_allowed=None,
                media_body_received_elapsed_ns=None,issue_to_action_body_received_ns=None,
                first_pixel_presented_ns=None,endpoint='new_loopback_offline_replay_not_camera_or_historical_auth')
    result['challenge_http_status'],challenge=client.post('/api/challenge',{})
    if result['challenge_http_status']!=200:return result
    result['media_http_status'],media=client.media(challenge['media_url'])
    if result['media_http_status']!=200:return result
    result['media_body_received_elapsed_ns']=client.last_body_received_ns-start
    frames=frame_provider(media)
    result['submit_http_status'],evaluation=client.post('/api/submit',dict(challenge_id=challenge['challenge_id'],frames=frames))
    result.update({key:evaluation.get(key) for key in ('score_pass','gate_pass','validation_pass')})
    # Preserve the actual returned score/gate diagnostics only in private output.
    result['evaluation']={key:value for key,value in evaluation.items() if key!='grant_id'}
    grant=evaluation.get('grant_id');result['server_grant_issued']=bool(grant)
    if not grant:return result
    result['action_http_status'],action=client.post('/api/protected_action',dict(grant_id=grant))
    result['issue_to_action_body_received_ns']=client.last_body_received_ns-start
    result['protected_action_allowed']=action.get('protected_action_allowed')
    result['repeat_action_http_status'],repeat=client.post('/api/protected_action',dict(grant_id=grant))
    result['repeat_action_allowed']=repeat.get('protected_action_allowed')
    return result


def recover(raw):
    if not raw:return dict(state='LOG_LOST',requests=[])
    active=None;seen=set();rows=[];last=-1;terminal=False;count=0
    try:
        for index,line in enumerate(raw.splitlines(keepends=True)):
            if not line.endswith(b'\n'):
                if terminal:raise ValueError('Tail after terminal')
                break
            e=json.loads(line)
            if (terminal or type(e['event_id']) is not int or e['event_id']!=index or type(e['at_ns']) is not int
                    or e['at_ns']<0 or e['at_ns']<last):raise ValueError('Clock/event sequence')
            last=e['at_ns'];kind=e['kind'];base={'event_id','kind','at_ns'}
            if index==0:
                if kind!='client_timing_started' or type(e['schema_version']) is not int or e['schema_version']!=1 or e['clock_domain']!='client_monotonic':raise ValueError('Header')
                allowed=base|{'schema_version','clock_domain'}
            elif kind=='request_started':
                cid=e['correlation']
                if (active is not None or cid in seen or not isinstance(cid,str) or not re.fullmatch(r'[a-f0-9]{32}',cid)
                        or e['method'] not in ('GET','POST') or e['route'] not in ROUTES):raise ValueError('Request metadata')
                seen.add(cid);active=dict(correlation=cid,method=e['method'],route=e['route'],started_ns=last,
                                         elapsed_ns=None,http_status=None,outcome=None,body_received_ns=None)
                rows.append(active)
                allowed=base|{'correlation','method','route'}
            elif kind=='request_finished':
                if (active is None or e['correlation']!=active['correlation'] or type(e['elapsed_ns']) is not int
                        or type(e['measured_end_ns']) is not int or not active['started_ns']<=e['measured_end_ns']<=last
                        or e['elapsed_ns']!=e['measured_end_ns']-active['started_ns']):raise ValueError('Request duration')
                status=e['http_status'];body=e['body_received_ns'];size=e['response_bytes_n']
                if status is not None and (type(status) is not int or not 100<=status<=599):raise ValueError('HTTP status')
                if body is not None and (type(body) is not int or not active['started_ns']<=body<=e['measured_end_ns']):raise ValueError('Body receipt time')
                if (body is None)!=(size is None) or (size is not None and (type(size) is not int or size<0)):raise ValueError('Response bytes')
                if (e['outcome'] not in ('OK','ERROR','ABORTED') or (e['outcome']=='OK')!=(e['error_type'] is None)
                        or (e['error_type'] is not None and not isinstance(e['error_type'],str))):raise ValueError('Outcome')
                if e['outcome']=='OK' and (body is None or status is None):raise ValueError('Unknown successful receipt')
                active.update(elapsed_ns=e['elapsed_ns'],http_status=status,outcome=e['outcome'],body_received_ns=body);active=None
                allowed=base|{'correlation','elapsed_ns','measured_end_ns','http_status','body_received_ns','response_bytes_n','outcome','error_type'}
            elif kind=='client_timing_finished':
                if active is not None:raise ValueError('Active request at terminal')
                terminal=True
                allowed=base
            else:raise ValueError('Unexpected event')
            if set(e)!=allowed:raise ValueError('Unexpected metadata fields')
            count+=1
    except (ValueError,KeyError,TypeError,UnicodeError):return dict(state='LOG_CORRUPT',valid_events_n=count,requests=[])
    return dict(state='COMPLETED' if terminal else 'INTERRUPTED',valid_events_n=count,
                clock_domain='client_monotonic',requests=rows,server_clock_subtraction_performed=False)


def reconcile(client_raw,server_raw):
    client,server=recover(client_raw),recover_server(server_raw)
    if client['state']!='COMPLETED' or server['state']!='COMPLETED':
        raise ValueError('Complete client/server traces required for final reconciliation')
    by_id={}
    for row in server['requests']:
        key=row['correlation']
        if key is not None:
            if key in by_id:raise ValueError('Ambiguous client/server correlation')
            by_id[key]=row
    rows=[];matched=set()
    for row in client['requests']:
        remote=by_id.get(row['correlation'])
        if remote is not None:
            if (row['method'],row['route'])!=(remote['method'],remote['route']):raise ValueError('Correlated route differs')
            matched.add(row['correlation'])
        rows.append(dict(client=row,server=remote))
    return dict(client_clock_domain=client['clock_domain'],server_clock_domain=server['clock_domain'],
                requests=rows,unmatched_server_requests_n=len(server['requests'])-len(matched),
                server_clock_subtraction_performed=False,authentication_or_first_pixel_proven=False)
