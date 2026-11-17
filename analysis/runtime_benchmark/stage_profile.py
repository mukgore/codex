"""Scoped stage1 instrumentation; no replacement extraction/model algorithm.

Call durations exclude trace writes. Gaps include Python bookkeeping and trace
I/O, so result conversion gaps are not isolated coordinate-conversion timings.
"""
from contextlib import contextmanager
import json
import os
import threading
import time

VERSION = 'scoped_stage1_calls_and_explicit_trace_io_gaps_v1'
_LOCK = threading.Lock()


class Trace:
    def __init__(self, sink=None, clock=None, workload_role='unspecified'):
        self.sink = sink
        self.clock = clock or (lambda: (time.perf_counter_ns(), time.process_time_ns()))
        self.clock_role = 'actual_process_monotonic' if clock is None else 'injected_fixture'
        self.workload_role = workload_role
        self.events = []; self.segments = []; self.active = None; self.started = False; self.closed = False

    def _stamp(self):
        value = self.clock()
        if (not isinstance(value, tuple) or len(value) != 2 or
                any(type(x) is not int or x < 0 for x in value)):
            raise ValueError('Nonnegative integer wall/own CPU clocks required')
        return value

    def _emit(self, value):
        self.events.append(value)
        if self.sink:
            self.sink(value)

    def start(self):
        if self.started:
            raise ValueError('Fresh trace required')
        self.started = True; self.begin = self.last = self._stamp(); self.gap = 'setup_python_and_trace_io'
        self._emit({'kind': 'run_started', 'wall_ns': self.begin[0], 'own_cpu_ns': self.begin[1],
                    'clock_role': self.clock_role, 'workload_role': self.workload_role})

    def _segment(self, kind, phase, start, end, **fields):
        if end[0] < start[0] or end[1] < start[1]:
            raise ValueError('Clock regression; no fabricated zero duration')
        row = {'kind': kind, 'phase': phase, 'start_wall_ns': start[0], 'end_wall_ns': end[0],
               'start_own_cpu_ns': start[1], 'end_own_cpu_ns': end[1],
               'wall_ns': end[0]-start[0], 'own_cpu_ns': end[1]-start[1], **fields}
        self.segments.append(row); return row

    def call(self, phase, operation, fields=None, result_fields=None):
        if not self.started or self.closed or self.active is not None:
            raise ValueError('One active call in a live trace required')
        token = len([e for e in self.events if e['kind'] == 'call_started'])
        # Persist intent BEFORE the operation. If killed without a finish,
        # whether the operation started/completed remains unknown.
        self.active = token
        self._emit({'kind': 'call_started', 'call_id': token, 'phase': phase,
                    'operation_start_not_yet_recorded': True, **(fields or {})})
        start = self._stamp()
        self._segment('gap', self.gap, self.last, start)
        try:
            result = operation()
        except BaseException as error:
            end = self._stamp(); self.last = end
            row = self._segment('call', phase, start, end, call_id=token, outcome='ERROR', error_type=type(error).__name__, **(fields or {}))
            self.active = None; self.gap = 'exception_cleanup_and_trace_io'
            self._emit({**row, 'kind': 'call_finished'}); raise
        end = self._stamp(); self.last = end
        try:
            extra = result_fields(result) if result_fields else {}
        except Exception as error:
            extra = {'metadata_error_type': type(error).__name__}
        row = self._segment('call', phase, start, end, call_id=token, outcome='RETURNED', **(fields or {}), **extra)
        self.active = None
        self.gap = ('result_conversion_loop_and_trace_io' if phase == 'hands_process' else
                    'post_close_timeline_checks_and_trace_io' if phase == 'hands_close' else
                    'metadata_loop_dispatch_and_trace_io')
        self._emit({**row, 'kind': 'call_finished'})
        return result

    def finish(self, status, error_type=None, namespace_restored=True):
        if not self.started or self.closed or self.active is not None:
            raise ValueError('One trace terminal required')
        end = self._stamp(); self._segment('gap', self.gap, self.last, end)
        self.closed = True; self.status = status; self.end = end; self.error_type = error_type
        self.namespace_restored = namespace_restored
        self._emit({'kind': 'run_finished', 'status': status, 'error_type': error_type,
                    'wall_ns': end[0], 'own_cpu_ns': end[1], 'namespace_restored': namespace_restored})

    def summary(self):
        if not self.closed:
            raise ValueError('No complete timing summary for an unfinished trace')
        phases = {}
        for row in self.segments:
            group = phases.setdefault(row['phase'], {'kind': row['kind'], 'calls_or_gaps_n': 0,
                                                       'wall_ns': 0, 'own_cpu_ns': 0, 'errors_n': 0})
            group['calls_or_gaps_n'] += 1; group['wall_ns'] += row['wall_ns']; group['own_cpu_ns'] += row['own_cpu_ns']
            group['errors_n'] += row.get('outcome') == 'ERROR'
        wall, cpu = self.end[0]-self.begin[0], self.end[1]-self.begin[1]
        if sum(r['wall_ns'] for r in self.segments) != wall or sum(r['own_cpu_ns'] for r in self.segments) != cpu:
            raise ValueError('Exclusive accounting lost time')
        return {'version': VERSION, 'status': self.status, 'error_type': self.error_type,
                'workload_role': self.workload_role,
                'clock_role': self.clock_role, 'clock_domain': 'one_worker_process',
                'profile_window_wall_ns': wall, 'profile_window_own_cpu_ns': cpu,
                'exclusive_accounting_complete': True, 'phases': phases,
                'namespace_restored': self.namespace_restored,
                'measurement_metadata_errors_n': sum('metadata_error_type' in r for r in self.segments),
                'call_ns_excludes_trace_write': True, 'gaps_include_trace_io_and_python': True,
                'final_summary_write_and_namespace_restore_excluded': True,
                'gpu_completion_measured': False,
                'limitations': ['Hands.process is a complete graph call, not a neural-forward count or isolated model kernel.',
                                'Result-conversion gaps include loop/PTS/bookkeeping and trace I/O.',
                                'Own CPU excludes child processes; parallel native threads may make CPU exceed wall.',
                                'No cold/warm control or online camera/authentication latency claim.']}


