"""Supplemental sampled intersections outside a topologically shared simplex.

Independent floating-point plane sections / convex half-plane clipping. This
does not replace the existing non-shared-pair SAT or establish volume/CCD.
"""
import numpy as np

VERSION = 'shared_simplex_plane_sections_clip_v1'
EPSILON = 1e-7  # Relative to complete mesh diagonal, not physical clearance.
EXPECTED = 'EXPECTED_SHARED_SIMPLEX_ONLY'
OVERLAP = 'NONLOCAL_OVERLAP_INDICATOR'
UNRESOLVED = 'NUMERICALLY_UNRESOLVED'
DEGENERATE = 'UNMEASURABLE_DEGENERATE_TRIANGLES'


def topology(faces, vertex_count):
    f = np.asarray(faces)
    if (f.dtype.kind not in 'iu' or f.ndim != 2 or f.shape[1:] != (3,) or
            not 1 <= len(f) <= 2000 or type(vertex_count) is not int or
            not 3 <= vertex_count <= 10000 or f.min() < 0 or f.max() >= vertex_count):
        raise ValueError('Bounded integer topology required')
    if any((f[:, a] == f[:, b]).any() for a, b in ((0, 1), (0, 2), (1, 2))):
        raise ValueError('Repeated face vertex')
    if len(np.unique(np.sort(f, axis=1), axis=0)) != len(f):
        raise ValueError('Duplicate face')
    i, j = np.triu_indices(len(f), 1)
    shared = (f[i, :, None] == f[j, None, :]).sum(axis=(1, 2))
    keep = shared > 0
    return {'faces': f.astype(np.int32), 'vertex_count': vertex_count,
            'pair_i': i[keep], 'pair_j': j[keep], 'shared_n': shared[keep],
            'all_face_pairs_n': len(i), 'shared_pairs_n': int(keep.sum())}


def _clip(a, b, normal, epsilon):
    """Intersection polygon in the common plane; vertices suffice by convexity."""
    polygon = list(a)
    for k in range(3):
        origin = b[k]; edge = b[(k+1) % 3]-origin
        inward = np.cross(normal, edge)
        inward /= np.linalg.norm(inward)
        clipped = []
        if not polygon:
            break
        for p, q in zip(polygon, polygon[1:]+polygon[:1]):
            dp, dq = float((p-origin)@inward), float((q-origin)@inward)
            # Snap only signed boundary distances at the registered numeric
            # resolution; never discard an exact shared endpoint by roundoff.
            dp = 0.0 if abs(dp) <= epsilon else dp
            dq = 0.0 if abs(dq) <= epsilon else dq
            if dp >= 0:
                clipped.append(p)
            if (dp < 0 < dq) or (dq < 0 < dp):
                clipped.append(p+(q-p)*(dp/(dp-dq)))
        polygon = clipped
    return np.asarray(polygon).reshape(-1, 3)


def _outside(points, shared, epsilon):
    delta = points-shared[0]
    if len(shared) == 1:
        distances = np.linalg.norm(delta, axis=1)
    else:
        edge = shared[1]-shared[0]
        t = np.clip((delta@edge)/(edge@edge), 0, 1)
        distances = np.linalg.norm(delta-t[:, None]*edge, axis=1)
    return bool((distances > epsilon).any())


def _section(triangle, distances):
    points = [p for p, d in zip(triangle, distances) if d == 0]
    for k in range(3):
        j = (k+1) % 3
        if distances[k]*distances[j] < 0:
            points.append(triangle[k]+(triangle[j]-triangle[k])*(distances[k]/(distances[k]-distances[j])))
    return np.asarray(points).reshape(-1, 3)


