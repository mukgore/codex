"""Recorded CPF-region/legacy-proxy union audit of existing private videos.

No model inference, new video encoding, annotation adoption or source mutation.
The source numeric-ID/name correspondence is a project paper/palette review,
checked against model geometry, not independent human anatomical annotation.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from analysis.runtime_benchmark.author_surface_regions import (
    review_neutral,whole_region_faces,protective_union,undirected_topology_equal,
)
from analysis.runtime_benchmark.common_camera_mask import (
    project,surface_weight_interval,WIDTH,HEIGHT,
)
from analysis.runtime_benchmark.mano_common_camera_rerender import raster_masks,check_proxy_encoded
from analysis.runtime_benchmark.private_mesh_raster import rasterize,BACKGROUND_FACE
from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private,canonical


def blob(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def bound(root,record):
    root=_private(root);record=_private(record);status=verify(record)
    receipt=json.loads((record/'receipt.private.json').read_text())
    if status['state']!='EXITED_ZERO' or receipt['artifact_roots']!=[str(root)]:
        raise ValueError('Completed immutable source and exact bound root required')
    return root,record,status


def source_profile(profile,assignment,review):
    profile=json.loads(Path(profile).read_text());review=_private(review)
    if (profile['version']!='cpf_paper_palette_geometry_region_review_v1'
            or profile['release_allowed'] is not False or profile['review_target_region_ids']!=[6,7]
            or blob(assignment)!=profile['assignment_blob_sha']
            or blob(review/'cpf_viz_utils.py')!=profile['author_palette_blob_sha']
            or blob(review/'author_manolayer.py')!='0e96fe330efee46ed898e4211896a50db2f05eba'):
        raise ValueError('Pinned source blobs and explicit review-only region profile required')
    # Parse literal RGB assignments without importing/executing author code.
    tree=ast.parse((review/'cpf_viz_utils.py').read_text());colors={}
    for node in ast.walk(tree):
        if not isinstance(node,ast.Assign) or len(node.targets)!=1:continue
        target=node.targets[0];value=node.value
        if not (isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='vertex_color'
                and isinstance(target.slice,ast.Compare) and isinstance(target.slice.left,ast.Name) and target.slice.left.id=='x'
                and len(target.slice.ops)==1 and isinstance(target.slice.ops[0],ast.Eq)
                and isinstance(target.slice.comparators[0],ast.Constant) and type(target.slice.comparators[0].value) is int
                and isinstance(value,ast.BinOp) and isinstance(value.op,ast.Div) and isinstance(value.left,ast.Call)
                and isinstance(value.left.func,ast.Attribute) and isinstance(value.left.func.value,ast.Name)
                and value.left.func.value.id=='np' and value.left.func.attr=='array'
                and isinstance(value.right,ast.Constant) and value.right.value==255.):continue
        colors[target.slice.comparators[0].value]=ast.literal_eval(value.left.args[0])
    if any(colors.get(r['id'])!=r['rgb'] for r in profile['regions']):
        raise ValueError('Project region colors do not match the pinned author palette')
    labels=np.loadtxt(assignment,dtype=int)
    if labels.shape!=(778,) or set(labels.tolist())!=set(range(17)):
        raise ValueError('Exact 778-vertex/17-region author assignment required')
    return profile,labels


def execute(source,source_record,rendered,rendered_record,assignment,review,profile,worker_root,output):
    source,source_record,source_before=bound(source,source_record)
    rendered,rendered_record,rendered_before=bound(rendered,rendered_record)
    output=_private(output)
    if output.exists() or any(output.is_relative_to(r) or r.is_relative_to(output) for r in (source,source_record,rendered,rendered_record,_private(review))):
        raise ValueError('Fresh output outside immutable source/evidence roots required')
    import sys
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    import cv2
    from dataset_pipeline.common import LANDMARK_NAMES
    from dataset_pipeline.stage6_occlusion import project_occlusion_circle
    cv2.setNumThreads(1)
    profile,labels=source_profile(profile,assignment,review)
    ss=json.loads((source/'summary.json').read_text());rs=json.loads((rendered/'summary.json').read_text())
    if (ss.get('primitive_profile')!='non_target_cues_open_preflex20' or ss['cases_n']!=16
            or rs['camera_mode']!='hand_neutral_registered' or len(rs['cases'])!=32
            or rs['rendered_source_frames_n']!=800 or rs['release_allowed'] is not False):
        raise ValueError('Explicit paired-preflex recorded source and fixed-camera rerender required')
    journal=Journal(output/'journal',{'condition_id':'AUTHOR_REGION_PLUS_EXISTING_PROXY_UNION_AUDIT',
        'endpoint':'model_region_correspondence_and_existing_masked_video_union_pixel_audit',
        'input_exposure':'private recorded meshes/source camera and masked renditions; no model inference',
        'cache_state':'sequential recorded arrays; OS/module/video caches uncontrolled',
        'planned_frames':800,'timeout_seconds':900,
        'scope':'model-region review and conservative union audit; no anatomical/human/security release approval'})
    completed=0;neutrals={};definitions={};cases=[]
    try:
        with journal.stage('pinned_profile_neutral_geometry_and_connectivity'):
            camera=json.loads((rendered/'shared_camera.private.json').read_text())
            for hand in ('right','left'):
                with np.load(source/(hand+'_fresh_neutral.private.npz'),allow_pickle=False) as data:
                    v=data['vertices'][0].copy();j=data['points'].copy();faces=data['faces'].copy()
                review_row=review_neutral(labels,v,j,faces)
                (output/(hand+'_neutral_region_review.private.json')).write_bytes(canonical(review_row))
                selected=whole_region_faces(labels,faces,profile['review_target_region_ids'])
                with np.load(rendered/(hand+'_proxy_definition.private.npz'),allow_pickle=False) as old:
                    previous=old['protected_face_ids'].copy()
                union=protective_union(previous,selected,len(faces))
                np.savez_compressed(output/(hand+'_union_definition.private.npz'),
                    author_region_faces=selected,previous_proxy_faces=previous,union_faces=union)
                definitions[hand]=(faces,selected,previous,union)
                neutrals[hand]={'vertices':v,'joints':j,'review':review_row}
            topology_same=undirected_topology_equal(definitions['right'][0],definitions['left'][0])
            if not topology_same:raise ValueError('Left/right vertex-index connectivity does not agree')
            # Diagnostic region diagrams only; use the actual recorded basis,
            # but do not assert calibrated anatomy from colors or one view.
            for hand in ('right','left'):
                first=next(c for c in rs['cases'] if c['hand']==hand)
                use=json.loads((rendered/first['directory_id']/'camera_use.private.json').read_text())
                matrix=np.array(use['native_to_registered_basis_columns']);neutral=neutrals[hand]
                registered=(neutral['vertices']-neutral['joints'][0])@matrix
                faces,selected,previous,union=definitions[hand]
                palette=np.array([r['rgb'] for r in profile['regions']],float)[:,::-1]
                colors=np.rint(palette[labels[faces]].mean(axis=1)).astype(np.uint8)
                for view in ('reference_positive','reference_negative'):
                    xy,z=project(registered,np.zeros(3),camera,view)
                    image,_,_,_=rasterize(xy,z,faces,colors)
                    ok,png=cv2.imencode('.png',image)
                    if not ok:raise ValueError('Region diagram encoding failed')
                    (output/(hand+'_'+view+'_regions.private.png')).write_bytes(png.tobytes())
        for index,case in enumerate(rs['cases']):
            journal.check_budget();start=time.perf_counter_ns();cpu=time.process_time_ns();utc=time.time_ns()
            directory=output/f'c{index:02d}';directory.mkdir();old_dir=rendered/case['directory_id']
            with journal.stage(case['case']+'_'+case['view']+'_union_render_and_saved_rendition_QA'):
                with np.load(source/case['case']/'native_output.private.npz',allow_pickle=False) as data:
                    vertices=data['vertices'].copy();joints=data['canonical_joints'].copy();faces=data['faces'].copy()
                base_faces,selected,previous,union=definitions[case['hand']]
                if not np.array_equal(faces,base_faces):raise ValueError('Source animated topology changed')
                use=json.loads((old_dir/'camera_use.private.json').read_text())
                matrix=np.array(use['native_to_registered_basis_columns']);root=np.array(use['native_first_wrist'])
                vertices=(vertices-root)@matrix;joints=(joints-root)@matrix
                xy,z=project(vertices,np.array(use['first_wrist_origin']),camera,case['view'])
                joint_xy,_=project(joints,np.array(use['first_wrist_origin']),camera,case['view'])
                with np.load(old_dir/'visibility_proxy.private.npz',allow_pickle=False) as data:
                    old_targets=data['amodal_proxy'].copy();old_points=data['projected_joints_px'].copy()
                residual=float(np.max(np.abs(joint_xy-old_points)))
                if residual>1e-8:raise ValueError('Audit projection differs from actual saved rendition reference')
                amodal=[];frame_rows=[]
                for frame in range(25):
                    _,ids,_,_=rasterize(xy[frame],z[frame],faces[union],np.full((len(union),3),255,np.uint8))
                    target=ids!=BACKGROUND_FACE
                    if not target.any():raise ValueError('Empty model-region union denominator')
                    if (old_targets[frame]&~target).any():raise ValueError('Union shrank original proxy raster coverage')
                    amodal.append(target)
                    frame_rows.append({'frame_idx':frame,'union_pixels_n':int(target.sum()),
                                       'added_pixels_n':int((target&~old_targets[frame]).sum())})
                    journal.frame_completed(completed,True);completed+=1
                diagnostic=json.loads((old_dir/'mask_diagnostics.private.json').read_text())
                interval=surface_weight_interval(diagnostic['legacy'],joint_xy,amodal)
                np.savez_compressed(directory/'union_amodal.private.npz',union_amodal=np.array(amodal))
                original_roi=None;candidate_qa=h264_qa=None
                if case['H264_rendition_created']:
                    reference=json.loads((old_dir/'reference.private.json').read_text());frames=reference['frames']
                    weight=diagnostic['surface_interval']['proposed_w3']
                    masks,cores,geometries=raster_masks(frames,weight,project_occlusion_circle,LANDMARK_NAMES)
                    for target,mask,core,geometry,row in zip(amodal,masks,cores,geometries,frame_rows):
                        row.update(outside_original_mask_pixels_n=int((target&~mask).sum()),
                                   outside_original_codec_core_pixels_n=int((target&~core).sum()),
                                   circle_border_clipped=geometry['circle_border_clipped'])
                    original_roi=all(r['outside_original_mask_pixels_n']==0 and r['outside_original_codec_core_pixels_n']==0
                                     and not r['circle_border_clipped'] for r in frame_rows)
                    candidates=list(old_dir.glob('candidates/*/masked.mp4'));renditions=list(old_dir.glob('renditions/*/video.mp4'))
                    if len(candidates)!=1 or len(renditions)!=1:raise ValueError('Unique original candidate/rendition required')
                    fps=reference['source_info']['fps']
                    candidate_qa=check_proxy_encoded(candidates[0],amodal,fps)
                    h264_qa=check_proxy_encoded(renditions[0],amodal,fps)
                    (directory/'saved_media_union_QA.private.json').write_bytes(canonical({'frames':frame_rows,
                        'candidate':candidate_qa,'H264':h264_qa}))
                (directory/'union_interval.private.json').write_bytes(canonical(interval))
            row={'case':case['case'],'hand':case['hand'],'view':case['view'],
                'frames_n':25,'projection_matches_saved_reference':True,
                'original_proxy_raster_preserved_all_frames':True,
                'added_union_pixel_instances_n':sum(r['added_pixels_n'] for r in frame_rows),
                'union_radius_interval_feasible':interval['feasible'],
                'original_masked_pair_present':case['H264_rendition_created'],
                'original_mask_covers_union_and_codec_core_all_frames':original_roi,
                'candidate_decoded_union_pixel_QA_passed':None if candidate_qa is None else candidate_qa['passed'],
                'H264_decoded_union_pixel_QA_passed':None if h264_qa is None else h264_qa['passed'],
                'union_extra_hold_on_original_masked_pair':bool(case['H264_rendition_created'] and not
                    (original_roi and candidate_qa['passed'] and h264_qa['passed'])),
                'audit_wall_ns':time.perf_counter_ns()-start,'audit_own_process_cpu_ns':time.process_time_ns()-cpu,
                'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),
                'new_video_created':False,'accepted_into_pool':False,'release_allowed':False}
            (directory/'decision.private.json').write_bytes(canonical(row));cases.append(row)
            print('Author-region union cases '+str(len(cases))+'/32',flush=True)
        if verify(source_record)!=source_before or verify(rendered_record)!=rendered_before:
            raise ValueError('Original source or rendition evidence changed')
        if completed!=800:raise ValueError('Union audit frame denominator differs from design')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');verified=verify_bundle(output/'journal_bundle.private.zip')
    summary={'version':profile['version'],'scope':'paper/palette/model-region correspondence and conservative union audit only',
        'neutral_finger_centroid_matches_n':{hand:neutrals[hand]['review']['finger_centroids_matching_expected_links_n'] for hand in neutrals},
        'neutral_finger_centroid_denominator_per_hand':15,'left_right_undirected_index_connectivity_equal':topology_same,
        'palm_carpal_text_merge_conflict_resolved':False,'independent_anatomical_annotations_verified':False,
        'cases':cases,'cases_n':len(cases),'amodal_union_frames_n':completed,
        'original_masked_pairs_n':sum(c['original_masked_pair_present'] for c in cases),
        'original_masked_pairs_passing_added_union_QA_n':sum(c['original_masked_pair_present'] and not c['union_extra_hold_on_original_masked_pair'] for c in cases),
        'original_masked_pairs_with_additional_hold_n':sum(c['union_extra_hold_on_original_masked_pair'] for c in cases),
        'journal_status':verified['status'],'new_model_inference':False,'new_video_created':False,
        'prior_protection_shrunk':False,'source_or_rendition_modified':False,'production_region_definition_changed':False,
        'accepted_into_pool_n':0,'release_allowed':False,
        'limitations':['Paper numeric ID/name correspondence is inferred from named colors and pinned author palette, then checked geometrically.',
            'Centroid/mesh connectivity agreement does not validate every boundary, version, biological condition or subject.',
            'A.2 control-point merge labels conflict with Figure4/A.3; no silent correction or literal segmentation recreation.',
            'Saved parent and H264 pixel tolerance is unchanged at channel30; no re-encoding/retuning.',
            'No final human readability, multiple-answer, shadow/reflection, independent attack or operating release approval.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','rendered','rendered-record','assignment','review','profile','worker-root','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(execute(a.source,a.source_record,a.rendered,a.rendered_record,
                                            a.assignment,a.review,a.profile,a.worker_root,a.output)))
