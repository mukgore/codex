"""Stage user-downloaded MANO ZIP files without deserializing model pickles."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

from .journal import REPO

MAX_TOTAL=512*1024*1024
MAX_FILE=128*1024*1024


def _digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()


def stage_mano(archive_path, output):
    source=Path(archive_path).resolve(strict=True);root=Path(output).resolve()
    if not root.is_relative_to(REPO.parent/'private_artifacts'):
        raise ValueError('Use the dedicated private_artifacts tree')
    if root.exists():raise FileExistsError(root)
    archive_hash=_digest(source) if source.stat().st_size<=MAX_TOTAL else None
    if archive_hash is None:raise ValueError('Archive exceeds byte budget')
    with zipfile.ZipFile(source) as archive:
        members=archive.infolist()
        if len(members)>10000 or sum(x.file_size for x in members)>MAX_TOTAL:raise ValueError('Archive expansion budget exceeded')
        names=set();files={}
        for entry in members:
            name=entry.filename;path=PurePosixPath(name)
            if ('\\' in name or ':' in name or path.is_absolute() or '..' in path.parts or
                    any(p.endswith((' ','.')) for p in path.parts) or
                    stat.S_IFMT(entry.external_attr>>16)==stat.S_IFLNK or entry.flag_bits&1):
                raise ValueError('Unsafe or encrypted archive member')
            key=name.casefold()
            if key in names:raise ValueError('Duplicate archive member')
            names.add(key)
            if not entry.is_dir():files[name]=entry
        selected={}
        for role in ('MANO_LEFT.pkl','MANO_RIGHT.pkl'):
            matches=[name for name in files if PurePosixPath(name).name==role]
            if len(matches)!=1:raise ValueError('Exactly one official model file per hand required')
            selected[role]=files[matches[0]]
        parents={PurePosixPath(entry.filename).parent for entry in selected.values()}
        if len(parents)!=1:raise ValueError('Left and right model versions must share a directory')
        parent=next(iter(parents))
        for name,entry in files.items():
            path=PurePosixPath(name)
            if path.parent==parent and path.name.lower() in ('license.txt','info.txt'):selected[path.name]=entry
        if not any(name.lower()=='license.txt' for name in selected):
            raise ValueError('Keep the official accompanying LICENSE.txt; do not stage stripped model files')
        if any(not 0<entry.file_size<=MAX_FILE for entry in selected.values()):raise ValueError('Empty or oversized model/license file')
        root.mkdir(parents=True,exist_ok=False);models=root/'models';models.mkdir()
        records=[]
        for name,entry in selected.items():
            total=0;digest=hashlib.sha256()
            with archive.open(entry) as incoming,(models/name).open('xb') as outgoing:
                for chunk in iter(lambda:incoming.read(1024*1024),b''):
                    total+=len(chunk)
                    if total>entry.file_size:raise ValueError('Member exceeds declared size')
                    digest.update(chunk);outgoing.write(chunk)
            if total!=entry.file_size:raise ValueError('Truncated member')
            records.append({'filename':name,'bytes':total,'sha256':digest.hexdigest()})
    if _digest(source)!=archive_hash:raise ValueError('Archive changed during staging')
    report={'schema_version':1,'state':'FILES_STAGED_NOT_LOADED','archive_sha256':archive_hash,
            'files':records,'pickle_deserialized':False,'release_allowed':False,
            'rights_status':'UNREVIEWED','source':'user_supplied_download_claim_not_independently_authenticated',
            'limitations':['filenames/hash/CRC do not prove valid MANO parameter structure',
                           'no license approval or permission to redistribute models',
                           'no HaMeR/Text2HOI inference has run']}
    with (root/'asset_manifest.json').open('x',encoding='utf8') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();report=stage_mano(args.archive,args.output)
    print(json.dumps({'state':report['state'],'files':len(report['files']),'pickle_deserialized':False}))
