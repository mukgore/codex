"""Timed release of preloaded pixels to a separate, trusted worker process.

No model is supplied by this module. Parent service latency includes IPC and
observation/logging. Setup and cleanup remain separate from queue lifetime.
"""
import base64
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import queue as mailbox
import signal
import subprocess
import sys
import threading
import time

from .arrival_queue import ArrivalQueue
from .arrival_record import RecordedQueue
from .journal import _private
from .replay_worker import MAX_LINE
from .stage_profile import JsonlSink
from .supervisor import _WindowsJob

MAX_BATCH_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class ScheduledFrame:
    offset_ns: int
    source_pts_ns: int
    pixels: bytes


def _write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())


def _reader(stream, inbox):
    try:
        while True:
            line = stream.readline(MAX_LINE+1)
            if not line: break
            if len(line) > MAX_LINE or not line.endswith(b'\n'):
                raise ValueError('Oversized/incomplete worker message')
            inbox.put((time.perf_counter_ns(), json.loads(line)))
    except Exception as error:
        inbox.put((time.perf_counter_ns(), dict(kind='protocol_error', error_type=type(error).__name__)))


def run(schedule, worker_entry, directory, *, policy='fifo', capacity=1,
        min_batch=1, max_batch=1, max_wait_ns=0, timeout_seconds=5,
        setup_timeout_seconds=10, input_role):
    """Run preloaded, fixed timed-release inputs; not a camera/security sandbox.

    Use a trusted importable module:function handler. Whole schedule/pixel
    collection stays in the parent. Handler receives only a current batch.
    input_role declares synthetic/reference/development; no authentication
    endpoint is measured here. Bytes/decoding preparation costs are excluded.
    """
    schedule = tuple(schedule)
    if input_role not in ('synthetic_fixture', 'preloaded_development_pixels', 'preloaded_reference_pixels'):
        raise ValueError('Explicit preloaded input role required')
    for value in (timeout_seconds, setup_timeout_seconds):
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError('Finite positive run/setup timeouts required')
    if not isinstance(worker_entry, str) or worker_entry.count(':') != 1:
        raise ValueError('Trusted importable module:function required')
    previous = -1
    for frame in schedule:
        if (not isinstance(frame, ScheduledFrame) or type(frame.offset_ns) is not int or frame.offset_ns < previous
                or frame.offset_ns < 0 or type(frame.source_pts_ns) is not int or frame.source_pts_ns < 0
                or type(frame.pixels) is not bytes or not frame.pixels):
            raise ValueError('Ordered nonnegative offsets/PTS and owned nonempty pixels required')
        previous = frame.offset_ns
    config = dict(policy=policy, capacity=capacity, min_batch=min_batch, max_batch=max_batch,
                  max_wait_ns=max_wait_ns, planned_frames=len(schedule))
    # Validate before creating files/processes. This injected queue is never a run.
    ArrivalQueue(**config, clock=lambda: 0)
    if schedule and max(len(f.pixels) for f in schedule)*max_batch > MAX_BATCH_BYTES:
        raise ValueError('IPC batch byte budget exceeded')
    root = _private(directory); root.mkdir(parents=True, exist_ok=False)
    _write_json(root/'plan.private.json', dict(worker_entry=worker_entry, queue=config,
                input_role=input_role, timeout_seconds=timeout_seconds,
                setup_timeout_seconds=setup_timeout_seconds,
                preparation='preloaded pixels; reading/decoding costs excluded',
                schedule=[dict(sequence=i,offset_ns=f.offset_ns,source_pts_ns=f.source_pts_ns,
                               pixel_bytes_n=len(f.pixels),pixel_sha256=hashlib.sha256(f.pixels).hexdigest())
                          for i,f in enumerate(schedule)]))
    transcript = JsonlSink(root/'transport.private.jsonl')
    process = None; job = None; reader = None; record = None; queue_result = None
    status = 'ERROR'; error_type = None; phase = 'setup'; delivered = 0
    started = time.perf_counter_ns(); epoch = None; stopped = None
    inbox = mailbox.Queue(); proc_stdin_closed = False

    def observed_message():
        try: received, message = inbox.get_nowait()
        except mailbox.Empty: return None
        transcript(dict(kind='worker_message', received_parent_ns=received,
                        observed_parent_ns=time.perf_counter_ns(), message=message))
        return message

    def send(message):
        data = json.dumps(message, allow_nan=False).encode()+b'\n'
        if len(data) > MAX_LINE: raise ValueError('Worker request byte budget exceeded')
        process.stdin.write(data); process.stdin.flush()

    try:
        if os.name == 'nt': job = _WindowsJob()
        with (root/'worker_stderr.private.log').open('xb') as stderr:
            process = subprocess.Popen([sys.executable, '-m', 'analysis.runtime_benchmark.replay_worker', '--entry', worker_entry],
                                       cwd=Path(__file__).resolve().parents[2], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=stderr, start_new_session=os.name != 'nt')
            if job: job.attach(process)
            reader = threading.Thread(target=_reader,args=(process.stdout,inbox),daemon=True); reader.start()
            process.stdin.write(b'G\n');process.stdin.flush()
            setup_deadline = started+int(setup_timeout_seconds*1e9)
            while True:
                message=observed_message()
                if time.perf_counter_ns() >= setup_deadline:
                    status='TIMEOUT';raise TimeoutError('Worker setup deadline')
                if message is not None:
                    if message != {'kind':'ready'}: raise RuntimeError('Worker setup/protocol failed')
                    break
                if process.poll() is not None: raise RuntimeError('Worker exited during setup')
                time.sleep(.001)
            epoch=time.perf_counter_ns();deadline=epoch+int(timeout_seconds*1e9)
            record=RecordedQueue(root/'queue',**config,deadline_ns=deadline); q=record.queue; consumer=q.consumer()
            phase='timed_release'; active=None; eos=False
            while True:
                message=observed_message()
                if message is not None:
                    if (not isinstance(message,dict) or message.get('kind')!='result' or active is None
                            or message.get('token')!=active.token
                            or message.get('sequences')!=[f.sequence for f in active.frames]):
                        raise RuntimeError('Unexpected worker batch result')
                    outcome=message['result']['outcome'];consumer.finish(active,outcome=outcome);active=None
                    if outcome=='error':
                        status='ERROR';q.close(reason='error');break
                now=time.perf_counter_ns()
                if now>=deadline:
                    status='TIMEOUT';q.close(reason='timeout');break
                # Delivery continues while a batch is computing in another process.
                while delivered<len(schedule) and epoch+schedule[delivered].offset_ns<=now:
                    frame=schedule[delivered];q.arrive(delivered,frame.source_pts_ns,frame.pixels)
                    transcript(dict(kind='delivery',sequence=delivered,scheduled_parent_ns=epoch+frame.offset_ns,
                                    actual_ingress_ns=q.last_clock,lateness_ns=q.last_clock-epoch-frame.offset_ns))
                    delivered+=1
                    now=time.perf_counter_ns()
                    if now>=deadline:break
                if time.perf_counter_ns()>=deadline:
                    status='TIMEOUT';q.close(reason='timeout');break
                if delivered==len(schedule) and not eos:q.end_input();eos=True
                if active is None:
                    active=consumer.take()
                    if active is not None:
                        transcript(dict(kind='dispatch',token=active.token,sequences=[f.sequence for f in active.frames]))
                        send(dict(kind='batch',token=active.token,frames=[dict(sequence=f.sequence,source_pts_ns=f.source_pts_ns,
                                  pixels_b64=base64.b64encode(f.pixels).decode('ascii')) for f in active.frames]))
                    elif eos and not q.pending:
                        status='COMPLETED';q.close(reason='completed');break
                if process.poll() is not None and inbox.empty():raise RuntimeError('Worker exited before settlement')
                time.sleep(.001)
            stopped=time.perf_counter_ns()
            if status=='COMPLETED':
                send({'kind':'stop'});process.stdin.close();proc_stdin_closed=True
                try:process.wait(timeout=1)
                except subprocess.TimeoutExpired:status='ERROR';error_type='WorkerShutdownTimeout'
                if process.poll() is not None and process.returncode!=0:
                    status='ERROR';error_type='WorkerShutdownExit'
    except KeyboardInterrupt:
        status='ABORTED';error_type='KeyboardInterrupt'
        if record is not None and not record.queue.closed and not record.queue.broken:record.queue.close(reason='aborted')
    except Exception as error:
        error_type=type(error).__name__
        if status!='TIMEOUT':status='ERROR'
        if record is not None and not record.queue.closed and not record.queue.broken:record.queue.close(reason='error')
    finally:
        stopped=stopped or time.perf_counter_ns()
        if process is not None:
            if job:job.close();job=None
            elif os.name!='nt':
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            if process.poll() is None:process.kill()
            process.wait(timeout=5)
            if not proc_stdin_closed:process.stdin.close()
            if reader:reader.join(timeout=2)
            process.stdout.close()
        elif job:job.close()
        if record is not None:queue_result=record.finish_recording()
        transcript.close()
    result=dict(status=status,error_type=error_type,phase=phase,input_role=input_role,
                planned_frames_n=len(schedule),delivered_frames_n=delivered,
                queue_recovery=queue_result,worker_returncode=None if process is None else process.returncode,
                setup_ns=None if epoch is None else epoch-started,
                timed_release_ns=None if epoch is None else stopped-epoch,
                cleanup_ns=time.perf_counter_ns()-stopped,
                endpoint='preloaded_timed_release_transport_only',authentication_proven=False,
                model_performance_proven=False,tree_containment='windows_job' if os.name=='nt' else 'posix_process_group')
    _write_json(root/'result.private.json',result)
    return result
