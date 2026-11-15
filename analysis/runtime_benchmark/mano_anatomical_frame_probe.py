"""Independent anatomical-basis algebra vs selected pinned author methods.

BIO-09: CPF, ICCV2021 Sec.3 / Supp.A.1; distinguish current manotorch
a2a70c591f91551078b7bb2af9b5d9f275b626e0 from its original posed-axis method.
This is a coordinate/implementation check, not clinical calibration. Author
source and licensed models remain private, with no package installation.
"""
import argparse
import ast
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation

from analysis.runtime_benchmark.mano_recorded_producer import (
    RAW_PARENTS, TIP_NAMES, ORDER, authorize_inputs, canonicalize, point_contract,
)
from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from validation_v03.session_artifacts import canonical, _private
from validation_v03.run_manifest import snapshot_file

VERSION = 'mano_anatomical_template_conjugation_author_method_probe_v1'
PLANNED = 1130  # 2 templates + 2 hands * 3 shapes * 2 roots * 94 poses
AUTHOR_REVISION = 'a2a70c591f91551078b7bb2af9b5d9f275b626e0'


def _proper(matrices, shape):
    value = np.asarray(matrices, float)
    if value.shape != shape or not np.isfinite(value).all():
        raise ValueError('Complete finite rotation matrices required')
    if not np.allclose(np.swapaxes(value, -1, -2) @ value, np.eye(3), atol=1e-6, rtol=0) or (np.linalg.det(value) < 0).any():
        raise ValueError('Proper rotation matrices required')
    return value


def template_basis(points, hand):
    """Mean-neutral incoming-link construction matching current author basis.

    Columns: twist, spread, bend. Thumb up reference differs from other links.
    Root is an authored coordinate convention, not a measured wrist joint axis.
    """
    points = np.asarray(points, float)
    if points.shape != (21, 3) or not np.isfinite(points).all() or hand not in ('right', 'left'):
        raise ValueError('Explicit hand and complete finite canonical points required')
    reverse = [ORDER.index(j) for j in range(16)]
    twist = np.vstack(([1. if hand == 'right' else -1., 0., 0.],
        [points[reverse[RAW_PARENTS[j]]]-points[reverse[j]] for j in range(1, 16)]))
    up = np.tile([0., 1., 0.], (16, 1))
    up[13:] = [1. if hand == 'right' else -1., 1., 1.]
    bend = np.cross(twist, up)
    spread = np.cross(bend, twist)
    columns = []
    for axis in (twist, spread, bend):
        lengths = np.linalg.norm(axis, axis=1)
        if (lengths <= 1e-10).any():
            raise ValueError('Degenerate anatomical template direction')
        columns.append(axis/lengths[:, None])
    return _proper(np.stack(columns, axis=-1), (16, 3, 3))


def compose_anatomical(angles, basis):
    """For each non-root joint: R_native = B_j Rx(x) Ry(y) Rz(z) B_j^T."""
    angles = np.asarray(angles, float); basis = _proper(basis, (16, 3, 3))
    if angles.ndim != 3 or angles.shape[1:] != (15, 3) or not len(angles) or not np.isfinite(angles).all():
        raise ValueError('Nonempty batch of fifteen finite Euler triples required')
    local = Rotation.from_euler('XYZ', angles.reshape(-1, 3)).as_matrix().reshape(-1, 15, 3, 3)
    native = basis[None, 1:] @ local @ basis[None, 1:].swapaxes(-1, -2)
    return Rotation.from_matrix(native.reshape(-1, 3, 3)).as_rotvec().reshape(-1, 45)


def extract_anatomical(pose, basis):
    """Non-root angles only; root orientation must be stored separately."""
    pose = np.asarray(pose, float); basis = _proper(basis, (16, 3, 3))
    if pose.ndim != 2 or pose.shape[1] != 45 or not len(pose) or not np.isfinite(pose).all():
        raise ValueError('Nonempty batch of native non-root poses required')
    native = Rotation.from_rotvec(pose.reshape(-1, 3)).as_matrix().reshape(-1, 15, 3, 3)
    anatomy = basis[None, 1:].swapaxes(-1, -2) @ native @ basis[None, 1:]
    if (np.abs(anatomy[..., 0, 2]) >= 1.-1e-8).any():
        raise ValueError('Euler gimbal neighborhood is outside this diagnostic contract')
    return Rotation.from_matrix(anatomy.reshape(-1, 3, 3)).as_euler('XYZ').reshape(-1, 15, 3)


