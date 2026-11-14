"""Private command/run/output evidence; hashes are not independent attestation.

Fresh runs are launched here after a provenance snapshot. Existing runs may
only be inventoried retrospectively; no past command/time is manufactured.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from validation_v03.run_manifest import prepare, read, verify_current
from validation_v03.session_artifacts import canonical, decode, _private

MAX_FILES = 10000
MAX_BYTES = 16 * 1024**3


def _write(path, value):
    with Path(path).open('xb') as stream:
        stream.write(canonical(value) + b'\n'); stream.flush(); os.fsync(stream.fileno())


def _file(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Regular evidence file required; links are not evidence')
    before = path.stat(); total = 0; checksum = hashlib.sha256()
    if before.st_size > MAX_BYTES: raise ValueError('Evidence byte budget exceeded')
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            total += len(block)
            if total > before.st_size: raise ValueError('Evidence grew during hashing')
            checksum.update(block)
    after = path.stat()
    if total != before.st_size or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Evidence changed during hashing')
    return {'bytes': total, 'sha256': checksum.hexdigest()}


def _inventory(roots, *, allow_missing=False):
    entries = []; seen = set(); total = 0
    for value in roots:
        root = _private(value)
        if allow_missing and not root.exists(): continue
        if not root.is_dir() or root.is_symlink(): raise ValueError('Existing private artifact root required')
        files = sorted(root.rglob('*'))
        for path in files:
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError('Artifact links/escapes are forbidden')
            if path.is_dir(): continue
            resolved = str(path.resolve())
            if resolved in seen: raise ValueError('Overlapping artifact roots')
            seen.add(resolved); info = _file(path); total += info['bytes']
            if len(entries) >= MAX_FILES or total > MAX_BYTES: raise ValueError('Artifact inventory budget exceeded')
            entries.append({'path': resolved, **info})
    if not entries and not allow_missing: raise ValueError('At least one output file is required')
    return entries


def _seal(output, record):
    _write(output/'receipt.private.json', record)
    digest = _file(output/'receipt.private.json')['sha256']
    with (output/'receipt.sha256').open('x', encoding='ascii') as stream:
        stream.write(digest + '\n'); stream.flush(); os.fsync(stream.fileno())
    return record


def _stop(process):
    """Stop this run's process group/tree; never enumerate or kill other jobs."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=False)
    else:
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
    process.wait(timeout=15)


