"""INFERENCE-SIDE MODULE -- see blind_cache.py's header for the import
restriction this file must respect (enforced by
tests/test_no_topology_leakage.py).

Task brief section 4: infer a directed predictive graph Ghat = (Delta_{i<-j})
from observed heading trajectories alone, for EVERY target bird i and every
ordered source j != i, with no notion of "neighbour" ever supplied.

Preferred procedure (brief's own wording):
  1. fit the regularized full predictor (bird i's next heading ~ own current
     heading + all 99 other current headings, one-hot, L2-regularized
     multinomial logistic regression -- nodewise_model.NodewiseModel, same
     frozen hyperparameters as Stage 6.5/6.6);
  2. identify a coefficient-based shortlist (sum of |coef| across bird j's
     4 one-hot columns and all fitted class rows) -- a computational-
     feasibility step (100 targets x 99 candidate sources is a lot of
     leave-one-out refits; the shortlist is disclosed, not hidden, and
     capped at `shortlist_k`, default 25 matching stage6_5/boundary_inference
     /code/api.py's own default);
  3. for each shortlisted source j, remove it from the conditioning set and
     recompute held-out log-loss;
  4. Delta_{i<-j} = ell_i^{(-j)} - ell_i^{(full)}. Positive Delta means
     removing j made bird i's prediction WORSE, i.e. j carried predictive
     information about i's next state.

Non-shortlisted (i, j) pairs get Delta=0 exactly -- a disclosed approximation
(section 4 explicitly permits "held-out predictive contribution wherever
COMPUTATIONALLY FEASIBLE"), never silently treated as missing.
"""
from __future__ import annotations

import multiprocessing as mp

import numpy as np

from blind_cache import BlindCache


def _all_other_birds(i: int, n_bird: int) -> list[int]:
    return [j for j in range(n_bird) if j != i]


def coefficient_shortlist(cache: BlindCache, i: int, n_bird: int, shortlist_k: int) -> list[int]:
    """Ranks every source j != i by the fitted full model's |coefficient|
    mass on j's one-hot block, returns the top `shortlist_k` bird ids.
    Returns [] if bird i's next heading was constant on the training fold
    (NodewiseModel's own degenerate-target fallback -- no coefficients exist)."""
    others = _all_other_birds(i, n_bird)
    model = cache.get_model(i, others)
    m = model.models_[i]
    if isinstance(m, tuple) and m[0] == "constant":
        return []
    cond_set = model.cond_set  # sorted({i} | others) == sorted(range(n_bird))
    pos = {b: k for k, b in enumerate(cond_set)}
    coef = np.abs(m.coef_)  # (n_classes_fitted, len(cond_set)*NU)
    scores = {}
    for j in others:
        p = pos[j]
        scores[j] = float(coef[:, p * 4:(p + 1) * 4].sum())
    ranked = sorted(others, key=lambda j: -scores[j])
    return ranked[:shortlist_k]


def leave_one_out_deltas(cache: BlindCache, i: int, shortlist: list[int], n_bird: int) -> tuple[float, dict]:
    others = _all_other_birds(i, n_bird)
    full_loss = cache.get_loss(i, others)
    deltas = {}
    for j in shortlist:
        minus = [x for x in others if x != j]
        loss_minus = cache.get_loss(i, minus)
        deltas[int(j)] = float(loss_minus - full_loss)
    return float(full_loss), deltas


def _infer_row(args):
    (i, train_prev, train_next, val_prev, val_next, n_bird, shortlist_k, model_kwargs) = args
    cache = BlindCache(train_prev, train_next, val_prev, val_next, **model_kwargs)
    shortlist = coefficient_shortlist(cache, i, n_bird, shortlist_k)
    full_loss, deltas = leave_one_out_deltas(cache, i, shortlist, n_bird)
    row = {j: 0.0 for j in _all_other_birds(i, n_bird)}
    row.update(deltas)
    return i, full_loss, row, shortlist, cache.stats()


def infer_directed_graph(train_prev: np.ndarray, train_next: np.ndarray,
                          val_prev: np.ndarray, val_next: np.ndarray,
                          n_bird: int | None = None, shortlist_k: int = 25,
                          model_kwargs: dict | None = None, n_jobs: int = 1) -> dict:
    """Returns dict(G={i: {j: delta}}, full_losses={i: loss}, shortlists={i:[j..]},
    n_fits_total). G has a full row for every i in range(n_bird), a full column
    for every j != i (non-shortlisted entries = 0.0 exactly, per this module's
    docstring)."""
    model_kwargs = model_kwargs or {}
    n_bird = n_bird or train_prev.shape[-1]

    tasks = [(i, train_prev, train_next, val_prev, val_next, n_bird, shortlist_k, model_kwargs)
             for i in range(n_bird)]

    if n_jobs > 1:
        with mp.Pool(n_jobs) as pool:
            results = pool.map(_infer_row, tasks)
    else:
        results = [_infer_row(t) for t in tasks]

    G, full_losses, shortlists = {}, {}, {}
    n_fits_total = 0
    for i, full_loss, row, shortlist, stats in results:
        G[i] = row
        full_losses[i] = full_loss
        shortlists[i] = shortlist
        n_fits_total += stats["n_fits"]

    return dict(G=G, full_losses=full_losses, shortlists=shortlists,
                n_bird=n_bird, shortlist_k=shortlist_k, n_fits_total=n_fits_total)
