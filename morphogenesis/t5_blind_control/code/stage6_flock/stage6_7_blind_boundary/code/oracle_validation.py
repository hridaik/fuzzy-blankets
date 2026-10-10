"""EVALUATION-SIDE MODULE. THE ONLY module in this stage permitted to reveal
the true Moore-neighbour graph for scientific conclusions (task brief:
"Only the final oracle_validation.py module may reveal the true graph").
Must run strictly AFTER `Bhat^pred(I)` and `Bhat^causal(I)` have been
computed and frozen by the inference-side pipeline for every candidate --
never used to retroactively tune `directed_graph_inference.py`, `graph_bootstrap.py`,
`predictive_boundary.py`, or `causal_discovery.py` (task brief section 9,
"Do not use these metrics to retroactively tune the estimator").

Computes B^D(I) = one_hop_neighbors(I) (the true structural shell, task
brief's B^D(I) = {j not in I : j~i for some i in I}), then
precision/recall/Jaccard for Bhat^pred and Bhat^causal against it.
"""
from __future__ import annotations

import numpy as np

from common_67 import lattice_100, one_hop_neighbors


def true_shell(I, lattice=None) -> np.ndarray:
    lattice = lattice or lattice_100()
    return one_hop_neighbors(lattice, np.array(sorted(int(i) for i in I), dtype=int))


def graph_recovery_metrics(B_hat, B_true, n_exterior: int) -> dict:
    B_hat, B_true = set(int(b) for b in B_hat), set(int(b) for b in B_true)
    tp = len(B_hat & B_true)
    fp = len(B_hat - B_true)
    fn = len(B_true - B_hat)
    tn = n_exterior - tp - fp - fn
    precision = tp / len(B_hat) if B_hat else float("nan")
    recall = tp / len(B_true) if B_true else float("nan")
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else float("nan")
    jaccard = tp / len(B_hat | B_true) if (B_hat | B_true) else 1.0
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, precision=precision, recall=recall, f1=f1, jaccard=jaccard,
                size_hat=len(B_hat), size_true=len(B_true), exact_match=bool(B_hat == B_true))


def overlap_categories(B_pred, B_causal, B_true) -> dict:
    """Section 15's four overlay categories: predictive-only, causal-only,
    both, and true-shell members missed by both."""
    B_pred, B_causal, B_true = set(int(b) for b in B_pred), set(int(b) for b in B_causal), set(int(b) for b in B_true)
    return dict(
        predictive_only=sorted(B_pred - B_causal),
        causal_only=sorted(B_causal - B_pred),
        both=sorted(B_pred & B_causal),
        true_missed_by_both=sorted(B_true - B_pred - B_causal),
    )


def validate_candidate(I, B_hat_pred, B_hat_causal, n_bird: int = 100, lattice=None) -> dict:
    lattice = lattice or lattice_100()
    B_D = true_shell(I, lattice=lattice)
    n_exterior = n_bird - len(set(int(i) for i in I))
    out = dict(
        I=sorted(int(i) for i in I), B_D=sorted(int(b) for b in B_D.tolist()),
        predictive=graph_recovery_metrics(B_hat_pred, B_D, n_exterior),
    )
    if B_hat_causal is not None:
        out["causal"] = graph_recovery_metrics(B_hat_causal, B_D, n_exterior)
        out["overlap"] = overlap_categories(B_hat_pred, B_hat_causal, B_D)
    return out


def classify_outcome(excess_loss: float, jaccard: float, delta_pred: float = 0.01,
                      jaccard_high: float = 0.5) -> str:
    """Task brief section 10's four outcomes, applied per candidate:
    A: high predictive sufficiency + high structural recovery
    B: high predictive sufficiency + low structural recall (reduced predictive
       interface -- NOT a failure, means true causal parents were
       observationally redundant here)
    C: poor predictive sufficiency + high structural recovery
    D: poor both."""
    pred_sufficient = excess_loss <= delta_pred
    struct_recovered = jaccard >= jaccard_high
    if pred_sufficient and struct_recovered:
        return "A_identifiable"
    if pred_sufficient and not struct_recovered:
        return "B_reduced_interface"
    if not pred_sufficient and struct_recovered:
        return "C_estimator_inadequate"
    return "D_failed"