def run(config, repo, output, command, artifact_roots):
    """Launch one foreground command and bind its actual process outcome/files.

    Use foreground programs only; detached services require their own lifecycle
    recorder. Exit zero does not certify a scientific hypothesis or participant.
    """
    output = _private(output); repo = Path(repo).resolve(strict=True)
    roots = [_private(p) for p in artifact_roots]
    if not roots or len(set(roots)) != len(roots): raise ValueError('Distinct artifact roots required')
    if any(p.exists() for p in roots) or output.exists(): raise FileExistsError('Never overwrite prior evidence/output')
    if any(output.is_relative_to(p) or p.is_relative_to(output) for p in roots):
        raise ValueError('Run evidence and experiment outputs must be separate')
    if not isinstance(command, list) or not command or any(not isinstance(a, str) or not a or '\0' in a for a in command):
        raise ValueError('Explicit command argument array required; no shell expansion')
    executable = Path(command[0])
    if not executable.is_absolute(): raise ValueError('Absolute executable path required')
    tool = _file(executable)
    manifest, fingerprint = prepare(config, repo, output/'provenance')
    started = time.time_ns(); clock = time.perf_counter_ns()
    start = {'schema_version': 1, 'mode': 'RECORDED_COMMAND_EXECUTION', 'run_id': manifest['configuration']['run_id'],
             'started_utc_epoch_ns': started, 'command': command, 'cwd': str(repo),
             'executable': {'path': str(executable), **tool}, 'provenance_sha256': fingerprint,
             'artifact_roots': [str(p) for p in roots], 'recorder': _file(__file__),
             'timeout_seconds': manifest['configuration']['timeout_seconds']}
    _write(output/'started.private.json', start)
    with (output/'recorder.source.py').open('xb') as stream:
        stream.write(Path(__file__).read_bytes()); stream.flush(); os.fsync(stream.fileno())
    if _file(output/'recorder.source.py') != start['recorder']:
        raise ValueError('Recorder changed during evidence preparation')
    process = None; error = None; code = None; state = 'ERROR'; inventory = []
    with (output/'stdout.private.log').open('xb') as stdout, (output/'stderr.private.log').open('xb') as stderr:
        try:
            kwargs = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
            process = subprocess.Popen(command, cwd=repo, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, shell=False, **kwargs)
            code = process.wait(timeout=start['timeout_seconds'])
            state = 'EXITED_ZERO' if code == 0 else 'PROCESS_ERROR'
        except subprocess.TimeoutExpired:
            state = 'TIMED_OUT'; error = 'TimeoutExpired'
        except KeyboardInterrupt:
            state = 'ABORTED'; error = 'KeyboardInterrupt'
        except OSError as exc:
            error = type(exc).__name__
        finally:
            if process is not None and process.poll() is None:
                _stop(process)
            if process is not None: code = process.returncode
            for stream in (stdout, stderr): stream.flush(); os.fsync(stream.fileno())
    postflight = None
    try:
        postflight = verify_current(output/'provenance')
        if _file(executable) != tool: raise ValueError('Executable changed during execution')
        if _file(__file__) != start['recorder']: raise ValueError('Recorder changed during execution')
        _write(output/'postflight.private.json', postflight)
    except (ValueError, OSError) as exc:
        state = 'POSTFLIGHT_REJECTED'; error = type(exc).__name__
    try:
        inventory = _inventory(roots)
    except (ValueError, OSError) as exc:
        if state == 'EXITED_ZERO': state = 'OUTPUT_REJECTED'
        error = error or type(exc).__name__
        inventory = _inventory(roots, allow_missing=True)
    record = {'schema_version': 1, 'mode': 'RECORDED_COMMAND_EXECUTION', 'state': state,
              'run_id': start['run_id'], 'recorded_utc_epoch_ns': time.time_ns(),
              'elapsed_ns': time.perf_counter_ns()-clock, 'process_exit_code': code, 'error_type': error,
              'started_sha256': _file(output/'started.private.json')['sha256'],
              'provenance_sha256': fingerprint, 'postflight_snapshot_matched': postflight is not None and state != 'POSTFLIGHT_REJECTED',
              'record_files': [{'path': name, **_file(output/name)} for name in
                               ('stdout.private.log', 'stderr.private.log', 'started.private.json',
                                'recorder.source.py', 'provenance/manifest.json', 'provenance/manifest.sha256')],
              'artifact_roots': start['artifact_roots'], 'artifacts': inventory,
              'missing_artifact_roots': [str(p) for p in roots if not p.exists()],
              'scientific_result_or_source_authentication_proven': False,
              'limitations': ['Local clock and caller metadata are not independent timestamps/identity/consent.',
                             'Checksums detect changed files relative to this receipt, not a dishonest rewrite of all records.',
                             'Foreground command outcome only; detached jobs are unsupported.',
                             'Process exit/output presence does not establish experimental validity.']}
    if (output/'postflight.private.json').is_file():
        record['record_files'].append({'path': 'postflight.private.json', **_file(output/'postflight.private.json')})
    return _seal(output, record)


def inventory_existing(output, artifact_roots, *, run_id):
    """Bind files observed NOW; never assert an earlier execution time/command."""
    output = _private(output)
    if output.exists(): raise FileExistsError('Preserve prior evidence')
    if not isinstance(run_id, str) or not run_id.strip(): raise ValueError('Run label required')
    roots = [_private(p) for p in artifact_roots]
    if any(output.is_relative_to(p) or p.is_relative_to(output) for p in roots):
        raise ValueError('Inventory and evidence directory must be separate')
    entries = _inventory(roots); output.mkdir(parents=True, exist_ok=False)
    return _seal(output, {'schema_version': 1, 'mode': 'RETROSPECTIVE_ARTIFACT_INVENTORY',
                         'state': 'EXISTING_FILES_BOUND_NOT_EXECUTION_ATTESTED', 'run_id': run_id,
                         'recorded_utc_epoch_ns': time.time_ns(), 'started_utc_epoch_ns': None,
                         'command': None, 'process_exit_code': None, 'artifact_roots': [str(p) for p in roots],
                         'record_files': [], 'artifacts': entries,
                         'scientific_result_or_source_authentication_proven': False,
                         'limitations': ['Inventory created after the run; no historical start/end/command reconstructed.',
                                        'Local checksums are not independent identity/timestamp/consent evidence.']})


