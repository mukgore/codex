"""Forward-only ingress for trusted local streaming adapters.

Source timestamps are metadata; all latency uses one monotonic ingress clock.
This is an API boundary, not a sandbox for hostile Python code. The producer
must deliver only available pixels, never a filename or precomputed answer.
"""
from collections import deque
from dataclasses import dataclass
import time


@dataclass(frozen=True)
class Frame:
    sequence: int
    source_pts_ns: int
    pixels: bytes
    arrived_ns: int


@dataclass(frozen=True)
class Batch:
    token: int
    frames: tuple
    started_ns: int


class Consumer:
    """Only arrived frames can be claimed; there is no index/path lookup API."""
    def __init__(self, queue):
        self.__queue = queue

    def take(self):
        return self.__queue._take()

    def finish(self, batch, *, outcome):
        return self.__queue._finish(batch, outcome=outcome)


class ArrivalQueue:
    """Serialized event-loop queue; producer ingress continues between calls.

    A blocking model must run outside the ingress loop. No thread-safety or
    preemption is implied. FIFO drops incoming overflow; latest has capacity1
    and replaces the waiting frame, never the in-flight frame. Batch waiting
    ends at min_batch, oldest arrival + max_wait, or EOS. Deadline is exclusive.
    """
    def __init__(self, *, policy, capacity, min_batch=1, max_batch=1,
                 max_wait_ns=0, deadline_ns=None, planned_frames=None, clock=None, sink=None):
        if policy not in ('fifo', 'latest'):
            raise ValueError('Explicit fifo/latest policy required')
        values = (capacity, min_batch, max_batch)
        if any(type(v) is not int or v < 1 for v in values):
            raise ValueError('Positive integer capacity/batch sizes required')
        if not min_batch <= max_batch <= capacity or (policy == 'latest' and capacity != 1):
            raise ValueError('Batch must fit queue; latest requires capacity1')
        if type(max_wait_ns) is not int or max_wait_ns < 0:
            raise ValueError('Nonnegative batch wait required')
        if deadline_ns is not None and (type(deadline_ns) is not int or deadline_ns < 0):
            raise ValueError('Absolute monotonic deadline required')
        if planned_frames is not None and (type(planned_frames) is not int or planned_frames < 0):
            raise ValueError('Nonnegative planned frame count required')
        self.policy, self.capacity = policy, capacity
        self.min_batch, self.max_batch, self.max_wait_ns = min_batch, max_batch, max_wait_ns
        self.deadline_ns, self.clock, self.sink = deadline_ns, clock or time.perf_counter_ns, sink
        self.clock_role = 'actual_monotonic' if clock is None else 'injected_fixture'
        self.pending = deque(); self.active = None; self.events = []
        self.last_clock = None; self.last_sequence = -1; self.next_token = 0
        self.eos = False; self.closed = False; self.broken = False
        self.planned_frames = planned_frames; self.arrived_n = 0
        self._event('queue_started', self._now(), schema_version=1,
                    policy=policy, capacity=capacity, min_batch=min_batch, max_batch=max_batch,
                    max_wait_ns=max_wait_ns, deadline_ns=deadline_ns, planned_frames=planned_frames,
                    clock_role=self.clock_role)

    def consumer(self):
        return Consumer(self)

    def _now(self):
        if self.broken:
            raise RuntimeError('Queue recording failed; continuation prohibited')
        now = self.clock()
        if type(now) is not int or now < 0 or (self.last_clock is not None and now < self.last_clock):
            raise ValueError('Nonnegative monotonic integer clock required')
        self.last_clock = now
        return now

    def _event(self, kind, now, **fields):
        event = dict(event_id=len(self.events), kind=kind, at_ns=now, **fields)
        # Fail closed on logging failure, without a fabricated completion.
        self.events.append(event)
        if self.sink:
            try:
                self.sink(event)
            except BaseException:
                self.broken = True
                raise

    def _expired(self, now):
        return self.deadline_ns is not None and now >= self.deadline_ns

    def _drop(self, frame, now, reason):
        self._event('drop', now, sequence=frame.sequence, reason=reason)

    def arrive(self, sequence, source_pts_ns, pixels):
        """Push bytes already delivered now. There is no future schedule input."""
        if self.eos or self.closed:
            raise RuntimeError('Ingress ended')
        if type(sequence) is not int or sequence <= self.last_sequence:
            raise ValueError('Strictly increasing nonnegative frame IDs required')
        if self.planned_frames is not None and sequence >= self.planned_frames:
            raise ValueError('Sequence outside registered frame roster')
        if type(source_pts_ns) is not int or source_pts_ns < 0 or type(pixels) is not bytes or not pixels:
            raise ValueError('Nonnegative source PTS and owned nonempty pixel bytes required')
        now = self._now(); self.last_sequence = sequence; self.arrived_n += 1
        frame = Frame(sequence, source_pts_ns, pixels, now)
        self._event('arrival', now, sequence=sequence, source_pts_ns=source_pts_ns,
                    pixel_bytes_n=len(pixels), waiting_n=len(self.pending))
        if self._expired(now):
            self._drop(frame, now, 'deadline')
            return False
        if len(self.pending) == self.capacity:
            if self.policy == 'fifo':
                self._drop(frame, now, 'incoming_overflow')
                return False
            self._drop(self.pending.popleft(), now, 'replaced_by_latest')
        self.pending.append(frame)
        return True

    def end_input(self):
        if self.eos or self.closed:
            raise RuntimeError('Ingress already ended')
        now = self._now(); self.eos = True
        self._event('end_input', now)

    def _take(self):
        if self.closed:
            raise RuntimeError('Queue closed')
        if self.active is not None:
            raise RuntimeError('Only one in-flight batch supported')
        now = self._now()
        if self._expired(now):
            while self.pending:
                self._drop(self.pending.popleft(), now, 'deadline')
            return None
        if not self.pending:
            return None
        if (len(self.pending) < self.min_batch and not self.eos
                and now - self.pending[0].arrived_ns < self.max_wait_ns):
            return None
        frames = tuple(self.pending.popleft() for _ in range(min(len(self.pending), self.max_batch)))
        batch = Batch(self.next_token, frames, now); self.next_token += 1
        self.active = batch
        self._event('start', now, token=batch.token, sequences=[f.sequence for f in frames],
                    queue_wait_ns=[now-f.arrived_ns for f in frames])
        return batch

    def _finish(self, batch, *, outcome):
        if self.closed or batch is not self.active or self.active is None:
            raise ValueError('Exact active batch identity required')
        if outcome not in ('response_ready', 'no_detection', 'error', 'aborted'):
            raise ValueError('Explicit processing outcome required')
        now = self._now()
        event = dict(token=batch.token, sequences=[f.sequence for f in batch.frames], outcome=outcome,
                     service_ns=now-batch.started_ns,
                     arrival_to_finish_ns=[now-f.arrived_ns for f in batch.frames],
                     deadline_met=not self._expired(now))
        self._event('finish', now, **event); self.active = None
        return event

    def close(self, *, reason):
        if self.closed or reason not in ('completed', 'timeout', 'error', 'aborted'):
            raise ValueError('Fresh explicit terminal reason required')
        if reason == 'completed' and (not self.eos or self.pending or self.active is not None):
            raise ValueError('Completion requires EOS and all arrived frames settled')
        if reason == 'completed' and self.planned_frames is not None and self.arrived_n != self.planned_frames:
            raise ValueError('Completion requires every planned frame to arrive')
        now = self._now()
        while self.pending:
            self._drop(self.pending.popleft(), now, 'closed_'+reason)
        # Active operation may have been interrupted. Its finish/time stays unknown.
        self._event('close', now, reason=reason,
                    unfinished_token=None if self.active is None else self.active.token)
        self.closed = True
