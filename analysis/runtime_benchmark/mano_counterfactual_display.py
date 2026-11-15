"""Frozen-camera/frozen-mask native counterfactual display comparisons.

Exact decoded pixels/file bytes are evidence of equality only for these
recorded conditions. No tolerance is promoted to human indistinguishability,
no generator-side oracle comparison is labeled a successful real attack.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

from analysis.runtime_benchmark.common_camera_mask import project,view_basis,WIDTH,HEIGHT
from analysis.runtime_benchmark.hidden_motion_counterfactual import frame_difference,aggregate_differences
from analysis.runtime_benchmark.private_mesh_raster import rasterize,BACKGROUND_FACE
from analysis.runtime_benchmark.mano_common_camera_rerender import raster_masks,check_proxy_encoded,source_timing
from analysis.runtime_benchmark.mano_conditioned_generator import Timings
from analysis.runtime_benchmark.mano_author_surface_audit import bound
from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,_private


def compare_videos(parent,variant,masks,fps):
    import cv2
    a=cv2.VideoCapture(str(parent));b=cv2.VideoCapture(str(variant));rows=[]
    try:
        if not a.isOpened() or not b.isOpened():raise ValueError('Both actual comparison videos must decode')
        for index,mask in enumerate(masks):
            ok_a,x=a.read();ok_b,y=b.read()
            if not ok_a or not ok_b or x.shape!=(HEIGHT,WIDTH,3) or y.shape!=x.shape:
                raise ValueError('Missing actual comparison frames')
            if any(abs(c.get(cv2.CAP_PROP_POS_MSEC)-index*1000/fps)>.01 for c in (a,b)):
                raise ValueError('Comparison timestamps differ')
            rows.append(frame_difference(x,y,mask))
        if a.read()[0] or b.read()[0]:raise ValueError('Extra comparison frames')
    finally:
        a.release();b.release()
    result=aggregate_differences(rows)
    prefix=[r for i,r in enumerate(rows) if i/fps<=1.+1e-9]
    result['initial_second_frames_n']=len(prefix)
    result['initial_second_exact_decoded_pixels_equal']=all(r['all_changed_pixels_n']==0 for r in prefix)
    result['exact_whole_file_bytes_equal']=Path(parent).read_bytes()==Path(variant).read_bytes()
    return result


def lossless_decode(path,pixel_hashes,fps):
    import cv2
    capture=cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():raise ValueError('Counterfactual source cannot decode')
        for i,digest in enumerate(pixel_hashes):
            ok,image=capture.read()
            if not ok or image.shape!=(HEIGHT,WIDTH,3) or hashlib.sha256(image.tobytes()).hexdigest()!=digest:
                raise ValueError('Counterfactual lossless source frame differs')
            if abs(capture.get(cv2.CAP_PROP_POS_MSEC)-i*1000/fps)>.01:raise ValueError('Source timestamp differs')
        if capture.read()[0]:raise ValueError('Extra source frame')
    finally:capture.release()


def execute(native,native_record,guarded,guarded_record,worker_root,ffmpeg,ffprobe,output):
    native,native_record,nbefore=bound(native,native_record);guarded,guarded_record,gbefore=bound(guarded,guarded_record)
    output=_private(output)
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (native,native_record,guarded,guarded_record)):
        raise ValueError('Fresh output outside immutable parent/evidence roots required')
    ns=json.loads((native/'summary.json').read_text());gs=json.loads((guarded/'summary.json').read_text())
    if ns['cases_n']!=32 or ns['native_forward_frames_n']!=802 or gs['protection_mode']!='author_region_union':
        raise ValueError('Registered eight-parent/four-variant native source and union-protected parents required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    import cv2
    from dataset_pipeline.common import LANDMARK_NAMES
    from dataset_pipeline.config import PipelineConfig
    from dataset_pipeline.stage6_occlusion import project_occlusion_circle
    from dataset_pipeline.stage7_gate import gate_clip
    from dataset_pipeline.candidate import build_candidate
    from dataset_pipeline.rendition import build_h264_rendition
    cv2.setNumThreads(1);config=PipelineConfig()
    journal=Journal(output/'journal',{'condition_id':'FROZEN_DISPLAY_RELATIVE_MIDDLE_COUNTERFACTUAL',
        'endpoint':'exact_existing_parent_vs_counterfactual_source_masked_H264_comparison',
        'input_exposure':'generator-side access to private native alternatives and frozen parent display',
        'cache_state':'cached recorded arrays/parent files; OS/module/codec cache uncontrolled',
        'planned_frames':1600,'timeout_seconds':900,
        'scope':'oracle model/display diagnostic, not human-valid answers or real attack success'})
    cases=[];media=[];completed=0
    try:
        setup_start=time.perf_counter_ns()
        camera=json.loads((guarded/'shared_camera.private.json').read_text());proxies={}
        for hand in ('right','left'):
            with np.load(guarded/(hand+'_proxy_definition.private.npz'),allow_pickle=False) as data:
                if 'author_region_face_ids' not in data:raise ValueError('Parent does not contain actual author-union protection')
                proxies[hand]={key:data[key].copy() for key in data.files}
        shared_ns=time.perf_counter_ns()-setup_start
        (output/'frozen_display_scope.private.json').write_bytes(canonical({'camera_recalibrated':False,
            'mask_recalibrated':False,'protection_mode':'frozen_recorded_author_union','appearance_from_parent':True,
            'camera_and_proxy_read_wall_ns':shared_ns,'native_model_inference_in_this_process':False}))
        for native_index,case in enumerate(ns['cases']):
            parent_views=[c for c in gs['cases'] if c['case']==case['parent_case'] and c['H264_rendition_created']]
            if len(parent_views)!=2:raise ValueError('Both actual technical parent views required')
            for view_index,parent in enumerate(parent_views):
                journal.check_budget();directory=output/f'c{native_index:02d}v{view_index}';directory.mkdir()
                parent_dir=guarded/parent['directory_id'];timer=Timings();ready=None;state='INCOMPLETE'
                try:
                    with journal.stage(case['case_id']+'_'+parent['view']+'_frozen_source_render'):
                        with timer.phase('frozen_parent_variant_read_and_projection'):
                            with np.load(native/case['case_id']/'native_output.private.npz',allow_pickle=False) as data:
                                vertices=data['vertices'].astype(float);raw_joints=data['canonical_joints'].astype(float)
                                faces=data['faces'].copy();times=data['times_seconds'].copy()
                            use=json.loads((parent_dir/'camera_use.private.json').read_text())
                            reference=json.loads((parent_dir/'reference.private.json').read_text())
                            diagnostic=json.loads((parent_dir/'mask_diagnostics.private.json').read_text())
                            proposal=json.loads((native/case['case_id']/'proposal.private.json').read_text())
                            info=reference['source_info'];fps=info['fps'];weight=diagnostic['surface_interval']['proposed_w3']
                            if not np.allclose(times*1000,[f['source_pts_ms'] for f in reference['frames']],rtol=0,atol=1e-8):
                                raise ValueError('Counterfactual time axis changed')
                            matrix=np.array(use['native_to_registered_basis_columns']);root=np.array(use['native_first_wrist'])
                            registered=(vertices-root)@matrix;joints=(raw_joints-root)@matrix;origin=np.array(use['first_wrist_origin'])
                            xy,z=project(registered,origin,camera,parent['view']);joint_xy,joint_z=project(joints,origin,camera,parent['view'])
                            basis,_=view_basis(camera,parent['view']);proxy=proxies[case['hand']]
                            frames=[{**old,'origin_type':'recorded_native_counterfactual_frozen_camera',
                                'landmarks_px':{name:{'x':float(p[0]),'y':float(p[1]),'z':float(depth)}
                                    for name,p,depth in zip(LANDMARK_NAMES,points,depths)},
                                'landmarks_world':{name:dict(zip(('x','y','z'),p.tolist())) for name,p in zip(LANDMARK_NAMES,world)}}
                                for old,points,depths,world in zip(reference['frames'],joint_xy,joint_z,raw_joints)]
                            masks,cores,geometry=raster_masks(reference['frames'],weight,project_occlusion_circle,LANDMARK_NAMES)
                            new_masks,_,new_geometry=raster_masks(frames,weight,project_occlusion_circle,LANDMARK_NAMES)
                            mask_frozen=all(np.array_equal(a,b) for a,b in zip(masks,new_masks)) and geometry==new_geometry
                            if not mask_frozen:raise ValueError('Relative finger perturbation changed frozen mask pixel geometry')
                            gate=gate_clip(frames,weight,config)
                            (directory/'reference.private.json').write_bytes(canonical({'frames':frames,'source_info':info}))
                        source=directory/'source.private.avi';targets=[];owners=[];pixel_hashes=[]
                        with timer.phase('encoder_open'):
                            writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'FFV1'),fps,(WIDTH,HEIGHT))
                        try:
                            if not writer.isOpened():raise ValueError('Counterfactual source encoder unavailable')
                            for frame in range(25):
                                with timer.phase('full_and_frozen_union_raster'):
                                    tri=registered[frame,faces];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
                                    shade=np.abs(normal@basis[:,2])/np.maximum(np.linalg.norm(normal,axis=1),1e-12)
                                    colors=np.rint(np.array(proposal['base_bgr'])[None]*(.55+.45*shade[:,None])).astype(np.uint8)
                                    image,ids,_,_=rasterize(xy[frame],z[frame],faces,colors)
                                    selected=proxy['protected_face_ids']
                                    _,isolated,_,_=rasterize(xy[frame],z[frame],faces[selected],colors[selected])
                                    target=isolated!=BACKGROUND_FACE
                                    if not target.any():raise ValueError('Missing counterfactual union target denominator')
                                    owners.append(ids);targets.append(target)
                                    pixel_hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
                                with timer.phase('encoder_write'):writer.write(image)
                                journal.frame_completed(completed,True);completed+=1
                        finally:
                            with timer.phase('encoder_finalize'):writer.release()
                        ready=time.perf_counter_ns();timer.video_ready_ns=ready
                        with timer.phase('source_decode_roi_patch_and_parent_comparison'):
                            lossless_decode(source,pixel_hashes,fps);qc=[]
                            for i,(target,mask,core,ids,g) in enumerate(zip(targets,masks,cores,owners,geometry)):
                                tips={k:int((np.isin(ids,proxy[k+'_patch_face_ids'])&~mask).sum())
                                      for k in ('thumb','index','ring','pinky')}
                                qc.append({'frame_idx':i,'union_outside_mask_pixels_n':int((target&~mask).sum()),
                                    'union_outside_codec_core_pixels_n':int((target&~core).sum()),
                                    'nonempty_visible_distal_patches_n':sum(n>0 for n in tips.values()),
                                    'circle_border_clipped':g['circle_border_clipped']})
                            allowed=bool(case['model_surface_eligible_for_display_comparison'] and gate['accepted'] and all(
                                r['union_outside_mask_pixels_n']==0 and r['union_outside_codec_core_pixels_n']==0
                                and r['nonempty_visible_distal_patches_n']>=2 and not r['circle_border_clipped'] for r in qc))
                            source_comparison=compare_videos(parent_dir/'source.private.avi',source,masks,fps)
                            if case['delta_degrees']==0 and not source_comparison['exact_decoded_pixels_equal']:
                                raise ValueError('Zero-perturbation rendered control differs from actual parent')
                            np.savez_compressed(directory/'visibility.private.npz',amodal_union=np.array(targets),
                                face_ids=np.array(owners),projected_joints_px=joint_xy,pixel_sha256=np.array(pixel_hashes))
                            (directory/'mask_QA.private.json').write_bytes(canonical({'frames':qc,'gate':gate,
                                'mask_pixel_geometry_frozen':mask_frozen,'allowed':allowed,'source_comparison':source_comparison}))
                        state='COMPLETED'
                finally:
                    source_time=source_timing(timer,ready,state,'recorded alternative/parent projection and raster through encoder-close; validated adds decode/ROI/parent comparison/store; SDK generation excluded')
                    (directory/'source_timing.private.json').write_bytes(canonical(source_time))
                media.append({'case_id':case['case_id'],'parent_case':case['parent_case'],'view':parent['view'],
                    'kind':'unmasked_FFV1_source','frames_n':25,'fps':fps,'video_bytes':source.stat().st_size,
                    'timing':source_time,'ready_boundary':'encoder finalized'})
                comparisons={};candidate=h264=None
                if allowed:
                    for kind in ('masked_candidate','masked_H264_rendition'):
                        mtimer=Timings();mready=None;mstate='INCOMPLETE'
                        try:
                            with journal.stage(case['case_id']+'_'+parent['view']+'_'+kind):
                                with mtimer.phase('library_encode_and_QA'):
                                    if kind=='masked_candidate':
                                        candidate=build_candidate(source,frames,info,weight,config,directory/'candidates')
                                        candidate_dir=directory/'candidates'/candidate['artifact_id'];video=candidate_dir/'masked.mp4'
                                        old=list(parent_dir.glob('candidates/*/masked.mp4'))
                                    else:
                                        h264=build_h264_rendition(candidate_dir,frames,info,weight,config,directory/'renditions',
                                            ffmpeg=ffmpeg,ffprobe=ffprobe,outside_mae_limit=2.0)
                                        video=directory/'renditions'/h264['output_sha256']/'video.mp4'
                                        old=list(parent_dir.glob('renditions/*/video.mp4'))
                                    mready=time.perf_counter_ns();mtimer.video_ready_ns=mready
                                with mtimer.phase('union_pixels_and_exact_parent_comparison'):
                                    if len(old)!=1:raise ValueError('Unique actual parent rendition required')
                                    encoded=check_proxy_encoded(video,targets,fps)
                                    if not encoded['passed']:raise ValueError('Encoded alternative union region is exposed')
                                    comparison=compare_videos(old[0],video,masks,fps)
                                    if case['delta_degrees']==0 and not comparison['exact_decoded_pixels_equal']:
                                        raise ValueError('Zero-perturbation encoded control differs from actual parent')
                                    (directory/(kind+'_QA.private.json')).write_bytes(canonical({'union':encoded,'comparison':comparison}))
                                    comparisons[kind]=comparison
                                mstate='COMPLETED'
                        finally:
                            mtime=source_timing(mtimer,mready,mstate,'library encode+internal QA return; validated adds union pixels/exact parent comparison; upstream cached source excluded')
                            (directory/(kind+'_timing.private.json')).write_bytes(canonical(mtime))
                        media.append({'case_id':case['case_id'],'parent_case':case['parent_case'],'view':parent['view'],
                            'kind':kind,'frames_n':25,'fps':fps,'video_bytes':video.stat().st_size,'timing':mtime,
                            'ready_boundary':'library return after encode and internal QA'})
                row={'case_id':case['case_id'],'parent_case':case['parent_case'],'hand':case['hand'],'view':parent['view'],
                    'delta_degrees':case['delta_degrees'],'directory_id':directory.name,'source_frames_n':25,
                    'mask_pixel_geometry_frozen':True,'camera_recalibrated':False,'shape_and_times_changed':False,
                    'model_surface_eligible_for_display_comparison':case['model_surface_eligible_for_display_comparison'],
                    'hidden_middle_point_max_displacement_native_units':case['hidden_middle_point_max_displacement_native_units'],
                    'anatomical_bend_input_max_difference_degrees':case['anatomical_bend_input_max_difference_degrees'],
                    'source_comparison':source_comparison,'masked_comparison':comparisons.get('masked_candidate'),
                    'H264_comparison':comparisons.get('masked_H264_rendition'),
                    'masked_candidate_created':candidate is not None,'H264_created':h264 is not None,
                    'model_alternative_with_exact_final_pixels':bool(case['delta_degrees']!=0 and h264 is not None
                        and case['hidden_middle_point_max_displacement_native_units']>0
                        and comparisons['masked_H264_rendition']['exact_decoded_pixels_equal']),
                    'human_valid_answer_proven':False,'actual_attacker_success_proven':False,
                    'decision':'QUARANTINED_GENERATOR_SIDE_DISPLAY_COUNTERFACTUAL','accepted_into_pool':False,'release_allowed':False}
                (directory/'decision.private.json').write_bytes(canonical(row));cases.append(row)
                print('Frozen display cases '+str(len(cases))+'/64',flush=True)
        if verify(native_record)!=nbefore or verify(guarded_record)!=gbefore:raise ValueError('Bound native/parent evidence changed')
        if completed!=1600 or len(cases)!=64:raise ValueError('Counterfactual display denominator differs')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');checked=verify_bundle(output/'journal_bundle.private.zip')
    summary={'version':'frozen_display_relative_middle_counterfactual_v1','cases':cases,'media':media,'cases_n':64,
        'rendered_source_frames_n':1600,'zero_control_views_n':sum(c['delta_degrees']==0 for c in cases),
        'nonzero_alternative_views_n':sum(c['delta_degrees']!=0 for c in cases),
        'exact_final_pixel_alternative_views_n':sum(c['model_alternative_with_exact_final_pixels'] for c in cases),
        'masked_candidate_videos_n':sum(c['masked_candidate_created'] for c in cases),
        'H264_videos_n':sum(c['H264_created'] for c in cases),'shared_camera_proxy_read_wall_ns':shared_ns,
        'journal_status':checked['status'],'new_model_inference':False,'new_independent_families_n':0,
        'scope':'generator-side model/display ambiguity diagnostic; exact equality only, no perceptual tolerance/real attack/human answer admission',
        'human_valid_answers_proven':False,'actual_attacker_success_proven':False,'accepted_into_pool_n':0,'release_allowed':False}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','native-record','guarded','guarded-record','worker-root','ffmpeg','ffprobe','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(execute(a.native,a.native_record,a.guarded,a.guarded_record,a.worker_root,a.ffmpeg,a.ffprobe,a.output)))
