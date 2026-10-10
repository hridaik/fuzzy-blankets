"""Greedy predictive boundary discovery (Part 1.5) with complexity control
(Part 1.6). INFERENCE-SIDE MODULE -- see nodewise_model.py's header for the
import restriction this file must respect.
"""
from __future__ import annotations

import numpy as np

from nodewise_model import NodewiseModel


def fit_eval(I0, cond_extra, train_prev, train_next, val_prev, val_next, **kw) -> float:
    m = NodewiseModel(I0, cond_extra, **kw).fit(train_prev, train_next)
    return m.mean_logloss(val_prev, val_next)


def screen_candidates(I0, candidates, train_prev, train_next, val_prev, val_next, **kw):
    """Single-candidate marginal screening: for each exterior bird alone, how
    much does it reduce held-out interior log-loss versus the interior-only
    baseline? This is the compute-feasibility step (Part 1.9's "sample-size
    analysis") that lets greedy forward selection restrict its search to a
    shortlist rather than scanning all exterior birds at every step -- a
    documented complexity trade-off, not a structural filter (every exterior
    bird is screened, none is excluded a priori by position or identity).
    Returns (baseline_loss, {candidate: gain}), gain = baseline - loss_with_candidate
    (positive = useful)."""
    baseline = fit_eval(I0, [], train_prev, train_next, val_prev, val_next, **kw)
    gains = {}
    for k in candidates:
        loss_k = fit_eval(I0, [k], train_prev, train_next, val_prev, val_next, **kw)
        gains[k] = baseline - loss_k
    return baseline, gains


def greedy_forward_select(I0, candidates, train_prev, train_next, val_prev, val_next,
                           full_loss: float, delta_tol: float, min_gain: float,
                           max_size: int | None = None, **kw):
    """Greedy forward selection (Part 1.5). Stops when EITHER:
      (a) the current boundary's excess loss over the full-exterior predictor
          is <= delta_tol ("screens almost as well as everything"), OR
      (b) the best remaining candidate's validated gain is <= min_gain (a
          predeclared null/uncertainty threshold -- Part 1.6's complexity
          control, so a larger B is not accepted purely because it can only
          help or tie in-sample).
    `candidates` is caller-supplied (e.g. a screened shortlist); this
    function performs no ranking of its own beyond the greedy loop.
    Returns (B_sorted, trace) -- trace records every accepted step so the
    stopping behavior is auditable, not just the final set."""
    remaining = list(candidates)
    B: list[int] = []
    cur_loss = fit_eval(I0, B, train_prev, train_next, val_prev, val_next, **kw)
    trace = [dict(step=0, added=None, B=list(B), loss=cur_loss,
                  excess_over_full=cur_loss - full_loss, gain=None)]
    while remaining and (max_size is None or len(B) < max_size):
        if cur_loss - full_loss <= delta_tol:
            trace[-1]["stop_reason"] = "delta_tol_reached"
            break
        best_k, best_loss, best_gain = None, None, -np.inf
        for k in remaining:
            loss_k = fit_eval(I0, B + [k], train_prev, train_next, val_prev, val_next, **kw)
            gain = cur_loss - loss_k
            if gain > best_gain:
                best_k, best_loss, best_gain = k, loss_k, gain
        if best_gain <= min_gain:
            trace[-1]["stop_reason"] = "no_candidate_above_min_gain"
            break
        B.append(int(best_k))
        remaining.remove(best_k)
        cur_loss = best_loss
        trace.append(dict(step=len(B), added=int(best_k), B=list(B), loss=cur_loss,
                           excess_over_full=cur_loss - full_loss, gain=float(best_gain)))
    else:
        if trace[-1].get("stop_reason") is None:
            trace[-1]["stop_reason"] = "exhausted_candidates_or_max_size"
    return sorted(B), trace
