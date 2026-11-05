"""Run one explicitly pinned private clip under a process-tree deadline."""
import argparse
import json
from pathlib import Path
import sys

from .journal import _private, export_bundle, verify_bundle
from .supervisor import run


def execute(output, *, video, expected_sha256, handcaptcha_root, planned_frames, timeout_seconds):
    root = _private(output); root.mkdir(parents=True, exist_ok=False)
    request = {'condition_id': 'local_batch_extraction_smoke', 'video': str(Path(video).resolve(strict=True)),
               'expected_input_sha256': expected_sha256, 'handcaptcha_root': str(Path(handcaptcha_root).resolve(strict=True)),
               'planned_frames': planned_frames, 'timeout_seconds': timeout_seconds,
               'cache_state': 'uncontrolled_existing_installed_assets_and_os_cache'}
    request_file = root/'request.json'
    request_file.write_text(json.dumps(request, allow_nan=False)+'\n', encoding='utf8')
    result = run([sys.executable, '-m', 'analysis.runtime_benchmark.extraction_worker', '--request', str(request_file)],
                 root/'supervised', cwd=Path(__file__).resolve().parents[2], timeout_seconds=timeout_seconds)
    journal = root/'supervised'/'worker_journal'
    if (journal/'events.jsonl').exists():
        export_bundle(journal, root/'worker_bundle.zip')
        result['bundle_recovered'] = verify_bundle(root/'worker_bundle.zip')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True); parser.add_argument('--video', required=True)
    parser.add_argument('--expected-sha256', required=True); parser.add_argument('--handcaptcha-root', required=True)
    parser.add_argument('--planned-frames', type=int, required=True); parser.add_argument('--timeout-seconds', type=float, required=True)
    args = parser.parse_args()
    result = execute(args.output, video=args.video, expected_sha256=args.expected_sha256,
                     handcaptcha_root=args.handcaptcha_root, planned_frames=args.planned_frames,
                     timeout_seconds=args.timeout_seconds)
    print(json.dumps(result)); sys.exit(0 if result['completed'] else 1)
