"""Rational fallback on binary64 input coordinates, not exact physical anatomy."""
from fractions import Fraction as F
import numpy as np

VERSION = 'binary64_rational_shared_simplex_v1'


def add(a, b): return tuple(x+y for x, y in zip(a, b))
def sub(a, b): return tuple(x-y for x, y in zip(a, b))
def mul(a, t): return tuple(x*t for x in a)
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def points(value):
    a = np.asarray(value, dtype=float)
    if a.ndim != 2 or a.shape[1] != 3 or not np.isfinite(a).all() or (np.abs(a) > 1e6).any():
        raise ValueError('Finite bounded binary64 point arrays required')
    return [tuple(F.from_float(float(x)) for x in row) for row in a]


def tolerance_squared(vertices, epsilon):
    if type(epsilon) not in (int, float) or not 1e-12 <= epsilon <= 1e-5:
        raise ValueError('Registered relative epsilon required')
    p = points(vertices)
    if not p:
        raise ValueError('Complete mesh extent required')
    # Compute the same diagonal definition in rational arithmetic; no sqrt or
    # rounded normalization is fed into this fallback.
    diagonal2 = sum((max(v[k] for v in p)-min(v[k] for v in p))**2 for k in range(3))
    if diagonal2 <= 0:
        raise ValueError('Positive mesh diagonal required')
    return diagonal2*F.from_float(float(epsilon))**2


def _clip(a, b, normal):
    polygon = list(a)
    for k in range(3):
        origin = b[k]; inward = cross(normal, sub(b[(k+1) % 3], origin)); result = []
        if not polygon:
            break
        for p, q in zip(polygon, polygon[1:]+polygon[:1]):
            dp, dq = dot(sub(p, origin), inward), dot(sub(q, origin), inward)
            if dp >= 0:
                result.append(p)
            if (dp < 0 < dq) or (dq < 0 < dp):
                result.append(add(p, mul(sub(q, p), dp/(dp-dq))))
        polygon = result
    return polygon


def _section(triangle, distances):
    result = [p for p, d in zip(triangle, distances) if d == 0]
    for k in range(3):
        j = (k+1) % 3
        if distances[k]*distances[j] < 0:
            result.append(add(triangle[k], mul(sub(triangle[j], triangle[k]), distances[k]/(distances[k]-distances[j]))))
    return result


def _distance2(point, shared):
    delta = sub(point, shared[0])
    if len(shared) == 1:
        return dot(delta, delta)
    edge = sub(shared[1], shared[0]); t = max(F(0), min(F(1), dot(delta, edge)/dot(edge, edge)))
    residual = sub(delta, mul(edge, t))
    return dot(residual, residual)


def pair(a, b, shared, native_tolerance_squared):
    a, b, shared = points(a), points(b), points(shared)
    if (len(a) != 3 or len(b) != 3 or len(shared) not in (1, 2) or
            len(set(shared)) != len(shared) or any(p not in a or p not in b for p in shared) or
            not isinstance(native_tolerance_squared, F) or native_tolerance_squared <= 0):
        raise ValueError('Triangles with their exact common simplex and rational tolerance required')
    origin = shared[0]
    a, b, shared = ([sub(p, origin) for p in value] for value in (a, b, shared))
    na = cross(sub(a[1], a[0]), sub(a[2], a[0])); nb = cross(sub(b[1], b[0]), sub(b[2], b[0]))
    if dot(na, na) == 0 or dot(nb, nb) == 0:
        return {'state': 'EXACT_DEGENERATE_TRIANGLE', 'resolved': False, 'version': VERSION}
    line = cross(na, nb); line2 = dot(line, line)
    if line2 == 0:
        polygon = _clip(a, b, nb); branch = 'coplanar_rational_convex_clip'
    elif len(shared) == 2:
        polygon = shared; branch = 'noncoplanar_shared_edge_identity'
    else:
        pa, pb = _section(a, [dot(p, nb) for p in a]), _section(b, [dot(p, na) for p in b])
        if not pa or not pb:
            raise ValueError('Exact shared point missing from plane section')
        ia, ib = [dot(p, line)/line2 for p in pa], [dot(p, line)/line2 for p in pb]
        low, high = max(min(ia), min(ib)), min(max(ia), max(ib))
        if low > high:
            raise ValueError('Exact section overlap lost shared point')
        polygon = [mul(line, low), mul(line, high)]; branch = 'noncoplanar_rational_section_interval'
    if not polygon:
        raise ValueError('Exact shared simplex disappeared')
    maximum = max(_distance2(p, shared) for p in polygon)
    beyond = maximum > native_tolerance_squared
    return {'version': VERSION, 'resolved': True, 'branch': branch,
            'state': 'EXACT_NONLOCAL_BEYOND_REGISTERED_RESOLUTION' if beyond else 'EXACT_WITHIN_REGISTERED_RESOLUTION',
            'intersection_outside_shared_simplex_exactly': maximum > 0,
            'beyond_registered_resolution': beyond,
            'maximum_distance_squared_native_float': float(maximum),
            'tolerance_squared_native_float': float(native_tolerance_squared),
            'comparison_used_rational_arithmetic': True,
            'input_coordinate_scope': 'exact binary64 values; no measurement/physical uncertainty model'}
