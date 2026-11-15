"""Pose/shape/root controls for BMC directions; no clinical or safety bounds.

Compose perturbations as rotations in the actual native parent frame. Compare
current geometric axes with frozen mean-neutral axes transported by root only.
The beta and pose values are engineering probes, not population/safe ranges.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation

from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from analysis.runtime_benchmark.mano_recorded_producer import (
    RAW_PARENTS, TIP_NAMES, ORDER, authorize_inputs, canonicalize, point_contract,
)
from analysis.runtime_benchmark.mano_axis_probe import pair_delta
from analysis.runtime_benchmark.mano_bmc_direction_probe import geometric_axes, native_axial_axes
from validation_v03.run_manifest import snapshot_file
from validation_v03.session_artifacts import canonical, _private

VERSION = 'mano_bmc_pose_shape_root_direction_controls_v1'
STEP = .02
PLANNED = 4346  # 2 mean-neutral + 24 contexts * (1 base + 180 changes)


def contexts():
    rows = []
    bent = np.array([[.12, (-1)**j*.07, .09] for j in range(15)])
    for beta in (-1., 0., 1.):
        shape = np.zeros(10); shape[0] = beta
        for pose_name, pose in (('flat', np.zeros((15, 3))), ('compound', bent)):
            for root_name, root in (('identity', [0., 0., 0.]), ('rotated', [.2, -.1, .15])):
                rows.append({'id': len(rows), 'beta0': beta, 'pose_name': pose_name,
                             'root_name': root_name, 'betas': shape.copy(),
                             'pose': pose.reshape(45).copy(), 'root': np.array(root)})
    return rows


def world_rotations(pose, root, parents=RAW_PARENTS):
    pose = np.asarray(pose, float); root = np.asarray(root, float)
    if pose.shape != (45,) or root.shape != (3,) or not np.isfinite(pose).all() or not np.isfinite(root).all():
        raise ValueError('Complete finite axis-angle pose/root required')
    if tuple(parents) != RAW_PARENTS:
        raise ValueError('Explicit MANO parent contract required')
    local = Rotation.from_rotvec(np.vstack((root, pose.reshape(15, 3)))).as_matrix()
    world = [local[0]]
    for joint in range(1, 16):
        world.append(world[parents[joint]] @ local[joint])
    return np.array(world)


def compose_world_delta(pose, root, joint, world_axis, radians):
    """R'_local = R_parent^T Exp(axis_world * step) R_parent R_local."""
    world = world_rotations(pose, root)
    axis = np.asarray(world_axis, float)
    if type(joint) is not int or not 1 <= joint < 16 or axis.shape != (3,) or not np.isfinite(axis).all():
        raise ValueError('Explicit joint and finite world axis required')
    if not np.isclose(np.linalg.norm(axis), 1., atol=1e-9, rtol=0) or not np.isfinite(radians) or abs(radians) > .1:
        raise ValueError('Unit axis and bounded engineering step required')
    result = np.asarray(pose, float).reshape(15, 3).copy()
    parent = world[RAW_PARENTS[joint]]
    delta = Rotation.from_rotvec(parent.T @ axis * radians).as_matrix()
    result[joint-1] = Rotation.from_matrix(delta @ Rotation.from_rotvec(result[joint-1]).as_matrix()).as_rotvec()
    return result.reshape(45)


def design(pose, root, adaptive_axes, frozen_axes, angle_native):
    poses = []; rows = []
    if len(angle_native) != 15 or sorted(angle_native) != list(range(1, 16)):
        raise ValueError('Complete center-to-native permutation required')
    for method, axes in (('adaptive', adaptive_axes), ('frozen_mean_neutral', frozen_axes)):
        axes = np.asarray(axes, float)
        if axes.shape != (15, 3, 3):
            raise ValueError('Fifteen triples of world directions required')
        for angle, joint in enumerate(angle_native):
            for direction, name in enumerate(('flexion', 'abduction', 'outgoing_twist')):
                for sign in (-1, 1):
                    poses.append(compose_world_delta(pose, root, joint, axes[angle, direction], STEP*sign))
                    expected = [STEP*sign if direction == 0 else 0., STEP*sign if direction == 1 else 0.]
                    rows.append({'frame_idx': len(rows), 'method': method, 'angle_index': angle,
                                 'native_joint_index': joint, 'direction': name, 'sign': sign,
                                 'world_axis': axes[angle, direction].tolist(), 'expected_radians': expected})
    return np.array(poses, np.float32), rows


