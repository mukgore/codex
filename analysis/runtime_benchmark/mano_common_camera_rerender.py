"""Recorded shared-camera rerender and conservative proxy-mask diagnostics.

No model inference or original array mutation. Existing Stage6/7 and codec
thresholds remain unchanged. Model surface proxy is not anatomical annotation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

from analysis.runtime_benchmark.common_camera_mask import (
    common_camera, view_basis, project, surface_proxy, surface_weight_interval, VIEWS, VERSION, WIDTH, HEIGHT,
)
from analysis.runtime_benchmark.private_mesh_raster import rasterize, BACKGROUND_FACE
from analysis.runtime_benchmark.mano_conditioned_generator import Timings
from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical, _private


def source_timing(timer, ready, state, boundary):
    row = timer.snapshot(ready, state)
    row.update(boundary=boundary, shared_calibration_included=False, new_model_inference=False,
               cache_state='cached recorded arrays/common camera; no model load; codec/OS caches uncontrolled',
               child_process_cpu_measured=False, cpu_scope='own Python process; ffmpeg subprocess CPU not included')
    return row


def raster_masks(frames, weight, circle, names):
    import cv2
    masks = []; cores = []; geometry = []
    yy, xx = np.ogrid[:HEIGHT, :WIDTH]
    for frame in frames:
        points = [(frame['landmarks_px'][name]['x'], frame['landmarks_px'][name]['y'], frame['landmarks_px'][name]['z']) for name in names]
        center, radius = circle(points, weight); cx, cy, r = int(center[0]), int(center[1]), int(radius)
        if not 0 <= cx < WIDTH or not 0 <= cy < HEIGHT or r < 1:
            raise ValueError('Invalid exact source mask geometry')
        mask = np.zeros((HEIGHT, WIDTH), np.uint8); cv2.circle(mask, (cx, cy), r, 1, -1)
        masks.append(mask.astype(bool)); cores.append((xx-cx)**2+(yy-cy)**2 <= max(0, r-2)**2)
        geometry.append({'center_int': [cx, cy], 'radius_int': r,
            'circle_border_clipped': cx-r < 0 or cy-r < 0 or cx+r >= WIDTH or cy+r >= HEIGHT})
    return masks, cores, geometry


def check_proxy_encoded(path, amodal, fps):
    import cv2
    capture = cv2.VideoCapture(str(path)); rows = []
    try:
        if not capture.isOpened(): raise ValueError('Final proxy-check video cannot be opened')
        for index, target in enumerate(amodal):
            ok, image = capture.read()
            if not ok or image.shape != (HEIGHT, WIDTH, 3) or not target.any():
                raise ValueError('Missing frame/target in final proxy denominator')
            if abs(capture.get(cv2.CAP_PROP_POS_MSEC)-index*1000/fps) > .01:
                raise ValueError('Final proxy check timestamp differs')
            bad = np.any(image[target] > 30, axis=1)
            rows.append({'frame_idx': index, 'proxy_pixels': int(target.sum()),
                         'pixels_above_existing_interior_tolerance': int(bad.sum()),
                         'maximum_proxy_channel_value': int(image[target].max())})
        if capture.read()[0]: raise ValueError('Extra final proxy-check frame')
    finally:
        capture.release()
    return {'frames_n': len(rows), 'frames': rows, 'mask_interior_tolerance': 30,
            'passed': all(r['pixels_above_existing_interior_tolerance'] == 0 for r in rows),
            'anatomical_coverage_proven': False, 'scope': 'declared rest-bone amodal surface proxy only'}


def execute(source, source_record, worker_root, ffmpeg, ffprobe, output):
    source = _private(source); output = _private(output); before = verify(source_record)
    receipt = json.loads((_private(source_record)/'receipt.private.json').read_text())
    if before['state'] != 'EXITED_ZERO' or receipt['artifact_roots'] != [str(source)]:
        raise ValueError('Completed recorded source root required')
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (source, _private(source_record))):
        raise ValueError('Fresh output separate from immutable inputs/evidence required')
    sys.path.insert(0, str(Path(worker_root).resolve(strict=True)))
    import cv2
    from dataset_pipeline.common import LANDMARK_NAMES
    from dataset_pipeline.config import PipelineConfig
    from dataset_pipeline.stage6_occlusion import project_occlusion_circle
    from dataset_pipeline.stage7_gate import gate_clip
    from experiments.motion_fixture.mask_feasibility import inspect as legacy_interval
    from dataset_pipeline.candidate import build_candidate
    from dataset_pipeline.rendition import build_h264_rendition
    cv2.setNumThreads(1)
    config = PipelineConfig(); source_summary = json.loads((source/'summary.json').read_text())
    if source_summary['cases_n'] != 16 or source_summary['release_allowed'] is not False:
        raise ValueError('Explicit sixteen quarantined source cases required')
    journal = Journal(output/'journal', {'condition_id': 'COMMON_CAMERA_PROXY_MASK_RERENDER',
        'endpoint': 'shared_camera_source_render_and_proxy_mask_codec_QA', 'input_exposure': 'recorded private mesh sequences',
        'cache_state': 'all source arrays loaded once; no model load/inference; local codec caches uncontrolled',
        'planned_frames': 800, 'timeout_seconds': 900,
        'scope': '32 source videos; masking only if unchanged geometry and conservative proxy gates allow; all quarantined'})
    completed = 0; cases = []; media = []
    try:
        shared_start = time.perf_counter_ns(); loaded = []; proxies = {}
        with journal.stage('bound_sources_static_proxies_and_one_shared_calibration'):
            for original in source_summary['cases']:
                directory = source/original['case']
                with np.load(directory/'native_output.private.npz', allow_pickle=False) as data:
                    case = {'vertices': data['vertices'].copy(), 'joints': data['canonical_joints'].copy(),
                            'faces': data['faces'].copy(), 'times': data['times_seconds'].copy(), 'original': original}
                if case['vertices'].shape != (25, 778, 3) or case['joints'].shape != (25, 21, 3):
                    raise ValueError('Full source sequence contract changed')
                proposal = json.loads((directory/'proposal.private.json').read_text()); case['color'] = proposal['recipe']['base_bgr']
                if case['times'].shape != (25,) or not np.isfinite(case['times']).all() or not (np.diff(case['times'])>0).all() or not np.allclose(np.diff(case['times']), case['times'][-1]/24, atol=1e-10):
                    raise ValueError('Explicit source zero-based CFR time axis required')
                if case['times'][0] != 0: raise ValueError('Source time origin changed')
                loaded.append(case)
            for hand in ('right', 'left'):
                with np.load(source/(hand+'_fresh_neutral.private.npz'), allow_pickle=False) as neutral:
                    proxy = surface_proxy(neutral['vertices'][0], neutral['points'], neutral['faces'])
                    proxy['faces'] = neutral['faces'].copy(); proxies[hand] = proxy
                    if hand == 'right': reference = neutral['points'].copy()
                np.savez_compressed(output/(hand+'_proxy_definition.private.npz'),
                    protected_face_ids=proxy['protected_face_ids'], vertex_nearest_edge=proxy['vertex_nearest_edge'],
                    **{k+'_patch_face_ids': v for k, v in proxy['tip_patches'].items()})
            camera = common_camera(reference, loaded, config)
            (output/'shared_camera.private.json').write_bytes(canonical(camera))
            shared_ns = time.perf_counter_ns()-shared_start
        for case_index, case in enumerate(loaded):
            original = case['original']; proxy = proxies[original['hand']]
            if not np.array_equal(case['faces'], proxy['faces']): raise ValueError('Proxy and source topology differ')
            for view_index, view in enumerate(VIEWS):
                journal.check_budget(); label = original['case']+'__'+view
                # Bound Windows path length before hashed candidate subfolders.
                directory = output/f'c{case_index:02d}v{view_index}'; directory.mkdir()
                timer = Timings(); ready = None; state = 'INCOMPLETE'
                try:
                    with journal.stage(label+'_source_and_proxy_render'):
                        with timer.phase('projection_and_reference'):
                            origin = case['joints'][0, 0].copy()
                            xy, depth = project(case['vertices'], origin, camera, view)
                            joint_xy, joint_depth = project(case['joints'], origin, camera, view)
                            basis, center = view_basis(camera, view); n = len(xy); fps = 24/float(case['times'][-1])
                            frames = [{'frame_idx': i, 'source_pts_ms': float(t*1000), 'detected': True,
                                'detection_semantics': 'known_model_reference_no_detector', 'origin_type': 'recorded_generated_3d_rerender',
                                'landmarks_px': {name: {'x': float(p[0]), 'y': float(p[1]), 'z': float(z)}
                                    for name, p, z in zip(LANDMARK_NAMES, points, zs)},
                                'landmarks_world': {name: dict(zip(('x','y','z'), p.tolist())) for name,p in zip(LANDMARK_NAMES, raw)}}
                                for i,(t,points,zs,raw) in enumerate(zip(case['times'],joint_xy,joint_depth,case['joints']))]
                            info = {'width': WIDTH, 'height': HEIGHT, 'fps': fps, 'total_frames': n}
                            (directory/'reference.private.json').write_bytes(canonical({'frames': frames, 'source_info': info,
                                'px_z_semantics': 'render-camera depth in unverified native length units, not pixel/metric depth',
                                'world_semantics': 'original SDK native coordinates; only renderer subtracts first wrist'}))
                            (directory/'camera_use.private.json').write_bytes(canonical({'view': view,
                                'basis_columns': basis.tolist(), 'center': center.tolist(), 'scale': camera['pixels_per_native_unit'],
                                'first_wrist_origin': origin.tolist(), 'shared_calibration': True}))
                        source_video = directory/'source.private.avi'
                        with timer.phase('encoder_open'):
                            writer = cv2.VideoWriter(str(source_video), cv2.VideoWriter_fourcc(*'FFV1'), fps, (WIDTH, HEIGHT))
                        images = []; owners = []; amodal = []; pixel_hashes = []
                        try:
                            if not writer.isOpened(): raise ValueError('Shared-camera source encoder unavailable')
                            for i in range(n):
                                with timer.phase('full_and_amodal_proxy_raster'):
                                    tri = case['vertices'][i, case['faces']].astype(float)
                                    normals = np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
                                    shade = np.abs(normals@basis[:,2])/np.maximum(np.linalg.norm(normals,axis=1),1e-12)
                                    colors = np.rint(np.array(case['color'])[None]*(.55+.45*shade[:,None])).astype(np.uint8)
                                    image, ids, _, _ = rasterize(xy[i],depth[i],case['faces'],colors)
                                    selected = proxy['protected_face_ids']
                                    _, isolated, _, _ = rasterize(xy[i],depth[i],case['faces'][selected],colors[selected])
                                    target = isolated != BACKGROUND_FACE
                                    pixel_hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
                                with timer.phase('encoder_write'): writer.write(image)
                                images.append(image); owners.append(ids); amodal.append(target)
                                journal.frame_completed(completed, True); completed += 1
                        finally:
                            with timer.phase('encoder_finalize'): writer.release()
                        ready = time.perf_counter_ns(); timer.video_ready_ns = ready
                        with timer.phase('source_decode_QA'):
                            capture = cv2.VideoCapture(str(source_video))
                            try:
                                for i, digest in enumerate(pixel_hashes):
                                    ok, decoded = capture.read()
                                    if not ok or hashlib.sha256(decoded.tobytes()).hexdigest() != digest:
                                        raise ValueError('Source frame bytes/count differ after lossless decode')
                                    if abs(capture.get(cv2.CAP_PROP_POS_MSEC)-i*1000/fps) > .01:
                                        raise ValueError('Source decoded timestamp differs')
                                if capture.read()[0]: raise ValueError('Extra source frame')
                            finally: capture.release()
                        with timer.phase('proxy_mask_interval_and_exact_pixel_QA'):
                            legacy = legacy_interval(frames, config)
                            interval = surface_weight_interval(legacy, joint_xy, amodal)
                            diagnostics = []; allowed = interval['feasible']; weight = interval['proposed_w3']; gate = None
                            if allowed:
                                gate = gate_clip(frames, weight, config); allowed = gate['accepted']
                                masks, cores, geometries = raster_masks(frames, weight, project_occlusion_circle, LANDMARK_NAMES)
                                for i, (mask, core, geometry) in enumerate(zip(masks, cores, geometries)):
                                    visible = np.isin(owners[i], proxy['protected_face_ids'])
                                    tips = {k: int((np.isin(owners[i],v)&~mask).sum()) for k,v in proxy['tip_patches'].items()}
                                    diagnostics.append({'frame_idx': i, 'amodal_proxy_pixels': int(amodal[i].sum()),
                                        'visible_proxy_pixels': int(visible.sum()),
                                        'amodal_outside_mask_pixels': int((amodal[i]&~mask).sum()),
                                        'amodal_outside_codec_core_pixels': int((amodal[i]&~core).sum()),
                                        'visible_tip_patch_pixels_outside_mask': tips,
                                        'tip_patch_count': sum(v > 0 for v in tips.values()), **geometry})
                                allowed = allowed and all(d['amodal_outside_mask_pixels']==0 and d['amodal_outside_codec_core_pixels']==0
                                    and d['tip_patch_count']>=config.condition2_min_visible_fingers and not d['circle_border_clipped'] for d in diagnostics)
                            np.savez_compressed(directory/'visibility_proxy.private.npz', face_ids=np.array(owners),
                                amodal_proxy=np.array(amodal), projected_joints_px=joint_xy, pixel_sha256=np.array(pixel_hashes))
                            (directory/'mask_diagnostics.private.json').write_bytes(canonical({'legacy': legacy,
                                'surface_interval': interval, 'stage7': gate, 'frames': diagnostics, 'technical_proxy_mask_allowed': bool(allowed),
                                'anatomical_coverage_proven': False, 'minimum_visible_patch_pixels': 1,
                                'patch_threshold_status': 'nonempty distal-segment proxy, not validated recognizability'}))
                            for suffix, image in (('source', images[12]), ('proxy', np.where(amodal[12][...,None], [0,0,255], images[12]).astype(np.uint8))):
                                ok, png = cv2.imencode('.png',image)
                                if not ok: raise ValueError('Shared-camera preview encoding failed')
                                (directory/(suffix+'_preview.private.png')).write_bytes(png.tobytes())
                        state = 'COMPLETED'
                finally:
                    timing = source_timing(timer,ready,state,'cached-source projection/raster through encoder finalize; validated adds decode, visibility and proxy interval/QC; common source load/calibration excluded')
                    (directory/'source_timing.private.json').write_bytes(canonical(timing))
                media.append({'case': original['case'], 'view': view, 'kind': 'unmasked_FFV1_source', 'timing': timing,
                    'frames_n': n, 'fps': fps, 'video_bytes': source_video.stat().st_size,
                    'ready_boundary': 'encoder finalized', 'parent_state': 'cached recorded arrays', 'gpu_used': False})
                candidate = rendition = final_proxy = None
                if allowed:
                    for kind in ('masked_candidate', 'masked_H264_rendition'):
                        mtimer = Timings(); mstate = 'INCOMPLETE'; mready = None
                        try:
                            with journal.stage(label+'_'+kind):
                                with mtimer.phase('library_encode_and_QA'):
                                    if kind == 'masked_candidate':
                                        candidate = build_candidate(source_video, frames, info, weight, config, directory/'candidates')
                                        parent = directory/'candidates'/candidate['artifact_id']; video = parent/'masked.mp4'
                                    else:
                                        rendition = build_h264_rendition(parent,frames,info,weight,config,directory/'renditions',
                                            ffmpeg=ffmpeg,ffprobe=ffprobe,outside_mae_limit=2.0)
                                        video = directory/'renditions'/rendition['output_sha256']/'video.mp4'
                                    # Library exposes completion after its encoding and QC, not the
                                    # internal encoder-close instant. Do not manufacture that split.
                                    mready = time.perf_counter_ns(); mtimer.video_ready_ns = mready
                                with mtimer.phase('all_frame_surface_proxy_encoded_QA'):
                                    final_proxy = check_proxy_encoded(video,amodal,fps)
                                    if not final_proxy['passed']: raise ValueError('Encoded surface proxy is exposed')
                                    (directory/(kind+'_proxy_QA.private.json')).write_bytes(canonical(final_proxy))
                                mstate = 'COMPLETED'
                        finally:
                            mtime = source_timing(mtimer,mready,mstate,'library return after encode plus library QC; then additional all-frame proxy pixel QA; upstream cached parent excluded')
                            mtime['case_origin_to_media_ready_ns'] = None if mready is None else mready-timer.start_wall
                            (directory/(kind+'_timing.private.json')).write_bytes(canonical(mtime))
                        media.append({'case':original['case'],'view':view,'kind':kind,'timing':mtime,
                            'frames_n':n,'fps':fps,'video_bytes':video.stat().st_size,'gpu_used':False,
                            'ready_boundary':'library return after encode and QC; internal encoder finalize not observed',
                            'parent_state':'cached source file/reference/mask' if kind=='masked_candidate' else 'cached masked candidate'})
                row = {'case':original['case'],'directory_id':directory.name,'hand':original['hand'],'view':view,'source_frames_n':n,
                    'legacy_landmark_interval_feasible':legacy['feasible'], 'surface_interval_feasible':interval['feasible'],
                    'technical_proxy_mask_allowed':bool(allowed),'masked_candidate_created':candidate is not None,
                    'H264_rendition_created':rendition is not None, 'final_proxy_pixels_verified':final_proxy is not None and final_proxy['passed'],
                    'minimum_visible_distal_patch_count':min((d['tip_patch_count'] for d in diagnostics),default=None),
                    'upstream_surface_indicator_frames_n':original['surface_indicator_frames_n'],
                    'upstream_model_prior_policy':original['policy'],'anatomical_surface_annotations_verified':False,
                    'decision':'QUARANTINED_RESEARCH_DIAGNOSTIC','accepted_into_pool':False,'release_allowed':False}
                (directory/'decision.private.json').write_bytes(canonical(row)); cases.append(row)
                print('Shared-camera cases completed: '+str(len(cases))+'/32',flush=True)
        if verify(source_record) != before: raise ValueError('Original source artifacts changed during rerender')
        if completed != 800: raise ValueError('Rendered source-frame denominator differs')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed: journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip'); recovered=verify_bundle(output/'journal_bundle.private.zip')
    summary={'version':VERSION,'scope':'shared proper cameras and rest-bone proxy mask/codec diagnostic, not anatomical/human/security approval',
        'source_cases_n':16,'views_n':2,'rendered_source_cases_n':len(cases),'rendered_source_frames_n':completed,
        'upstream_distinct_surface_indicator_frames_n':sum(c['surface_indicator_frames_n'] for c in source_summary['cases']),
        'upstream_collision_counts_are_reused_per_view_not_new_3D_tests':True,
        'cases':cases,'media':media,'shared_source_load_and_calibration_wall_ns':shared_ns,
        'masked_candidate_videos_n':sum(r['masked_candidate_created'] for r in cases),
        'H264_rendition_videos_n':sum(r['H264_rendition_created'] for r in cases),
        'runtime_journal_status':recovered['status'],'runtime_journal_completed_frames_n':recovered['completed_frames'],
        'opencv_version':cv2.__version__,'numpy_version':np.__version__,'new_model_inference':False,'source_arrays_modified':False,
        'source_record_reverified':True,'new_independent_families_n':0,'masked_sources_sent_to_browser_n':0,
        'full_anatomical_mask_coverage_proven':False,'biological_validity_proven':False,'accepted_into_pool_n':0,'release_allowed':False,
        'limitations':['Calibration fits current complete development sequences/circle envelopes, not a calibrated physical or causal live camera.',
            'Only first wrist translation is removed; both views use proper shared axes and reverse horizontal/depth signs.',
            'Nearest-rest-bone face sets and nonempty distal patches are geometric surrogates, not independent anatomical/recognizability labels.',
            'Opposite views and duplicate source policies are correlated and not independent tasks or security entropy.',
            'Original surface intersections/BMC/physical/human/attack holds remain; codec success is a separate lower-level check.',
            'Media timing scopes differ for encoder-close vs library-return boundaries; own-process CPU omits ffmpeg child CPU.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','worker-root','ffmpeg','ffprobe','output'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();print(json.dumps(execute(a.source,a.source_record,a.worker_root,a.ffmpeg,a.ffprobe,a.output)))
