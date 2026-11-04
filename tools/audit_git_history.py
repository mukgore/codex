"""Bounded, value-redacted audit of reachable Git blobs and ZIP members.

Detailed findings are private. This is a signature/inventory audit, not proof
that every photograph, video, personal datum or credential has been identified.
"""
import argparse
from collections import Counter
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

PATTERNS = {
    'private_key_marker': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'github_token_shape': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{40,})'),
    'aws_access_key_shape': re.compile(rb'(?:AKIA|ASIA)[0-9A-Z]{16}'),
    'api_secret_shape': re.compile(rb'sk-[A-Za-z0-9_-]{20,}'),
}
CHUNK = 1024 * 1024
MAX_ZIP = 64 * CHUNK
MAX_UNPACKED = 128 * CHUNK


def inspect_stream(stream, size):
    remaining = size
    overlap = b''
    found = set()
    raw_coordinates = False
    while remaining:
        chunk = stream.read(min(CHUNK, remaining))
        if not chunk:
            raise ValueError('Truncated object/member')
        remaining -= len(chunk)
        value = overlap + chunk
        found.update(name for name, pattern in PATTERNS.items() if pattern.search(value))
        raw_coordinates |= bool(re.search(rb'"landmarks(?:_px|_world|_norm)?"\s*:', value))
        overlap = value[-512:]
    return sorted(found), raw_coordinates


def audit(repo, output):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if output.is_relative_to(repo):
        raise ValueError('Private audit output must be outside repository')
    def git(*args, **kwargs):
        return subprocess.check_output(['git', '-C', str(repo), *args], **kwargs)
    refs = git('for-each-ref', '--format=%(refname) %(objectname)').decode().splitlines()
    objects = {}
    for line in git('rev-list', '--objects', '--all').decode('utf8').splitlines():
        sha, _, path = line.partition(' ')
        objects.setdefault(sha, set()).add(path)
    listing = git('cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize)',
                  input=('\n'.join(objects)+'\n').encode()).decode().splitlines()
    blobs = [(s, int(n)) for s, kind, n in (line.split() for line in listing) if kind == 'blob']
    output.mkdir(parents=True, exist_ok=False)
    findings, inventory, skipped = [], Counter(), []
    process = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    total_bytes, zip_members = 0, 0
    try:
        for sha, size in blobs:
            process.stdin.write((sha+'\n').encode());process.stdin.flush()
            header = process.stdout.readline().decode().split()
            if header != [sha, 'blob', str(size)]:
                raise ValueError('Unexpected Git object header')
            paths = sorted(p for p in objects[sha] if p)
            is_zip = any(p.lower().endswith('.zip') for p in paths)
            if is_zip and size <= MAX_ZIP:
                payload = process.stdout.read(size)
                if len(payload) != size:
                    raise ValueError('Truncated ZIP blob')
                matches, coordinates = inspect_stream(io.BytesIO(payload), size)
            else:
                payload = None
                matches, coordinates = inspect_stream(process.stdout, size)
            if process.stdout.read(1) != b'\n':
                raise ValueError('Unexpected Git object boundary')
            total_bytes += size
            suffixes = {Path(p).suffix.lower() for p in paths}
            inventory['blobs_with_media_or_archive_paths'] += bool(suffixes & {'.mp4','.avi','.mov','.png','.jpg','.jpeg','.zip'})
            inventory['json_coordinate_candidate_blobs'] += coordinates and '.json' in suffixes
            if matches:
                findings.append({'object': sha, 'paths': paths, 'categories': matches})
            if is_zip:
                if payload is None:
                    skipped.append({'object':sha, 'reason':'archive exceeds compressed-size budget'})
                    continue
                try:
                    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                        unpacked = 0
                        for member in archive.infolist():
                            if member.is_dir():continue
                            if member.file_size > MAX_ZIP or unpacked + member.file_size > MAX_UNPACKED:
                                skipped.append({'object':sha,'member':member.filename,'reason':'archive expansion budget'})
                                continue
                            with archive.open(member) as stream:
                                categories, raw = inspect_stream(stream, member.file_size)
                            unpacked += member.file_size;zip_members += 1
                            inventory['archive_coordinate_candidate_members'] += raw and member.filename.lower().endswith('.json')
                            if categories:findings.append({'object':sha,'member':member.filename,'categories':categories})
                except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as error:
                    skipped.append({'object':sha,'reason':type(error).__name__})
    finally:
        process.stdin.close();process.stdout.close();process.wait()
    if process.returncode:
        raise ValueError('Git object reader failed')
    summary = {'schema_version':1,'reachable_blobs_scanned':len(blobs),'blob_bytes_scanned':total_bytes,
               'zip_members_scanned':zip_members,'inventory':dict(inventory),
               'signature_candidate_items':len(findings),'signature_categories':dict(Counter(c for f in findings for c in f['categories'])),
               'skipped_archive_items':len(skipped),
               'scope':'all locally reachable refs after remote heads/tags fetch',
               'limitations':['no dangling/deleted/hidden GitHub refs','no nested/encrypted archive proof',
                              'no semantic review of every image/video','signature non-detection is not absence of secrets or personal data']}
    (output/'private_findings.json').write_text(json.dumps({'refs':refs,'findings':findings,'skipped':skipped},ensure_ascii=True,indent=2)+'\n',encoding='utf8')
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True);parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.repo, args.output)))
