"""Saved random MANO poses against pinned author model defaults, not humans.

BIO-09 current manotorch AnatomyConstraintLossEE defaults. No new inference,
parameter clipping, source mutation, clinical approval or pool admission.
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

from analysis.runtime_benchmark.mano_anatomical_frame_probe import extract_anatomical, AUTHOR_REVISION
from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical, _private

VERSION = 'saved_random_mano_author_model_prior_audit_v1'
LOSS_BLOB = '0e13cdb77a6dddcb2edc5e5c6d9bcd40c7f130ca'
AXES = ('twist', 'spread', 'bend')


def parse_interval(spec):
    if not isinstance(spec, str):
        raise ValueError('Explicit author interval string required')
    if spec.startswith('+-:'):
        bound = float(spec[3:]); bounds = [-bound, bound]
    elif spec.startswith('+:') and ',-:' in spec:
        positive, negative = spec[2:].split(',-:'); bounds = [-float(negative), float(positive)]
    else:
        raise ValueError('Unsupported author interval notation')
    if not np.isfinite(bounds).all() or bounds[0] > 0 or bounds[1] < 0 or max(abs(x) for x in bounds) > 180:
        raise ValueError('Finite nonnegative side magnitudes required')
    return bounds


def extract_profile(source):
    data = _private(source).read_bytes()
    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() != LOSS_BLOB:
        raise ValueError('Exact pinned author loss blob required')
    tree = ast.parse(data.decode('utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AnatomyConstraintLossEE')
    methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    setup = methods['setup']
    specs = {a.arg: ast.literal_eval(v) for a, v in zip(setup.args.args[1:], setup.args.defaults)}
    epsilon = next(ast.literal_eval(n.value) for n in ast.walk(methods['__init__']) if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Attribute) and t.attr == '_eps' for t in n.targets))
    symbols = {}; groups = {}; losses = {}; order = None

    def indices(node):
        if isinstance(node, ast.Name):
            return symbols[node.id]
        if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Name) or node.value.id != 'euler_angles':
            raise ValueError('Unexpected source joint indexing')
        dimension = node.slice.elts[1]
        if isinstance(dimension, ast.Name):
            return symbols[dimension.id]
        if isinstance(dimension, ast.Slice):
            lower = 0 if dimension.lower is None else ast.literal_eval(dimension.lower)
            upper = 16 if dimension.upper is None else ast.literal_eval(dimension.upper)
            if dimension.step is not None:
                raise ValueError('Unexpected strided joint slice')
            return list(range(lower, upper))
        raise ValueError('Unexpected source index dimension')

    for node in methods['forward'].body:
        if not isinstance(node, ast.Assign) or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id; value = node.value
        if isinstance(value, ast.List):
            symbols[name] = ast.literal_eval(value)
        elif isinstance(value, ast.Subscript):
            symbols[name] = indices(value)
        elif isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
            if value.func.attr == '_cal_loss_one_joint':
                group = value.args[1].attr; groups[group] = indices(value.args[0]); losses[name] = group
            elif value.func.attr == 'cat':
                order = [losses[v.id] for v in value.args[0].elts]
    if set(specs) != set(groups) or order is None or len(order) != len(groups):
        raise ValueError('Incomplete source groups or reduction order')
    flat = [j for group in order for j in groups[group]]
    if sorted(flat) != list(range(1, 16)) or not 0 < epsilon < .001:
        raise ValueError('Expected each non-root joint once and explicit zero mask')
    parsed = {k: [parse_interval(v) for v in values] for k, values in specs.items()}
    if any(len(v) != 3 for v in parsed.values()):
        raise ValueError('Three ordered anatomical axes required')
    return {'version': VERSION, 'source_id': 'BIO-09-IMPL-DEFAULTS', 'author_revision': AUTHOR_REVISION,
        'source_url': 'https://github.com/lixiny/manotorch/blob/'+AUTHOR_REVISION+'/manotorch/anatomy_loss.py',
        'source_functions': ['AnatomyConstraintLossEE.setup', '_cal_loss_one_axis', 'forward'],
        'source_blob': LOSS_BLOB, 'evidence_status': 'AUTHOR_MODEL_PRIOR_NOT_CLINICAL_LIMITS',
        'axes': list(AXES), 'euler_order': 'intrinsic XYZ', 'specs': specs,
        'intervals_degrees': parsed, 'native_joint_groups': groups, 'author_output_group_order': order,
        'zero_mask_radians': epsilon, 'thumb_pip_source_label_means_model_thumb_distal_joint_15': True,
        'clinical_population_or_task_validated': False, 'profile_admission_enabled': False,
        'limitations': ['Defaults extracted from author code; empirical provenance of individual numbers not established.',
            'Not the BMC two-angle representation and not a replacement for its six pending limits.',
            'Asymmetric spread defaults require hand-specific sign review; no automatic mirroring or correction.',
            'No coupling, dynamics, physical unit, collision, comfort, or human task validation.']}


def assess(angles, profile):
    angles = np.asarray(angles, float)
    if angles.ndim != 3 or angles.shape[1:] != (15, 3) or not len(angles) or not np.isfinite(angles).all():
        raise ValueError('Nonempty complete finite non-root Euler batch required')
    lower = np.zeros((15, 3)); upper = lower.copy(); covered = []
    for group, joints in profile['native_joint_groups'].items():
        intervals = np.asarray(profile['intervals_degrees'][group], float)
        if intervals.shape != (3, 2) or not np.isfinite(intervals).all() or (intervals[:, 0] > intervals[:, 1]).any():
            raise ValueError('Complete ordered finite bounds required')
        for j in joints:
            if type(j) is not int or not 1 <= j <= 15:
                raise ValueError('Explicit non-root joint required')
            covered.append(j); lower[j-1] = intervals[:, 0]*np.pi/180; upper[j-1] = intervals[:, 1]*np.pi/180
    if sorted(covered) != list(range(1, 16)):
        raise ValueError('Exactly one group per non-root joint required')
    eps = profile['zero_mask_radians']
    if type(eps) not in (int, float) or not np.isfinite(eps) or eps <= 0:
        raise ValueError('Explicit positive zero mask required')
    excess = np.maximum(np.maximum(lower-angles, angles-upper), 0.)
    effective = excess*(np.abs(angles) > eps)
    return excess, effective


def load_author_loss(source, torch):
    tree = ast.parse(_private(source).read_text(encoding='utf-8'))
    nodes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AnatomyConstraintLossEE']
    if len(nodes) != 1 or nodes[0].decorator_list:
        raise ValueError('Pinned loss class definition required')
    namespace = {'torch': torch, 'nn': torch.nn, '__name__': 'private_pinned_author_loss'}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    loss = namespace['AnatomyConstraintLossEE'](reduction='none'); loss.setup()
    return loss


def ideal_mirror_control(profile):
    # For an ideally reflected incoming-link basis B_left = S B_right
    # diag(1,1,-1), mirrored intrinsic XYZ angles are (-x,-y,z).
    # This is a coordinate control, not a fitted pair of actual model meshes.
    right = np.zeros((1, 15, 3)); right[0, 12, 1] = 30*np.pi/180
    mirrored = right*np.array([-1., -1., 1.])
    _, right_loss = assess(right, profile); _, left_loss = assess(mirrored, profile)
    return {'scope': 'ideal_mirrored_basis_angle_control_not_actual_mesh_or_clinical_hand',
        'synthetic_angle_cases_n': 2, 'native_joint': 13, 'axis': 'spread',
        'right_degrees': 30., 'mirrored_degrees': -30.,
        'angle_reflection_signs': [-1., -1., 1.],
        'right_max_axis_loss_radians': float(right_loss.max()),
        'mirrored_max_axis_loss_radians': float(left_loss.max()),
        'author_defaults_changed': False, 'clinical_asymmetry_proven': False}


def execute(random_root, random_record, anatomical_root, anatomical_record, loss_source, output):
    original_random = verify(random_record); original_anatomical = verify(anatomical_record)
    if any(r['state'] != 'EXITED_ZERO' for r in (original_random, original_anatomical)):
        raise ValueError('Previously recorded successful source runs required')
    random_root = _private(random_root); anatomical_root = _private(anatomical_root); output = _private(output)
    if output.exists():
        raise FileExistsError('Fresh private audit output required')
    for root, record in ((random_root, random_record), (anatomical_root, anatomical_record)):
        receipt = json.loads((_private(record)/'receipt.private.json').read_text(encoding='utf-8'))
        if [str(root)] != receipt['artifact_roots']:
            raise ValueError('Measured source root must be the root bound by its receipt')
        if any(output.is_relative_to(p) or p.is_relative_to(output) for p in (root, _private(record))):
            raise ValueError('Audit output must be separate from immutable source/evidence roots')
    profile = extract_profile(loss_source)
    files = sorted(random_root.glob('*/native_output.private.npz'))
    if len(files) != 8:
        raise ValueError('Explicit original eight diagnostic attempts required')
    journal = Journal(output/'journal', {'condition_id': 'G03_SAVED_RANDOM_AUTHOR_MODEL_PRIOR',
        'endpoint': 'saved_native_pose_anatomical_default_violation_audit',
        'input_exposure': 'previously recorded private poses and basis; no new model load',
        'cache_state': 'offline array computation', 'planned_frames': 192, 'timeout_seconds': 300,
        'scope': 'model-default penalty diagnostics, not clinical/human validity or pool admission'})
    cases = []; total = 0; counts = Counter(); strict_counts = Counter(); mirror = None
    try:
        import torch
        torch.set_num_threads(1)
        author = load_author_loss(loss_source, torch)
        ordered = [j-1 for g in profile['author_output_group_order'] for j in profile['native_joint_groups'][g]]
        (output/'applied_model_prior.private.json').write_bytes(canonical(profile))
        for file in files:
            case_name = file.parent.name; hand = case_name.split('_')[0]
            if hand not in ('right', 'left'):
                raise ValueError('Explicit saved hand label required')
            with journal.stage(case_name+'_extract_compare_and_count'):
                with np.load(anatomical_root/hand/'template.private.npz', allow_pickle=False) as template:
                    basis = template['basis'].copy()
                with np.load(file, allow_pickle=False) as saved:
                    full_pose = saved['full_pose_axis_angle'].copy()
                if full_pose.shape != (24, 48) or not np.isfinite(full_pose).all():
                    raise ValueError('Original complete 24-frame full-pose contract required')
                # Singularities are not silently dropped or filled. Abort preserves
                # the failed run evidence; the source data remain unchanged.
                angles = extract_anatomical(full_pose[:, 3:], basis)
                excess, effective = assess(angles, profile)
                ee16 = np.concatenate((np.zeros((len(angles), 1, 3)), angles), axis=1)
                with torch.no_grad():
                    author_joint = author(torch.from_numpy(ee16)).numpy()
                independent_joint = effective.sum(axis=2)[:, ordered]
                if author_joint.shape != independent_joint.shape or not np.isfinite(author_joint).all():
                    raise ValueError('Finite author per-joint loss contract required')
                error = float(np.abs(author_joint-independent_joint).max())
                strict_frames = np.any(excess > 0, axis=(1, 2)); effective_frames = np.any(effective > 0, axis=(1, 2))
                row = {'case': case_name, 'hand': hand, 'frames_n': len(angles),
                    'strict_outside_frames_n': int(strict_frames.sum()), 'author_penalized_frames_n': int(effective_frames.sum()),
                    'strict_outside_axis_cells_n': int((excess > 0).sum()), 'author_penalized_axis_cells_n': int((effective > 0).sum()),
                    'max_axis_excess_radians': float(excess.max()), 'max_frame_author_loss_radians': float(author_joint.sum(axis=1).max()),
                    'author_independent_max_abs_joint_loss_error_radians': error,
                    'model_prior_state': 'MODEL_PRIOR_VIOLATION' if effective_frames.any() else 'NO_MODEL_PRIOR_PENALTY_OBSERVED',
                    'accepted_into_pool': False, 'release_allowed': False}
                np.savez_compressed(output/(case_name+'_audit.private.npz'), anatomical_angles=angles,
                    strict_excess=excess, effective_axis_loss=effective, author_joint_loss=author_joint,
                    independent_joint_loss=independent_joint, root_axis_angle=full_pose[:, :3])
                (output/(case_name+'_summary.private.json')).write_bytes(canonical(row))
                for joint in range(15):
                    for axis, name in enumerate(AXES):
                        key = f'native_{joint+1:02d}_{name}'
                        counts[key] += int((effective[:, joint, axis] > 0).sum())
                        strict_counts[key] += int((excess[:, joint, axis] > 0).sum())
                for _ in range(len(angles)):
                    journal.frame_completed(total, True); total += 1
                cases.append(row)
        with journal.stage('ideal_mirrored_basis_control'):
            mirror = ideal_mirror_control(profile)
            (output/'ideal_mirror_control.private.json').write_bytes(canonical(mirror))
        with journal.stage('original_receipts_and_source_recheck'):
            if verify(random_record) != original_random or verify(anatomical_record) != original_anatomical:
                raise ValueError('Recorded source outputs changed')
            if extract_profile(loss_source) != profile:
                raise ValueError('Author model prior source changed')
        if total != 192:
            raise ValueError('Recorded audit frame count differs')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:
            journal.close_without_terminal()
    export_bundle(output/'journal', output/'journal_bundle.private.zip')
    verified = verify_bundle(output/'journal_bundle.private.zip')
    summary = {'version': VERSION, 'scope': 'saved_random_pose_author_model_default_diagnostic_not_biological_admission',
        'attempts_n': len(cases), 'frames_n': total, 'cases': cases,
        'strict_outside_frames_n': sum(r['strict_outside_frames_n'] for r in cases),
        'author_penalized_frames_n': sum(r['author_penalized_frames_n'] for r in cases),
        'model_prior_violation_attempts_n': sum(r['model_prior_state'] == 'MODEL_PRIOR_VIOLATION' for r in cases),
        'author_penalized_cells_by_native_joint_axis': dict(sorted(counts.items())),
        'strict_outside_cells_by_native_joint_axis': dict(sorted(strict_counts.items())),
        'author_independent_max_abs_joint_loss_error_radians': max(r['author_independent_max_abs_joint_loss_error_radians'] for r in cases),
        'runtime_journal_status': verified['status'], 'runtime_journal_completed_frames_n': verified['completed_frames'],
        'source_receipts_reverified': True, 'source_model_prior': 'BIO-09-IMPL-DEFAULTS',
        'ideal_mirror_control': mirror,
        'new_model_inference': False, 'new_random_motion_sampled': False, 'source_arrays_modified': False,
        'bmc_profile_changed': False, 'biological_validity_proven': False, 'accepted_into_pool_n': 0, 'release_allowed': False,
        'limitations': profile['limitations']+['Author penalties are geometric model diagnostics, not probabilities or measured human error.',
            'Raw strict excess and zero-mask effective penalties are distinct; no post-hoc relaxation.',
            'Only previously quarantined eight PCA attempts; no final video, dynamics, physics or people.']}
    (output/'summary.json').write_bytes(canonical(summary))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('random-root', 'random-record', 'anatomical-root', 'anatomical-record', 'loss-source', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(execute(args.random_root, args.random_record, args.anatomical_root,
                             args.anatomical_record, args.loss_source, args.output)))
