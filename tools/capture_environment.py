"""Read-only environment snapshot. Does not install or repair dependencies."""
import argparse
from datetime import datetime, timezone
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import subprocess

RELEVANT = ('numpy', 'scipy', 'mediapipe', 'protobuf', 'opencv-python',
            'opencv-contrib-python', 'opencv-python-headless', 'matplotlib', 'pypdf', 'openpyxl')


def capture(output):
    output = Path(output).resolve()
    repo = Path(__file__).resolve().parents[1]
    if output.is_relative_to(repo) or repo.is_relative_to(output):
        raise ValueError('Use a new private snapshot directory outside the repository')
    output.mkdir(parents=True, exist_ok=False)
    installed = {dist.metadata['Name'].lower(): dist.version for dist in metadata.distributions() if dist.metadata['Name']}
    check = subprocess.run([__import__('sys').executable, '-m', 'pip', 'check'], capture_output=True, text=True)
    node = subprocess.check_output(['node', '--version'], text=True).strip()
    summary = {'schema_version': 1, 'captured_at': datetime.now(timezone.utc).isoformat(),
               'python': platform.python_version(), 'implementation': platform.python_implementation(),
               'system': platform.system(), 'release': platform.release(), 'architecture': platform.machine(),
               'node': node, 'packages': {name: installed.get(name) for name in RELEVANT},
               'dependency_check_passed': check.returncode == 0,
               'snapshot_is_installable_lock': False, 'collector_installs_packages': False,
               'limitations': ['observed environment, not historical build recovery',
                               'no wheel hashes or isolated clean rebuild',
                               'dependency conflicts require a separately agreed environment repair']}
    private = {'summary': summary, 'installed_distributions': dict(sorted(installed.items())),
               'pip_check_returncode': check.returncode, 'pip_check_stdout': check.stdout,
               'pip_check_stderr': check.stderr}
    (output/'private_environment.json').write_text(json.dumps(private,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
    (output/'public_summary_candidate.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    print(json.dumps(capture(parser.parse_args().output)))
