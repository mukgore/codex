"""Export actual media timings from author-union guarded rerender only."""
import argparse
import csv
import json
from pathlib import Path
import statistics

from analysis.export_shared_camera_timings import read_bound
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def export(root,record,report,timings):
    root,record=_private(root),_private(record);report,timings=Path(report).resolve(),Path(timings).resolve()
    if report.exists() or timings.exists():raise FileExistsError('Fresh exports required')
    if any(p.is_relative_to(r) for p in (report,timings) for r in (root,record)):
        raise ValueError('Do not alter sealed experiment roots')
    summary,status,manifest=read_bound(root,record)
    scope=json.loads((root/'protection_scope.private.json').read_text())
    if (summary['protection_mode']!='author_region_union' or summary['legacy_reproduction_only']
            or summary['prior_protection_shrunk'] or summary['rendered_source_frames_n']!=800
            or summary['runtime_journal_status']!='COMPLETED' or summary['release_allowed'] is not False
            or scope['mode']!='author_region_union'
            or any(scope['hands'][hand]['author_finger_centroid_matches_n']!=15 for hand in ('right','left'))):
        raise ValueError('Completed recorded author-union guard without fallback required')
    rows=[]
    for media in summary['media']:
        t=media['timing']
        if t['state']!='COMPLETED' or t['video_ready_wall_ns'] is None or not 0<t['video_ready_wall_ns']<=t['validated_pipeline_wall_ns']:
            raise ValueError('Actual completed media timing required')
        row={'case':media['case'],'view':media['view'],'kind':media['kind'],
            'protection_mode':summary['protection_mode'],'frames_n':media['frames_n'],'fps':media['fps'],
            'motion_last_frame_seconds':(media['frames_n']-1)/media['fps'],
            'encoded_clip_duration_seconds':media['frames_n']/media['fps'],'video_bytes':media['video_bytes'],
            'started_utc_epoch_ns':t['started_utc_epoch_ns'],'ended_utc_epoch_ns':t['ended_utc_epoch_ns'],
            'ready_wall_seconds':t['video_ready_wall_ns']/1e9,'validated_wall_seconds':t['validated_pipeline_wall_ns']/1e9,
            'own_process_cpu_seconds':t['validated_pipeline_process_cpu_ns']/1e9,
            'ready_boundary':media['ready_boundary'],'timing_boundary':t['boundary'],
            'upstream_parent_state':media['parent_state'],'new_model_inference':False,
            'child_process_cpu_measured':False,'shared_setup_included':False}
        row.update({key+'_wall_seconds':value['wall_ns']/1e9 for key,value in t['phases'].items()})
        rows.append(row)
    stats={}
    for kind in sorted({r['kind'] for r in rows}):
        group=[r for r in rows if r['kind']==kind];stats[kind]={'videos_n':len(group)}
        for field in ('ready_wall_seconds','validated_wall_seconds'):
            values=[r[field] for r in group]
            stats[kind][field]={'min':min(values),'median':statistics.median(values),'max':max(values)}
    summary.update(execution_record=status,producer_code_commit=manifest['code_commit'],
        recorded_input_files_n=len(manifest['inputs']),dependency_pins_n=len(manifest['pinned_versions']),
        author_neutral_centroid_matches_n={h:scope['hands'][h]['author_finger_centroid_matches_n'] for h in ('right','left')},
        timing_rows_n=len(rows),timing_statistics=stats,
        timing_scope='actual new rerender/masked-media times only; cached source model inference and shared setup excluded',
        public_scope='synthetic decisions/timing aggregates only; no source mesh coordinates, ROI IDs/masks or individual hashes')
    fields=list(dict.fromkeys(key for row in rows for key in row))
    with timings.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    with report.open('x',encoding='utf-8') as stream:json.dump(summary,stream,indent=2);stream.write('\n')
    verify(record)
    return {'timing_rows_n':len(rows),'masked_candidates_n':summary['masked_candidate_videos_n'],
            'H264_renditions_n':summary['H264_rendition_videos_n'],'timing_statistics':stats}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','record','report','timings'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(export(a.root,a.record,a.report,a.timings)))
