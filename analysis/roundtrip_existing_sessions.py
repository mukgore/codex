"""Round-trip owned saved sessions and actual-JS synthetic exports in private storage."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from validation_v03.session_artifacts import canonical, inspect, load, save


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-root',required=True,type=Path)
    p.add_argument('--source-root',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();out=args.output.resolve()
    if out.exists() or 'private_artifacts' not in out.parts or any((parent/'.git').exists() for parent in out.parents):
        p.error('New private output outside repositories required')
    paths=sorted(args.raw_root.glob('2*/2*/*.json'))
    if len(paths)!=18:p.error('This archived-cohort diagnostic expects the known 18 sessions')
    out.mkdir(parents=True);summaries=[];lineage=[]
    for index,path in enumerate(paths):
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        folder=out/f'legacy_{index+1:02}'
        summary=save(path,folder);restored,reloaded=load(folder)
        if (summary!=reloaded or canonical(restored)!=canonical(json.loads(path.read_text(encoding='utf-8-sig')))
                or hashlib.sha256(path.read_bytes()).hexdigest()!=before):
            raise ValueError('Archived source or reloaded data changed')
        summaries.append(summary)
        lineage.append({'artifact':folder.name,'source_relative_path':str(path.relative_to(args.raw_root)),
                        'source_sha256':before})
    fixture=json.loads(subprocess.check_output(['node',str(Path(__file__).with_name('export_event_fixtures.cjs')),
                                               str(args.source_root.resolve())]))
    synthetic=[]
    for name,payload in fixture['fixtures'].items():
        path=out/f'{name}.source.json';path.write_bytes(canonical(payload))
        synthetic.append({'case':name,**save(path,out/name)})
    report={'scope':'saved_legacy_session_storage_and_owned_js_export_roundtrip',
            'legacy_sessions_attempted':len(paths),'legacy_sessions_verified':len(summaries),
            'legacy_segments':sum(x['segments_n'] for x in summaries),
            'legacy_segment_frames':sum(x['segment_frames_n'] for x in summaries),
            'legacy_missing_frames':sum(x['missing_segment_frames_n'] for x in summaries),
            'source_bytes_unchanged':True,'synthetic_js_exports_verified':synthetic,
            'new_human_observations':0,'source_authentication_proven':False,
            'limitations':['Checks persisted layout/counts/timelines and exact local round-trip.',
                           'No recovery of missing historical build, image size, playback/wait events or camera truth.',
                           'Synthetic exported events are not participant trials or authentication results.']}
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (out/'lineage.private.json').write_text(json.dumps(lineage,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('legacy_sessions_verified','legacy_segment_frames',
                                         'legacy_missing_frames','new_human_observations')}))


if __name__=='__main__':main()
