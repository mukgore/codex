"""Private primitive-conditioned MANO generation, QA and timed diagnostics.

Author model defaults and a distinct project mirror comparator are not human
limits. Every candidate stays quarantined, including zero-penalty candidates.
"""
import argparse
from contextlib import contextmanager
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np

from analysis.runtime_benchmark.mano_recorded_producer import (
    RAW_PARENTS, TIP_NAMES, authorize_inputs, canonicalize, point_contract, camera,
)
from analysis.runtime_benchmark.mano_anatomical_frame_probe import template_basis, compose_anatomical, extract_anatomical
from analysis.runtime_benchmark.mano_model_prior_audit import extract_profile, assess
from analysis.runtime_benchmark.private_mesh_raster import rasterize, VERSION as RASTER_VERSION
from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from validation_v03.execution_record import verify
from validation_v03.run_manifest import snapshot_file
from validation_v03.session_artifacts import canonical, _private

VERSION = 'primitive_conditioned_model_prior_mano_private_generator_v1'
FRAMES = 25
SEEDS = (7, 19)
PRIMITIVES = ('synchronous_flex_spread', 'sequential_flex_spread')
CUE_PRIMITIVES = ('middle_only_cues_open', 'middle_ring_cues_open')
PROFILES = {'legacy_all_fingers': PRIMITIVES, 'non_target_cues_open': CUE_PRIMITIVES}
PROFILES['non_target_cues_open_preflex20'] = CUE_PRIMITIVES
ALL_PRIMITIVES = PRIMITIVES + CUE_PRIMITIVES
POLICIES = ('author_exact', 'ideal_mirror_comparator')
PLANNED = 402  # two fresh neutral forwards plus sixteen 25-frame candidates


class Timings:
    """Nonoverlapping actual wall/own-process CPU times; no GPU/queue claims."""
    def __init__(self):
        self.start_wall = time.perf_counter_ns(); self.start_cpu = time.process_time_ns()
        self.start_utc = time.time_ns(); self.phases = {}; self.active = False; self.video_ready_ns = None

    @contextmanager
    def phase(self, name):
        if self.active:
            raise ValueError('Timing phases must not nest')
        self.active = True; w = time.perf_counter_ns(); c = time.process_time_ns()
        try:
            yield
        finally:
            wall = time.perf_counter_ns()-w; cpu = time.process_time_ns()-c
            row = self.phases.setdefault(name, {'wall_ns': 0, 'process_cpu_ns': 0, 'calls_n': 0})
            row['wall_ns'] += wall; row['process_cpu_ns'] += cpu; row['calls_n'] += 1; self.active = False

    def snapshot(self, ready_ns, state):
        ready_ns = self.video_ready_ns if ready_ns is None else ready_ns
        return {'started_utc_epoch_ns': self.start_utc, 'ended_utc_epoch_ns': time.time_ns(),
            'video_ready_wall_ns': None if ready_ns is None else ready_ns-self.start_wall,
            'validated_pipeline_wall_ns': time.perf_counter_ns()-self.start_wall,
            'validated_pipeline_process_cpu_ns': time.process_time_ns()-self.start_cpu,
            'phases': copy.deepcopy(self.phases), 'state': state,
            'boundary': 'case proposal start through video finalize; validated adds visibility store and lossless decode; decision/receipt sealing excluded',
            'shared_hand_model_setup_included': False, 'cache_state': 'model loaded; OS/module/codec caches uncontrolled',
            'queue_wait_scope': 'not_applicable_offline_sequential', 'gpu_used': False}


def smooth(x):
    x = np.clip(np.asarray(x, float), 0., 1.)
    return x*x*x*(10.-15.*x+6.*x*x)


