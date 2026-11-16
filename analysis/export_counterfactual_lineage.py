"""Public scalar/group-ID lineage inventory; file/geometry hashes stay private."""
import argparse
import json
from pathlib import Path
from analysis.export_shared_camera_timings import read_bound
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def export(root,record,report):
    root,record=_private(root),_private(record);report=Path(report).resolve()
    if report.exists():raise FileExistsError('Fresh export required')
    if report.is_relative_to(root) or report.is_relative_to(record):raise ValueError('Never alter sealed source roots')
    summary,status,manifest=read_bound(root,record)
    if summary['H264_files_n']!=64 or summary['new_video_created'] or summary['release_allowed'] is not False:
        raise ValueError('Bound actual64-file no-new-video inventory required')
    summary.update(execution_record=status,producer_code_commit=manifest['code_commit'],
                   recorded_input_files_n=len(manifest['inputs']),dependency_pins_n=len(manifest['pinned_versions']))
    with report.open('x',encoding='utf-8') as stream:json.dump(summary,stream,indent=2);stream.write('\n')
    verify(record)
    return {k:v for k,v in summary.items() if k not in ('groups','family_definition','scope')}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','record','report'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(export(a.root,a.record,a.report)))
