"""INFERENCE-SIDE MODULE. Generalization of `stage6_6_collective_landscape/
code/predictive_cache.py`'s `get_loss(i, mask)` WITHOUT the
`lattice.neighbor_ids` intersection that `predictive_cache.py`'s `mask_B`/
`mask_IB` helpers perform. Stage 6.6's cache is deliberately oracle-aware
(every mask it ever builds is a subset of bird i's TRUE lattice neighbours,
task brief section 10's explicit simplification) -- reusing it here would
silently drop any false-positive (non-neighbour) member of an inferred
boundary before scoring it, which is exactly the phenomenon Stage 6.7 needs
to be able to observe and report (task brief section 10, "B a proxy... acts
as an observational proxy").

This file and its sibling inference-side modules (`directed_graph_inference.py`,
`graph_bootstrap.py`, `predictive_boundary.py`, `causal_discovery.py`) must
never import `flock_sim.lattice`, `flock_sim.spectral`, `common_v2`,
`common_66`, `common_67`, `dynamical_shell`, or anything else that carries
the simulator's true interaction graph. Enforced by
tests/test_no_topology_leakage.py (AST-based, not a string grep). Every
function here accepts only integer heading arrays and bird-id index sets.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nodewise_model import NodewiseModel

MACHINE_EPS_TOL = 1e-9


def clamp_machine_eps(x: float, tol: float = MACHINE_EPS_TOL) -> float:
    """Only zero out negatives that are numerically indistinguishable from 0.
    Genuine finite-sample negative estimates are preserved, not hidden
    (mirrors stage6_6/code/predictive_cache.py's identical convention)."""
    return 0.0 if (x < 0 and abs(x) < tol) else float(x)


@dataclass
class BlindCache:
    """Caches held-out log-loss for a bird `i` under an ARBITRARY conditioning
    mask (no restriction to true neighbours). Key is (bird, frozenset(mask))."""
    train_prev: np.ndarray
    train_next: np.ndarray
    val_prev: np.ndarray
    val_next: np.ndarray
    C: float = 1.0
    penalty: str = "l2"
    solver: str = "liblinear"
    max_iter: int = 200
    _cache: dict = field(default_factory=dict)
    _models: dict = field(default_factory=dict)
    n_fits: int = 0
    n_hits: int = 0

    def get_loss(self, i: int, mask) -> float:
        key = (int(i), frozenset(int(m) for m in mask))
        if key in self._cache:
            self.n_hits += 1
            return self._cache[key]
        model = NodewiseModel(I0=[int(i)], cond_extra=sorted(key[1]),
                               C=self.C, penalty=self.penalty, solver=self.solver,
                               max_iter=self.max_iter)
        model.fit(self.train_prev, self.train_next)
        loss = model.mean_logloss(self.val_prev, self.val_next)
        self._cache[key] = loss
        self._models[key] = model
        self.n_fits += 1
        return loss

    def get_model(self, i: int, mask) -> NodewiseModel:
        """Fits (or returns the cached fit) and hands back the underlying
        NodewiseModel -- used by directed_graph_inference.py to read off fitted
        coefficients for the shortlist step, without re-fitting."""
        self.get_loss(i, mask)
        return self._models[(int(i), frozenset(int(m) for m in mask))]

    def stats(self) -> dict:
        return dict(n_fits=self.n_fits, n_hits=self.n_hits, n_cached=len(self._cache))