def recipe(seed, primitive, entry_pose='neutral'):
    if entry_pose not in ('neutral', 'preflex20') or (entry_pose != 'neutral' and primitive not in CUE_PRIMITIVES):
        raise ValueError('Explicit cue-only entry pose required')
    if type(seed) is not int or seed not in SEEDS or primitive not in ALL_PRIMITIVES:
        raise ValueError('Explicit registered engineering seed/primitive required')
    index = ALL_PRIMITIVES.index(primitive)
    domains = {name: [seed, index, domain] for name, domain in (('trajectory', 1), ('geometry', 2), ('appearance', 3))}
    motion = np.random.default_rng(np.random.SeedSequence(domains['trajectory']))
    geometry = np.random.default_rng(np.random.SeedSequence(domains['geometry']))
    appearance = np.random.default_rng(np.random.SeedSequence(domains['appearance']))
    spec = {'version': VERSION, 'seed': seed, 'primitive': primitive, 'rng': 'numpy.PCG64 via SeedSequence',
        'numpy_version': np.__version__, 'substreams_entropy': domains,
        'duration_seconds': float(motion.choice([2., 3.])), 'peak_fraction': float(motion.uniform(.4, .6)),
        'shared_bend_degrees': float(motion.uniform(40., 60.)),
        'shared_spread_degrees': float(motion.uniform(-3., 3.)),
        'thumb_cmc_twist_degrees': float(motion.uniform(-8., 8.)),
        'thumb_cmc_spread_degrees': float(motion.uniform(22., 34.)),
        'thumb_mcp_spread_degrees': float(motion.uniform(-6., 6.)),
        'beta0': float(geometry.uniform(-.5, .5)),
        'base_bgr': (np.array([170, 205, 225])+appearance.integers(-6, 7, size=3)).tolist(),
        'coupling': {'finger_weights_native_order': [1., .9, .7, .8], 'PIP_to_MCP': .85, 'DIP_to_MCP': .55,
                     'thumb_CMC_bend_to_shared': .4, 'thumb_MCP_bend_to_shared': .8, 'thumb_IP_bend_to_shared': .55},
        'engineering_parameters_not_clinical_or_population_ranges': True,
        'coupling_status': 'authored engineering synergy; not transferred Chen clinical coupling coefficients',
        'independent_joint_uniform_sampling': False, 'new_independent_family': False}
    if primitive in CUE_PRIMITIVES:
        # Native finger order is index, middle, pinky, ring. Holding authored
        # angles at zero is a proposal constraint, not proof of visible pixels
        # or of independent finger control/comfort in a human hand.
        spec['coupling']['finger_weights_native_order'] = [0., 1., 0., 0. if primitive == CUE_PRIMITIVES[0] else .8]
        spec.update(non_target_cue_constraint='index and pinky anatomical angles fixed at model neutral; thumb neutral',
                    visibility_verified=False, human_independent_finger_control_verified=False)
        if entry_pose == 'preflex20':
            spec.update(cue_entry_pose=entry_pose, cue_entry_bend_degrees=20.,
                        shared_bend_semantics='sampled peak; pulse interpolates from fixed authored entry bend to peak and back',
                        entry_pose_status='engineering development condition, not a measured human neutral or comfort limit')
    return spec