def design():
    angles = [np.zeros((15, 3))]; rows = [{'kind': 'neutral'}]
    for joint in range(15):
        for axis in range(3):
            for sign in (-1, 1):
                value = np.zeros((15, 3)); value[joint, axis] = sign*.12
                angles.append(value); rows.append({'kind': 'single_axis', 'native_joint': joint+1, 'axis': axis, 'sign': sign})
    for scale in (.5, 1., 1.5):
        angles.append(np.array([[.04*(-1)**j, .03, .12] for j in range(15)])*scale)
        rows.append({'kind': 'compound', 'scale': scale})
    return np.array(angles), rows


def author_methods(source_root, torch):
    """Execute function/class definitions only, never package imports/init.

    Exact selected author method bodies use supplied torch/NumPy globals.
    AxisLayerFK's model-loading constructor is bypassed explicitly. This is not
    a complete manotorch installation or a comparison of its full MANO layer.
    """
    namespace = {'torch': torch, 'np': np, 'Module': torch.nn.Module,
                 'F': torch.nn.functional, '__name__': 'private_pinned_author_methods'}
    root = _private(source_root)
    for name, accepted in (('manotorch/utils/geometry.py', None),
                           ('manotorch/axislayer.py', {'AxisAdaptiveLayer', 'AxisLayerFK'})):
        path = root/name; tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        nodes = [n for n in tree.body if (isinstance(n, ast.FunctionDef) if accepted is None
                 else isinstance(n, ast.ClassDef) and n.name in accepted)]
        if not nodes or any(n.decorator_list for n in nodes):
            raise ValueError('Unexpected pinned source definition/decorator layout')
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def sdk_transforms(full_pose, raw_joints, torch):
    from smplx.lbs import batch_rodrigues
    local = batch_rodrigues(full_pose.reshape(-1, 3)).reshape(-1, 16, 3, 3)
    world = [local[:, 0]]
    for j in range(1, 16):
        world.append(world[RAW_PARENTS[j]] @ local[:, j])
    transforms = torch.eye(4, dtype=full_pose.dtype).repeat(len(full_pose), 16, 1, 1)
    transforms[:, :, :3, :3] = torch.stack(world, dim=1)
    transforms[:, :, :3, 3] = raw_joints[:, :16]
    return transforms


