"""EVALUATION-SIDE. Reveals B^D / B^F only AFTER \\hat B has been frozen by
the inference-side pipeline, and compares them: graph-recovery metrics
(precision/recall/F1/Jaccard/size/FP/FN/exact-match) plus the more important
predictive comparison Delta-ell(B_hat) vs Delta-ell(B^D) vs Delta-ell(B^F) vs
random-matched vs full-exterior (Part 1.8-1.10). Allowed to import the
lattice/spectral machinery because this module's entire purpose is
ground-truth comparison, never boundary discovery.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))

from flock_sim.spectral import analyze_window  # noqa: E402
from common_v2 import dynamical_shell  # noqa: E402

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))
from nodewise_model import flatten_transitions  # noqa: E402
from greedy_selection import fit_eval  # noqa: E402


def graph_recovery_metrics(B_hat: set[int], B_true: set[int], n_exterior: int) -> dict:
    B_hat, B_true = set(int(b) for b in B_hat), set(int(b) for b in B_true)
    tp = len(B_hat & B_true)
    fp = len(B_hat - B_true)
    fn = len(B_true - B_hat)
    tn = n_exterior - tp - fp - fn
    precision = tp / len(B_hat) if B_hat else float("nan")
    recall = tp / len(B_true) if B_true else float("nan")
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else float("nan")
    jaccard = tp / len(B_hat | B_true) if (B_hat | B_true) else 1.0
    return dict(
        tp=tp, fp=fp, fn=fn, tn=tn, precision=precision, recall=recall, f1=f1, jaccard=jaccard,
        size_hat=len(B_hat), size_true=len(B_true), exact_match=bool(B_hat == B_true),
        false_positive_ids=sorted(B_hat - B_true), false_negative_ids=sorted(B_true - B_hat),
    )


def fiedler_boundary_from_trajectories(z_window: np.ndarray, I0: np.ndarray) -> np.ndarray:
    """B^F computed purely from observed headings (no lattice) -- the Stage-6
    spectral null. z_window: (TW, n_bird) heading snapshot, TW matching
    common_v2.TW. Returns exterior members of the spectral boundary."""
    sr = analyze_window(z_window, refclust=I0)
    I0_set = set(I0.tolist())
    boundary = [int(b) for b in sr.boundary_nodes.tolist() if b not in I0_set]
    return np.array(sorted(boundary), dtype=int)


def excess_loss(I0, B, train_prev, train_next, val_prev, val_next, full_loss: float, **kw) -> float:
    return fit_eval(I0, sorted(int(b) for b in B), train_prev, train_next, val_prev, val_next, **kw) - full_loss


def random_matched_baseline(candidates: list[int], size: int, n_draws: int, rng: np.random.Generator,
                             I0, train_prev, train_next, val_prev, val_next, full_loss: float, **kw):
    losses = []
    sets = []
    for _ in range(n_draws):
        draw = rng.choice(candidates, size=min(size, len(candidates)), replace=False)
        sets.append(sorted(int(d) for d in draw))
        losses.append(excess_loss(I0, draw, train_prev, train_next, val_prev, val_next, full_loss, **kw))
    return dict(mean_excess_loss=float(np.mean(losses)), std_excess_loss=float(np.std(losses)),
                draws=sets, excess_losses=losses)


def compare_boundaries(I0, B_hat, B_D, B_F, candidates, z_train, z_val, full_loss: float,
                        rng: np.random.Generator, n_random_draws: int = 20, **model_kwargs) -> dict:
    """The Part 1.8 comparison table: graph recovery of B_hat vs B^D, and the
    predictive Delta-ell of B_hat, B^D, B^F, a size-matched random baseline,
    and the full exterior set (all on the same held-out val split)."""
    train_prev, train_next = flatten_transitions(z_train)
    val_prev, val_next = flatten_transitions(z_val)

    recovery = graph_recovery_metrics(set(B_hat), set(B_D.tolist()), n_exterior=len(candidates))

    dl_hat = excess_loss(I0, B_hat, train_prev, train_next, val_prev, val_next, full_loss, **model_kwargs)
    dl_D = excess_loss(I0, B_D, train_prev, train_next, val_prev, val_next, full_loss, **model_kwargs)
    dl_F = excess_loss(I0, B_F, train_prev, train_next, val_prev, val_next, full_loss, **model_kwargs)
    dl_full = 0.0  # by definition, full exterior IS the reference for excess loss

    random_result = random_matched_baseline(candidates, size=max(len(B_hat), 1), n_draws=n_random_draws,
                                             rng=rng, I0=I0, train_prev=train_prev, train_next=train_next,
                                             val_prev=val_prev, val_next=val_next, full_loss=full_loss,
                                             **model_kwargs)

    return dict(
        recovery_vs_BD=recovery,
        excess_loss=dict(B_hat=dl_hat, B_D=dl_D, B_F=dl_F, full_exterior=dl_full,
                          random_matched_mean=random_result["mean_excess_loss"],
                          random_matched_std=random_result["std_excess_loss"]),
        random_matched_detail=random_result,
        B_hat=sorted(int(b) for b in B_hat), B_D=sorted(int(b) for b in B_D.tolist()),
        B_F=sorted(int(b) for b in B_F.tolist()),
    )
