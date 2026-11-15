"""Export actual native-counterfactual and media timings without raw geometry."""
import argparse
import csv
import json
from pathlib import Path

from analysis.export_shared_camera_timings import read_bound
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def write_csv(path,rows):
    fields=list(dict.fromkeys(key for row in rows for key in row))
    with path.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def export(native,native_record,display,display_record,report,native_timings,video_timings):
    native,native_record,display,display_record=map(_private,(native,native_record,display,display_record))
    paths=list(map(lambda x:Path(x).resolve(),(report,native_timings,video_timings)))
    if any(p.exists() for p in paths):raise FileExistsError('Fresh public export paths required')
    if any(p.is_relative_to(r) for p in paths for r in (native,native_record,display,display_record)):
        raise ValueError('Do not alter sealed source/evidence roots')
    ns,nstatus,nmanifest=read_bound(native,native_record);ds,dstatus,dmanifest=read_bound(display,display_record)
    if (ns['cases_n']!=32 or ns['native_forward_frames_n']!=802 or ds['cases_n']!=64
            or ds['rendered_source_frames_n']!=1600 or ds['zero_control_views_n']!=16
            or ns['release_allowed'] is not False or ds['release_allowed'] is not False):
        raise ValueError('Registered complete quarantined native and frozen-display runs required')
    native_rows=[];media_rows=[]
    for case in ns['cases']:
        t=case['timing']
        if t['state']!='COMPLETED' or t['video_ready_wall_ns'] is not None:
            raise ValueError('Native generation is not a completed encoded video')
        native_rows.append({'case_id':case['case_id'],'parent_case':case['parent_case'],'hand':case['hand'],
            'policy':case['policy'],'delta_degrees':case['delta_degrees'],'frames_n':case['frames_n'],
            'started_utc_epoch_ns':t['started_utc_epoch_ns'],'ended_utc_epoch_ns':t['ended_utc_epoch_ns'],
            'native_generation_wall_seconds':t['validated_pipeline_wall_ns']/1e9,
            'native_generation_own_cpu_seconds':t['validated_pipeline_process_cpu_ns']/1e9,
            'new_video_created':False,'timing_boundary':t['boundary']})
    for media in ds['media']:
        t=media['timing']
        if t['state']!='COMPLETED' or t['video_ready_wall_ns'] is None or not 0<t['video_ready_wall_ns']<=t['validated_pipeline_wall_ns']:
            raise ValueError('Actual positive completed media timing required')
        row={'case_id':media['case_id'],'parent_case':media['parent_case'],'view':media['view'],'kind':media['kind'],
            'frames_n':media['frames_n'],'fps':media['fps'],'video_bytes':media['video_bytes'],
            'motion_last_frame_seconds':24/media['fps'],'encoded_clip_duration_seconds':25/media['fps'],
            'started_utc_epoch_ns':t['started_utc_epoch_ns'],'ended_utc_epoch_ns':t['ended_utc_epoch_ns'],
            'ready_wall_seconds':t['video_ready_wall_ns']/1e9,'validated_wall_seconds':t['validated_pipeline_wall_ns']/1e9,
            'own_process_cpu_seconds':t['validated_pipeline_process_cpu_ns']/1e9,
            'ready_boundary':media['ready_boundary'],'timing_boundary':t['boundary'],
            'upstream_native_generation_included':False,'child_process_cpu_measured':False}
        row.update({key+'_wall_seconds':value['wall_ns']/1e9 for key,value in t['phases'].items()})
        media_rows.append(row)
    groups=[]
    for delta in (0.,-5.,5.,10.):
        rows=[c for c in ds['cases'] if c['delta_degrees']==delta]
        groups.append({'delta_degrees':delta,'case_views_n':len(rows),
            'masked_pairs_created_n':sum(c['H264_created'] for c in rows),
            'source_exact_pixels_n':sum(c['source_comparison']['exact_decoded_pixels_equal'] for c in rows),
            'masked_exact_pixels_n':sum(c['masked_comparison'] is not None and c['masked_comparison']['exact_decoded_pixels_equal'] for c in rows),
            'H264_exact_pixels_n':sum(c['H264_comparison'] is not None and c['H264_comparison']['exact_decoded_pixels_equal'] for c in rows),
            'model_alternative_with_exact_final_pixels_n':sum(c['model_alternative_with_exact_final_pixels'] for c in rows)})
    result={'native_generation':ns,'frozen_display':ds,'comparison_groups':groups,
        'execution':{'native':nstatus,'display':dstatus,'native_producer_commit':nmanifest['code_commit'],
            'display_producer_commit':dmanifest['code_commit'],'native_inputs_n':len(nmanifest['inputs']),
            'display_inputs_n':len(dmanifest['inputs'])},
        'native_timing_rows_n':len(native_rows),'video_timing_rows_n':len(media_rows),
        'scope':'generator-side model-constrained alternatives and actual final-display equality only; no human answer/attack admission',
        'source_motion_first_second_frozen':True,
        'UI_note':'existing reveal/fade uses the same first static frame; preserving source-motion first second is an additional control, not UI64 execution',
        'timing_note':'native coordinate generation and later cached-parent media preparation are separate offline intervals; no synthesized end-to-end latency',
        'public_scope':'synthetic scalar outcomes only; raw geometry/poses/masks/individual hashes remain private','release_allowed':False}
    write_csv(paths[1],native_rows);write_csv(paths[2],media_rows)
    with paths[0].open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    verify(native_record);verify(display_record)
    return {'native_rows_n':len(native_rows),'video_rows_n':len(media_rows),'comparison_groups':groups}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','native-record','display','display-record','report','native-timings','video-timings'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(export(a.native,a.native_record,a.display,a.display_record,a.report,a.native_timings,a.video_timings)))