def execute(intake, research_record, worker_root, author_source, output):
    sources = authorize_inputs(intake, research_record); output = _private(output)
    if output.exists():
        raise FileExistsError('Fresh private anatomical diagnostic required')
    source_root = _private(author_source)
    pinned = json.loads((source_root/'source_manifest.private.json').read_text(encoding='utf-8'))
    if pinned['revision'] != AUTHOR_REVISION:
        raise ValueError('Pinned author revision required')
    for row in pinned['files']:
        if snapshot_file(source_root/row['path'])['sha256'] != row['sha256']:
            raise ValueError('Pinned author file changed')
    sys.path.insert(0, str(Path(worker_root).resolve(strict=True)))
    from dataset_pipeline.common import LANDMARK_NAMES
    journal = Journal(output/'journal', {'condition_id': 'G03_MANO_ANATOMICAL_FRAMES',
        'endpoint': 'native_template_anatomical_algebra_and_author_selected_methods',
        'input_exposure': 'existing private model and pinned public author source',
        'cache_state': 'CPU OS/module cache uncontrolled', 'planned_frames': PLANNED, 'timeout_seconds': 600,
        'scope': 'coordinate implementation comparison, no clinical limits, human or motion-time tests'})
    counter = 0; cases = []; angles, rows = design()
    try:
        with journal.stage('runtime_and_author_method_setup'):
            import torch
            import smplx
            import importlib.metadata
            from smplx.vertex_ids import vertex_ids
            if str(torch.__version__) != '2.5.1+cpu' or importlib.metadata.version('smplx') != '0.1.28':
                raise ValueError('Existing CPU environment required')
            torch.set_num_threads(1); torch.manual_seed(0)
            author = author_methods(source_root, torch)
            tips = {n: vertex_ids['mano'][n] for n in TIP_NAMES}
            (output/'point_contract.private.json').write_bytes(canonical(point_contract(LANDMARK_NAMES, tips)))
            (output/'design.private.json').write_bytes(canonical({'rows': rows, 'anatomical_euler': angles.tolist(),
                'order': 'intrinsic XYZ = Rx Ry Rz', 'clinical_bounds_applied': False, 'sample_order_is_time': False}))
        for hand in ('right', 'left'):
            directory = output/hand; directory.mkdir()
            with journal.stage(hand+'_template_basis'):
                authorize_inputs(intake, research_record)
                model = smplx.MANO(str(Path(intake).resolve()/'models'), is_rhand=hand == 'right',
                                   use_pca=False, flat_hand_mean=True, batch_size=1, dtype=torch.float32).to('cpu')
                model.eval()
                if tuple(model.parents.tolist()) != RAW_PARENTS:
                    raise ValueError('Native joint tree changed')
                with torch.no_grad():
                    ref = model(hand_pose=torch.zeros(1, 45), betas=torch.zeros(1, 10),
                        global_orient=torch.zeros(1, 3), transl=torch.zeros(1, 3), return_verts=True, return_full_pose=True)
                points = canonicalize(ref.vertices.numpy(), ref.joints.numpy(), tips)[0]
                basis = template_basis(points, hand)
                transforms = sdk_transforms(ref.full_pose, ref.joints, torch)
                with torch.no_grad():
                    axes = author['AxisAdaptiveLayer'](side=hand)(torch.from_numpy(points[None]), transforms)
                    author_basis = torch.stack(axes, dim=-1)
                basis_error = float(np.abs(author_basis.numpy()[0]-basis).max())
                # Supply the independently verified template to selected FK methods.
                fk = author['AxisLayerFK'].__new__(author['AxisLayerFK'])
                torch.nn.Module.__init__(fk)
                fk.transf_parent_mapping = [0]+list(RAW_PARENTS[1:])
                fk.register_buffer('TMPL_R_p_a', author_basis)
                poses = compose_anatomical(angles, basis)
                with torch.no_grad():
                    ee16 = torch.from_numpy(np.concatenate((np.zeros((len(angles), 1, 3)), angles), axis=1)).float()
                    author_pose = fk.compose(ee16).numpy()
                author_matrix = Rotation.from_rotvec(author_pose[:, 1:].reshape(-1, 3)).as_matrix()
                independent_matrix = Rotation.from_rotvec(poses.reshape(-1, 3)).as_matrix()
                compose_error = float(np.abs(author_matrix-independent_matrix).max())
                np.savez_compressed(directory/'template.private.npz', points=points, basis=basis,
                    author_basis=author_basis.numpy(), poses=poses, author_pose=author_pose)
                journal.frame_completed(counter, True); counter += 1
            for beta0 in (-1., 0., 1.):
                for root_name, root in (('identity', np.zeros(3)), ('rotated', np.array([.2, -.1, .15]))):
                    tag = f"{hand}_{int(beta0):+d}_{root_name}"
                    with journal.stage(tag+'_forward_and_roundtrip'):
                        n = len(poses); betas = np.zeros((n, 10), np.float32); betas[:, 0] = beta0
                        with torch.no_grad():
                            result = model(hand_pose=torch.from_numpy(poses.astype(np.float32)), betas=torch.from_numpy(betas),
                                global_orient=torch.tensor(np.broadcast_to(root, (n, 3)).copy(), dtype=torch.float32),
                                transl=torch.zeros(n, 3), return_verts=True, return_full_pose=True)
                            transforms = sdk_transforms(result.full_pose, result.joints, torch)
                            _, author_relative, author_angles = fk(transforms)
                        recovered = extract_anatomical(result.full_pose.numpy()[:, 3:], basis)
                        # Whole root is tracked separately because author's root parent is itself.
                        extracted_error = float(np.abs(recovered-author_angles.numpy()[:, 1:]).max())
                        intended_error = float(np.abs(recovered-angles).max())
                        restored = compose_anatomical(recovered, basis)
                        restored_matrices = Rotation.from_rotvec(restored.reshape(-1, 3)).as_matrix()
                        sdk_matrices = Rotation.from_rotvec(result.full_pose.numpy()[:, 3:].reshape(-1, 3)).as_matrix()
                        roundtrip = float(np.abs(restored_matrices-sdk_matrices).max())
                        wrong_order = Rotation.from_euler('xyz', angles.reshape(-1, 3)).as_matrix()
                        correct_order = Rotation.from_euler('XYZ', angles.reshape(-1, 3)).as_matrix()
                        np.savez_compressed(directory/(tag+'_output.private.npz'), vertices=result.vertices.numpy(),
                            raw_joints=result.joints.numpy(), full_pose_axis_angle=result.full_pose.numpy(),
                            betas=betas, transforms=transforms.numpy(), anatomical_recovered=recovered,
                            author_angles=author_angles.numpy(), author_relative=author_relative.numpy(),
                            roundtrip_pose=restored, faces=model.faces)
                        cases.append({'hand': hand, 'beta0': beta0, 'root_name': root_name, 'samples_n': n,
                            'basis_max_abs_error': basis_error, 'compose_rotation_matrix_max_abs_error': compose_error,
                            'author_vs_independent_angle_max_abs_error_radians': extracted_error,
                            'intended_angle_max_abs_error_radians': intended_error,
                            'roundtrip_rotation_matrix_max_abs_error': roundtrip,
                            'root_input_max_abs_error_radians': float(np.abs(result.full_pose.numpy()[:, :3]-root).max()),
                            'author_extracted_root_max_abs_radians': float(np.abs(author_angles.numpy()[:, 0]).max()),
                            'author_composed_root_max_abs_radians': float(np.abs(author_pose[:, 0]).max()),
                            'wrong_euler_order_rotation_matrix_max_abs_error': float(np.abs(wrong_order-correct_order).max()),
                            'clinical_axis_verified': False})
                        for _ in range(n):
                            journal.frame_completed(counter, True); counter += 1
            del model, ref, result, fk
        with journal.stage('scope_and_original_inputs_recheck'):
            authorize_inputs(intake, research_record)
            for row in sources.values():
                if snapshot_file(row['path']) != row:
                    raise ValueError('Original model input changed')
            for row in pinned['files']:
                if snapshot_file(source_root/row['path'])['sha256'] != row['sha256']:
                    raise ValueError('Pinned author file changed')
        if counter != PLANNED:
            raise ValueError('Forward sample count differs')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:
            journal.close_without_terminal()
    export_bundle(output/'journal', output/'journal_bundle.private.zip')
    verified = verify_bundle(output/'journal_bundle.private.zip')
    summary = {'version': VERSION, 'scope': 'anatomical_template_coordinate_algebra_not_clinical_calibration',
        'author_revision': AUTHOR_REVISION, 'author_execution_scope': 'selected definitions; SDK-supplied template and transforms; package constructor not run',
        'native_forward_samples_n': counter, 'contexts_n': len(cases), 'poses_per_context_n': len(angles), 'cases': cases,
        'runtime_journal_status': verified['status'], 'runtime_journal_completed_frames_n': verified['completed_frames'],
        'new_model_inference': True, 'clinical_axes_verified_n': 0, 'numeric_profile_changed': False,
        'biological_validity_proven': False, 'release_allowed': False,
        'limitations': ['Selected current author methods, not the full manotorch MANO layer or original 2021 method.',
            'Mean neutral incoming-link template and thumb up reference are model conventions, not measured clinical axes.',
            'Root orientation is external to the non-root anatomical Euler representation.',
            'Small authored engineering angles, one beta coefficient, and two roots do not cover global pose space or Euler singularities.',
            'No clinical limits, coupling, velocity, collision, physics, comfort or people were validated.']}
    (output/'summary.json').write_bytes(canonical(summary))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('intake', 'research-record', 'worker-root', 'author-source', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(execute(args.intake, args.research_record, args.worker_root, args.author_source, args.output)))