def execute(intake, research_record, worker_root, output):
    sources = authorize_inputs(intake, research_record); output = _private(output)
    if output.exists():
        raise FileExistsError('Fresh private context diagnostic required')
    sys.path.insert(0, str(Path(worker_root).resolve(strict=True)))
    from dataset_pipeline.common import LANDMARK_NAMES
    from experiments.motion_fixture.biomechanical_features import extract, GeometryError, ANGLE_RECORDS
    mapping = [ORDER[LANDMARK_NAMES.index(r['canonical_center_point'])] for r in ANGLE_RECORDS]
    children = [LANDMARK_NAMES.index(r['outgoing_bone_child_point']) for r in ANGLE_RECORDS]
    centers = [LANDMARK_NAMES.index(r['canonical_center_point']) for r in ANGLE_RECORDS]
    kinds = ['mesh_surface_tip' if r['outgoing_bone_child_point'].endswith('_TIP') else 'native_child_joint' for r in ANGLE_RECORDS]
    journal = Journal(output/'journal', {'condition_id': 'G03_MANO_BMC_CONTEXT_CONTROLS',
        'endpoint': 'pose_shape_root_geometric_direction_controls', 'input_exposure': 'existing private model',
        'cache_state': 'CPU OS/module cache uncontrolled', 'planned_frames': PLANNED, 'timeout_seconds': 600,
        'scope': 'independent engineering samples; no clinical range, time series or population distribution'})
    counter = 0; all_observations = []; summaries = []
    try:
        with journal.stage('runtime_source_before_load'):
            import torch
            import smplx
            from smplx.vertex_ids import vertex_ids
            if str(torch.__version__) != '2.5.1+cpu' or importlib.metadata.version('smplx') != '0.1.28':
                raise ValueError('Existing CPU runtime required')
            torch.set_num_threads(1); torch.manual_seed(0)
            tips = {n: vertex_ids['mano'][n] for n in TIP_NAMES}
            (output/'point_contract.private.json').write_bytes(canonical(point_contract(LANDMARK_NAMES, tips)))
        for hand in ('right', 'left'):
            directory = output/hand; directory.mkdir()
            with journal.stage(hand+'_mean_neutral_reference'):
                authorize_inputs(intake, research_record)
                model = smplx.MANO(str(Path(intake).resolve()/'models'), is_rhand=hand == 'right',
                                   use_pca=False, flat_hand_mean=True, batch_size=1, dtype=torch.float32).to('cpu')
                model.eval()
                if tuple(model.parents.tolist()) != RAW_PARENTS or model.betas.shape[1] != 10:
                    raise ValueError('Native parent/shape contract changed')
                with torch.no_grad():
                    ref = model(hand_pose=torch.zeros(1, 45), betas=torch.zeros(1, 10),
                                global_orient=torch.zeros(1, 3), transl=torch.zeros(1, 3), return_verts=True)
                ref_points = canonicalize(ref.vertices.numpy(), ref.joints.numpy(), tips)[0]
                ref_features = extract(ref_points, handedness=hand)
                frozen = native_axial_axes(geometric_axes(ref_features['local_frames'], ref_features['joint_angles_radians']), hand)
                np.savez_compressed(directory/'mean_neutral.private.npz', vertices=ref.vertices.numpy(),
                                    raw_joints=ref.joints.numpy(), canonical_joints=ref_points, frozen_world_axes=frozen)
                journal.frame_completed(counter, True); counter += 1
            for context in contexts():
                tag = f"{hand}_{context['id']:02d}"
                with journal.stage(tag+'_base_and_design'):
                    shape = context['betas']; pose = context['pose']; root = context['root']
                    with torch.no_grad():
                        base = model(hand_pose=torch.tensor(pose[None], dtype=torch.float32),
                            betas=torch.tensor(shape[None], dtype=torch.float32),
                            global_orient=torch.tensor(root[None], dtype=torch.float32),
                            transl=torch.zeros(1, 3), return_verts=True, return_full_pose=True)
                    points = canonicalize(base.vertices.numpy(), base.joints.numpy(), tips)[0]
                    features = extract(points, handedness=hand)
                    adaptive = native_axial_axes(geometric_axes(features['local_frames'], features['joint_angles_radians']), hand)
                    root_rotation = Rotation.from_rotvec(root).as_matrix()
                    transported_frozen = frozen @ root_rotation.T
                    poses, rows = design(pose, root, adaptive, transported_frozen, mapping)
                    (directory/f"context_{context['id']:02d}_design.private.json").write_bytes(canonical({
                        'context': {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in context.items()},
                        'rows': rows, 'step_radians': STEP, 'engineering_not_biological_bounds': True,
                        'frozen_axes_transport': 'native root rotation only; actual parent composition in both methods'}))
                    journal.frame_completed(counter, True); counter += 1
                with journal.stage(tag+'_forward_and_observe'):
                    n = len(poses)
                    with torch.no_grad():
                        changed = model(hand_pose=torch.from_numpy(poses),
                            betas=torch.tensor(np.broadcast_to(shape, (n, 10)).copy(), dtype=torch.float32),
                            global_orient=torch.tensor(np.broadcast_to(root, (n, 3)).copy(), dtype=torch.float32),
                            transl=torch.zeros(n, 3), return_verts=True, return_full_pose=True)
                    if not np.array_equal(changed.full_pose.numpy()[:, 3:], poses):
                        raise ValueError('Composed axis-angle inputs changed')
                    if not np.array_equal(changed.full_pose.numpy()[:, :3], np.broadcast_to(root.astype(np.float32), (n, 3))):
                        raise ValueError('Root input changed')
                    changed_points = canonicalize(changed.vertices.numpy(), changed.joints.numpy(), tips)
                    np.savez_compressed(directory/f"context_{context['id']:02d}_output.private.npz",
                        base_vertices=base.vertices.numpy(), base_raw_joints=base.joints.numpy(), base_points=points,
                        vertices=changed.vertices.numpy(), raw_joints=changed.joints.numpy(), canonical_joints=changed_points,
                        pose_axis_angle=poses, full_pose_axis_angle=changed.full_pose.numpy(), faces=model.faces)
                    observed = []
                    for row, new_points in zip(rows, changed_points):
                        journal.frame_completed(counter, True); counter += 1
                        a = row['angle_index']
                        try:
                            new_angles = extract(new_points, handedness=hand)['joint_angles_radians']
                            delta = pair_delta(new_angles, features['joint_angles_radians'])[a]
                            residual = float(np.abs(delta-np.array(row['expected_radians'])).max())
                            error = None
                        except GeometryError as exc:
                            delta = None; residual = None; error = exc.code
                        c, ch = centers[a], children[a]
                        expected_bone = Rotation.from_rotvec(np.array(row['world_axis'])*STEP*row['sign']).apply(points[ch]-points[c])
                        bone_error = float(np.abs((new_points[ch]-new_points[c])-expected_bone).max())
                        observation = {**row, 'hand': hand, 'context_id': context['id'],
                            'beta0': context['beta0'], 'pose_name': context['pose_name'], 'root_name': context['root_name'],
                            'child_kind': kinds[a], 'target_delta_radians': None if delta is None else delta.tolist(),
                            'angle_residual_radians': residual, 'geometry_error': error,
                            'world_outgoing_bone_residual_native_units': bone_error}
                        observed.append(observation); all_observations.append(observation)
                    (directory/f"context_{context['id']:02d}_observations.private.json").write_bytes(canonical(observed))
                summaries.append({'hand': hand, 'context_id': context['id'], 'beta0': context['beta0'],
                                  'pose_name': context['pose_name'], 'root_name': context['root_name']})
            del model, ref, base, changed
        with journal.stage('scope_and_source_after_forward'):
            authorize_inputs(intake, research_record)
            for source in sources.values():
                if snapshot_file(source['path']) != source:
                    raise ValueError('Original model source changed')
        if counter != PLANNED:
            raise ValueError('Forward count differs from design')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:
            journal.close_without_terminal()
    export_bundle(output/'journal', output/'journal_bundle.private.zip')
    verified = verify_bundle(output/'journal_bundle.private.zip')
    groups = []
    for method in ('adaptive', 'frozen_mean_neutral'):
        for kind in ('native_child_joint', 'mesh_surface_tip'):
            rows = [r for r in all_observations if r['method'] == method and r['child_kind'] == kind]
            residuals = [r['angle_residual_radians'] for r in rows if r['geometry_error'] is None]
            groups.append({'method': method, 'child_kind': kind, 'samples_n': len(rows),
                'geometry_errors_n': sum(r['geometry_error'] is not None for r in rows),
                'max_angle_residual_radians': max(residuals) if residuals else None,
                'median_angle_residual_radians': float(np.median(residuals)) if residuals else None,
                'max_world_bone_residual_native_units': max(r['world_outgoing_bone_residual_native_units'] for r in rows)})
    summary = {'version': VERSION, 'scope': 'engineering_pose_shape_root_geometric_directions_not_clinical',
        'contexts_n': len(summaries), 'context_design': summaries, 'native_forward_samples_n': counter, 'groups': groups,
        'runtime_journal_status': verified['status'], 'runtime_journal_completed_frames_n': verified['completed_frames'],
        'step_radians': STEP, 'new_model_inference': True, 'clinical_axes_verified_n': 0,
        'numeric_profile_changed': False, 'biological_validity_proven': False, 'release_allowed': False,
        'limitations': ['One shape coefficient only; beta +/-1 is engineering, not a population validity range.',
            'Two authored poses and two roots do not cover global motion space or singularities.',
            'Geometric axes are not measured clinical axes; no clinical limits are applied.',
            'Mesh surface tips are not rigid native joints.',
            'Independent samples are not a time series; no speed, physics, comfort or human task was tested.']}
    (output/'summary.json').write_bytes(canonical(summary))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('intake', 'research-record', 'worker-root', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(execute(args.intake, args.research_record, args.worker_root, args.output)))
