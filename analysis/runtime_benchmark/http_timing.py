"""Optional private server timing. Inclusive stages include tracing overhead.

Clock domains are explicit. Server write completion is not client receipt or
first rendered pixel. No credentials, bodies or challenge/grant IDs are logged.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import json
import re
import secrets
import threading
import time

from .journal import _private
from .stage_profile import JsonlSink

_CURRENT = ContextVar('local_http_timing_request', default=None)
_IDENTIFIER = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
ROUTES = ('/','/app.js','/api/session','/api/challenge','/api/submit','/api/protected_action','/media/:challenge','other')


class RequestTiming:
    def __init__(self,recorder,request_id,started):
        self.recorder=recorder;self.request_id=request_id;self.started=started
        self.stack=[];self.next_phase=0;self.http_status=None;self.response_write_completed=False

    def call(self,name,operation,*args):
        if not isinstance(name,str) or not _IDENTIFIER.fullmatch(name):raise ValueError('Bounded phase name required')
        phase=self.next_phase;self.next_phase+=1
        parent=self.stack[-1] if self.stack else None;self.stack.append(phase)
        started=self.recorder.emit('phase_started',request_id=self.request_id,phase_id=phase,parent_id=parent,name=name)['at_ns']
        outcome='OK';error_type=None
        try:return operation(*args)
        except BaseException as error:
            outcome='ABORTED' if isinstance(error,KeyboardInterrupt) else 'ERROR';error_type=type(error).__name__
            raise
        finally:
            self.stack.pop()
            self.recorder.emit('phase_finished',started=started,request_id=self.request_id,
                               phase_id=phase,outcome=outcome,error_type=error_type)


class ServerTiming:
    def __init__(self,path,*,clock=None):
        self.lock=threading.Lock();self.idle=threading.Condition(self.lock);self.clock=clock or time.perf_counter_ns
        self.clock_role='actual_monotonic' if clock is None else 'injected_fixture'
        self.sink=JsonlSink(_private(path));self.events=[];self.active=set();self.last_time=None
        self.closed=False;self.broken=False
        try:self.emit('timing_started',schema_version=1,clock_domain='server_monotonic',clock_role=self.clock_role)
        except BaseException:self.sink.close();raise

    def emit(self,kind,*,started=None,**fields):
        with self.lock:
            if self.closed or self.broken:raise RuntimeError('Timing storage closed/failed')
            now=self.clock()
            if type(now) is not int or now<0 or (self.last_time is not None and now<self.last_time):
                raise ValueError('Monotonic nonnegative integer clock required')
            self.last_time=now
            event=dict(event_id=len(self.events),kind=kind,at_ns=now,**fields)
            if started is not None:event['elapsed_ns']=now-started
            try:self.sink(event)
            except BaseException:self.broken=True;raise
            self.events.append(event);return event

    @contextmanager
    def request(self,correlation,method,route):
        if method not in ('GET','POST') or route not in ROUTES:raise ValueError('Allowlisted method/route required')
        correlation=correlation if isinstance(correlation,str) and _IDENTIFIER.fullmatch(correlation) else None
        request_id=secrets.token_hex(16)
        # Registration and close share the same lock. Do not close a live trace.
        with self.lock:
            if self.closed or self.broken:raise RuntimeError('Timing storage closed/failed')
            self.active.add(request_id)
        token=None;trace=None;outcome='OK';error_type=None
        try:
            started=self.emit('request_started',request_id=request_id,correlation=correlation,method=method,route=route)['at_ns']
            trace=RequestTiming(self,request_id,started);token=_CURRENT.set(trace)
            try:yield trace
            except BaseException as error:
                outcome='ABORTED' if isinstance(error,KeyboardInterrupt) else 'ERROR';error_type=type(error).__name__
                raise
            finally:
                self.emit('request_finished',started=started,request_id=request_id,outcome=outcome,
                          error_type=error_type,http_status=trace.http_status,
                          response_write_completed=trace.response_write_completed)
        finally:
            if token is not None:_CURRENT.reset(token)
            with self.idle:
                self.active.discard(request_id);self.idle.notify_all()

    def wait_idle(self,timeout=2):
        with self.idle:return self.idle.wait_for(lambda:not self.active,timeout=timeout)

    def close(self):
        with self.lock:
            if self.closed:raise RuntimeError('Timing already closed')
            if self.active:raise RuntimeError('Live requests prevent timing close')
            # Block new requests before releasing the lock for the terminal write.
            self.closed=True
            if self.broken:self.sink.close();return
            try:
                now=self.clock()
                if type(now) is not int or now<self.last_time:raise ValueError('Clock regression at close')
                event=dict(event_id=len(self.events),kind='timing_finished',at_ns=now)
                self.sink(event);self.events.append(event)
            finally:self.sink.close()


class TimedEvaluator:
    """Delegate unchanged evaluation, timing nested inside the HTTP submit."""
    def __init__(self,evaluator,timing):self.evaluator=evaluator;self.timing=timing
    def __getattr__(self,name):return getattr(self.evaluator,name)
    def evaluate(self,*args):
        trace=_CURRENT.get()
        if trace is None:return self.evaluator.evaluate(*args)
        if trace.recorder is not self.timing:raise RuntimeError('Evaluator/request timing mismatch')
        return trace.call('evaluator',self.evaluator.evaluate,*args)


def recover(raw):
    if not raw:return dict(state='LOG_LOST',requests=[])
    requests={};phases={};last=-1;terminal=False;events_n=0;clock_role=None
    try:
        for index,line in enumerate(raw.splitlines(keepends=True)):
            if not line.endswith(b'\n'):
                if terminal:raise ValueError('Tail after terminal')
                break
            e=json.loads(line)
            if (terminal or type(e['event_id']) is not int or e['event_id']!=index or type(e['at_ns']) is not int
                    or e['at_ns']<0 or e['at_ns']<last):raise ValueError('Event order/clock mismatch')
            last=e['at_ns'];kind=e['kind'];base={'event_id','at_ns','kind'}
            if index==0:
                if (kind!='timing_started' or type(e['schema_version']) is not int or e['schema_version']!=1
                        or e['clock_domain']!='server_monotonic' or e['clock_role'] not in ('actual_monotonic','injected_fixture')):
                    raise ValueError('Timing header required')
                allowed=base|{'schema_version','clock_domain','clock_role'};clock_role=e['clock_role']
            elif kind=='request_started':
                rid=e['request_id'];correlation=e['correlation']
                if (not isinstance(rid,str) or not _IDENTIFIER.fullmatch(rid) or rid in requests
                        or (correlation is not None and (not isinstance(correlation,str) or not _IDENTIFIER.fullmatch(correlation)))
                        or e['method'] not in ('GET','POST') or e['route'] not in ROUTES):raise ValueError('Request metadata')
                requests[rid]=dict(request_id=rid,correlation=correlation,method=e['method'],route=e['route'],
                                   started_ns=last,elapsed_ns=None,outcome=None,http_status=None,
                                   response_write_completed=False,stack=[],phases=[])
                phases[rid]={};allowed=base|{'request_id','correlation','method','route'}
            elif kind in ('phase_started','phase_finished','request_finished'):
                rid=e['request_id'];r=requests[rid]
                if r['outcome'] is not None:raise ValueError('Events after request finish')
                if kind=='phase_started':
                    pid=e['phase_id'];parent=r['stack'][-1] if r['stack'] else None
                    if (type(pid) is not int or pid!=len(phases[rid]) or e['parent_id']!=parent
                            or (e['parent_id'] is not None and type(e['parent_id']) is not int)
                            or not isinstance(e['name'],str) or not _IDENTIFIER.fullmatch(e['name'])):raise ValueError('Phase sequence/parent')
                    phases[rid][pid]=dict(phase_id=pid,parent_id=parent,name=e['name'],started_ns=last,elapsed_ns=None,outcome=None)
                    r['stack'].append(pid);allowed=base|{'request_id','phase_id','parent_id','name'}
                else:
                    if e['outcome'] not in ('OK','ERROR','ABORTED') or (e['error_type'] is not None and not isinstance(e['error_type'],str)):
                        raise ValueError('Explicit outcome required')
                    if (e['outcome']=='OK')!=(e['error_type'] is None):raise ValueError('Error outcome mismatch')
                    if kind=='phase_finished':
                        if type(e['phase_id']) is not int or not r['stack'] or e['phase_id']!=r['stack'].pop():raise ValueError('Unmatched phase')
                        p=phases[rid][e['phase_id']]
                        if type(e['elapsed_ns']) is not int or e['elapsed_ns']!=last-p['started_ns']:raise ValueError('Phase duration')
                        p.update(elapsed_ns=e['elapsed_ns'],outcome=e['outcome']);allowed=base|{'request_id','phase_id','elapsed_ns','outcome','error_type'}
                    else:
                        if r['stack'] or type(e['elapsed_ns']) is not int or e['elapsed_ns']!=last-r['started_ns']:raise ValueError('Request duration/incomplete phase')
                        status=e['http_status']
                        if (status is not None and (type(status) is not int or not 100<=status<=599)) or type(e['response_write_completed']) is not bool:
                            raise ValueError('HTTP status/response marker')
                        if e['response_write_completed'] and (status is None or not any(p['name']=='response_write' and p['outcome']=='OK' for p in phases[rid].values())):
                            raise ValueError('Response completion without write')
                        r.update(elapsed_ns=e['elapsed_ns'],outcome=e['outcome'],http_status=status,response_write_completed=e['response_write_completed'])
                        allowed=base|{'request_id','elapsed_ns','outcome','error_type','http_status','response_write_completed'}
            elif kind=='timing_finished':
                if any(r['outcome'] is None for r in requests.values()):raise ValueError('Live requests at terminal')
                terminal=True;allowed=base
            else:raise ValueError('Unknown event')
            if set(e)!=allowed:raise ValueError('Unexpected metadata fields')
            events_n+=1
    except (ValueError,KeyError,TypeError,UnicodeError):
        return dict(state='LOG_CORRUPT',valid_events_n=events_n,requests=[])
    rows=[]
    for rid,r in requests.items():
        r.pop('stack');r['phases']=list(phases[rid].values());rows.append(r)
    return dict(state='COMPLETED' if terminal else 'INTERRUPTED',valid_events_n=events_n,
                clock_domain='server_monotonic',clock_role=clock_role,requests=rows,
                durations_are_inclusive_do_not_sum_nested_stages=True,
                client_receipt_or_authentication_proven=False)
