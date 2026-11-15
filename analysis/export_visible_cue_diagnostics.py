"""Export actual cue-proposal generation/rerender times and sanitized decisions.

No raw model arrays, camera matrices, mask radii, ROI identifiers or file hashes.
Failed/incomplete runs must be reported separately, never labeled successful.
"""
import argparse
import csv
import json
from pathlib import Path
import statistics

from analysis.export_conditioned_timings import timing_row
from analysis.export_shared_camera_timings import read_bound
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def export(source, source_record, rendered, rendered_record, report, timings):
    report, timings = Path(report).resolve(), Path(timings).resolve()
    if report.exists() or timings.exists(): raise FileExistsError('Fresh public export required')
    roots = list(map(_private, (source, source_record, rendered, rendered_record)))
    if any(p.is_relative_to(r) for p in (report,timings) for r in roots):
        raise ValueError('Never alter sealed private roots')
    generated, generation_status, generation_manifest = read_bound(source,source_record)
    rerender, render_status, render_manifest = read_bound(rendered,rendered_record)
    if (generated.get('primitive_profile') not in ('non_target_cues_open','non_target_cues_open_preflex20')
            or generated['cases_n'] != 16 or generated['native_forward_frames_n'] != 402
            or rerender['rendered_source_frames_n'] != 800
            or generated['release_allowed'] is not False or rerender['release_allowed'] is not False):
        raise ValueError('Explicit completed quarantined cue generation and shared-camera rerender required')
    rows = []
    for case in generated['cases']:
        row = timing_row(case['case'],case['timing'],'native_generation',case['render'],case)
        row.update(kind='unmasked_FFV1_native_diagnostic',view='',
                   ready_boundary='encoder finalized',timing_boundary=case['timing']['boundary'])
        rows.append(row)
    for media in rerender['media']:
        timer = media['timing']
        metadata = next(c for c in generated['cases'] if c['case'] == media['case'])
        row = timing_row(media['case'],timer,'shared_camera',metadata=metadata)
        row.update(kind=media['kind'],view=media['view'],decoded_frames=media['frames_n'],
                   video_bytes=media['video_bytes'],fps=media['fps'],
                   ready_boundary=media['ready_boundary'],timing_boundary=timer['boundary'])
        for key,value in timer['phases'].items(): row[key+'_seconds'] = value['wall_ns']/1e9
        rows.append(row)
    for row in rows:
        row['primitive_profile'] = generated['primitive_profile']
        if (row['state'] != 'COMPLETED' or row['decoded_frames'] != 25
                or not 0 < row['video_ready_seconds'] <= row['observed_pipeline_seconds']
                or row['ended_utc_epoch_ns'] < row['started_utc_epoch_ns']):
            raise ValueError('Actual positive completed timings and full-frame denominator required')
    decisions = []
    for case in rerender['cases']:
        diagnostics = json.loads((roots[2]/case['directory_id']/'mask_diagnostics.private.json').read_text())
        decisions.append({**case,
            'individually_infeasible_legacy_frames_n':sum(not f['feasible'] for f in diagnostics['legacy']['frame_intervals']),
            'exact_pixel_QA_executed_frames_n':len(diagnostics['frames']),
            'empty_proxy_frames_n':diagnostics['surface_interval']['empty_proxy_frames_n']})
    stats = {}
    for kind in sorted({r['kind'] for r in rows}):
        group = [r for r in rows if r['kind'] == kind]
        stats[kind] = {'videos_n':len(group)}
        for field in ('video_ready_seconds','observed_pipeline_seconds'):
            values = [r[field] for r in group]
            stats[kind][field] = {'min':min(values),'median':statistics.median(values),'max':max(values)}
    result = {'schema_version':1,'scope':'local fixed-order quarantined cue proposals, not biological/human/security admission',
        'generation':generated,'shared_camera':{**rerender,'cases':decisions},
        'execution':{'generation':generation_status,'rerender':render_status,
            'generation_commit':generation_manifest['code_commit'],'rerender_commit':render_manifest['code_commit'],
            'generation_inputs_n':len(generation_manifest['inputs']),'rerender_inputs_n':len(render_manifest['inputs'])},
        'timing_rows_n':len(rows),'timing_statistics':stats,
        'timing_scope':'shared setup/receipt sealing excluded; actual own-process CPU; no subprocess CPU or fair cold-cache/method benchmark',
        'release_allowed':False}
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with timings.open('x',encoding='utf-8',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    with report.open('x',encoding='utf-8') as stream: json.dump(result,stream,indent=2); stream.write('\n')
    verify(source_record); verify(rendered_record)
    return {'timing_rows_n':len(rows),'generation_cases_n':generated['cases_n'],
            'render_cases_n':len(decisions),'timing_statistics':stats}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','rendered','rendered-record','report','timings'):
        p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args()
    print(json.dumps(export(a.source,a.source_record,a.rendered,a.rendered_record,a.report,a.timings)))
