"""Experimental metric primitives; not a production CAPTCHA or human probability.

DTW uses endpoint-constrained dynamic programming with squared Euclidean cost.
No missing-data imputation, classifier training, or legacy log adapter is implicit.
Only contiguous, complete, per-segment features may enter the sequence routines.
"""
from dataclasses import dataclass
import math
import numpy as np


def _series(value):
    x = np.asarray(value, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or min(x.shape) < 1 or not np.isfinite(x).all():
        raise ValueError("Expected a nonempty finite (time, features) array")
    return x


@dataclass(frozen=True)
class DTWResult:
    distance: float
    path_rmse: float
    path: tuple


def constrained_dtw(reference, response, *, radius):
    """Exact DTW in the explicit index band |i-j| <= radius.

    Standard distance=sqrt(sum squared feature errors on the min-cost path).
    path_rmse is a separate derived summary, sqrt(cost/(path length*features));
    it does NOT optimize average path cost. Ties prefer diagonal, then up, left.
    Unequal lengths require radius >= abs(n-m); the band is never widened silently.
    Caller must preselect a sample/length limit: runtime and memory are O(n*m).
    """
    x, y = _series(reference), _series(response)
    if x.shape[1] != y.shape[1]:
        raise ValueError("Feature dimensions differ")
    if isinstance(radius, bool) or not isinstance(radius, (int, np.integer)) or radius < 0:
        raise ValueError("radius must be a nonnegative integer")
    n, m = len(x), len(y)
    if abs(n-m) > radius:
        raise ValueError("Endpoints cannot connect within the specified band")
    if n*m > 1_000_000:
        raise ValueError("Experimental DTW cell budget exceeded; resample explicitly")
    cost = np.full((n+1, m+1), np.inf)
    previous = np.full((n, m), -1, dtype=np.int8)
    cost[0, 0] = 0.0
    for i in range(1, n+1):
        for j in range(max(1, i-radius), min(m, i+radius)+1):
            options = (cost[i-1, j-1], cost[i-1, j], cost[i, j-1])
            k = int(np.argmin(options))
            local = float(np.dot(x[i-1]-y[j-1], x[i-1]-y[j-1]))
            cost[i, j] = local + options[k]
            previous[i-1, j-1] = k
    if not np.isfinite(cost[n, m]):
        raise ValueError("No finite alignment path")
    i, j, path = n, m, []
    while i > 0 and j > 0:
        path.append((i-1, j-1))
        k = previous[i-1, j-1]
        if k == 0:
            i, j = i-1, j-1
        elif k == 1:
            i -= 1
        else:
            j -= 1
    path.reverse()
    return DTWResult(math.sqrt(cost[n, m]),
                     math.sqrt(cost[n, m]/(len(path)*x.shape[1])), tuple(path))


def time_derivatives(values, times_seconds, *, max_gap_seconds):
    """Time-aware velocity/acceleration of complete contiguous feature sequences.

    Uses numpy.gradient with nonuniform coordinates and second-order edges.
    Units follow input features/s and features/s^2, NOT physical m/s^2 unless
    positions are metric. No smoothing is applied; derivatives amplify noise.
    Gap limits are a protocol choice, not a built-in claim about safe dropout.
    """
    x = _series(values)
    t = np.asarray(times_seconds, dtype=float)
    if t.ndim != 1 or len(t) != len(x) or len(t) < 3 or not np.isfinite(t).all():
        raise ValueError("At least three matching finite timestamps required")
    if not np.isfinite(max_gap_seconds) or max_gap_seconds <= 0:
        raise ValueError("Positive finite max_gap_seconds required")
    dt = np.diff(t)
    if (dt <= 0).any() or (dt > max_gap_seconds).any():
        raise ValueError("Timestamps unordered/duplicated or gap exceeds protocol")
    velocity = np.gradient(x, t, axis=0, edge_order=2)
    acceleration = np.gradient(velocity, t, axis=0, edge_order=2)
    return velocity, acceleration


def _labelled_scores(labels, scores):
    """1=legitimate human, 0=specified attack; higher score favors human."""
    y, s = np.asarray(labels), np.asarray(scores, dtype=float)
    if y.ndim != 1 or s.ndim != 1 or len(y) != len(s) or len(y) == 0:
        raise ValueError("Matching nonempty one-dimensional arrays required")
    if not np.isin(y, [0, 1]).all() or set(y.tolist()) != {0, 1}:
        raise ValueError("Both human=1 and attack=0 labels required")
    if not np.isfinite(s).all():
        raise ValueError("Missing/nonfinite scores require explicit failure accounting")
    return y.astype(int), s


def operating_point(labels, scores, threshold):
    """Empirical score-only rates; not whole-session security or confidence bounds."""
    y, s = _labelled_scores(labels, scores)
    if math.isnan(float(threshold)):
        raise ValueError("threshold cannot be NaN")
    accepted = s >= threshold
    nh, na = int((y == 1).sum()), int((y == 0).sum())
    ha, aa = int(accepted[y == 1].sum()), int(accepted[y == 0].sum())
    return {"threshold": float(threshold), "human_n": nh, "attack_n": na,
            "human_accepted": ha, "attack_accepted": aa,
            "human_accept_rate": ha/nh, "attack_accept_rate": aa/na,
            "human_reject_rate": 1-ha/nh}


def threshold_table(labels, scores):
    """Empirical ROC/DET operating points with all ties handled together."""
    _, s = _labelled_scores(labels, scores)
    thresholds = [math.inf] + sorted(set(s.tolist()), reverse=True)
    return [operating_point(labels, scores, t) for t in thresholds]


def select_validation_threshold(labels, scores, *, split_name,
                                min_human_accept, max_attack_accept):
    """Select on VALIDATION only; caller must enforce actual group separation.

    Maximizes human acceptance under both empirical constraints, then minimizes
    attack acceptance, then prefers higher threshold. No feasible threshold -> None.
    This does not certify population risk or invent a production threshold.
    """
    if split_name != "validation":
        raise ValueError("Threshold selection requires the validation split")
    for limit in (min_human_accept, max_attack_accept):
        if not np.isfinite(limit) or not 0 <= limit <= 1:
            raise ValueError("Acceptance constraints must be in [0,1]")
    choices = [p for p in threshold_table(labels, scores)
               if p["human_accept_rate"] >= min_human_accept
               and p["attack_accept_rate"] <= max_attack_accept]
    if not choices:
        return None
    return max(choices, key=lambda p: (p["human_accept_rate"],
                                      -p["attack_accept_rate"], p["threshold"]))


def assert_disjoint_groups(split_groups):
    """Check caller-supplied source/participant/capture IDs, independently by type.

    For multi-source challenges include EVERY constituent source ID. Call again
    for participant and capture identities; a composite ID is not sufficient.
    """
    seen = set()
    for name, groups in split_groups.items():
        current = set(groups)
        if not current or None in current or "" in current:
            raise ValueError(f"Missing group IDs in {name}")
        if seen.intersection(current):
            raise ValueError(f"Group leakage into {name}")
        seen.update(current)