def trajectory(spec, hand, policy):
    if hand not in ('right', 'left') or policy not in POLICIES or spec['version'] != VERSION:
        raise ValueError('Explicit hand/policy and generator version required')
    times = np.linspace(0., spec['duration_seconds'], FRAMES); u = times/spec['duration_seconds']
    result = np.zeros((FRAMES, 15, 3)); peak = spec['peak_fraction']
    def pulse(delay):
        phase = (u-delay)/(1.-delay)
        return np.where(phase <= peak, smooth(phase/peak), smooth((1.-phase)/(1.-peak)))
    coupling = spec['coupling']; shared = spec['shared_bend_degrees']
    for finger, start in enumerate((0, 3, 6, 9)):
        delay = .055*finger if spec['primitive'] == 'sequential_flex_spread' else 0.
        p = pulse(delay)
        if spec.get('cue_entry_pose') == 'preflex20':
            floor = spec['cue_entry_bend_degrees']; level = floor+(shared-floor)*p
            bend = level*coupling['finger_weights_native_order'][finger]
            result[:, start, 2] = bend; result[:, start+1, 2] = bend*coupling['PIP_to_MCP']
            result[:, start+2, 2] = bend*coupling['DIP_to_MCP']
        else:
            # Preserve legacy arithmetic order as well as the random draws.
            bend = shared*coupling['finger_weights_native_order'][finger]
            result[:, start, 2] = bend*p; result[:, start+1, 2] = bend*coupling['PIP_to_MCP']*p
            result[:, start+2, 2] = bend*coupling['DIP_to_MCP']*p
        result[:, start, 1] = spec['shared_spread_degrees']*(1.-finger*.15)*p
    if spec['primitive'] in CUE_PRIMITIVES:
        # No index/pinky MCP spread despite a nonzero sampled shared-spread
        # value; keep the unused random draw in the reproducible proposal.
        result[:, [0, 6], :] = 0.
        if spec['primitive'] == CUE_PRIMITIVES[0]: result[:, 9:12, :] = 0.
        if hand == 'left' and policy == 'ideal_mirror_comparator':
            result *= np.array([-1., -1., 1.])
        return times, result*np.pi/180
    p = pulse(.08 if spec['primitive'] == 'sequential_flex_spread' else 0.)
    result[:, 12, 0] = spec['thumb_cmc_twist_degrees']*p
    result[:, 12, 1] = spec['thumb_cmc_spread_degrees']*p
    result[:, 12, 2] = shared*coupling['thumb_CMC_bend_to_shared']*p
    result[:, 13, 1] = spec['thumb_mcp_spread_degrees']*p
    result[:, 13, 2] = shared*coupling['thumb_MCP_bend_to_shared']*p
    result[:, 14, 2] = shared*coupling['thumb_IP_bend_to_shared']*p
    if hand == 'left' and policy == 'ideal_mirror_comparator':
        result *= np.array([-1., -1., 1.])
    return times, result*np.pi/180


def policy_profile(source, hand, policy):
    if hand not in ('right', 'left') or policy not in POLICIES:
        raise ValueError('Explicit generation policy required')
    result = copy.deepcopy(source)
    if hand == 'left' and policy == 'ideal_mirror_comparator':
        for intervals in result['intervals_degrees'].values():
            for axis in (0, 1):
                lower, upper = intervals[axis]; intervals[axis] = [-upper, -lower]
        result['evidence_status'] = 'PROJECT_IDEAL_MIRROR_COMPARATOR_NOT_AUTHOR_DEFAULT_OR_CLINICAL_LIMIT'
    result['generation_policy'] = policy; result['generation_hand'] = hand
    result['mirror_transform_applied'] = hand == 'left' and policy == 'ideal_mirror_comparator'
    result['specs_describe_original_author_defaults_not_transformed_intervals'] = True
    result['mirror_assumption'] = 'ideal B_left=S B_right diag(1,1,-1); actual left/right meshes not asserted identical'
    return result


