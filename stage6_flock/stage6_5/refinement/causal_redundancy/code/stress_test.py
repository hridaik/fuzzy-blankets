"""A5: stress-test the frozen predictive models (M_full, M_{B^D}, M_{B_hat})
under intervention-generated states. Refits these models on the SAME
training split Part 1 used (deterministic reproduction, not a re-tune of the
inference pipeline -- see load_frozen_inputs.py), then evaluates them using
EXACT cross-entropy against the true generative next-heading distribution
(from exact_intervention.py) rather than a finite validation sample -- so
Delta-ell here has zero Monte-Carlo noise and Delta_shift = Delta-ell over
natural minus Delta-ell over intervention is a clean, directly comparable
difference. This is a new, exact operationalization of Delta-ell for this
refinement's own 30-checkpoint set; it is not identical to (but is
consistent with) Part 1's own empirical validation-split Delta-ell.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))
BOUNDARY_INFERENCE_CODE = Path(__file__).resolve().parents[3] / "boundary_inference" / "code"
sys.path.insert(0, str(BOUNDARY_INFERENCE_CODE))

from nodewise_model import NodewiseModel, design_matrix, flatten_transitions, NU  # noqa: E402
from exact_intervention import default_precomputed_model, next_heading_dist_all, do_next_heading_dist_all  # noqa: E402

EPS = 1e-9


def fit_models(fl: dict) -> dict:
    """Fits M_full (full 80-bird exterior), M_{B^D} (true shell), M_{B_hat}
    (inferred shell) on Part 1's own training split. Returns {name: NodewiseModel}."""
    I0 = fl["I0"]
    train_prev, train_next = flatten_transitions(fl["z_train"])
    n_bird = fl["z_train"].shape[-1]
    I0_set = set(int(i) for i in I0.tolist())
    full_exterior = [j for j in range(n_bird) if j not in I0_set]

    models = {}
    for name, cond_extra in (("full", full_exterior), ("B_D", fl["B_D"]), ("B_hat", fl["B_hat"])):
        m = NodewiseModel(I0.tolist(), cond_extra).fit(train_prev, train_next)
        models[name] = m
    return models


def _predicted_dist(model: NodewiseModel, prev_states: np.ndarray, eps: float = EPS) -> dict:
    """Replicates NodewiseModel._predict_proba_full's logic (that method is
    private/internal to the frozen module, so this small piece of glue is
    reproduced here rather than reaching into a leading-underscore method)
    for every interior bird at once."""
    X = design_matrix(prev_states, model.cond_set)
    n = prev_states.shape[0]
    out = {}
    for i in model.I0:
        m = model.models_[i]
        if isinstance(m, tuple) and m[0] == "constant":
            p = np.full((n, NU), eps)
            p[:, m[1]] = 1 - eps * (NU - 1)
        else:
            proba_sparse = m.predict_proba(X)
            p = np.full((n, NU), eps)
            for k, c in enumerate(m.classes_):
                p[:, c] = proba_sparse[:, k]
            p = p / p.sum(axis=1, keepdims=True)
        out[i] = p
    return out


def exact_cross_entropy_loss(model: NodewiseModel, prev_states: np.ndarray,
                              true_dist_all: np.ndarray) -> float:
    """Mean (over interior birds and rows) of CE(p_true_i, p_model_i), where
    true_dist_all is the (n_rows, n_bird, nu) EXACT generative next-heading
    distribution (natural or do-intervened) for every row. This has no
    sampling noise -- it IS the model's expected log-loss under the true
    generative process, not an estimate of it."""
    pred = _predicted_dist(model, prev_states)
    per_bird_ce = []
    for i in model.I0:
        p_true = np.clip(true_dist_all[:, i, :], EPS, 1.0)
        p_model = np.clip(pred[i], EPS, 1.0)
        ce = -(p_true * np.log(p_model)).sum(axis=1)
        per_bird_ce.append(ce.mean())
    return float(np.mean(per_bird_ce))


def natural_excess_losses(fl: dict, models: dict, checkpoints: np.ndarray) -> dict:
    pm = default_precomputed_model()
    lattice = fl["lattice"]
    true_dist_all = np.stack([next_heading_dist_all(pm, lattice, z) for z in checkpoints])  # (n, nn, 4)
    losses = {name: exact_cross_entropy_loss(m, checkpoints, true_dist_all) for name, m in models.items()}
    return dict(loss=losses, excess=dict(
        B_D=losses["B_D"] - losses["full"],
        B_hat=losses["B_hat"] - losses["full"],
    ))


def intervention_excess_losses(fl: dict, models: dict, checkpoints: np.ndarray,
                                bird_ids: list[int]) -> dict:
    """Per bird j (pooled over checkpoints and alternative headings): exact
    excess loss of M_{B^D}/M_{B_hat} relative to M_full, evaluated at the
    do-intervened state."""
    pm = default_precomputed_model()
    lattice = fl["lattice"]
    out = {}
    for j in bird_ids:
        rows_prev = []
        rows_true = []
        for X_t in checkpoints:
            z_j = int(X_t[j])
            for z_prime in range(NU):
                if z_prime == z_j:
                    continue
                X_do = X_t.copy()
                X_do[j] = z_prime
                rows_prev.append(X_do)
                rows_true.append(do_next_heading_dist_all(pm, lattice, X_t, j, z_prime))
        rows_prev = np.array(rows_prev)
        rows_true = np.stack(rows_true)
        losses = {name: exact_cross_entropy_loss(m, rows_prev, rows_true) for name, m in models.items()}
        out[j] = dict(loss=losses, excess=dict(
            B_D=losses["B_D"] - losses["full"],
            B_hat=losses["B_hat"] - losses["full"],
        ), n_samples=len(rows_prev))
    return out


def compute_delta_shift(natural: dict, intervention_by_bird: dict) -> dict:
    """Delta_shift(B; j) = Delta-ell_intervention(B; j) - Delta-ell_natural(B),
    for B in {B_D, B_hat}."""
    out = {}
    for j, res in intervention_by_bird.items():
        out[j] = dict(
            B_D=res["excess"]["B_D"] - natural["excess"]["B_D"],
            B_hat=res["excess"]["B_hat"] - natural["excess"]["B_hat"],
        )
    return out