class JsonlSink:
    def __init__(self, path):
        self.stream = open(path, 'xb')
    def __call__(self, event):
        self.stream.write(json.dumps(event, sort_keys=True, allow_nan=False).encode()+b'\n')
        self.stream.flush(); os.fsync(self.stream.fileno())
    def close(self): self.stream.close()


def recover_events(raw):
    """Partial intent never becomes a zero-duration completed operation."""
    records = []; truncated = bool(raw and not raw.endswith(b'\n'))
    for line in raw.splitlines(keepends=True):
        if not line.endswith(b'\n'):
            break
        records.append(json.loads(line))
    if not records:
        return {'state': 'TRUNCATED' if truncated else 'LOG_LOST', 'finished_calls_n': 0,
                'unknown_outcome_calls_n': 0, 'unknown_call_durations': None,
                'not_an_independent_integrity_attestation': True}
    if records[0].get('kind') != 'run_started':
        raise ValueError('Trace start missing')
    pending = set(); finished = set(); phases = {}; terminal = None
    for event in records:
        if terminal is not None:
            raise ValueError('Events after trace terminal')
        if event['kind'] == 'call_started':
            key = event['call_id']
            if pending or key in finished: raise ValueError('Duplicate or overlapping call intent')
            pending.add(key); phases[key] = event['phase']
        elif event['kind'] == 'call_finished':
            key = event['call_id']
            if key not in pending: raise ValueError('Finish without intent')
            if event['phase'] != phases[key] or event['outcome'] not in ('RETURNED', 'ERROR'):
                raise ValueError('Call phase/outcome mismatch')
            pending.remove(key); finished.add(key)
        elif event['kind'] == 'run_finished':
            if event['status'] not in ('COMPLETED', 'ERROR', 'ABORTED'): raise ValueError('Unknown terminal state')
            terminal = event['status']
        elif event['kind'] == 'run_started':
            if event is not records[0]: raise ValueError('Duplicate trace start')
        else: raise ValueError('Unknown trace event')
    if terminal is not None and pending:
        raise ValueError('Completed trace cannot contain unfinished calls')
    return {'state': 'TRUNCATED' if truncated else 'INCOMPLETE' if terminal is None else terminal,
            'finished_calls_n': len(finished), 'unknown_outcome_calls_n': len(pending),
            'unknown_call_durations': None, 'not_an_independent_integrity_attestation': True}


