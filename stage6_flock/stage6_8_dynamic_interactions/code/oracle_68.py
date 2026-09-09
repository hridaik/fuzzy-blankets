"""ORACLE / VALIDATION-ONLY module (task brief sections 4, 17, 18).

EVALUATION-SIDE. This is the ONLY module in Stage 6.8 permitted to compute the
true FOV interaction graph and the true dynamic causal interface

    B_t^D = { j not in I_t : j -> i for some i in I_t }

It is imported by validation and figure scripts only, strictly AFTER every
inference decision has been written to disk, and is never used to retune an
estimator, a threshold, a shortlist size or a stopping rule. No inference-side
module may import it (enforced by tests/test_no_topology_leakage_68.py).
"""
from __future__ import annotations

import numpy as np

from common_68 import jaccard


def oracle_B_D(sim, active_mask: np.ndarray, I) -> np.ndarray:
    return sim.oracle_B_D(active_mask, np.asarray(sorted(int(x) for x in I)))


def interface_series(sim, active_mask_hist: np.ndarray, I_series: dict) -> dict:
    """|B_t^D|, symmetric difference |B_{t+1}^D triangle B_t^D|, and interface
    turnover/lifetime, for a time-indexed dict {t: I_t}."""
    ts = sorted(I_series)
    B = {t: set(int(x) for x in oracle_B_D(sim, active_mask_hist[t], I_series[t])) for t in ts}
    sizes = {t: len(B[t]) for t in ts}
    symdiff, turnover, retention = {}, {}, {}
    for a, b in zip(ts[:-1], ts[1:]):
        if b != a + 1:
            continue
        symdiff[b] = len(B[b] ^ B[a])
        turnover[b] = len(B[b] - B[a]) / max(1, len(B[b]))
        retention[b] = len(B[b] & B[a]) / max(1, len(B[a]))
    # per-node interface lifetime: longest consecutive run of membership
    lifetimes = []
    allnodes = set().union(*B.values()) if B else set()
    for j in allnodes:
        run = 0
        for t in ts:
            if j in B[t]:
                run += 1
            else:
                if run:
                    lifetimes.append(run)
                run = 0
        if run:
            lifetimes.append(run)
    return dict(
        t=ts, B={t: sorted(B[t]) for t in ts}, size=sizes, symdiff=symdiff,
        turnover=turnover, retention=retention,
        mean_size=float(np.mean(list(sizes.values()))) if sizes else float("nan"),
        mean_symdiff=float(np.mean(list(symdiff.values()))) if symdiff else float("nan"),
        mean_turnover=float(np.mean(list(turnover.values()))) if turnover else float("nan"),
        mean_node_lifetime=float(np.mean(lifetimes)) if lifetimes else float("nan"),
    )


def edge_turnover(active_mask_hist: np.ndarray) -> dict:
    """Global FOV edge churn: fraction of directed Moore edges whose live/dead
    status flips between consecutive steps."""
    A = active_mask_hist
    flips = (A[1:] != A[:-1]).mean(axis=1)
    return dict(mean_edge_flip_fraction=float(flips.mean()),
                sd_edge_flip_fraction=float(flips.std()),
                mean_live_fraction=float(A.mean()),
                per_step=flips.tolist())


def compare_sets(B_hat, B_true) -> dict:
    """Precision / recall / Jaccard / size error of an inferred interface."""
    a = set(int(x) for x in B_hat)
    b = set(int(x) for x in B_true)
    tp = len(a & b)
    prec = tp / len(a) if a else (1.0 if not b else 0.0)
    rec = tp / len(b) if b else (1.0 if not a else 0.0)
    return dict(precision=float(prec), recall=float(rec), jaccard=jaccard(a, b),
                size_hat=len(a), size_true=len(b), size_error=len(a) - len(b),
                n_true_positive=tp)


def turnover_similarity(B_t, B_prev, BD_t, BD_prev) -> float:
    """T_B(t) = J( B_t triangle B_{t-1},  B_t^D triangle B_{t-1}^D )
    (task brief section 18). Answers: does the INFERRED interface change when
    the TRUE interface changes?"""
    a = set(int(x) for x in B_t) ^ set(int(x) for x in B_prev)
    b = set(int(x) for x in BD_t) ^ set(int(x) for x in BD_prev)
    return jaccard(a, b)


def temporal_lag(B_series: dict, BD_series: dict, max_lag: int = 4) -> dict:
    """Lag (in steps) at which the inferred interface best matches the true
    one. Positive lag = the inferred interface trails the truth."""
    ts = sorted(set(B_series) & set(BD_series))
    best, curve = 0, {}
    for lag in range(0, max_lag + 1):
        vals = [jaccard(B_series[t], BD_series[t - lag])
                for t in ts if (t - lag) in BD_series]
        curve[lag] = float(np.mean(vals)) if vals else float("nan")
    finite = {k: v for k, v in curve.items() if v == v}
    best = max(finite, key=finite.get) if finite else 0
    return dict(curve=curve, best_lag=int(best),
                jaccard_at_best=float(finite[best]) if finite else float("nan"),
                jaccard_at_zero=float(curve.get(0, float("nan"))))
