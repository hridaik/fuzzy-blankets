"""Bootstrap boundary-membership frequency (Part 1.7). INFERENCE-SIDE
MODULE -- see nodewise_model.py's header for the import restriction.
"""
from __future__ import annotations

import numpy as np

from nodewise_model import flatten_transitions
from greedy_selection import fit_eval, screen_candidates, greedy_forward_select


def bootstrap_membership(I0, candidates, z_train, z_val, n_boot: int, shortlist_k: int,
                          delta_tol: float | None, min_gain: float | None,
                          rng: np.random.Generator, delta_tol_frac: float | None = None,
                          min_gain_frac: float | None = None, **kw):
    """z_train: (n_traj, n_time, n_bird), resampled WITH REPLACEMENT along the
    trajectory axis only (never timesteps -- a resampled trajectory keeps all
    its own timesteps intact, so no transition is created that never
    happened). z_val is held fixed across replicates (its own disjoint
    trajectory-level split) so validated loss is comparable bootstrap-to-
    bootstrap. If delta_tol_frac/min_gain_frac are given, the absolute
    threshold is recomputed PER bootstrap replicate as that fraction of the
    replicate's own (interior_only_loss - full_loss) gap (mirroring
    api.infer_boundary's operationalization of "relative to the full
    predictor"), rather than reusing one absolute value fit to the original
    sample -- so a replicate with an unusually small or large total gap gets
    a threshold scaled to it. Returns (membership: {bird: P(bird in B_hat)},
    list of the n_boot inferred boundary sets)."""
    n_traj = z_train.shape[0]
    val_prev, val_next = flatten_transitions(z_val)
    counts = {k: 0 for k in candidates}
    boundary_sets = []
    for _ in range(n_boot):
        idx = rng.integers(0, n_traj, size=n_traj)
        z_b = z_train[idx]
        train_prev, train_next = flatten_transitions(z_b)
        full_loss = fit_eval(I0, candidates, train_prev, train_next, val_prev, val_next, **kw)
        interior_only_loss = fit_eval(I0, [], train_prev, train_next, val_prev, val_next, **kw)
        this_delta_tol, this_min_gain = delta_tol, min_gain
        if delta_tol_frac is not None:
            this_delta_tol = max(delta_tol_frac * (interior_only_loss - full_loss), 1e-4)
        if min_gain_frac is not None:
            this_min_gain = max(min_gain_frac * (interior_only_loss - full_loss), 1e-5)
        _, gains = screen_candidates(I0, candidates, train_prev, train_next, val_prev, val_next, **kw)
        shortlist = sorted(gains, key=lambda k: -gains[k])[:shortlist_k]
        B, _ = greedy_forward_select(I0, shortlist, train_prev, train_next, val_prev, val_next,
                                      full_loss=full_loss, delta_tol=this_delta_tol,
                                      min_gain=this_min_gain, **kw)
        boundary_sets.append(B)
        for k in B:
            counts[k] += 1
    membership = {int(k): counts[k] / n_boot for k in candidates}
    return membership, boundary_sets