def rebuild_summary(raw):
    """Rebuild complete call/gap accounting from persisted clock boundaries."""
    recovered = recover_events(raw)
    if recovered['state'] not in ('COMPLETED', 'ERROR', 'ABORTED'):
        raise ValueError('Incomplete trace cannot become a complete timing summary')
    events = [json.loads(line) for line in raw.splitlines()]
    first, terminal = events[0], events[-1]
    trace = Trace(workload_role=first['workload_role'])
    trace.clock_role = first['clock_role']; trace.started = True
    trace.begin = trace.last = (first['wall_ns'], first['own_cpu_ns'])
    gap = 'setup_python_and_trace_io'
    for event in events:
        if event['kind'] != 'call_finished': continue
        start = event['start_wall_ns'], event['start_own_cpu_ns']
        end = event['end_wall_ns'], event['end_own_cpu_ns']
        if event['wall_ns'] != end[0]-start[0] or event['own_cpu_ns'] != end[1]-start[1]:
            raise ValueError('Stored duration differs from actual boundaries')
        trace._segment('gap', gap, trace.last, start)
        row = dict(event); row['kind'] = 'call'; trace.segments.append(row); trace.last = end
        gap = ('exception_cleanup_and_trace_io' if event['outcome'] == 'ERROR' else
               'result_conversion_loop_and_trace_io' if event['phase'] == 'hands_process' else
               'post_close_timeline_checks_and_trace_io' if event['phase'] == 'hands_close' else
               'metadata_loop_dispatch_and_trace_io')
    trace.end = terminal['wall_ns'], terminal['own_cpu_ns']
    trace._segment('gap', gap, trace.last, trace.end)
    trace.closed = True; trace.status = terminal['status']; trace.error_type = terminal['error_type']
    trace.namespace_restored = terminal['namespace_restored']
    return trace.summary()


class _Delegate:
    def __init__(self, target): self.target = target
    def __getattr__(self, name): return getattr(self.target, name)


class _Capture(_Delegate):
    def __init__(self, target, trace): super().__init__(target); self.trace = trace; self.next = 0
    def read(self):
        result = self.trace.call('decoder_read', self.target.read, {'frame_idx': self.next},
                                 lambda value: {'read_success': bool(value[0])})
        self.next += bool(result[0]); return result
    def release(self): return self.trace.call('decoder_close', self.target.release)


class _Hands(_Delegate):
    def __init__(self, target, trace): super().__init__(target); self.trace = trace; self.next = 0
    def process(self, *args, **kwargs):
        result = self.trace.call('hands_process', lambda: self.target.process(*args, **kwargs), {'frame_idx': self.next})
        self.next += 1; return result
    def close(self): return self.trace.call('hands_close', self.target.close)


class _CV2(_Delegate):
    def __init__(self, target, trace): super().__init__(target); self.trace = trace
    def VideoCapture(self, *args, **kwargs):
        return _Capture(self.trace.call('decoder_open', lambda: self.target.VideoCapture(*args, **kwargs)), self.trace)
    def cvtColor(self, *args, **kwargs):
        return self.trace.call('rgb_preprocess', lambda: self.target.cvtColor(*args, **kwargs))


@contextmanager
def profile_stage1(module, trace):
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError('Isolated single-worker profiling only; no nested/concurrent namespace changes')
    try:
        cv2, mp = module.cv2, module.mp
        wrapped_cv = _CV2(cv2, trace)
        hands_module = _Delegate(mp.solutions.hands)
        hands_module.Hands = lambda *a, **k: _Hands(trace.call('hands_setup', lambda: mp.solutions.hands.Hands(*a, **k)), trace)
        solutions = _Delegate(mp.solutions); solutions.hands = hands_module
        wrapped_mp = _Delegate(mp); wrapped_mp.solutions = solutions
    except BaseException:
        _LOCK.release(); raise
    error_type = None; state = 'COMPLETED'; intact = True
    try:
        module.cv2, module.mp = wrapped_cv, wrapped_mp; trace.start()
        try:
            yield trace
        except BaseException as error:
            error_type = type(error).__name__; state = 'ABORTED' if isinstance(error, KeyboardInterrupt) else 'ERROR'
            raise
        finally:
            intact = module.cv2 is wrapped_cv and module.mp is wrapped_mp
            if not intact: state, error_type = 'ERROR', 'PROFILE_NAMESPACE_DRIFT'
            # End the measured window before unconditional namespace cleanup.
            trace.finish(state, error_type, namespace_restored=True)
    finally:
        try:
            module.cv2, module.mp = cv2, mp
        finally:
            _LOCK.release()
    if not intact:
        raise RuntimeError('Profiled module namespace changed during extraction')
