"""Public shared-camera summaries/timings; model/ROI data stay private."""
import argparse
import csv
import json
from pathlib import Path
import statistics

import numpy as np

from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def read_bound(root, record):
    root = _private(root); record = _private(record); checked = verify(record)
    receipt = json.loads((record/'receipt.private.json').read_text())
    if checked['state'] != 'EXITED_ZERO' or receipt['artifact_roots'] != [str(root)]:
        raise ValueError('Completed source root bound by its execution receipt required')
    manifest = json.loads((record/'provenance/manifest.json').read_text())
    return json.loads((root/'summary.json').read_text()), checked, manifest


def export(world_root, world_record, registered_root, registered_record, startup_record, report, timings, suite, offline_tests):
    roots = [(_private(world_root), world_record, 'world_shared'),
             (_private(registered_root), registered_record, 'hand_neutral_registered')]
    report = Path(report).resolve(); timings = Path(timings).resolve()
    if report.exists() or timings.exists(): raise FileExistsError('Fresh public export files required')
    if any(p.is_relative_to(r) for p in (report,timings) for root,record,_ in roots for r in (root,_private(record))):
        raise ValueError('Export must not alter immutable sources/evidence')
    summaries = {}; csv_rows = []
    for root, record, mode in roots:
        summary, status, manifest = read_bound(root, record); fixed = {}; scales = set(); upright = 0; individually_bad = 0
        empty = 0; global_gaps = []; protected_counts = []
        for case in summary['cases']:
            directory = root/case['directory_id']; camera = json.loads((directory/'camera_use.private.json').read_text())
            b = np.array(camera['basis_columns']); scales.add(camera['scale'])
            if not np.allclose(b.T@b,np.eye(3),atol=1e-10) or np.linalg.det(b)<0:
                raise ValueError('Export observed non-proper camera')
            key = case['view']; signature = (camera['basis_columns'],camera['center'])
            if key in fixed and fixed[key] != signature: raise ValueError('Camera refit per case')
            fixed[key] = signature
            reference = json.loads((directory/'reference.private.json').read_text())['frames']
            upright += int(all(f['landmarks_px']['MIDDLE_MCP']['y']<f['landmarks_px']['WRIST']['y'] for f in reference))
            mask = json.loads((directory/'mask_diagnostics.private.json').read_text())
            individually_bad += sum(not f['feasible'] for f in mask['legacy']['frame_intervals'])
            empty += mask['surface_interval']['empty_proxy_frames_n']
            if not mask['legacy']['feasible']:
                global_gaps.append(mask['legacy']['minimum_w3']-mask['legacy']['maximum_w3'])
            with np.load(directory/'visibility_proxy.private.npz',allow_pickle=False) as data:
                protected_counts.extend(np.count_nonzero(data['amodal_proxy'],axis=(1,2)).tolist())
        if len(scales)!=1 or len(fixed)!=2: raise ValueError('Expected one scale and two fixed shared views')
        summary.update(execution_record=status,producer_code_commit=manifest['code_commit'],
            recorded_input_files_n=len(manifest['inputs']),recorded_dependency_pins_n=len(manifest['pinned_versions']),
            camera_consistency_verified=True,image_middle_MCP_above_wrist_cases_n=upright,
            individually_infeasible_view_frame_instances_n=individually_bad,
            empty_projected_proxy_frame_instances_n=empty,
            proxy_projected_pixel_count_range=[min(protected_counts),max(protected_counts)],
            infeasible_constant_weight_gap_range=[min(global_gaps),max(global_gaps)] if global_gaps else None)
        stats = {}
        for media in summary['media']:
            timer = media['timing']; phases = timer['phases']; kind = media['kind']
            def seconds(name): return '' if name not in phases else phases[name]['wall_ns']/1e9
            csv_rows.append({'camera_mode':mode,'case':media['case'],'view':media['view'],'media_kind':kind,
                'state':timer['state'],'started_utc_epoch_ns':timer['started_utc_epoch_ns'],'ended_utc_epoch_ns':timer['ended_utc_epoch_ns'],
                'ready_boundary':media['ready_boundary'],'cached_parent_state':media['parent_state'],
                'ready_seconds':None if timer['video_ready_wall_ns'] is None else timer['video_ready_wall_ns']/1e9,
                'validated_pipeline_seconds':timer['validated_pipeline_wall_ns']/1e9,
                'own_process_cpu_seconds':timer['validated_pipeline_process_cpu_ns']/1e9,
                'projection_seconds':seconds('projection_and_reference'),'source_and_proxy_raster_seconds':seconds('full_and_amodal_proxy_raster'),
                'encoder_open_seconds':seconds('encoder_open'),'encoder_write_seconds':seconds('encoder_write'),
                'encoder_finalize_seconds':seconds('encoder_finalize'),'source_decode_seconds':seconds('source_decode_QA'),
                'proxy_interval_and_store_seconds':seconds('proxy_mask_interval_and_exact_pixel_QA'),
                'library_encode_and_QA_seconds':seconds('library_encode_and_QA'),
                'frames':media['frames_n'],'fps':media['fps'],'encoded_duration_seconds':media['frames_n']/media['fps'],
                'video_bytes':media['video_bytes'],'new_model_inference':False,'shared_calibration_included':False})
            stats.setdefault(kind,[]).append(timer)
        summary['timing_statistics_seconds'] = {kind:{
            field:{'min':min(values),'median':statistics.median(values),'max':max(values)}
            for field,values in ((field,[t[key]/1e9 for t in timers if t[key] is not None]) for field,key in (
                ('ready','video_ready_wall_ns'),('validated_pipeline','validated_pipeline_wall_ns')))} for kind,timers in stats.items()}
        summaries[mode] = summary
    first_status = verify(startup_record)
    first_receipt = json.loads((_private(startup_record)/'receipt.private.json').read_text())
    if first_status['state'] == 'EXITED_ZERO' or first_status['artifact_files_n'] != 0:
        raise ValueError('Expected retained failure before any output video')
    result = {'scope':'two camera modes on the same quarantined recorded development meshes; no new inference or independent families',
        'runs':summaries,'timing_rows_n':len(csv_rows),'new_model_inference':False,'accepted_into_pool_n':0,'release_allowed':False,
        'initial_startup_failure':{'execution_record':first_status,'video_attempts_n':0,
            'execution_runner_elapsed_seconds':first_receipt['elapsed_ns']/1e9,
            'observed_failure':'legacy Stage6 helper eagerly imported MediaPipe absent in model CPU environment',
            'remedy':'same code in existing offline video runtime; no installs or existing environment changes'},
        'caller_reported_tests':{'current_research_suite':suite,'offline_camera_raster':offline_tests,
            'scope':'observed suite counts, not independently attested test execution; exporter checked on actual bound data'},
        'timing_scope':'cached-source rerenders; shared input loading/calibration and receipt sealing excluded; no cold-cache or controlled method benchmark',
        'mask_coverage_scope':'rest-bone proxy is not independent anatomical labeling; rejected mask/codec branches are not counted as executed'}
    with timings.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
    with report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    for _,record,_ in roots:verify(record)
    verify(startup_record)
    return {'runs_n':2,'media_timing_rows_n':len(csv_rows),'source_records_intact':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('world-root','world-record','registered-root','registered-record','startup-record','report','timings'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--suite-passed',type=int,required=True);p.add_argument('--offline-tests-passed',type=int,required=True)
    a=p.parse_args();print(json.dumps(export(a.world_root,a.world_record,a.registered_root,a.registered_record,
        a.startup_record,a.report,a.timings,a.suite_passed,a.offline_tests_passed)))
