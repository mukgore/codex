"""Batch MediaPipe adapter for the owned-process supervisor, not online scoring."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys

from .journal import Journal


def _digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''): value.update(chunk)
    return value.hexdigest()


def execute(request):
    planned = request['planned_frames']
    manifest = {'condition_id': request['condition_id'], 'endpoint': 'offline_batch_mediapipe_extraction',
                'input_exposure': 'full_unmasked_video', 'cache_state': request['cache_state'],
                'planned_frames': planned, 'timeout_seconds': request['timeout_seconds'],
                'expected_input_sha256': request['expected_input_sha256'],
                'scope': 'batch_wall_time_including_resource_worker_and_logging_not_online_authentication'}
    journal = Journal(os.environ['RUNTIME_JOURNAL_DIRECTORY'], manifest)
    try:
        with journal.stage('input_and_adapter_integrity'):
            source = Path(request['video']).resolve(strict=True)
            root = Path(request['handcaptcha_root']).resolve(strict=True)
            if source.is_relative_to(root) or root.is_relative_to(source):
                raise ValueError('Use a private input outside the repository')
            if _digest(source) != request['expected_input_sha256']:
                raise ValueError('Input hash mismatch')
            adapter_files = {name: _digest(root/'dataset_pipeline'/name) for name in
                             ('stage1_extract.py', 'resource_worker.py', 'common.py')}
        missing_dependency = False
        with journal.stage('import_runtime'):
            sys.path.insert(0, str(root))
            try:
                from dataset_pipeline.stage1_extract import extract_landmarks
            except ModuleNotFoundError:
                # No package is installed or downloaded automatically.
                missing_dependency = True
        if missing_dependency:
            journal.finish('UNAVAILABLE', reason='missing_extraction_dependency')
            return {'status': 'UNAVAILABLE'}
        with journal.stage('batch_extract'):
            frames, info = extract_landmarks(str(source), worker_timeout_seconds=request['timeout_seconds'])
        with journal.stage('check_and_account_frames'):
            if len(frames) != planned or info['decoded_frames'] != planned or not info['timestamps_monotonic']:
                raise ValueError('Planned frame count or decoder timeline mismatch')
            for index, frame in enumerate(frames):
                if frame['frame_idx'] != index or type(frame['detected']) is not bool:
                    raise ValueError('Incomplete or malformed extraction denominator')
                journal.frame_completed(index, frame['detected'])
            if _digest(source) != request['expected_input_sha256']:
                raise ValueError('Input changed during extraction')
            if any(_digest(root/'dataset_pipeline'/name) != value for name, value in adapter_files.items()):
                raise ValueError('Adapter changed during extraction')
            versions = {name: importlib.metadata.version(name) for name in ('mediapipe', 'numpy', 'protobuf')}
            result = {'schema_version': 1, 'model': 'installed_mediapipe_hands', 'versions': versions,
                      'input_sha256': request['expected_input_sha256'], 'adapter_files': adapter_files,
                      'planned_frames': planned, 'decoded_frames': len(frames),
                      'detected_frames': sum(frame['detected'] for frame in frames),
                      'timestamps_monotonic': info['timestamps_monotonic'],
                      'resource_fingerprint': info.get('resource_fingerprint'),
                      'coordinate_output_saved': False, 'scope': manifest['scope'],
                      'limitations': ['not HaMeR/Text2HOI or an attack benchmark',
                                      'frame events accounted after batch extraction, not per-frame latency',
                                      'existing environment may have metadata dependency conflicts',
                                      'cold/warm resource and OS cache not controlled by this adapter']}
            with (journal.directory/'extraction_result.json').open('x', encoding='utf8') as stream:
                json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
        journal.finish('COMPLETED')
        return result
    finally:
        if not journal.closed: journal.close_without_terminal()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--request', required=True)
    execute(json.loads(Path(parser.parse_args().request).read_text(encoding='utf8')))
