"""Export recorded aggregate region review; raw masks/mesh coordinates stay private."""
import argparse
import csv
import json
from pathlib import Path

from analysis.export_shared_camera_timings import read_bound
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def export(root,record,report,timings):
    root,record=_private(root),_private(record);report,timings=Path(report).resolve(),Path(timings).resolve()
    if report.exists() or timings.exists():raise FileExistsError('Fresh exports required')
    if any(p.is_relative_to(r) for p in (report,timings) for r in (root,record)):
        raise ValueError('Never add exports within sealed evidence/source roots')
    summary,status,manifest=read_bound(root,record)
    if (summary['cases_n']!=32 or summary['amodal_union_frames_n']!=800
            or summary['journal_status']!='COMPLETED' or summary['release_allowed'] is not False
            or summary['new_video_created'] or summary['prior_protection_shrunk']):
        raise ValueError('Completed recorded no-shrink/no-new-video union audit required')
    rows=[]
    for case in summary['cases']:
        if (case['frames_n']!=25 or case['audit_wall_ns']<=0 or
                case['ended_utc_epoch_ns']<case['started_utc_epoch_ns']):
            raise ValueError('Actual complete audit interval required')
        rows.append({**case,'audit_wall_seconds':case['audit_wall_ns']/1e9,
                     'audit_own_process_cpu_seconds':case['audit_own_process_cpu_ns']/1e9})
    summary.update(execution_record=status,producer_code_commit=manifest['code_commit'],
                   recorded_input_files_n=len(manifest['inputs']),dependency_pins_n=len(manifest['pinned_versions']),
                   timing_scope='existing video inspection and new union raster audit; no new generation or encoding time',
                   public_scope='aggregate geometry/QC/timing only; no vertex/face IDs, centroids, matrices or amodal masks')
    with timings.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with report.open('x',encoding='utf-8') as stream:json.dump(summary,stream,indent=2);stream.write('\n')
    verify(record)
    return {'cases_n':len(rows),'previous_masked_pairs_n':summary['original_masked_pairs_n'],
            'additional_union_passed_n':summary['original_masked_pairs_passing_added_union_QA_n'],
            'additional_union_hold_n':summary['original_masked_pairs_with_additional_hold_n']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','record','report','timings'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(export(a.root,a.record,a.report,a.timings)))