def pair(a, b, shared, *, epsilon=EPSILON):
    """Already normalized triangles sharing exactly these mesh vertices."""
    a, b, shared = (np.asarray(x, float) for x in (a, b, shared))
    if (a.shape != (3, 3) or b.shape != (3, 3) or shared.shape not in ((1, 3), (2, 3)) or
            not all(np.isfinite(x).all() for x in (a, b, shared)) or
            type(epsilon) not in (float, int) or not 1e-12 <= epsilon <= 1e-5):
        raise ValueError('Finite triangles/common simplex and bounded tolerance required')
    if any(not any(np.array_equal(p, v) for v in tri) for p in shared for tri in (a, b)):
        raise ValueError('Common simplex must consist of exact shared mesh vertices')
    if len(shared) == 2 and np.array_equal(shared[0], shared[1]):
        raise ValueError('Distinct shared edge endpoints required')
    # Local origin makes the shared point exactly zero in both plane equations.
    origin = shared[0]; a, b, shared = a-origin, b-origin, shared-origin
    normals = []
    for tri in (a, b):
        edges = np.roll(tri, -1, axis=0)-tri
        normal = np.cross(edges[0], edges[1]); area = np.linalg.norm(normal)
        if area <= epsilon*np.linalg.norm(edges, axis=1).max():
            return DEGENERATE
        normals.append(normal/area)
    na, nb = normals
    da, db = a@nb, b@na
    cross = np.cross(na, nb); cross_norm = np.linalg.norm(cross)
    if cross_norm <= 1e-12:
        # Parallel planes with a shared vertex are coplanar mathematically.
        # A residual inconsistent with this identity is not declared clear.
        if max(np.abs(da).max(), np.abs(db).max()) > epsilon:
            return UNRESOLVED
        polygon = _clip(a, b, nb, epsilon)
        if not len(polygon):
            return UNRESOLVED  # Shared vertex cannot disappear in exact arithmetic.
        return OVERLAP if _outside(polygon, shared, epsilon) else EXPECTED
    # Noncoplanar triangles sharing an edge intersect only on that edge.
    if len(shared) == 2:
        return EXPECTED if cross_norm > epsilon else UNRESOLVED
    # Strict one-sidedness gives only the common point, without unstable division.
    for distances, tri in ((da, a), (db, b)):
        d = distances[np.any(tri != 0, axis=1)]
        if (d > epsilon).all() or (d < -epsilon).all():
            return EXPECTED
    if cross_norm <= epsilon:
        return UNRESOLVED
    if any(((np.abs(d) <= epsilon) & (d != 0)).any() for d in (da, db)):
        return UNRESOLVED
    line = cross/cross_norm
    pa, pb = _section(a, da), _section(b, db)
    if not len(pa) or not len(pb):
        return UNRESOLVED
    ia, ib = pa@line, pb@line
    low, high = max(ia.min(), ib.min()), min(ia.max(), ib.max())
    if low > high+epsilon:
        return UNRESOLVED
    points = np.array([low, high])[:, None]*line
    return OVERLAP if _outside(points, shared, epsilon) else EXPECTED


def frame(vertices, mesh, *, epsilon=EPSILON):
    v = np.asarray(vertices, float)
    if v.shape != (mesh['vertex_count'], 3) or not np.isfinite(v).all():
        raise ValueError('Finite complete vertices required')
    if type(epsilon) not in (float, int) or not 1e-12 <= epsilon <= 1e-5:
        raise ValueError('Locked bounded relative epsilon required')
    lo, hi = v.min(axis=0), v.max(axis=0)
    scale = float(np.linalg.norm(hi-lo))
    if not 1e-12 < scale < 1e6:
        raise ValueError('Nondegenerate bounded mesh extent required')
    normalized = (v-(lo+hi)/2)/scale
    states = {key: [] for key in (EXPECTED, OVERLAP, UNRESOLVED, DEGENERATE)}
    f = mesh['faces']
    for i, j in zip(mesh['pair_i'], mesh['pair_j']):
        shared = np.intersect1d(f[i], f[j], assume_unique=True)
        state = pair(normalized[f[i]], normalized[f[j]], normalized[shared], epsilon=epsilon)
        states[state].append([int(i), int(j)])
    return {'version': VERSION, 'scope': 'shared_simplex_supplement_only_sampled_float_geometry',
            'all_face_pairs_n': mesh['all_face_pairs_n'], 'shared_pairs_n': mesh['shared_pairs_n'],
            'shared_vertex_only_pairs_n': int((mesh['shared_n'] == 1).sum()),
            'shared_edge_pairs_n': int((mesh['shared_n'] == 2).sum()),
            'relative_epsilon': epsilon, 'native_epsilon': epsilon*scale,
            'counts': {key: len(value) for key, value in states.items()},
            'indicator_pair_ids': states[OVERLAP],
            'unresolved_pair_ids': states[UNRESOLVED], 'degenerate_pair_ids': states[DEGENERATE],
            'supplement_clear': not any(states[k] for k in (OVERLAP, UNRESOLVED, DEGENERATE)),
            'nonshared_pairs_tested': False, 'continuous_collision_free_proven': False,
            'volume_penetration_free_proven': False, 'biological_validity_proven': False,
            'release_allowed': False}
