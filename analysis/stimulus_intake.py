"""Local research intake; keep outputs outside all repository/web roots.

Inventories video/archive candidates without treating copies as new captures.
Does not grant rights, infer missing originals, or approve experiment stimuli.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZipFile, BadZipFile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root, out = args.workspace.resolve(), args.output.resolve()
    if out.exists():
        parser.error('Output must be new')
    if ('private_artifacts' not in out.parts
            or any((parent / '.git').exists() for parent in out.parents)):
        parser.error('Output must be in private_artifacts outside repository roots')
    out.mkdir(parents=True)
    videos, archives, errors = [], [], []
    excluded = {'.git', '.venv', 'venv', 'node_modules', '__pycache__',
                'private_artifacts', 'private_tools'}
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in excluded)
        for name in sorted(files):
            path = Path(folder) / name
            suffix = path.suffix.lower()
            if suffix not in {'.mp4', '.mov', '.avi', '.webm', '.mkv', '.zip'}:
                continue
            relative = str(path.relative_to(root))
            if suffix == '.zip':
                try:
                    with ZipFile(path) as z:
                        members = [{'member': item.filename, 'bytes': item.file_size,
                                    'crc32': item.CRC} for item in z.infolist()
                                   if Path(item.filename).suffix.lower() in
                                   {'.mp4', '.mov', '.avi', '.webm', '.mkv', '.zip'}]
                    archives.append({'path': relative, 'media_members': members,
                                     'nested_archives_not_expanded': True})
                except (BadZipFile, OSError) as exc:
                    errors.append({'path': relative, 'error': str(exc)})
            else:
                videos.append({'path': relative, 'bytes': path.stat().st_size,
                               'sha256': digest(path)})
    groups = {}
    for video in videos:
        groups.setdefault(video['sha256'], []).append(video['path'])
    report = {'scope': str(root), 'excluded_directory_names': sorted(excluded),
              'videos': videos, 'archives': archives, 'errors': errors,
              'unique_video_bytes': len(groups), 'video_files': len(videos),
              'duplicate_groups': [p for p in groups.values() if len(p) > 1],
              'rights_status': 'UNREVIEWED', 'release_allowed': False,
              'limitations': ['Byte identity is not capture/family independence.',
                              'Nested archives, cloud and paths outside workspace not audited.',
                              'Private generated artifacts excluded; inspect known original separately.']}
    (out / 'inventory.private.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'video_files': len(videos), 'unique_video_bytes': len(groups),
                      'archives': len(archives), 'errors': len(errors)}))


if __name__ == '__main__':
    main()
