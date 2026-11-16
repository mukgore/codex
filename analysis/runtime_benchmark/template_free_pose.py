"""Preregistered PCA pose proposals without an action primitive or time curve.

The normal coefficient scale is an engineering proposal, not a learned density
or a clinical distribution. A measured model/surface gate never releases data.
"""
import numpy as np

SEEDS = (7, 19)
HANDS = ('right', 'left')
A_INDICES = (0, 3, 6, 9, 12, 15, 18, 24)
STREAM_DOMAIN = 62026
VERSION = 'tf02_static_pca6_sigma05_v1'


def propose(hand, seed, attempt):
    if hand not in HANDS or type(seed) is not int or seed not in SEEDS or type(attempt) is not int or not 0 <= attempt < 8:
        raise ValueError('Registered hand, seed and attempt required')
    entropy = [seed, HANDS.index(hand), attempt, STREAM_DOMAIN]
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(entropy)))
    draw = rng.normal(0., .5, size=6)
    return draw, {'version': VERSION, 'entropy': entropy, 'rng': 'numpy.PCG64/SeedSequence',
                  'numpy_version': np.__version__, 'primitive': None, 'time_curve': None,
                  'coefficient_distribution': 'engineering N(0,0.5^2), not estimated population',
                  'corrections': []}


def expand(coefficients, components):
    c = np.asarray(coefficients, dtype=np.float32)
    b = np.asarray(components, dtype=np.float32)
    if c.shape != (6,) or b.shape != (6, 45) or not np.isfinite(c).all() or not np.isfinite(b).all():
        raise ValueError('Finite six coefficients and 6x45 model basis required')
    return (c @ b).reshape(1, 45)


def representation_errors(first, second):
    errors = {}
    for name, shape in (('full_pose', (1, 48)), ('joints', (1, 16, 3)), ('vertices', (1, 778, 3))):
        a = np.asarray(first[name]); b = np.asarray(second[name])
        if a.shape != shape or b.shape != shape or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError('Complete finite actual SDK representation outputs required')
        errors[name] = float(np.abs(a-b).max())
    if max(errors.values()) > 1e-6:
        raise ValueError('PCA and full-pose SDK representations disagree beyond1e-6')
    return errors


def decide(effective_excess, surface):
    excess = np.asarray(effective_excess, float)
    if excess.shape != (1, 15, 3) or not np.isfinite(excess).all() or (excess < 0).any():
        raise ValueError('Complete nonnegative model excess required')
    if surface.get('state') not in ('NO_TESTED_PAIR_INTERSECTION', 'SURFACE_INTERSECTION_INDICATORS',
                                   'UNMEASURABLE_DEGENERATE_TRIANGLES'):
        raise ValueError('Explicit surface measurement state required')
    reasons = []
    if excess.any(): reasons.append('AUTHOR_MODEL_PRIOR_EXCESS')
    if surface['state'] == 'UNMEASURABLE_DEGENERATE_TRIANGLES': reasons.append('SURFACE_UNMEASURABLE')
    elif surface['state'] == 'SURFACE_INTERSECTION_INDICATORS' or surface['pair_ids'].get('intersects'):
        reasons.append('SAMPLED_SURFACE_INTERSECTION')
    return {'model_surface_eligible': not reasons, 'rejection_reasons': reasons,
            'status': 'MODEL_CONSTRAINED_RESEARCH_ONLY', 'accepted_into_pool': False,
            'release_allowed': False, 'biological_validity_proven': False,
            'pending_BMC_state': 'UNRESOLVED_LIMITS', 'temporal_assessment': 'NOT_APPLICABLE_STATIC_POSE'}
