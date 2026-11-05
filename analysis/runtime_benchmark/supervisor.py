"""Run trusted local commands under an owned process-tree deadline.

The supervisor result and the worker journal are separate evidence. A zero
exit code never substitutes for a complete frame journal. No shell is used.
"""
import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

if __package__:
    from .journal import _private, recover_bytes
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from analysis.runtime_benchmark.journal import _private, recover_bytes


class _WindowsJob:
    """Kill descendants on handle close; attach before releasing worker gate."""
    def __init__(self):
        from ctypes import wintypes as w
        class Basic(ctypes.Structure):
            _fields_ = [('ProcessTime', ctypes.c_int64), ('JobTime', ctypes.c_int64),
                        ('Flags', w.DWORD), ('MinWorkingSet', ctypes.c_size_t),
                        ('MaxWorkingSet', ctypes.c_size_t), ('ActiveProcesses', w.DWORD),
                        ('Affinity', ctypes.c_size_t), ('Priority', w.DWORD), ('Scheduling', w.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in
                        ('ReadOps', 'WriteOps', 'OtherOps', 'ReadBytes', 'WriteBytes', 'OtherBytes')]
        class Extended(ctypes.Structure):
            _fields_ = [('Basic', Basic), ('IO', IO), ('ProcessMemory', ctypes.c_size_t),
                        ('JobMemory', ctypes.c_size_t), ('PeakProcessMemory', ctypes.c_size_t),
                        ('PeakJobMemory', ctypes.c_size_t)]
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        self.api.CreateJobObjectW.restype = w.HANDLE
        self.api.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
        self.api.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        self.api.CloseHandle.argtypes = [w.HANDLE]
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Extended(); limits.Basic.Flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error()); self.close(); raise error

    def attach(self, process):
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle); self.handle = None


def _bootstrap(plan):
    # This process cannot spawn the supplied command before the parent has
    # installed containment. EOF (including parent failure) launches nothing.
    if sys.stdin.buffer.read(1) != b'G':
        return 125
    config = json.loads(Path(plan).read_text(encoding='utf8'))
    environment = dict(os.environ)
    environment['RUNTIME_JOURNAL_DIRECTORY'] = str(Path(plan).parent / 'worker_journal')
    return subprocess.call(config['command'], cwd=config['cwd'], env=environment,
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, shell=False)


def run(command, output, *, cwd, timeout_seconds):
    if (not isinstance(command, (list, tuple)) or not command or
            not all(isinstance(x, str) and x and '\0' not in x for x in command)):
        raise ValueError('Nonempty argument array required; shell strings are not accepted')
    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or
            not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
        raise ValueError('Finite positive deadline required')
    cwd = Path(cwd).resolve(strict=True)
    if not cwd.is_dir():
        raise ValueError('Existing working directory required')
    root = _private(output); root.mkdir(parents=True, exist_ok=False)
    plan = root / 'supervisor_manifest.json'
    plan.write_text(json.dumps({'schema_version': 1, 'command': list(command), 'cwd': str(cwd),
                               'timeout_seconds': timeout_seconds}, allow_nan=False) + '\n', encoding='utf8')
    process = None; job = None; released = False; status = 'ERROR'; returncode = None
    started = time.perf_counter_ns(); reason = None
    try:
        if os.name == 'nt':
            job = _WindowsJob()
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--bootstrap', str(plan)],
                                   stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   start_new_session=os.name != 'nt')
        if job:
            job.attach(process)
        remaining = timeout_seconds - (time.perf_counter_ns() - started) / 1e9
        if remaining <= 0:
            status = 'TIMED_OUT'; reason = 'deadline_before_release'
        else:
            process.stdin.write(b'G'); process.stdin.close(); released = True
            try:
                returncode = process.wait(timeout=remaining)
                status = 'EXITED' if returncode == 0 else 'ERROR'
                reason = None if returncode == 0 else 'nonzero_worker_exit'
            except subprocess.TimeoutExpired:
                status = 'TIMED_OUT'; reason = 'process_tree_deadline'
    except KeyboardInterrupt:
        status = 'ABORTED'; reason = 'supervisor_keyboard_interrupt'
    except (OSError, ValueError):
        status = 'ERROR'; reason = 'containment_or_launch_failure'
    finally:
        if process is not None:
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
            if job:
                job.close()  # includes descendants even after the leader exits
            elif os.name != 'nt':
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            if returncode is None:
                returncode = process.returncode
        elif job:
            job.close()
    elapsed = time.perf_counter_ns() - started
    journal_path = root / 'worker_journal' / 'events.jsonl'
    if journal_path.exists() and journal_path.stat().st_size <= 32 * 1024 * 1024:
        recovered = recover_bytes(journal_path.read_bytes())
    else:
        recovered = {'status': 'LOG_LOST', 'reason': 'missing_or_oversized_worker_journal'}
    # Never rewrite a killed worker's missing terminal as a journal TIMED_OUT.
    completed = status == 'EXITED' and recovered['status'] == 'COMPLETED'
    result = {'schema_version': 1, 'supervisor_status': status, 'reason': reason,
              'returncode': returncode, 'elapsed_ns': elapsed, 'worker_released': released,
              'tree_containment': 'windows_job' if os.name == 'nt' else 'posix_process_group',
              'worker_journal': recovered, 'completed': completed,
              'scope': 'local_owned_process_tree_not_model_performance'}
    with (root / 'supervisor_result.json').open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    return result


if __name__ == '__main__':
    # Direct bootstrap launch avoids depending on the caller's module path.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap', required=True)
    sys.exit(_bootstrap(parser.parse_args().bootstrap))
