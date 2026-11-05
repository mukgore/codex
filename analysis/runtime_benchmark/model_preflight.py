"""Inventory core model assets without importing models or unpickling weights."""
import argparse
import hashlib
import json
from pathlib import Path

from .journal import REPO


def inspect(profile, root, output):
    profiles=json.loads(Path(__file__).with_name('model_profiles.json').read_text(encoding='utf8'))
    if profile not in profiles:raise ValueError('Known explicit profile required')
    spec=profiles[profile];root=Path(root).resolve(strict=True);output=Path(output).resolve()
    if not root.is_dir() or not output.is_relative_to(REPO.parent/'private_artifacts'):
        raise ValueError('Existing asset root and dedicated private report path required')
    if output.exists():raise FileExistsError(output)
    missing=[];files=[];total=0
    for relative in spec['files']:
        path=(root/relative).resolve()
        if not path.is_relative_to(root):raise ValueError('Asset path escapes root')
        if not path.is_file() or path.stat().st_size==0:missing.append(relative);continue
        before=path.stat();total+=before.st_size
        if total>16*1024**3:raise ValueError('Core file hashing budget exceeded')
        value=hashlib.sha256();count=0
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):
                count+=len(chunk)
                if count>before.st_size or count>8*1024**3:raise ValueError('Changing/oversized asset')
                value.update(chunk)
        after=path.stat()
        if count!=before.st_size or (after.st_size,after.st_mtime_ns)!=(before.st_size,before.st_mtime_ns):
            raise ValueError('Asset changed during inventory')
        files.append({'path':relative,'bytes':count,'sha256':value.hexdigest()})
    for relative in spec['directories']:
        path=(root/relative).resolve()
        if not path.is_relative_to(root):raise ValueError('Directory escapes root')
        if not path.is_dir() or not any(path.iterdir()):missing.append(relative+'/')
    result={'schema_version':1,'profile':profile,'repository':spec['repository'],
            'expected_source_revision':spec['expected_revision'],'actual_revision_verified':False,
            'state':'UNAVAILABLE_MISSING_CORE_ASSETS' if missing else 'CORE_ASSETS_PRESENT_NOT_LOADED',
            'missing':missing,'files':files,'remaining_requirements':spec['additional_requirements'],
            'models_imported':False,'weights_deserialized':False,'inference_ready':False,'release_allowed':False}
    output.mkdir(parents=True,exist_ok=False)
    (output/'preflight.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('profile','root','output'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();result=inspect(args.profile,args.root,args.output)
    print(json.dumps({'state':result['state'],'missing_count':len(result['missing']),'inference_ready':False}))
