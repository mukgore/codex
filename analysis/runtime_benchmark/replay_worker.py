"""Gated trusted worker. Receives current batches, never the replay schedule."""
import argparse
import base64
from contextlib import redirect_stdout
import importlib
import json
import sys
import time

MAX_LINE = 32 * 1024 * 1024


def _write(value):
    sys.stdout.buffer.write(json.dumps(value, allow_nan=False).encode()+b'\n')
    sys.stdout.buffer.flush()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry', required=True)
    args = parser.parse_args(argv)
    # Parent installs owned process-tree containment before allowing imports.
    if sys.stdin.buffer.readline(3) != b'G\n': return 125
    try:
        with redirect_stdout(sys.stderr):
            module, name = args.entry.split(':')
            handler = getattr(importlib.import_module(module), name)
        if not callable(handler): raise ValueError('Callable entry required')
    except Exception as error:
        _write(dict(kind='setup_error', error_type=type(error).__name__))
        return 1
    _write(dict(kind='ready'))
    while True:
        line = sys.stdin.buffer.readline(MAX_LINE+1)
        if not line: return 0
        if len(line) > MAX_LINE or not line.endswith(b'\n'): return 2
        message = json.loads(line)
        if message == {'kind': 'stop'}: return 0
        if message.get('kind') != 'batch': return 2
        frames = tuple(dict(sequence=f['sequence'], source_pts_ns=f['source_pts_ns'],
                            pixels=base64.b64decode(f['pixels_b64'], validate=True))
                       for f in message['frames'])
        started = time.perf_counter_ns(); cpu_started = time.process_time_ns()
        try:
            with redirect_stdout(sys.stderr):
                result = handler(frames)
            if not isinstance(result, dict) or result.get('outcome') not in ('response_ready', 'no_detection'):
                raise ValueError('Explicit response/no_detection object required')
            # Check serialization before claiming that a response can be sent.
            json.dumps(result, allow_nan=False)
        except Exception as error:
            result = dict(outcome='error', error_type=type(error).__name__)
        _write(dict(kind='result', token=message['token'],
                    sequences=[f['sequence'] for f in frames], result=result,
                    handler_wall_ns=time.perf_counter_ns()-started,
                    handler_own_cpu_ns=time.process_time_ns()-cpu_started))


if __name__ == '__main__': sys.exit(main())
