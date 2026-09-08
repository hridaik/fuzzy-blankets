"""Metric 2 (internal predictive integration G_I) and Metric 3 (budgeted
predictive blanket leakage L_I), and the mask-cache that makes evaluating
thousands of candidates cheap (task brief section 5).

Reuses stage6_5's frozen NodewiseModel/design_matrix verbatim (same
hyperparameters: C=1.0, penalty=l2, solver=liblinear, max_iter=200). The only
new idea here is which conditioning set gets fed to it: for a given bird i,
subset_loss[i, mask] is the held-out log-loss of a NodewiseModel with
I0=[i], cond_extra=mask (mask subseteq neighbours(i)), which by construction
always includes bird i's own current state as a conditioning feature (I0=[i]
puts i itself in cond_set, task brief section 5's "the bird's own current
state always included").

Cache key is (bird, frozenset(mask)); cost is bounded by
sum_i 2^deg(i) over touched birds regardless of how many candidates are
evaluated, since the cache saturates (see PLAN.md "Scope-narrowing
decisions", item 1).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from common_66 import Lattice, NodewiseModel

MACHINE_EPS_TOL = 1e-9


def clamp_machine_eps(x: float, tol: float = MACHINE_EPS_TOL) -> float:
    """Only zero out negatives that are numerically indistinguishable from 0
    (floating-point residue from two nearly-identical held-out log-losses).
    Genuine finite-sample negative estimates (e.g. a "helpful" boundary
    subset that, by sampling noise, outperforms the full-neighbour model on
    the held-out fold) are preserved as-is and must be reported, not hidden
    (task brief section 5, final paragraph)."""
    return 0.0 if (x < 0 and abs(x) < tol) else float(x)


@dataclass
class PredictiveCache:
    lattice: Lattice
    train_prev: np.ndarray   # (n_train, n_bird)
    train_next: np.ndarray
    val_prev: np.ndarray     # (n_val, n_bird)
    val_next: np.ndarray
    C: float = 1.0
    penalty: str = "l2"
    solver: str = "liblinear"
    max_iter: int = 200
    _cache: dict = field(default_factory=dict)
    _neighbor_sets: dict = field(default_factory=dict)
    n_fits: int = 0
    n_hits: int = 0

    def neighbor_set(self, i: int) -> frozenset:
        if i not in self._neighbor_sets:
            self._neighbor_sets[i] = frozenset(int(j) for j in self.lattice.neighbor_ids[i])
        return self._neighbor_sets[i]

    def mask_B(self, i: int, B) -> frozenset:
        return self.neighbor_set(i) & frozenset(int(b) for b in B)

    def mask_IB(self, i: int, I, B) -> frozenset:
        return self.neighbor_set(i) & (frozenset(int(x) for x in I) | frozenset(int(b) for b in B))

    def mask_full(self, i: int) -> frozenset:
        return self.neighbor_set(i)

    def get_loss(self, i: int, mask: frozenset) -> float:
        key = (int(i), mask)
        if key in self._cache:
            self.n_hits += 1
            return self._cache[key]
        model = NodewiseModel(I0=[int(i)], cond_extra=sorted(mask),
                               C=self.C, penalty=self.penalty, solver=self.solver,
                               max_iter=self.max_iter)
        model.fit(self.train_prev, self.train_next)
        loss = model.mean_logloss(self.val_prev, self.val_next)
        self._cache[key] = loss
        self.n_fits += 1
        return loss

    def stats(self) -> dict:
        return dict(n_fits=self.n_fits, n_hits=self.n_hits, n_cached=len(self._cache))


def per_bird_G_L(cache: PredictiveCache, i: int, I, B) -> tuple[float, float]:
    """G_i = ell_i(mask_B) - ell_i(mask_IB); L_i = ell_i(mask_IB) - ell_i(mask_full).
    Raw (unclamped except machine-eps) per task brief section 5."""
    ell_B = cache.get_loss(i, cache.mask_B(i, B))
    ell_IB = cache.get_loss(i, cache.mask_IB(i, I, B))
    ell_full = cache.get_loss(i, cache.mask_full(i))
    G_i = clamp_machine_eps(ell_B - ell_IB)
    L_i = clamp_machine_eps(ell_IB - ell_full)
    return G_i, L_i


def G_and_L(cache: PredictiveCache, I, B) -> dict:
    """G_I, L_I averaged over I, plus the raw per-bird breakdown (never
    discarded -- needed to detect and report finite-sample issues, task
    brief section 5)."""
    I = list(I)
    per_bird = {}
    for i in I:
        G_i, L_i = per_bird_G_L(cache, i, I, B)
        per_bird[int(i)] = dict(G_i=G_i, L_i=L_i)
    G_I = float(np.mean([v["G_i"] for v in per_bird.values()]))
    L_I = float(np.mean([v["L_i"] for v in per_bird.values()]))
    n_negative_G = sum(1 for v in per_bird.values() if v["G_i"] < 0)
    n_negative_L = sum(1 for v in per_bird.values() if v["L_i"] < 0)
    return dict(G_I=G_I, L_I=L_I, per_bird=per_bird,
                n_negative_G_i=n_negative_G, n_negative_L_i=n_negative_L)