def verify(output):
    """Verify historical recorded files without requiring today's code/env match."""
    output = _private(output); raw = (output/'receipt.private.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != (output/'receipt.sha256').read_text().strip():
        raise ValueError('Receipt bytes changed')
    record = decode(raw)
    if record.get('schema_version') != 1 or record.get('mode') not in ('RECORDED_COMMAND_EXECUTION', 'RETROSPECTIVE_ARTIFACT_INVENTORY'):
        raise ValueError('Unsupported execution evidence')
    for row in record['record_files']:
        path = output/row['path']
        if not path.resolve().is_relative_to(output) or _file(path) != {k: row[k] for k in ('bytes', 'sha256')}:
            raise ValueError('Recorded evidence file changed')
    allow_missing = record['mode'] == 'RECORDED_COMMAND_EXECUTION' and record['state'] != 'EXITED_ZERO'
    if ([str(p) for p in map(_private, record['artifact_roots']) if not p.exists()] != record.get('missing_artifact_roots', [])
            or _inventory(record['artifact_roots'], allow_missing=allow_missing) != record['artifacts']):
        raise ValueError('Output set/bytes changed, removed or added')
    if record['mode'] == 'RECORDED_COMMAND_EXECUTION':
        start = decode((output/'started.private.json').read_bytes()); manifest, fingerprint = read(output/'provenance')
        if (fingerprint != record['provenance_sha256'] or fingerprint != start['provenance_sha256']
                or start['run_id'] != record['run_id'] or start['run_id'] != manifest['configuration']['run_id']
                or manifest['created_utc_epoch_ns'] > start['started_utc_epoch_ns']
                or record['recorded_utc_epoch_ns'] < start['started_utc_epoch_ns']
                or _file(output/'started.private.json')['sha256'] != record['started_sha256']):
            raise ValueError('Run/provenance chronology or linkage mismatch')
        if record['postflight_snapshot_matched']:
            post = decode((output/'postflight.private.json').read_bytes())
            if post['manifest_sha256'] != fingerprint or post['status'] != 'CURRENT_SNAPSHOT_MATCHES':
                raise ValueError('Postflight linkage mismatch')
        if record['state'] == 'EXITED_ZERO' and (record['process_exit_code'] != 0 or not record['postflight_snapshot_matched']):
            raise ValueError('Successful command requires zero exit and matching snapshot')
    return {'integrity': 'RECORDED_FILES_MATCH', 'mode': record['mode'], 'state': record['state'],
            'artifact_files_n': len(record['artifacts']), 'scientific_result_or_source_authentication_proven': False}


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='action', required=True)
    check = sub.add_parser('verify'); check.add_argument('--record', type=Path, required=True)
    old = sub.add_parser('inventory'); old.add_argument('--record', type=Path, required=True)
    old.add_argument('--run-id', required=True); old.add_argument('--artifact-root', action='append', type=Path, required=True)
    fresh = sub.add_parser('run')
    for field in ('config', 'repo', 'record'): fresh.add_argument('--'+field, type=Path, required=True)
    fresh.add_argument('--artifact-root', action='append', type=Path, required=True)
    fresh.add_argument('command', nargs=argparse.REMAINDER)
    args = p.parse_args()
    if args.action == 'run':
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        record = run(args.config, args.repo, args.record, command, args.artifact_root)
        print(json.dumps(verify(args.record)))
        if record['state'] != 'EXITED_ZERO': raise SystemExit(2)
    elif args.action == 'inventory':
        inventory_existing(args.record, args.artifact_root, run_id=args.run_id)
        print(json.dumps(verify(args.record)))
    else: print(json.dumps(verify(args.record)))


if __name__ == '__main__': main()
