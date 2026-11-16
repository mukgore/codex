"""Evaluate the registered nonlinear Euler path at previously unsampled times."""
import numpy as np

VERSION = 'TF03_quintic_continuous_definition_midpoint_probe_v1'


def evaluate(waypoints, times):
    p, t = np.asarray(waypoints, float), np.asarray(times, float)
    if (p.shape != (3, 15, 3) or t.ndim != 1 or not len(t) or
            not np.isfinite(p).all() or not np.isfinite(t).all() or
            (t < 0).any() or (t > 3).any() or (np.diff(t) <= 0).any()):
        raise ValueError('Three finite Euler waypoints and increasing times in [0,3] required')
    rows = []
    for value in t:
        if value in (0., 1.5, 3.):
            rows.append(p[int(value/1.5)].copy()); continue
        segment = 0 if value < 1.5 else 1
        u = (value-1.5*segment)/1.5
        w = 6*u**5-15*u**4+10*u**3
        rows.append(p[segment]+(p[segment+1]-p[segment])*w)
    return np.array(rows)


def midpoint_chord_error(parent_vertices, midpoint_vertices, parent_times, midpoint_times):
    p, m = np.asarray(parent_vertices, float), np.asarray(midpoint_vertices, float)
    t, mt = np.asarray(parent_times, float), np.asarray(midpoint_times, float)
    if (p.shape != (25, 778, 3) or m.shape != (24, 778, 3) or t.shape != (25,) or mt.shape != (24,) or
            not all(np.isfinite(x).all() for x in (p, m, t, mt)) or
            not np.allclose(t, np.linspace(0, 3, 25), rtol=0, atol=1e-12) or
            not np.allclose(mt, (t[:-1]+t[1:])/2, rtol=0, atol=1e-12)):
        raise ValueError('Complete registered parent/midpoint geometry and time grids required')
    chord = (p[:-1]+p[1:])/2
    errors = np.linalg.norm(m-chord, axis=2)
    # Local endpoint extent defines only a dimensionless diagnostic scale.
    extent = np.maximum(p[:-1].max(axis=1), p[1:].max(axis=1))-np.minimum(p[:-1].min(axis=1), p[1:].min(axis=1))
    diagonal = np.linalg.norm(extent, axis=1)
    if (diagonal <= 1e-12).any():
        raise ValueError('Nondegenerate interval endpoint extent required')
    return {'per_vertex_native_error': errors,
            'interval_max_native_error': errors.max(axis=1),
            'interval_max_relative_to_endpoint_diagonal': errors.max(axis=1)/diagonal,
            'trajectory': 'quintic_Euler_then_native_rotation_and_MANO_LBS_not_vertex_chords',
            'observed_midpoint_errors_are_supremum_bounds': False,
            'continuous_collision_free_proven': False}
