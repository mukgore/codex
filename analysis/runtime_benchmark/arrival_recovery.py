"""Validate queue event semantics by deterministic replay; no pixels loaded.

External execution receipts authenticate stored file bytes separately. This
validator detects inconsistent semantics, not a maliciously rewritten history.
"""
from collections import Counter
import json

from .arrival_queue import ArrivalQueue


class _EndOfPrefix(Exception):
    pass


def recover(raw):
    if not raw:
        return {'state': 'LOG_LOST', 'valid_events_n': 0, 'summary': None}
    events = []
    truncated = False
    parse_error = False
    for line in raw.splitlines(keepends=True):
        if not line.endswith(b'\n'):
            truncated = True
            break
        try:
            value = json.loads(line)
            if not isinstance(value, dict): raise ValueError('Object required')
            events.append(value)
        except (ValueError, UnicodeError):
            parse_error = True
            break
    if not events:
        return {'state': 'LOG_CORRUPT' if parse_error else 'INTERRUPTED', 'valid_events_n': 0, 'summary': None}
    cursor = 0
    now = events[0].get('at_ns')
    current_arrival_size = None

    def compare(event):
        nonlocal cursor
        if cursor == len(events): raise _EndOfPrefix()
        # Replay uses one dummy byte; size is metadata, never allocation input.
        if event['kind'] == 'arrival': event['pixel_bytes_n'] = current_arrival_size
        def canonical(value):
            return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
        if canonical(event) != canonical(events[cursor]): raise ValueError('Queue event semantics differ')
        cursor += 1

    try:
        head = events[0]
        if head.get('kind') != 'queue_started' or head.get('schema_version') != 1:
            raise ValueError('Versioned configuration header required')
        if head['clock_role'] not in ('actual_monotonic', 'injected_fixture'):
            raise ValueError('Unknown clock role')
        config = {k: head[k] for k in ('policy','capacity','min_batch','max_batch','max_wait_ns','deadline_ns','planned_frames')}

        class ReplayQueue(ArrivalQueue):
            def _event(self, kind, stamp, **fields):
                if kind == 'queue_started': fields['clock_role'] = head['clock_role']
                return super()._event(kind, stamp, **fields)

        queue = ReplayQueue(**config, clock=lambda: now, sink=compare)
        while cursor < len(events):
            event = events[cursor]; now = event['at_ns']
            kind = event['kind']
            if kind == 'arrival':
                current_arrival_size = event['pixel_bytes_n']
                if type(current_arrival_size) is not int or current_arrival_size < 1:
                    raise ValueError('Positive byte count required')
                queue.arrive(event['sequence'], event['source_pts_ns'], b'x')
            elif kind == 'start':
                before = cursor; queue._take()
                if cursor == before: raise ValueError('Batch started before ready')
            elif kind == 'finish':
                queue._finish(queue.active, outcome=event['outcome'])
            elif kind == 'end_input': queue.end_input()
            elif kind == 'close': queue.close(reason=event['reason'])
            elif kind == 'drop':
                reason = event['reason']
                if reason.startswith('closed_'): queue.close(reason=reason[len('closed_'):])
                elif reason == 'deadline':
                    before = cursor; queue._take()
                    if cursor == before: raise ValueError('Invalid deadline drop')
                else: raise ValueError('Missing arrival before overflow/replacement')
            else: raise ValueError('Unexpected event kind')
    except _EndOfPrefix:
        # Prefix can end between arrival/drop or drop/close durable writes.
        pass
    except (ValueError, KeyError, TypeError, RuntimeError, AttributeError):
        return {'state': 'LOG_CORRUPT', 'valid_events_n': cursor, 'summary': None}

    terminal = events[-1]['kind'] == 'close'
    if parse_error or (terminal and truncated):
        return {'state': 'LOG_CORRUPT', 'valid_events_n': cursor, 'summary': None}
    frames = {}; waits = {}; latencies = {}; outcomes = Counter(); drops = Counter(); batches = []
    for event in events:
        kind = event['kind']
        if kind == 'arrival': frames[event['sequence']] = 'unsettled'
        elif kind == 'drop':
            frames[event['sequence']] = 'dropped'; drops[event['reason']] += 1
        elif kind == 'start':
            for sequence, wait in zip(event['sequences'], event['queue_wait_ns']):
                frames[sequence] = 'unfinished'; waits[sequence] = wait
        elif kind == 'finish':
            batches.append({k: event[k] for k in ('token','sequences','outcome','service_ns','deadline_met')})
            for sequence, latency in zip(event['sequences'], event['arrival_to_finish_ns']):
                frames[sequence] = 'finished'; latencies[sequence] = latency
                outcomes[event['outcome']] += 1
    counts = Counter(frames.values())
    planned = head['planned_frames']
    summary = dict(clock_role=head['clock_role'], planned_frames_n=planned,
                   arrived_frames_n=len(frames), not_arrived_frames_n=None if planned is None else planned-len(frames),
                   finished_frames_n=counts['finished'], dropped_frames_n=counts['dropped'],
                   unfinished_frames_n=counts['unfinished'], unsettled_frames_n=counts['unsettled'],
                   outcomes=dict(outcomes), drop_reasons=dict(drops),
                   finished_batches=batches,
                   queue_wait_ns_by_sequence=waits, arrival_to_finish_ns_by_sequence=latencies,
                   elapsed_ns=events[-1]['at_ns']-head['at_ns'] if terminal else None,
                   authentication_or_gate_success_proven=False)
    state = events[-1]['reason'].upper() if terminal else 'INTERRUPTED'
    return {'state': state, 'valid_events_n': cursor, 'summary': summary}
