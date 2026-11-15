"""Shared proper cameras and a rest-bone surface proxy, not anatomy labels."""
import math
import numpy as np

WIDTH, HEIGHT = 512, 420
VIEWS = ('reference_positive', 'reference_negative')
BASES = (1, 5, 9, 13, 17)
EDGES = tuple((0, b) for b in BASES)+tuple((b+j, b+j+1) for b in BASES for j in range(3))
PROTECTED_EDGES = ((9, 10), (10, 11))
TIP_EDGES = {'thumb': (3, 4), 'index': (7, 8), 'ring': (15, 16), 'pinky': (19, 20)}
VERSION = 'shared_reference_camera_and_rest_nearest_bone_proxy_v1'
CAMERA_MODES = ('world_shared', 'hand_neutral_registered')


def neutral_registration(reference, hand):
    """Proper fixed model-neutral basis; left lateral sign preserves chirality.

    This is a model reference convention, not measured clinical palm/back axes.
    Apply row-vector coordinates as (points - first_wrist) @ basis for all
    frames. No reflection, scale change or per-frame orientation fitting.
    """
    p = np.asarray(reference, float)
    if p.shape != (21, 3) or not np.isfinite(p).all() or hand not in ('right', 'left'):
        raise ValueError('Finite neutral reference and explicit hand required')
    y = unit(p[9]-p[0]); x = p[17]-p[5]; x = unit(x-(x@y)*y)
    if hand == 'left': x *= -1
    result = np.column_stack((x, y, np.cross(x, y)))
    if not np.allclose(result.T@result, np.eye(3), atol=1e-10) or np.linalg.det(result) < 0:
        raise ValueError('Proper neutral registration required')
    return result


def unit(vector):
    vector = np.asarray(vector, float); length = np.linalg.norm(vector)
    if not np.isfinite(vector).all() or length <= 1e-10:
        raise ValueError('Finite nondegenerate reference axis required')
    return vector/length


def common_camera(reference, cases, config):
    """One calibration for all cases, including admissible-circle envelopes.

    Only each case's first wrist translation is removed; later root motion is
    preserved. Fit uses all current development sequences, not unseen/live data.
    """
    reference = np.asarray(reference, float)
    if reference.shape != (21, 3) or not np.isfinite(reference).all() or not cases:
        raise ValueError('Recorded neutral reference and nonempty cases required')
    y = unit(reference[9]-reference[0]); x = reference[17]-reference[5]
    x = unit(x-(x@y)*y); normal = np.cross(x, y); basis = np.column_stack((x, y, normal))
    if not np.allclose(basis.T@basis, np.eye(3), atol=1e-10) or np.linalg.det(basis) < 0:
        raise ValueError('Proper shared reference camera required')
    low = []; high = []
    for case in cases:
        vertices = np.asarray(case['vertices'], float); joints = np.asarray(case['joints'], float)
        if vertices.ndim != 3 or vertices.shape[2] != 3 or joints.shape != (len(vertices), 21, 3) or not np.isfinite(vertices).all() or not np.isfinite(joints).all():
            raise ValueError('Complete finite registered source sequences required')
        origin = joints[0, 0]; flat = (vertices-origin)@basis[:, :2]
        points = (joints-origin)@basis[:, :2]
        low.append(flat.min(axis=(0, 1))); high.append(flat.max(axis=(0, 1)))
        centers = (points[:, 0]+points[:, 9])/2
        distances = np.linalg.norm(points[:, [4, 8, 16, 20]]-centers[:, None], axis=2)
        maximum_radius = np.sort(distances, axis=1)[:, -config.condition2_min_visible_fingers]/(1+config.condition2_margin_frac)
        low.append((centers-maximum_radius[:, None]).min(axis=0))
        high.append((centers+maximum_radius[:, None]).max(axis=0))
    lo = np.min(low, axis=0); hi = np.max(high, axis=0); extent = hi-lo
    if (extent <= 1e-10).any(): raise ValueError('Degenerate global frame extent')
    return {'version': VERSION, 'basis_columns': basis.tolist(), 'center_base': ((lo+hi)/2).tolist(),
        'pixels_per_native_unit': float(min((WIDTH-70)/extent[0], (HEIGHT-70)/extent[1])),
        'width': WIDTH, 'height': HEIGHT, 'pixel_origin': [WIDTH/2, HEIGHT/2],
        'fit_scope': 'all registered development meshes and maximum legacy-cue-admissible circle envelopes',
        'root_transform': 'one first-frame wrist translation per case; no frame-wise recentering',
        'physical_camera_calibrated': False, 'independent_palm_back_annotation': False}