def render_video(case, vertices, joints, faces, spec, timer):
    import cv2
    with timer.phase('camera_projection'):
        xy, joint_xy, depth, normal, cam = camera(vertices, joints)
        (case/'camera.private.json').write_bytes(canonical({**cam, 'fit_scope': 'full precomputed sequence; not a calibrated or causal live camera'}))
    fps = (FRAMES-1)/spec['duration_seconds']; path = case/'unmasked_diagnostic.private.avi'
    with timer.phase('encoder_open'):
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'FFV1'), fps, (512, 420))
    ids = []; depths = []; raster_rows = []; pixel_hashes = []
    try:
        if not writer.isOpened():
            raise ValueError('Lossless CPU encoder unavailable')
        encoder_backend = writer.getBackendName()
        for frame in range(FRAMES):
            with timer.phase('rasterization'):
                tri = vertices[frame, faces].astype(float)
                normals = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
                shade = np.abs(normals@normal)/np.maximum(np.linalg.norm(normals, axis=1), 1e-12)
                colors = np.rint(np.array(spec['base_bgr'])[None]*(.55+.45*shade[:, None])).astype(np.uint8)
                image, visible_faces, z, report = rasterize(xy[frame], depth[frame], faces, colors)
                pixel_hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
            with timer.phase('encoder_write'):
                writer.write(image)
            ids.append(visible_faces); depths.append(z); raster_rows.append(report)
            if frame == 12:
                with timer.phase('preview_store'):
                    # OpenCV's direct image filename API is not Unicode-safe on
                    # this Windows runtime; encode bytes, then use pathlib I/O.
                    ok, png = cv2.imencode('.png', image)
                    if not ok:
                        raise ValueError('Preview PNG encoding failed')
                    (case/'preview.private.png').write_bytes(png.tobytes())
    finally:
        with timer.phase('encoder_finalize'):
            writer.release()
    ready = time.perf_counter_ns()
    timer.video_ready_ns = ready
    with timer.phase('visibility_artifact_store'):
        np.savez_compressed(case/'visibility.private.npz', face_ids=np.array(ids), depth_native_units=np.array(depths),
                            projected_joints_px=joint_xy, pixel_sha256=np.array(pixel_hashes))
    with timer.phase('decode_qa'):
        cap = cv2.VideoCapture(str(path)); count = 0
        try:
            if not cap.isOpened(): raise ValueError('Diagnostic video decoder unavailable')
            decoder_backend = cap.getBackendName()
            if abs(cap.get(cv2.CAP_PROP_FPS)-fps) > 1e-6: raise ValueError('Decoded FPS differs from planned timeline')
            for index in range(FRAMES):
                ok, decoded = cap.read()
                if not ok or decoded.shape != (420, 512, 3):
                    raise ValueError('Diagnostic source video frame missing')
                if abs(cap.get(cv2.CAP_PROP_POS_MSEC)-index*1000/fps) > .01:
                    raise ValueError('Diagnostic source timestamp mismatch')
                if hashlib.sha256(decoded.tobytes()).hexdigest() != pixel_hashes[index]:
                    raise ValueError('Lossless decoded source pixels differ from rendered frame')
                # Lossless decoded pixel support is bound to the visibility pass.
                foreground = ids[index] != 65535
                if not foreground.any() or not np.any(decoded[foreground] != [40, 32, 24]):
                    raise ValueError('Empty diagnostic hand raster')
                count += 1
            if cap.read()[0]:
                raise ValueError('Extra diagnostic video frames')
        finally:
            cap.release()
    return ready, {'frames_n': count, 'fps': fps, 'motion_last_frame_time_seconds': spec['duration_seconds'],
        'encoded_clip_duration_seconds': FRAMES/fps, 'video_bytes': path.stat().st_size,
        'width': 512, 'height': 420, 'codec': 'FFV1 AVI', 'raster_version': RASTER_VERSION,
        'encoder_backend': encoder_backend, 'decoder_backend': decoder_backend,
        'visible_pixels_min': min(r['visible_pixels_n'] for r in raster_rows),
        'projected_degenerate_face_instances_n': sum(r['projected_degenerate_faces_n'] for r in raster_rows),
        'decoded_pixel_hashes_match': True, 'masked_video': False, 'final_delivery_rendition_checked': False}


