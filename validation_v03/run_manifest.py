"""Private pre-execution provenance snapshot and post-execution drift check.

Presence/integrity validation is not source consent, honest metadata, camera
authenticity, task completion or a claim of a fully isolated environment.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from validation_v03.session_artifacts import canonical, decode, _private, _read

TEXT_FIELDS=('run_id','protocol_version','scoring_version','challenge_manifest_version',
             'input_protection_version','hardware','browser','os','endpoint','input_exposure')
SCOPES=('offline_coordinate','offline_video','owned_js_fixture','live_camera','human_screening','local_service')
MAX_HASH_BYTES=4*1024**3


def _text(value):
    return isinstance(value,str) and bool(value.strip()) and len(value)<=1024 and value.strip().lower() not in (
        'unknown','todo','tbd','none','unspecified')


def validate_config(config):
    if (not isinstance(config,dict) or type(config.get('schema_version')) is not int or config['schema_version']!=1
            or any(not _text(config.get(key)) for key in TEXT_FIELDS)):
        raise ValueError('Explicit non-placeholder run/protocol/scoring/source/environment metadata required')
    if config.get('execution_scope') not in SCOPES or config.get('split') not in ('diagnostic','development','validation','test'):
        raise ValueError('Known execution scope and split required')
    if config['browser']=='not_applicable_offline' and config['execution_scope'] in ('live_camera','human_screening'):
        raise ValueError('Live camera/human runs require an actual browser description')
    seed=config.get('seed')
    if not ((type(seed) is int and seed>=0) or
            (isinstance(seed,list) and seed and all(type(v) is int and v>=0 for v in seed) and len(set(seed))==len(seed)) or
            (seed is None and _text(config.get('seed_not_applicable_reason')))):
        raise ValueError('Explicit seed(s) or a reason why no seed applies required')
    timeout=config.get('timeout_seconds')
    if type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=86400:
        raise ValueError('Explicit bounded runtime budget required')
    if not isinstance(config.get('parameters'),dict) or not config['parameters']:
        raise ValueError('Explicit experiment parameters required')
    if not isinstance(config.get('code_files'),list) or not config['code_files']:
        raise ValueError('Explicit local code files required')
    if not isinstance(config.get('input_files'),list) or not config['input_files']:
        raise ValueError('Explicit input/reference file list required')
    seen={'run_config'}
    for item in config['input_files']:
        if not isinstance(item,dict) or set(item)!={'id','role','path'} or any(not _text(v) for v in item.values()):
            raise ValueError('Each input requires local id, role and path')
        if item['id'] in seen:raise ValueError('Duplicate input reference id')
        seen.add(item['id'])
    if not _text(config.get('dependency_lock')):raise ValueError('Actual dependency lock file required')


def snapshot_file(path):
    path=Path(path).resolve(strict=True)
    if not path.is_file():raise ValueError('Snapshot input must be a regular local file')
    before=path.stat()
    if not 0<before.st_size<=MAX_HASH_BYTES:raise ValueError('Hash input exceeds explicit byte budget')
    digest=hashlib.sha256();count=0
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            count+=len(block)
            if count>before.st_size:raise ValueError('File grew during hashing')
            digest.update(block)
    after=path.stat()
    if count!=before.st_size or (after.st_size,after.st_mtime_ns)!=(before.st_size,before.st_mtime_ns):
        raise ValueError('File changed during hashing')
    return {'path':str(path),'bytes':count,'sha256':digest.hexdigest()}


def _git(repo,*arguments):
    return subprocess.check_output(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),*arguments],
                                   stderr=subprocess.DEVNULL)


def code_state(repo):
    repo=Path(repo).resolve(strict=True)
    commit=_git(repo,'rev-parse','HEAD').decode().strip()
    difference=_git(repo,'diff','--binary','HEAD','--')
    untracked=[];untracked_bytes=0
    names=_git(repo,'ls-files','--others','--exclude-standard','-z').decode('utf-8').split('\0')
    if len(names)>10001:raise ValueError('Untracked code snapshot budget exceeded')
    for name in sorted(n for n in names if n):
        path=(repo/name).resolve(strict=True)
        if not path.is_relative_to(repo):raise ValueError('Untracked file escapes code repository')
        untracked_bytes+=path.stat().st_size
        if untracked_bytes>64*1024*1024:raise ValueError('Untracked byte budget exceeded')
        item=snapshot_file(path);untracked.append({'path':name,'bytes':item['bytes'],'sha256':item['sha256']})
    if sum(row['bytes'] for row in untracked)>64*1024*1024 or len(difference)>64*1024*1024:
        raise ValueError('Dirty code snapshot budget exceeded')
    return {'code_commit':commit,'dirty_diff_hash':hashlib.sha256(difference+b'\0'+canonical(untracked)).hexdigest(),
            'untracked_files':untracked,'tracked_diff_present':bool(difference)}


def _normalize_name(name):return re.sub(r'[-_.]+','-',name).lower()


def dependency_state(lock):
    lock=Path(lock).resolve(strict=True);pins={}
    if lock.stat().st_size>4*1024*1024:raise ValueError('Dependency lock text exceeds budget')
    for line in lock.read_text(encoding='utf-8-sig').splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)(?:\s+--hash=sha256:[a-f0-9]{64})*',line)
        if not match:raise ValueError('Flat exact-version dependency pins required')
        name,version=_normalize_name(match[1]),match[2]
        if name in pins:raise ValueError('Duplicate dependency pin')
        pins[name]=version
    if not pins:raise ValueError('Dependency lock has no exact pins')
    installed={}
    for distribution in importlib.metadata.distributions():
        name=_normalize_name(distribution.metadata['Name']);version=distribution.version
        if name in installed and installed[name]!=version:raise ValueError('Ambiguous installed package metadata')
        installed[name]=version
    if any(installed.get(name)!=version for name,version in pins.items()):
        raise ValueError('Installed package metadata does not match declared lock')
    return {'dependency_lock_hash':snapshot_file(lock)['sha256'],'lock_path':str(lock),'pinned_versions':pins,
            'installed_versions':dict(sorted(installed.items())),
            'additional_installed_packages':sorted(set(installed)-set(pins)),
            'verification_scope':'exact installed metadata versions; wheel bytes/dependency consistency not reverified'}


def _resolve(base,path):
    path=Path(path)
    return path.resolve(strict=True) if path.is_absolute() else (base/path).resolve(strict=True)


def prepare(config_path,repo,output):
    config_path=Path(config_path).resolve(strict=True);repo=Path(repo).resolve(strict=True)
    raw=_read(config_path);config=decode(raw);validate_config(config)
    output=_private(output)
    if output.exists():raise FileExistsError('Provenance snapshot output already exists')
    total_bytes=0
    def capture(path):
        nonlocal total_bytes
        if total_bytes+Path(path).stat().st_size>MAX_HASH_BYTES:raise ValueError('Total hash budget exceeded')
        value=snapshot_file(path);total_bytes+=value['bytes'];return value
    sources=[{'id':'run_config','role':'configuration',**capture(config_path)}]
    for item in config['input_files']:
        sources.append({'id':item['id'],'role':item['role'],**capture(_resolve(config_path.parent,item['path']))})
    code=[]
    for name in config['code_files']:
        if not _text(name):raise ValueError('Explicit code path required')
        path=_resolve(repo,name)
        if not path.is_relative_to(repo):raise ValueError('Code file escapes declared repository')
        code.append(capture(path))
    if sum(row['bytes'] for row in sources+code)>MAX_HASH_BYTES:raise ValueError('Total hash budget exceeded')
    lock=_resolve(config_path.parent,config['dependency_lock'])
    state=code_state(repo);dependencies=dependency_state(lock)
    manifest={'schema_version':1,'snapshot_role':'before_execution_by_caller',
              'created_utc_epoch_ns':time.time_ns(),'repository':str(repo),'configuration':config,
              **state,**dependencies,'inputs':sources,'code_files':code,
              'python':{'version':sys.version,'executable':sys.executable},
              'tool_sha256':snapshot_file(__file__)['sha256'],
              'limitations':['Metadata/permissions are caller assertions, not independent consent or identity evidence.',
                             'This snapshot does not execute or certify completion of the declared task.',
                             'Dirty/untracked fingerprints are private; do not publish this manifest.']}
    encoded=canonical(manifest);fingerprint=hashlib.sha256(encoded).hexdigest()
    output.mkdir(parents=True,exist_ok=False)
    for name,value in [('manifest.json',encoded),('manifest.sha256',(fingerprint+'\n').encode())]:
        with (output/name).open('xb') as stream:stream.write(value);stream.flush();os.fsync(stream.fileno())
    return manifest,fingerprint


def read(directory):
    directory=_private(directory);raw=_read(directory/'manifest.json')
    fingerprint=(directory/'manifest.sha256').read_text().strip()
    if hashlib.sha256(raw).hexdigest()!=fingerprint:raise ValueError('Provenance manifest bytes changed')
    manifest=decode(raw)
    if manifest.get('schema_version')!=1 or manifest.get('snapshot_role')!='before_execution_by_caller':
        raise ValueError('Unsupported provenance snapshot')
    validate_config(manifest['configuration'])
    return manifest,fingerprint


def verify_current(directory):
    manifest,fingerprint=read(directory)
    for entry in manifest['inputs']+manifest['code_files']:
        actual=snapshot_file(entry['path'])
        if actual['sha256']!=entry['sha256'] or actual['bytes']!=entry['bytes']:
            raise ValueError('Declared input/code bytes drifted since snapshot')
    current=code_state(Path(manifest['repository']))
    if any(current[key]!=manifest[key] for key in ('code_commit','dirty_diff_hash')):
        raise ValueError('Repository code state drifted since snapshot')
    dependencies=dependency_state(manifest['lock_path'])
    if any(dependencies[key]!=manifest[key] for key in ('dependency_lock_hash','installed_versions')):
        raise ValueError('Environment metadata drifted since snapshot')
    if snapshot_file(__file__)['sha256']!=manifest['tool_sha256']:
        raise ValueError('Provenance checker code changed')
    if manifest['python']!={'version':sys.version,'executable':sys.executable}:
        raise ValueError('Python runtime differs from snapshot')
    return {'schema_version':1,'manifest_sha256':fingerprint,'status':'CURRENT_SNAPSHOT_MATCHES',
            'task_completion_proven':False,'source_authentication_proven':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--config',type=Path);group.add_argument('--verify',type=Path)
    p.add_argument('--repo',type=Path);p.add_argument('--output',type=Path)
    args=p.parse_args()
    try:
        if args.config:
            if not args.repo or not args.output:p.error('Prepare requires repo and a new private output')
            _,fingerprint=prepare(args.config,args.repo,args.output)
            result={'status':'PREPARED_NOT_EXECUTED','manifest_sha256':fingerprint}
        else:
            if args.repo or args.output:p.error('Verify never writes or changes repository')
            result=verify_current(args.verify)
    except (OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'REJECTED','error_type':type(error).__name__}),file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(result))


if __name__=='__main__':main()
