"""Conditional boxes through the selected SciPy/float32/SDK LBS path.

Engineering backend-error assumptions remain unvalidated. These candidates
must not issue CCD clearance, even if all stored observations are contained.
"""
import numpy as np

from analysis.runtime_benchmark.interval_boxes import Box, Unresolved, elementary, atan2_positive, norm, pack, hull, iv

VERSION = 'conditional_scipy_1101_sdk_rodrigues_lbs_boxes_v1'
ASSUMPTIONS = {'producer_polynomial_absolute_error': 1e-12,
               'float64_transcendental_absolute_error': 1e-14,
               'float32_sin_cos_absolute_error': 1e-6,
               'basic_arithmetic': 'IEEE binary32/binary64, ordinary finite reductions/FMA, bounded underflow',
               'backend_error_bounds_validated': False}


def matrix(rows, bits=64):
    return pack([pack([x if isinstance(x, Box) else Box(x, bits=bits) for x in row], bits=bits) for row in rows], bits=bits)


def euler_range(waypoints, t0, t1):
    p = np.asarray(waypoints, float)
    if (p.shape != (3, 15, 3) or not np.isfinite(p).all() or not 0 <= t0 < t1 <= 3 or
            t0 < 1.5 < t1):
        raise Unresolved('FINITE_SINGLE_SEGMENT_TIME_INTERVAL_REQUIRED')
    segment = 0 if t1 <= 1.5 else 1
    weights = []
    # Quintic is monotone on [0,1]. Use endpoint interval evaluation, not the
    # dependency-heavy natural polynomial over the complete input interval.
    for t in (t0, t1):
        u = (iv.mpf(float(t))-iv.mpf(1.5*segment))/iv.mpf(1.5)
        w = 6*u**5-15*u**4+10*u**3
        weights.append((float(w.a), float(w.b)))
    w = Box.rounded(weights[0][0], weights[1][1], 64)
    q = Box(p[segment])+(Box(p[segment+1])-Box(p[segment]))*w
    error = ASSUMPTIONS['producer_polynomial_absolute_error']
    return Box.rounded(q.lo-error, q.hi+error, 64)


def quat_mul(a, b):
    x, y, z, w = (a[i] for i in range(4)); X, Y, Z, W = (b[i] for i in range(4))
    return pack([w*X+W*x+y*Z-z*Y, w*Y+W*y+z*X-x*Z,
                 w*Z+W*z+x*Y-y*X, w*W-x*X-y*Y-z*Z])


def euler_matrix(angles):
    delta = ASSUMPTIONS['float64_transcendental_absolute_error']
    q = Box(np.array([0., 0., 0., 1.]))
    for axis in range(3):
        vector = [Box(0.), Box(0.), Box(0.), elementary('cos', angles[axis]/2, delta)]
        vector[axis] = elementary('sin', angles[axis]/2, delta)
        q = quat_mul(q, pack(vector))
    x, y, z, w = (q[i] for i in range(4))
    x2, y2, z2, w2 = x.square(), y.square(), z.square(), w.square()
    return matrix([[x2-y2-z2+w2, 2*(x*y-z*w), 2*(x*z+y*w)],
                   [2*(x*y+z*w), -x2+y2-z2+w2, 2*(y*z-x*w)],
                   [2*(x*z-y*w), 2*(y*z+x*w), -x2-y2+z2+w2]])


def matrix_quaternion(m):
    trace = m[0, 0]+m[1, 1]+m[2, 2]
    decision = [m[0, 0], m[1, 1], m[2, 2], trace]
    candidates = []
    for choice in range(4):
        if any(float(decision[choice].hi) < float(decision[j].lo) for j in range(4)):
            continue
        if choice == 3:
            q = pack([m[2, 1]-m[1, 2], m[0, 2]-m[2, 0], m[1, 0]-m[0, 1], 1+trace])
        else:
            i, j, k = choice, (choice+1) % 3, (choice+2) % 3
            values = [Box(0.) for _ in range(4)]
            values[i] = 1-trace+2*m[i, i]
            values[j] = m[j, i]+m[i, j]; values[k] = m[k, i]+m[i, k]
            values[3] = m[k, j]-m[j, k]; q = pack(values)
        q = q/norm(q)
        if float(q[3].hi) < 0:
            q = -q
        elif float(q[3].lo) < 0:
            raise Unresolved('QUATERNION_CANONICAL_SIGN_NOT_RESOLVED')
        candidates.append(q)
    if not candidates:
        raise Unresolved('NO_MATRIX_QUATERNION_BRANCH')
    return hull(candidates)


def quaternion_rotvec(q):
    delta = ASSUMPTIONS['float64_transcendental_absolute_error']
    angle = 2*atan2_positive(norm(q[:3]), q[3], delta)
    choices = []
    if float(angle.lo) <= 1e-3:
        a = Box(max(0., float(angle.lo)), min(1e-3, float(angle.hi)))
        square = a.square(); choices.append(2+square/12+7*square.square()/2880)
    if float(angle.hi) > 1e-3:
        a = Box(max(1e-3, float(angle.lo)), float(angle.hi))
        choices.append(a/elementary('sin', a/2, delta))
    return q[:3]*hull(choices)