def view_basis(camera, view):
    if view not in VIEWS: raise ValueError('Explicit named camera view required')
    basis = np.asarray(camera['basis_columns'], float); center = np.array(camera['center_base'], float)
    if view == VIEWS[1]:
        basis = basis@np.diag([-1., 1., -1.]); center[0] *= -1
    if not np.allclose(basis.T@basis, np.eye(3), atol=1e-10) or np.linalg.det(basis) < 0:
        raise ValueError('Proper camera basis required')
    return basis, center


def project(points, origin, camera, view):
    basis, center = view_basis(camera, view)
    points = np.asarray(points, float); origin = np.asarray(origin, float)
    if points.shape[-1] != 3 or origin.shape != (3,) or not np.isfinite(points).all() or not np.isfinite(origin).all():
        raise ValueError('Finite source coordinates and fixed first wrist required')
    transformed = points-origin; flat = (transformed@basis[:, :2]-center)*camera['pixels_per_native_unit']
    flat[..., 0] += WIDTH/2; flat[..., 1] = HEIGHT/2-flat[..., 1]
    return flat, transformed@basis[:, 2]


def surface_proxy(vertices, joints, faces):
    """Static conservative face sets via nearest neutral skeleton segments.

    Whole faces touching a vertex assigned to either middle PIP incident link
    are protected. This geometric surrogate requires independent anatomy review.
    """
    vertices = np.asarray(vertices, float); joints = np.asarray(joints, float); faces = np.asarray(faces)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or joints.shape != (21, 3) or not np.isfinite(vertices).all() or not np.isfinite(joints).all():
        raise ValueError('Finite recorded neutral mesh/joints required')
    if faces.dtype.kind not in 'iu' or faces.ndim != 2 or faces.shape[1] != 3 or faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError('Matching valid native mesh faces required')
    a = joints[[e[0] for e in EDGES]]; b = joints[[e[1] for e in EDGES]]; d = b-a
    length2 = (d*d).sum(axis=1)
    if (length2 <= 1e-20).any(): raise ValueError('Degenerate neutral skeleton segment')
    t = np.clip(np.einsum('nsc,sc->ns', vertices[:, None]-a, d)/length2, 0., 1.)
    distance2 = ((vertices[:, None]-(a+t[..., None]*d))**2).sum(axis=2)
    owner = distance2.argmin(axis=1)
    def face_set(edges):
        indices = [EDGES.index(e) for e in edges]
        return np.flatnonzero(np.isin(owner[faces], indices).any(axis=1)).astype(np.int32)
    protected = face_set(PROTECTED_EDGES)
    if not len(protected): raise ValueError('Empty protected surface proxy')
    return {'protected_face_ids': protected, 'tip_patches': {k: face_set([v]) for k, v in TIP_EDGES.items()},
            'vertex_nearest_edge': owner.astype(np.int32), 'anatomical_coverage_proven': False,
            'definition': 'rest nearest-segment proxy; entire incident faces; middle MCP-PIP and PIP-DIP links'}


def surface_weight_interval(legacy, projected_joints, amodal):
    points = np.asarray(projected_joints, float)
    if points.ndim != 3 or points.shape[1:] != (21, 2) or len(points) != len(amodal) or not np.isfinite(points).all():
        raise ValueError('Complete projected joints and per-frame proxy denominator required')
    lower = float(legacy['minimum_w3']); upper = float(legacy['maximum_w3']); rows = []; empty = 0
    for frame, target in enumerate(amodal):
        target = np.asarray(target)
        if target.shape != (HEIGHT, WIDTH) or target.dtype != bool:
            raise ValueError('Explicit full-resolution amodal proxy raster required')
        yy, xx = np.nonzero(target); center = (points[frame, 0]+points[frame, 9])/2
        scale = np.linalg.norm(points[frame, 0]-points[frame, 9])
        if scale <= 1e-10 or not 0 <= int(center[0]) < WIDTH or not 0 <= int(center[1]) < HEIGHT:
            raise ValueError('Degenerate or out-of-frame mask center')
        if not len(xx): empty += 1; rows.append(None); continue
        # Two pixels are a predeclared raster/codec buffer, not anatomical mm.
        required_radius = math.ceil(float(np.hypot(xx-int(center[0]), yy-int(center[1])).max()))+2
        value = float(2*required_radius/scale); lower = max(lower, value); rows.append(value)
    feasible = bool(not empty and bool(legacy['feasible']) and lower <= upper)
    return {'minimum_w3': lower, 'maximum_w3': upper, 'feasible': feasible,
        'proposed_w3': (lower+upper)/2 if feasible else None, 'empty_proxy_frames_n': empty,
        'raster_buffer_pixels': 2, 'surface_frame_minimum_w3': rows,
        'scope': 'source-specific legacy joint/cue bounds plus conservative model surface proxy; not global calibration'}