def execute(intake, research_record, worker_root, anatomical_root, anatomical_record, loss_source, output, profile='legacy_all_fingers'):
    if profile not in PROFILES: raise ValueError('Explicit registered primitive profile required')
    primitives = PROFILES[profile]
    entry_pose = 'preflex20' if profile == 'non_target_cues_open_preflex20' else 'neutral'
    planned = 2 + 2*len(SEEDS)*len(primitives)*len(POLICIES)*FRAMES
    sources = authorize_inputs(intake, research_record); verify(anatomical_record)
    anatomical_root = _private(anatomical_root); output = _private(output)
    receipt = json.loads((_private(anatomical_record)/'receipt.private.json').read_text(encoding='utf-8'))
    if receipt['state'] != 'EXITED_ZERO' or receipt['artifact_roots'] != [str(anatomical_root)]:
        raise ValueError('Bound anatomical template source required')
    if output.exists() or output.is_relative_to(anatomical_root) or output.is_relative_to(_private(anatomical_record)):
        raise ValueError('Fresh output outside immutable template/evidence roots required')
    sys.path.insert(0, str(Path(worker_root).resolve(strict=True)))
    from dataset_pipeline.common import LANDMARK_NAMES
    from experiments.motion_fixture.biomechanical_profile import pending_profile, assess as assess_pending
    from experiments.motion_fixture.mesh_intersections import topology, frame as surface_frame
    source_prior = extract_profile(loss_source)
    pending = pending_profile(); pending.update(length_unit='model_native_units', profile_version='native_pending_limits_conditioned_v1')
    journal = Journal(output/'journal', {'condition_id': 'G04_CONDITIONED_PRIVATE_MESH_VIDEOS',
        'endpoint': 'conditioned_native_generation_surface_and_unmasked_video_QA',
        'input_exposure': 'existing private research model and source model defaults',
        'cache_state': 'sequential hand-shared model; OS/module/codec caches uncontrolled',
        'planned_frames': planned, 'timeout_seconds': 900,
        'scope': 'model-conditioned engineering primitives, not biological, human, object, security or pool approval'})
    cases = []; setups = []; completed = 0; fingerprints = {}; video_fingerprints = {}
    try:
        import torch
        import smplx
        from smplx.vertex_ids import vertex_ids
        if str(torch.__version__) != '2.5.1+cpu' or importlib.metadata.version('smplx') != '0.1.28':
            raise ValueError('Existing CPU environment required')
        torch.set_num_threads(1); torch.manual_seed(0)
        import cv2
        cv2.setNumThreads(1)
        environment = {'platform': platform.platform(), 'processor': platform.processor(),
            'logical_cpus_available': os.cpu_count(), 'python': sys.version,
            'versions': {n: importlib.metadata.version(n) for n in ('torch', 'smplx', 'numpy', 'opencv-contrib-python')},
            'torch_threads': torch.get_num_threads(), 'opencv_threads': cv2.getNumThreads(),
            'numpy_BLAS_and_FFmpeg_codec_thread_counts': 'not separately controlled or measured',
            'gpu_used': False, 'benchmark_scope': 'one sequential local diagnostic run; no background-load/cache control'}
        (output/'environment.private.json').write_bytes(canonical(environment))
        (output/'opencv_build.private.txt').write_text(cv2.getBuildInformation(), encoding='utf-8')
        tips = {n: vertex_ids['mano'][n] for n in TIP_NAMES}; contract = point_contract(LANDMARK_NAMES, tips)
        kinds = [r['point_kind'] for r in contract['canonical_points']]
        (output/'point_contract.private.json').write_bytes(canonical(contract))
        (output/'author_model_prior.private.json').write_bytes(canonical(source_prior))
        with (output/'attempts.private.jsonl').open('xb', buffering=0) as log:
            for hand in ('right', 'left'):
                setup_start = time.perf_counter_ns()
                with journal.stage(hand+'_shared_model_setup_and_fresh_template_check'):
                    authorize_inputs(intake, research_record)
                    model = smplx.MANO(str(Path(intake).resolve()/'models'), is_rhand=hand == 'right',
                        use_pca=False, flat_hand_mean=True, batch_size=1, dtype=torch.float32).to('cpu'); model.eval()
                    if tuple(model.parents.tolist()) != RAW_PARENTS:
                        raise ValueError('Native kinematic contract changed')
                    with torch.no_grad():
                        neutral = model(hand_pose=torch.zeros(1, 45), betas=torch.zeros(1, 10),
                            global_orient=torch.zeros(1, 3), transl=torch.zeros(1, 3), return_verts=True)
                    points = canonicalize(neutral.vertices.numpy(), neutral.joints.numpy(), tips)[0]
                    with np.load(anatomical_root/hand/'template.private.npz', allow_pickle=False) as old:
                        error = float(np.abs(points-old['points']).max())
                        if error > 1e-8:
                            raise ValueError('Fresh neutral differs from recorded template')
                    basis = template_basis(points, hand); faces = model.faces.astype(np.int32)
                    mesh = topology(faces, 778)
                    np.savez_compressed(output/(hand+'_fresh_neutral.private.npz'), points=points, basis=basis,
                        vertices=neutral.vertices.numpy(), raw_joints=neutral.joints.numpy(), faces=faces)
                    journal.frame_completed(completed, True); completed += 1
                setups.append({'hand': hand, 'wall_ns': time.perf_counter_ns()-setup_start,
                               'fresh_neutral_max_abs_error_native_units': error, 'scope': 'shared setup excluded from per-video times'})
                for seed in SEEDS:
                    for primitive in primitives:
                        for policy in POLICIES:
                            journal.check_budget(); label = f'{hand}_s{seed}_{primitive}_{policy}'
                            case = output/label; case.mkdir(); timer = Timings(); ready = None; state = 'INCOMPLETE'
                            log.write(canonical({'event': 'STARTED', 'case': label, 'started_utc_epoch_ns': timer.start_utc})+b'\n')
                            try:
                                with journal.stage(label+'_proposal_native_QA_and_video'):
                                    with timer.phase('proposal_and_compose'):
                                        spec = recipe(seed, primitive, entry_pose); times, angles = trajectory(spec, hand, policy)
                                        _, replay = trajectory(recipe(seed, primitive, entry_pose), hand, policy)
                                        if not np.array_equal(replay, angles):
                                            raise ValueError('Seed replay differs within locked runtime')
                                        applied = policy_profile(source_prior, hand, policy)
                                        if assess(angles, applied)[1].any():
                                            raise ValueError('Proposal violates its declared generation policy; no clipping')
                                        poses = compose_anatomical(angles, basis).astype(np.float32)
                                        (case/'proposal.private.json').write_bytes(canonical({'recipe': spec, 'hand': hand,
                                            'policy': policy, 'times_seconds': times.tolist(), 'anatomical_euler_radians': angles.tolist(),
                                            'parameter_corrections': [], 'parent_recipe': f's{seed}_{primitive}'}))
                                        (case/'applied_policy.private.json').write_bytes(canonical(applied))
                                        log.write(canonical({'event': 'PROPOSED', 'case': label, 'recipe': spec,
                                            'hand': hand, 'policy': policy, 'parameter_corrections': []})+b'\n')
                                    with timer.phase('native_forward'):
                                        betas = torch.zeros(FRAMES, 10); betas[:, 0] = spec['beta0']
                                        with torch.no_grad():
                                            result = model(hand_pose=torch.from_numpy(poses), betas=betas,
                                                global_orient=torch.zeros(FRAMES, 3), transl=torch.zeros(FRAMES, 3),
                                                return_verts=True, return_full_pose=True)
                                        vertices = result.vertices.numpy(); raw = result.joints.numpy(); full = result.full_pose.numpy()
                                        if not np.array_equal(full[:, 3:], poses) or np.any(full[:, :3]):
                                            raise ValueError('Native pose/root input changed')
                                        joints = canonicalize(vertices, raw, tips)
                                    with timer.phase('native_availability_journal'):
                                        for _ in range(FRAMES): journal.frame_completed(completed, True); completed += 1
                                    with timer.phase('native_artifact_store'):
                                        np.savez_compressed(case/'native_output.private.npz', vertices=vertices, raw_joints=raw,
                                            canonical_joints=joints, full_pose_axis_angle=full, betas=betas.numpy(),
                                            times_seconds=times, faces=faces, parents=np.array(RAW_PARENTS))
                                    with timer.phase('prior_and_pending_feature_QA'):
                                        recovered = extract_anatomical(full[:, 3:], basis)
                                        source_loss = assess(recovered, source_prior)[1]; policy_loss = assess(recovered, applied)[1]
                                        # Three anatomical Euler axes in the small authored branch;
                                        # no BMC two-angle unwrapping or clinical speed limits implied.
                                        all_velocity = np.diff(recovered, axis=0)/np.diff(times)[:, None, None]
                                        all_acceleration = np.diff(all_velocity, axis=0)/((np.diff(times)[:-1]+np.diff(times)[1:])/2)[:, None, None]
                                        pending_result = assess_pending(joints, times, pending, handedness=hand,
                                            length_unit='model_native_units', point_kinds=kinds)
                                        (case/'pending_bmc_assessment.private.json').write_bytes(canonical(pending_result))
                                    with timer.phase('sampled_triangle_surface_QA'):
                                        surfaces = [surface_frame(v, mesh) for v in vertices]
                                        (case/'surface_QA.private.json').write_bytes(canonical(surfaces))
                                    ready, render = render_video(case, vertices, joints, faces, spec, timer)
                                    with timer.phase('lineage_and_aggregate_QA'):
                                        fingerprint = hashlib.sha256(vertices.tobytes()+raw.tobytes()+times.tobytes()).hexdigest()
                                        video_fingerprint = snapshot_file(case/'unmasked_diagnostic.private.avi')['sha256']
                                        fingerprints.setdefault(fingerprint, []).append(label)
                                        video_fingerprints.setdefault(video_fingerprint, []).append(label)
                                        (case/'lineage.private.json').write_bytes(canonical({'native_geometry_time_sha256': fingerprint,
                                            'video_sha256': video_fingerprint, 'parent_recipe': f's{seed}_{primitive}',
                                            'hand': hand, 'generation_policy': policy, 'new_independent_family': False}))
                                    state = 'COMPLETED'
                            except BaseException as exc:
                                log.write(canonical({'event': 'ERROR', 'case': label, 'exception_type': type(exc).__name__})+b'\n')
                                raise
                            finally:
                                timing = timer.snapshot(ready, state)
                                (case/'timing.private.json').write_bytes(canonical(timing))
                            reasons = ['MODEL_PRIOR_ONLY_NOT_BIOLOGICAL_ADMISSION', 'BMC_LIMITS_UNRESOLVED',
                                'CONTACT_OBJECT_PHYSICS_NOT_TESTED', 'FINAL_MASKED_RENDITION_NOT_CHECKED',
                                'HUMAN_FEASIBILITY_NOT_OBSERVED', 'NO_EVIDENCE_BACKED_POOL_ADMISSION']
                            if policy_loss.any(): reasons.append('GENERATION_POLICY_RESIDUAL_VIOLATION')
                            if source_loss.any(): reasons.append('AUTHOR_DEFAULT_RESIDUAL_VIOLATION')
                            intersections = sum(bool(s['pair_ids'].get('intersects')) for s in surfaces)
                            unmeasurable = sum(s['state'] == 'UNMEASURABLE_DEGENERATE_TRIANGLES' for s in surfaces)
                            if intersections: reasons.append('SAMPLED_SURFACE_INTERSECTION_INDICATOR')
                            if unmeasurable: reasons.append('SURFACE_QA_UNMEASURABLE')
                            row = {'case': label, 'hand': hand, 'seed': seed, 'primitive': primitive, 'policy': policy,
                                'frames_n': FRAMES, 'recipe_replay_exact': True, 'parameter_corrections_n': 0,
                                'policy_penalized_frames_n': int(np.any(policy_loss > 0, axis=(1, 2)).sum()),
                                'author_default_penalized_frames_n': int(np.any(source_loss > 0, axis=(1, 2)).sum()),
                                'angle_roundtrip_max_abs_radians': float(np.abs(recovered-angles).max()),
                                'max_anatomical_axis_speed_rad_s': float(np.abs(all_velocity).max()),
                                'max_anatomical_axis_acceleration_rad_s2': float(np.abs(all_acceleration).max()),
                                'speed_acceleration_limits_verified': False, 'pending_BMC_state': pending_result['state'],
                                'surface_indicator_frames_n': intersections, 'surface_unmeasurable_frames_n': unmeasurable,
                                'surface_candidate_pair_tests_n': sum(s['tested_pairs_n'] for s in surfaces),
                                'surface_boundary_edges_n': mesh['boundary_edges_n'],
                                'surface_scope': 'nonshared-vertex sampled triangles only; no continuous/volume/adjacent-face proof',
                                'render': render, 'timing': timing, 'decision': 'QUARANTINED_DIAGNOSTIC',
                                'rejection_reasons': reasons, 'accepted_into_pool': False, 'release_allowed': False}
                            (case/'decision.private.json').write_bytes(canonical(row)); cases.append(row)
                            log.write(canonical({'event': 'DECIDED', **row})+b'\n')
                del model, result, neutral
        with journal.stage('source_and_scope_after_generation'):
            authorize_inputs(intake, research_record); verify(anatomical_record)
            for row in sources.values():
                if snapshot_file(row['path']) != row: raise ValueError('Original model input changed')
            if extract_profile(loss_source) != source_prior: raise ValueError('Pinned prior source changed')
        if completed != planned: raise ValueError('Native forward/QC sample count differs from design')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed: journal.close_without_terminal()
    export_bundle(output/'journal', output/'journal_bundle.private.zip'); verified = verify_bundle(output/'journal_bundle.private.zip')
    summary = {'version': VERSION, 'primitive_profile': profile, 'scope': 'private_model_conditioned_primitives_surface_and_unmasked_video_diagnostics',
        'cases_n': len(cases), 'frames_per_case': FRAMES, 'native_forward_frames_n': completed,
        'rendered_decoded_frames_n': sum(r['render']['frames_n'] for r in cases), 'cases': cases, 'shared_hand_setups': setups,
        'runtime_environment': environment,
        'exact_duplicate_native_geometry_time_groups': [v for v in fingerprints.values() if len(v) > 1],
        'exact_duplicate_video_byte_groups': [v for v in video_fingerprints.values() if len(v) > 1],
        'native_geometry_time_unique_n': len(fingerprints), 'video_byte_unique_n': len(video_fingerprints),
        'runtime_journal_status': verified['status'], 'runtime_journal_completed_frames_n': verified['completed_frames'],
        'new_model_inference': True, 'random_motion_sampled': True, 'new_independent_families_n': 0,
        'masked_videos_n': 0, 'accepted_into_pool_n': 0, 'quarantined_cases_n': len(cases),
        'biological_validity_proven': False, 'physical_unit_verified': False, 'full_generator_ready': False, 'release_allowed': False,
        'limitations': ['Author model defaults and project mirrored comparator are distinct and not clinical limits.',
            'Primitive coupling, time, shape and appearance sampling are authored engineering parameters.',
            'Sampled triangle QA excludes shared vertices and cannot prove volume/continuous/adjacent-face clearance.',
            'Z-buffer diagnostic source videos are unmasked, nonphotorealistic and not delivery/security approved.',
            'Per-video times exclude shared model setup and final receipt sealing; fixed-order local run, no fair method/cold-cache benchmark.',
            'No object/contact physics, independent human/attack study or pool admission.']}
    (output/'summary.json').write_bytes(canonical(summary)); return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('intake', 'research-record', 'worker-root', 'anatomical-root', 'anatomical-record', 'loss-source', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--profile', choices=tuple(PROFILES), default='legacy_all_fingers')
    a = parser.parse_args()
    print(json.dumps(execute(a.intake, a.research_record, a.worker_root, a.anatomical_root,
                             a.anatomical_record, a.loss_source, a.output, a.profile)))
