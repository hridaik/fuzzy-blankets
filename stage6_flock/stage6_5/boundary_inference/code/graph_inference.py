"""Per-(i, j) directed observational dependency (Part 1.3's Ĝ_{i<-j} and
Part 2.1). INFERENCE-SIDE MODULE -- see nodewise_model.py's header for the
import restriction.
"""
from __future__ import annotations

from nodewise_model import NodewiseModel


def infer_incidence_graph(I0, B_hat, train_prev, train_next, val_prev, val_next,
                           edge_gain_tol: float = 0.0, **model_kwargs):
    """For each i in I0, j in B_hat: is j predictively supported as an input
    to i's next-state model, given the rest of I0 ∪ B_hat? Leave-one-out
    marginal test -- fit i's model with the full frozen conditioning set and
    with j removed; j is judged a directed edge j -> i if removing it
    increases i's held-out log-loss by more than `edge_gain_tol` (a small
    predeclared tolerance against the direction-agnostic full model's own
    optimization noise). Returns (G, gains, full_loss):
      G[i][j]     -> bool, the inferred edge j -> i
      gains[i][j] -> float, loss increase from removing j (the raw evidence)
      full_loss   -> {i: loss} of the full B_hat-conditioned model, for reference.
    Never touches the true lattice adjacency -- this is exactly the
    observational procedure of Part 1, restricted to the already-frozen
    B_hat, so the resulting Ĝ can be used to build a controller (Part 2)
    without revealing B^D.
    """
    I0 = sorted(int(i) for i in I0)
    B_hat = sorted(int(b) for b in B_hat)

    full_model = NodewiseModel(I0, B_hat, **model_kwargs).fit(train_prev, train_next)
    full_loss = full_model.per_bird_logloss(val_prev, val_next)

    G = {i: {} for i in I0}
    gains = {i: {} for i in I0}
    for j in B_hat:
        reduced_extra = [b for b in B_hat if b != j]
        m = NodewiseModel(I0, reduced_extra, **model_kwargs).fit(train_prev, train_next)
        loss_wo_j = m.per_bird_logloss(val_prev, val_next)
        for i in I0:
            gain = loss_wo_j[i] - full_loss[i]
            gains[i][j] = float(gain)
            G[i][j] = bool(gain > edge_gain_tol)
    return G, gains, full_loss