def sdk_rodrigues(rotvec):
    r = rotvec.cast32(); zero = Box(0., bits=32)
    shifted = r+Box(float(np.float32(1e-8)), bits=32)
    angle = norm(shifted)
    if float(angle.lo) <= 0:
        raise Unresolved('SDK_SHIFTED_NORM_INCLUDES_ZERO')
    direction = r/angle
    x, y, z = (direction[i] for i in range(3))
    skew = matrix([[zero, -z, y], [z, zero, -x], [-y, x, zero]], bits=32)
    delta = ASSUMPTIONS['float32_sin_cos_absolute_error']
    sin = elementary('sin', angle, delta); cos = elementary('cos', angle, delta)
    return Box(np.eye(3), bits=32)+sin*skew+(1-cos)*(skew@skew)


def local_rotations(waypoints, basis, t0, t1):
    basis = np.asarray(basis, float)
    if basis.shape != (16, 3, 3) or not np.isfinite(basis).all():
        raise Unresolved('COMPLETE_BOUND_NATIVE_BASIS_REQUIRED')
    angles = euler_range(waypoints, t0, t1)
    rotations = [Box(np.eye(3), bits=32)]  # exact zero global axis-angle
    for j in range(15):
        native = Box(basis[j+1])@euler_matrix(angles[j])@Box(basis[j+1].T)
        rotations.append(sdk_rodrigues(quaternion_rotvec(matrix_quaternion(native))))
    return rotations


def lbs_box(rotations, template, regressor, posedirs, weights, parents):
    """beta=0/root=0/flat mean=0, with the actual float32 buffer values."""
    template, regressor, posedirs, weights = (np.asarray(x, np.float32) for x in (template, regressor, posedirs, weights))
    if (template.shape != (778, 3) or regressor.shape != (16, 778) or posedirs.shape != (135, 2334) or
            weights.shape != (778, 16) or len(rotations) != 16 or len(parents) != 16 or parents[0] != -1 or
            any(not np.isfinite(x).all() for x in (template, regressor, posedirs, weights)) or
            any(not 0 <= parents[j] < j for j in range(1, 16))):
        raise Unresolved('REGISTERED_FINITE_LBS_BUFFERS_AND_TREE_REQUIRED')
    v = Box(template, bits=32)
    joints = Box(regressor, bits=32)@v
    feature = pack([r-Box(np.eye(3), bits=32) for r in rotations[1:]], bits=32).reshape(1, 135)
    posed = (feature@Box(posedirs, bits=32)).reshape(778, 3)+v
    world = []; corrected = []
    for j, rotation in enumerate(rotations):
        offset = joints[j] if j == 0 else joints[j]-joints[parents[j]]
        local = matrix([[rotation[a, b] if b < 3 else offset[a] for b in range(4)] for a in range(3)]+[[0, 0, 0, 1]], bits=32)
        transform = local if j == 0 else world[parents[j]]@local
        world.append(transform)
        joint_h = pack([joints[j, 0], joints[j, 1], joints[j, 2], Box(0., bits=32)], bits=32).reshape(4, 1)
        shift = transform@joint_h
        corrected.append(matrix([[transform[a, b]-(shift[a, 0] if b == 3 else 0) for b in range(4)] for a in range(4)], bits=32))
    blended = (Box(weights, bits=32)@pack(corrected, bits=32).reshape(16, 16)).reshape(778, 4, 4)
    homogeneous = Box(np.concatenate((posed.lo, np.ones((778, 1))), axis=1),
                      np.concatenate((posed.hi, np.ones((778, 1))), axis=1), bits=32).reshape(778, 4, 1)
    return (blended@homogeneous)[:, :3, 0]


def chord_remainder(box, parent_start, parent_end, fraction0, fraction1):
    p0, p1 = np.asarray(parent_start, float), np.asarray(parent_end, float)
    if p0.shape != (778, 3) or p1.shape != p0.shape or not 0 <= fraction0 < fraction1 <= 1:
        raise Unresolved('REGISTERED_CHORD_AND_LEAF_FRACTIONS_REQUIRED')
    a = Box(p0)+(Box(p1)-Box(p0))*fraction0
    b = Box(p0)+(Box(p1)-Box(p0))*fraction1
    low, high = np.minimum(a.lo, b.lo), np.maximum(a.hi, b.hi)
    max_axis = np.maximum(np.abs(box.lo-high), np.abs(box.hi-low))
    squared = Box(max_axis).square()
    total = squared[:, 0]+squared[:, 1]+squared[:, 2]
    upper = Box(np.maximum(total.lo, 0), total.hi).sqrt().hi
    return np.nextafter(upper, np.inf)
