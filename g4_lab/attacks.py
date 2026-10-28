"""Deterministic, local-only diagnostic responses for the authorized G4 lab.

Scope and assumptions
---------------------
This module only transforms an in-memory ``(T, 21, 2)`` trajectory supplied by
the caller. It performs no file, camera, browser, network, server, or CAPTCHA
submission operations. Treat the supplied trajectory as a known development /
exploratory baseline. ``exact_replay`` is an explicit oracle upper-bound
control, not an attacker success claim. The remaining responses are simple
fixed baselines; they are not learned, searched, tuned, or validated on a
holdout set. Their output must not be described as generalization to unseen
source families.
"""

from __future__ import annotations

import numpy as np


def generate_attacks(
    base: np.ndarray, seed: int = 20261028
) -> dict[str, np.ndarray]:
    """Return deterministic baseline responses for a ``(T, 21, 2)`` trajectory.

    ``base`` is interpreted as one known development/exploratory trajectory.
    Inputs must be non-empty, finite numeric arrays. Each returned array has
    the same shape and floating-point dtype. ``bounded_random`` samples each
    coordinate within that coordinate's observed min/max in ``base``.
    """
    frames = np.asarray(base, dtype=np.float64)
    if frames.ndim != 3 or frames.shape[1:] != (21, 2):
        raise ValueError("base must have shape (T, 21, 2)")
    if frames.shape[0] == 0:
        raise ValueError("base must contain at least one frame")
    if not np.isfinite(frames).all():
        raise ValueError("base must contain only finite coordinates")

    n_frames = frames.shape[0]
    middle = (n_frames - 1) // 2

    # Independent child streams keep each seeded baseline stable if the
    # implementation order of other baselines changes later.
    shuffle_seed, random_seed = np.random.SeedSequence(seed).spawn(2)
    shuffle_rng = np.random.default_rng(shuffle_seed)
    random_rng = np.random.default_rng(random_seed)

    fraction = np.linspace(0.0, 1.0, n_frames, dtype=np.float64)[:, None, None]
    endpoint_interpolation = (
        frames[0][None, :, :] * (1.0 - fraction)
        + frames[-1][None, :, :] * fraction
    )

    lows = frames.min(axis=0)
    highs = frames.max(axis=0)

    return {
        # Oracle positive control: exact access to the supplied target sequence.
        "exact_replay": frames.copy(),
        # Static posture controls use one known pose for the entire attempt.
        "hold_first": np.repeat(frames[0:1], n_frames, axis=0),
        "hold_middle": np.repeat(frames[middle : middle + 1], n_frames, axis=0),
        "hold_last": np.repeat(frames[-1:], n_frames, axis=0),
        # Straight-line temporal baseline between observed endpoint poses.
        "endpoint_interpolation": endpoint_interpolation,
        # Time-reversal and deterministic frame-order permutation controls.
        "reverse": frames[::-1].copy(),
        "frame_shuffle": frames[shuffle_rng.permutation(n_frames)].copy(),
        # Degenerate and seeded, coordinate-bounded negative controls.
        "all_zero": np.zeros_like(frames),
        "bounded_random": random_rng.uniform(lows, highs, size=frames.shape),
    }
