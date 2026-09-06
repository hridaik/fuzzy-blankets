"""Public boundary-inference API (Part 1). This is the ONLY inference-side
entry point intended for external callers (evaluation/driver scripts). It
accepts plain heading arrays and integer bird-id index sets -- never a
Lattice object, never B^D, never a graph-distance feature. See
tests/test_no_lattice_leakage.py for the enforced check (AST-based import
and call-signature scan of every module this one imports).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nodewise_model import flatten_transitions
from greedy_selection import fit_eval, screen_candidates, greedy_forward_select
from bootstrap import bootstrap_membership


@dataclass
class BoundaryInferenceResult:
    B_hat: list[int]
    trace: list[dict]
    full_loss: float
    interior_only_loss: float
    excess_loss_B_hat: float
    screening_gains: dict[int, float]
    membership: dict[int, float] | None = None
    bootstrap_sets: list[list[int]] | None = None
    params: dict = field(default_factory=dict)


def infer_boundary(
    z_train: np.ndarray,
    z_val: np.ndarray,
    I0: list[int],
    n_bird: int | None = None,
    shortlist_k: int = 25,
    delta_tol: float | None = 0.01,
    min_gain: float | None = 0.002,
    delta_tol_frac: float | None = None,
    min_gain_frac: float | None = None,
    max_size: int | None = None,
    n_boot: int = 0,
    rng: np.random.Generator | None = None,
    model_kwargs: dict | None = None,
) -> BoundaryInferenceResult:
    """z_train, z_val: (n_traj, n_time, n_bird) integer heading arrays,
    trajectory-level disjoint from each other (and from any test split the
    caller holds out for ground-truth/predictive evaluation). I0: interior
    bird ids. n_bird: total bird count (inferred from z_train's last axis if
    omitted). Candidates are every bird id not in I0 -- nothing else about
    exterior structure (position, topology, distance) is used anywhere in
    this call.
    """
    model_kwargs = model_kwargs or {}
    n_bird = n_bird or z_train.shape[-1]
    I0 = sorted(int(i) for i in I0)
    candidates = [j for j in range(n_bird) if j not in set(I0)]

    train_prev, train_next = flatten_transitions(z_train)
    val_prev, val_next = flatten_transitions(z_val)

    full_loss = fit_eval(I0, candidates, train_prev, train_next, val_prev, val_next, **model_kwargs)
    interior_only_loss = fit_eval(I0, [], train_prev, train_next, val_prev, val_next, **model_kwargs)

    # Part 1.5 says "delta relative to the full predictor". Operationalized
    # here (when *_frac is supplied) as a fraction of the TOTAL gap the full
    # exterior closes over interior-only prediction -- so a flock whose
    # exterior barely helps at all (small total gap) does not get an
    # absolute-nats threshold that is either trivially already satisfied or
    # unreachable; delta_tol/min_gain (absolute nats) remain the primitive
    # knobs greedy_selection.py actually consumes and are always reported
    # alongside the frac that produced them, so this substitution is
    # auditable, not hidden.
    total_gap = interior_only_loss - full_loss
    if delta_tol_frac is not None:
        delta_tol = max(delta_tol_frac * total_gap, 1e-4)
    if min_gain_frac is not None:
        min_gain = max(min_gain_frac * total_gap, 1e-5)
    assert delta_tol is not None and min_gain is not None, (
        "must supply either (delta_tol, min_gain) or (delta_tol_frac, min_gain_frac)"
    )

    _, gains = screen_candidates(I0, candidates, train_prev, train_next, val_prev, val_next, **model_kwargs)
    shortlist = sorted(gains, key=lambda k: -gains[k])[:shortlist_k]

    B_hat, trace = greedy_forward_select(
        I0, shortlist, train_prev, train_next, val_prev, val_next,
        full_loss=full_loss, delta_tol=delta_tol, min_gain=min_gain,
        max_size=max_size, **model_kwargs,
    )

    excess = fit_eval(I0, B_hat, train_prev, train_next, val_prev, val_next, **model_kwargs) - full_loss

    membership, boot_sets = None, None
    if n_boot > 0:
        rng = rng or np.random.default_rng(0)
        membership, boot_sets = bootstrap_membership(
            I0, candidates, z_train, z_val, n_boot=n_boot, shortlist_k=shortlist_k,
            delta_tol=delta_tol, min_gain=min_gain, delta_tol_frac=delta_tol_frac,
            min_gain_frac=min_gain_frac, rng=rng, **model_kwargs,
        )

    return BoundaryInferenceResult(
        B_hat=B_hat, trace=trace, full_loss=full_loss, interior_only_loss=interior_only_loss,
        excess_loss_B_hat=excess, screening_gains={int(k): float(v) for k, v in gains.items()},
        membership=membership, bootstrap_sets=boot_sets,
        params=dict(shortlist_k=shortlist_k, delta_tol=delta_tol, min_gain=min_gain,
                    delta_tol_frac=delta_tol_frac, min_gain_frac=min_gain_frac,
                    total_gap=float(total_gap), max_size=max_size, n_boot=n_boot, **model_kwargs),
    )
