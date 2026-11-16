"""TF-04 fixed prod scores, file-backed lineage and18-pose display screening."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

from analysis.frozen_prod_score_diagnostic import bridge
from analysis.runtime_benchmark.mano_author_surface_audit import bound
from analysis.runtime_benchmark.common_camera_mask import project,view_basis,VIEWS,WIDTH,HEIGHT
from analysis.runtime_benchmark.private_mesh_raster import rasterize,BACKGROUND_FACE
from analysis.runtime_benchmark.mano_common_camera_rerender import raster_masks
from validation_v03.execution_record import verify
from validation_v03.lineage_manifest import audit as lineage_audit
from validation_v03.run_manifest import snapshot_file
from validation_v03.session_artifacts import canonical,_private

CONDITIONS=('self','static_start','partial_half','A_reference')
MODES=('full_interval','auto_keyframes')


def exact_buckets(items):
    buckets={}
    for name,payload in items:
        key=hashlib.sha256(payload).hexdigest();bucket=buckets.setdefault(key,{'payload':payload,'members':[]})
        if bucket['payload']!=payload:raise ValueError('Hash bucket failed exact byte verification')
        bucket['members'].append(name)
    return [{'group_id':f'E{i+1:02d}','members':b['members']} for i,b in enumerate(buckets.values())]


def decoded_key(path):
    import cv2
    capture=cv2.VideoCapture(str(path));checksum=hashlib.sha256()
    try:
        if not capture.isOpened():raise ValueError('Actual media must decode')
        for i in range(25):
            ok,frame=capture.read()
            if not ok or frame.shape!=(HEIGHT,WIDTH,3) or abs(capture.get(cv2.CAP_PROP_POS_MSEC)-i*125.)>.01:
                raise ValueError('Decoded frame shape/count/PTS differs from matched8FPS grid')
            checksum.update(frame.tobytes())
        if capture.read()[0]:raise ValueError('Extra decoded frame')
    finally:capture.release()
    return checksum.hexdigest()


def equal_decoded(first,second):
    import cv2
    a=cv2.VideoCapture(str(first));b=cv2.VideoCapture(str(second))
    try:
        for _ in range(25):
            ax,x=a.read();by,y=b.read()
            if not ax or not by or not np.array_equal(x,y):return False
        return not a.read()[0] and not b.read()[0]
    finally:a.release();b.release()


def execute(native,native_record,display,display_record,projected,projected_record,static_audit,static_audit_record,
            prod,node,worker_root,output,resume_results=None,resume_record=None):
    bindings=[bound(root,rec) for root,rec in ((native,native_record),(display,display_record),(static_audit,static_audit_record))]
    (native,native_record,nb),(display,display_record,db),(static_audit,static_audit_record,ab)=bindings
    projected=_private(projected);projected_record=_private(projected_record);pb=verify(projected_record)
    pr=json.loads((projected_record/'receipt.private.json').read_text())
    if pb['state']!='PROCESS_ERROR' or pr['artifact_roots']!=[str(projected)] or not pr['postflight_snapshot_matched']:
        raise ValueError('Explicit audited producer-error parent required')
    cached=None;cache_status=None
    if (resume_results is None)!=(resume_record is None):raise ValueError('Resume output and receipt must be paired')
    if resume_results is not None:
        resume_results=_private(resume_results);resume_record=_private(resume_record)
        cache_status=verify(resume_record);receipt=json.loads((resume_record/'receipt.private.json').read_text())
        if (cache_status['state']!='PROCESS_ERROR' or receipt['artifact_roots']!=[str(resume_results)]
                or receipt['postflight_snapshot_matched'] is not True):raise ValueError('Complete recorded process-error partial results required')
        manifest=json.loads((resume_record/'provenance/manifest.json').read_text())
        for entry in manifest['inputs']:
            actual=snapshot_file(entry['path'])
            if actual['sha256']!=entry['sha256'] or actual['bytes']!=entry['bytes']:
                raise ValueError('Original analysis inputs changed; partial results cannot be reused')
        cached={'scores':json.loads((resume_results/'scores.private.json').read_text())['rows'],
          'static':json.loads((resume_results/'static_screen.private.json').read_text())['rows']}
        with np.load(resume_results/'static_visibility.private.npz',allow_pickle=False) as saved:
            if (saved['amodal_union'].shape!=(36,HEIGHT,WIDTH) or saved['face_ids'].shape!=(36,HEIGHT,WIDTH)
                    or saved['projected_joints_px'].shape!=(36,21,2) or not np.isfinite(saved['projected_joints_px']).all()):
                raise ValueError('Cached static raster contract differs')
    output=_private(output)
    parents=[p for root,rec,_ in bindings for p in (root,rec)]+[projected,projected_record]
    if resume_results is not None:parents.extend((resume_results,resume_record))
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in parents):
        raise ValueError('Fresh independent analysis output required')
    ns=json.loads((native/'summary.json').read_text());ds=json.loads((display/'summary.json').read_text())
    if (ns['version']!='tf04_matched_ABC_U_native_bundle_v1' or ds['rendered_source_cases_n']!=32
            or ds['camera_recalibrated'] is not False or ds['protection_mode']!='author_region_union'):
        raise ValueError('Complete frozen-camera four-arm display required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    import cv2
    from dataset_pipeline.common import LANDMARK_NAMES
    from dataset_pipeline.config import PipelineConfig
    from dataset_pipeline.stage6_occlusion import project_occlusion_circle
    from dataset_pipeline.stage7_gate import gate_clip
    from experiments.motion_fixture.mask_feasibility import inspect as legacy_interval
    cv2.setNumThreads(1);config=PipelineConfig()
    output.mkdir();wall=time.perf_counter_ns();cpu=time.process_time_ns();utc=time.time_ns()
    script=Path(__file__).resolve().parents[1]/'validation_v03/frozen_prod_score.cjs'
    projected_frames={};metadata=None;native_payloads={};entries=[];source_paths={};files=[];decoded={}
    if cached is not None:
        check=bridge(node,script,prod,{'cases':[]});metadata={k:check[k] for k in ('constants','extraction')}
        expected={(c['case'],c['view'],condition,mode) for c in ds['cases'] for condition in CONDITIONS for mode in MODES}
        observed={(r['case'],r['view'],r['condition'],r['segmentation']) for r in cached['scores']}
        if len(cached['scores'])!=256 or observed!=expected:raise ValueError('Cached256 score conditions differ')
    def entry(sid,path,parent_ids):
        entries.append({'source_id':sid,'path':str(Path(path).resolve(strict=True)),'parent_ids':parent_ids,
          'family_ids':['F_CURRENT_GENERATED_DEVELOPMENT'],'capture_ids':[],
          'lineage_status':'derived' if parent_ids else 'root_of_supplied_material','exposure':'used_in_development'})
    for c in ns['cases']:
        path=native/c['case']/'native_output.private.npz'
        with np.load(path,allow_pickle=False) as data:
            native_payloads[c['case']]=data['vertices'].tobytes()+data['canonical_joints'].tobytes()+data['times_seconds'].tobytes()
        entry('N_'+c['case'],path,[])
    intervals=[]
    for c in ds['cases']:
        folder=display/c['directory_id'];data=json.loads((folder/'reference.private.json').read_text())
        if len(data['frames'])!=25 or any(f['detection_semantics']!='known_model_reference_no_detector' for f in data['frames']):
            raise ValueError('Complete25 known-model frames required')
        if cached is None:
            result=bridge(node,script,prod,{'landmark_data':{**data,'video_info':data['source_info']}})
            projected_frames[c['case'],c['view']]=result['converted']['frames'];metadata={k:result[k] for k in ('constants','extraction')}
        diag=json.loads((folder/'mask_diagnostics.private.json').read_text());s=diag['surface_interval'];legacy=diag['legacy']
        intervals.append({'case':c['case'],'arm':c['arm'],'view':c['view'],'legacy_feasible':legacy['feasible'],
          'surface_feasible':s['feasible'],'surface_minimum_w3':s['minimum_w3'],'maximum_w3':s['maximum_w3'],
          'interval_gap':s['minimum_w3']-s['maximum_w3'],'upstream_model_surface_eligible':c['upstream_model_surface_eligible'],
          'mask_allowed':c['technical_proxy_mask_allowed'],'final_created':c['H264_rendition_created']})
        sid='S_'+c['directory_id'];source=folder/'source.private.avi';source_paths[c['case'],c['view']]=source
        entry(sid,source,['N_'+c['case']]);paths=[('source',source,sid)]
        if c['masked_candidate_created']:
            found=list(folder.glob('candidates/*/masked.mp4'))
            if len(found)!=1:raise ValueError('Unique actual masked candidate required')
            mid='M_'+c['directory_id'];entry(mid,found[0],[sid]);paths.append(('candidate',found[0],mid))
        if c['H264_rendition_created']:
            found=list(folder.glob('renditions/*/video.mp4'))
            if len(found)!=1:raise ValueError('Unique actual final rendition required')
            fid='V_'+c['directory_id'];entry(fid,found[0],['M_'+c['directory_id']]);paths.append(('final',found[0],fid))
        for kind,path,source_id in paths:
            key=decoded_key(path);bucket=decoded.setdefault((kind,key),{'path':path,'members':[]})
            if bucket['members'] and not equal_decoded(bucket['path'],path):raise ValueError('Decoded hash alias differs in actual pixels')
            bucket['members'].append(source_id)
            files.append({'kind':kind,'source_id':source_id,'path':path,'native_case':c['case'],'payload':path.read_bytes()})
    score_rows=[] if cached is None else cached['scores']
    for c in (ds['cases'] if cached is None else []):
        base=projected_frames[c['case'],c['view']];a_base=projected_frames[f"A_{c['hand']}_s{c['seed']}",c['view']]
        partial=[[[(p[k]+base[0][j][k])/2 for k in range(2)] for j,p in enumerate(f)] for f in base]
        cases=[]
        for condition in CONDITIONS:
            reference=a_base if condition=='A_reference' else base
            response=[base[0]]*25 if condition=='static_start' else partial if condition=='partial_half' else base
            for mode in MODES:cases.append({'id':condition+':'+mode,'mode':mode,'base':reference,'response':response})
        result=bridge(node,script,prod,{'cases':cases})
        for r in result['results']:
            condition,mode=r.pop('id').split(':')
            score_rows.append({'case':c['case'],'arm':c['arm'],'view':c['view'],'condition':condition,'segmentation':mode,
              'final_created':c['H264_rendition_created'],**r})
        print('Matched score views '+str(len(score_rows)//8)+'/32',flush=True)
    if len(score_rows)!=256:raise ValueError('Registered256 score diagnostic denominator differs')
    score_groups=defaultdict(list)
    for r in score_rows:score_groups[r['arm'],r['condition'],r['segmentation']].append(r)
    score_summary=[{'arm':k[0],'condition':k[1],'segmentation':k[2],'diagnostics_n':len(v),
      'score_min':min(r['score']['captcha'] for r in v),'score_max':max(r['score']['captcha'] for r in v),
      'score_threshold_met_n':sum(r['score_threshold_met'] for r in v),
      'all_keyframe_angle_conditions_met_n':sum(all(x['below_threshold'] for x in r['keyframe_angles']) for r in v)}
      for k,v in score_groups.items()]
    packet={'schema_version':1,'data_scope':'real_files_synthetic_allocation','source_origin':'generated_3d',
      'require_unexposed_test':True,'sources':entries,'allocations':[{'allocation_id':'ALL_DIAGNOSTIC','split':'diagnostic',
      'source_ids':[x['source_id'] for x in entries],'participant_ids':[],'capture_ids':[]}]}
    lineage=lineage_audit(packet,base=output)
    if lineage['summary']['declared_constraint_findings']!={'MISSING_INDEPENDENT_PARTITIONS':1}:
        raise ValueError('Unexpected declared-lineage finding')
    by_arm=[]
    for arm in ('A','B','C','U'):
        rows=[r for r in intervals if r['arm']==arm]
        by_arm.append({'arm':arm,'views_n':len(rows),'upstream_model_surface_eligible_n':sum(r['upstream_model_surface_eligible'] for r in rows),
          'legacy_feasible_n':sum(r['legacy_feasible'] for r in rows),'union_interval_feasible_n':sum(r['surface_feasible'] for r in rows),
          'mask_allowed_n':sum(r['mask_allowed'] for r in rows),'final_created_n':sum(r['final_created'] for r in rows),
          'interval_gap_min':min(r['interval_gap'] for r in rows),'interval_gap_max':max(r['interval_gap'] for r in rows)})
    camera=json.loads((display/'shared_camera.private.json').read_text())
    registrations=json.loads((display/'neutral_registration.private.json').read_text())['fixed_hand_bases']
    static_rows=[] if cached is None else cached['static'];targets=[];owners=[];pixels=[]
    candidates=[r for r in json.loads((static_audit/'cases.private.json').read_text())['cases'] if r['model_surface_eligible'] and r['bmc_geometry_error'] is None]
    if len(candidates)!=18:raise ValueError('Registered18 audited static candidates required')
    if cached is not None:
        expected={(c['case_id'],view) for c in candidates for view in VIEWS}
        if len(static_rows)!=36 or {(r['case_id'],r['view']) for r in static_rows}!=expected:
            raise ValueError('Cached36 static screens differ from registered18 candidates')
    for c in (candidates if cached is None else []):
        hand=c['hand'];matrix=np.array(registrations[hand])
        with np.load(native/(hand+'_fresh_neutral.private.npz'),allow_pickle=False) as data:faces=data['faces'].copy()
        with np.load(display/(hand+'_proxy_definition.private.npz'),allow_pickle=False) as data:
            proxy={k:data[k].copy() for k in data.files}
        if 'author_region_face_ids' not in proxy:raise ValueError('Current author-union source required; no fallback')
        with np.load(projected/c['case_id']/'native_output.private.npz',allow_pickle=False) as data:
            v=data['vertices'][0].astype(float);points=data['canonical_points'][0].astype(float)
        registered=(v-points[0])@matrix;joints=(points-points[0])@matrix
        for view in VIEWS:
            start=time.perf_counter_ns();pcpu=time.process_time_ns()
            xy,z=project(registered,np.zeros(3),camera,view);jxy,jz=project(joints,np.zeros(3),camera,view)
            basis,_=view_basis(camera,view);tri=registered[faces];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
            shade=np.abs(normal@basis[:,2])/np.maximum(np.linalg.norm(normal,axis=1),1e-12)
            colors=np.rint(np.array([170,205,225])[None]*(.55+.45*shade[:,None])).astype(np.uint8)
            _,ids,_,_=rasterize(xy,z,faces,colors);selected=proxy['protected_face_ids']
            _,isolated,_,_=rasterize(xy,z,faces[selected],colors[selected]);target=isolated!=BACKGROUND_FACE
            frame={'frame_idx':0,'source_pts_ms':0.,'detected':True,'landmarks_px':{name:{'x':float(p[0]),'y':float(p[1]),'z':float(depth)}
              for name,p,depth in zip(LANDMARK_NAMES,jxy,jz)}}
            frames=[{**frame,'frame_idx':i,'source_pts_ms':i*125.} for i in range(25)]
            legacy=legacy_interval(frames,config);interval=surface_weight_interval_for_static(legacy,jxy,target)
            allowed=interval['feasible'];gate=None;tip_count=None;outside=None;core_outside=None;border=None
            if allowed:
                gate=gate_clip(frames,interval['proposed_w3'],config);masks,cores,geometry=raster_masks([frame],interval['proposed_w3'],project_occlusion_circle,LANDMARK_NAMES)
                tip_count=sum(int((np.isin(ids,proxy[k+'_patch_face_ids'])&~masks[0]).sum())>0 for k in ('thumb','index','ring','pinky'))
                outside=int((target&~masks[0]).sum());core_outside=int((target&~cores[0]).sum());border=geometry[0]['circle_border_clipped']
                allowed=bool(gate['accepted'] and not outside and not core_outside and tip_count>=config.condition2_min_visible_fingers and not border)
            static_rows.append({'case_id':c['case_id'],'hand':hand,'seed':c['seed'],'attempt':c['attempt'],'view':view,
              'legacy_feasible':legacy['feasible'],'union_interval':interval,'stage7':gate,'tip_patch_count':tip_count,
              'union_outside_mask_pixels':outside,'union_outside_codec_core_pixels':core_outside,'circle_border_clipped':border,
              'static_display_eligible':bool(allowed),'codec_validated':False,'human_validated':False,'release_allowed':False,
              'timing':{'wall_ns':time.perf_counter_ns()-start,'own_cpu_ns':time.process_time_ns()-pcpu}})
            targets.append(target);owners.append(ids);pixels.append(jxy)
    file_groups={kind:exact_buckets([(f['source_id'],f['payload']) for f in files if f['kind']==kind]) for kind in ('source','candidate','final')}
    pixel_groups={kind:[{'group_id':f'P{i+1:02d}','members':b['members']} for i,b in enumerate(v for (k,_),v in decoded.items() if k==kind)] for kind in ('source','candidate','final')}
    native_groups=exact_buckets(list(native_payloads.items()))
    native_group_id={name:g['group_id'] for g in native_groups for name in g['members']}
    final_nonunique=sum(len({f['native_case'] for f in files if f['source_id'] in g['members']})>1 for g in file_groups['final'])
    final_multi_payload=sum(len({native_group_id[f['native_case']] for f in files if f['source_id'] in g['members']})>1 for g in file_groups['final'])
    if len(files)!=len(ds['media']) or len(static_rows)!=36:raise ValueError('Recorded media/static raster denominator differs')
    (output/'scores.private.json').write_bytes(canonical({'rows':score_rows}))
    (output/'intervals.private.json').write_bytes(canonical({'rows':intervals}))
    (output/'static_screen.private.json').write_bytes(canonical({'rows':static_rows}))
    if cached is None:np.savez_compressed(output/'static_visibility.private.npz',amodal_union=targets,face_ids=owners,projected_joints_px=pixels)
    else:(output/'static_visibility.private.npz').write_bytes((resume_results/'static_visibility.private.npz').read_bytes())
    (output/'lineage_packet.private.json').write_bytes(canonical(packet))
    (output/'lineage_details.private.json').write_bytes(canonical(serializable_lineage(lineage)))
    (output/'groups.private.json').write_bytes(canonical({'native':native_groups,'file':file_groups,'pixels':pixel_groups}))
    timing_rows=[]
    for m in ds['media']:
        t=m['timing'];r={k:m[k] for k in ('case','view','kind','frames_n','fps','video_bytes','ready_boundary')}
        r.update(nominal_video_length_seconds=m['frames_n']/m['fps'],started_utc_epoch_ns=t['started_utc_epoch_ns'],
          ended_utc_epoch_ns=t['ended_utc_epoch_ns'],state=t['state'],ready_wall_ns=t['video_ready_wall_ns'],
          validated_wall_ns=t['validated_pipeline_wall_ns'],own_cpu_ns=t['validated_pipeline_process_cpu_ns'],
          ffmpeg_child_cpu_measured=False,shared_source_load_and_camera_read_included=False)
        for name,v in t['phases'].items():r[name+'_wall_ns']=v['wall_ns'];r[name+'_own_cpu_ns']=v['process_cpu_ns']
        timing_rows.append(r)
    fields=list(dict.fromkeys(k for r in timing_rows for k in r))
    with (output/'media_timings.csv').open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(timing_rows)
    for _,rec,status in bindings:
        if verify(rec)!=status:raise ValueError('Source evidence changed during analysis')
    if verify(projected_record)!=pb:raise ValueError('Audited static producer evidence changed')
    if cached is not None and verify(resume_record)!=cache_status:raise ValueError('Partial result receipt changed')
    summary={'version':'tf04_matched_display_analysis_v1','by_arm':by_arm,'score_aggregates':score_summary,'score_diagnostics_n':len(score_rows),
      'native_payload_groups_n':len(native_groups),'file_groups_n':{k:len(v) for k,v in file_groups.items()},
      'decoded_pixel_groups_n':{k:len(v) for k,v in pixel_groups.items()},'final_file_groups_with_multiple_native_cases_n':final_nonunique,
      'final_file_groups_with_distinct_native_payloads_n':final_multi_payload,
      'lineage_sources_n':len(entries),'lineage_findings':lineage['summary']['declared_constraint_findings'],
      'independent_evaluation_partitions_n':0,'media_timings_rows_n':len(timing_rows),'static_candidates_n':18,'static_raster_views_n':len(static_rows),
      'static_display_eligible_views_n':sum(r['static_display_eligible'] for r in static_rows),
      'static_eligible_native_cases_n':len({r['case_id'] for r in static_rows if r['static_display_eligible']}),
      'static_codec_or_human_approval':False,'new_model_inference_n':0,'new_videos_n':0,'new_independent_families_n':0,
      'reused_score_diagnostics_n':256 if cached is not None else 0,'new_score_diagnostics_n':0 if cached is not None else 256,
      'reused_static_raster_views_n':36 if cached is not None else 0,'new_static_raster_views_n':0 if cached is not None else 36,
      'prior_analysis_state':'PROCESS_ERROR' if cached is not None else None,
      'human_trials_n':0,'release_allowed':False,'accepted_into_pool_n':0,'hold_or_authentication_validated':False,
      'timing':{'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),'wall_ns':time.perf_counter_ns()-wall,
        'own_python_cpu_ns':time.process_time_ns()-cpu,'node_child_cpu_measured':False,
        'scope':('saved-result copy, existing media decode/file-lineage/store and parent recheck; original score/raster calculation, initial original-input hash verification and recorder excluded'
          if cached is not None else 'conversion/scoring/decode/file-lineage/static raster screen/store and parent recheck; initial parent verification/recorder excluded')},**metadata}
    (output/'summary.json').write_bytes(canonical(summary));return summary


def surface_weight_interval_for_static(legacy,jxy,target):
    from analysis.runtime_benchmark.common_camera_mask import surface_weight_interval
    return surface_weight_interval(legacy,np.repeat(jxy[None],25,axis=0),[target]*25)


def serializable_lineage(value):
    # Allocation internals contain sets; the auditable packet already preserves
    # those declarations. Preserve findings/summary without serializing internals.
    return {k:v for k,v in value.items() if k!='allocations'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','native-record','display','display-record','projected','projected-record','static-audit','static-audit-record',
                 'prod','node','worker-root','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('resume-results','resume-record'):p.add_argument('--'+name,type=Path)
    a=p.parse_args();s=execute(**vars(a));print(json.dumps({k:s[k] for k in ('score_diagnostics_n','media_timings_rows_n','static_display_eligible_views_n')}))
