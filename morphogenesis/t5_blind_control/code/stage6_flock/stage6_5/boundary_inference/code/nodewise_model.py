"""Nodewise multinomial-logistic predictive model (Part 1.3/1.4).

INFERENCE-SIDE MODULE. This file and its sibling inference-side modules
(`greedy_selection.py`, `bootstrap.py`, `graph_inference.py`, `api.py`) must
never import `flock_sim.lattice`, `flock_sim.spectral`, `common_v2`,
`common_v3`, or anything else that carries the simulator's true interaction
graph. Enforced by `tests/test_no_lattice_leakage.py` (AST-based, not a
string grep). Every function here accepts only integer heading arrays and
bird-id index sets.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression

NU = 4  # number of heading categories, read off the observed data alphabet


def _onehot(z: np.ndarray, nu: int = NU) -> np.ndarray:
    return np.eye(nu)[z]


def flatten_transitions(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """z: (n_traj, n_time, n_bird) -> (X_prev, X_next), each
    (n_traj*(n_time-1), n_bird). One row per (trajectory, timestep) sample of
    a one-step transition; trajectories are never mixed across time, so a
    trajectory-level train/val/test split (splitting the first axis) never
    leaks a transition across the split boundary."""
    prev = z[:, :-1, :]
    nxt = z[:, 1:, :]
    n_traj, n_step, n_bird = prev.shape
    return prev.reshape(n_traj * n_step, n_bird), nxt.reshape(n_traj * n_step, n_bird)


def design_matrix(prev_states: np.ndarray, cond_set: list[int], nu: int = NU) -> np.ndarray:
    """prev_states: (n_samples, n_bird) integer headings. cond_set: bird ids
    to condition on. Returns a one-hot design matrix
    (n_samples, len(cond_set) * nu). `cond_set` is supplied entirely by the
    caller (e.g. I0 ∪ a candidate exterior set) -- this function has no
    notion of "neighbor" and does not rank or filter birds by any structural
    criterion."""
    if len(cond_set) == 0:
        return np.zeros((prev_states.shape[0], 0))
    oh = _onehot(prev_states[:, cond_set], nu=nu)
    return oh.reshape(oh.shape[0], -1)


class NodewiseModel:
    """One regularized logistic-regression classifier per interior bird,
    sharing a common conditioning set (I0 ∪ cond_extra).

    Estimator choice (Part 1.4), frozen from a dev-flock timing/consistency
    check, not from held-out predictive quality: 'lbfgs' (true multinomial)
    and 'liblinear' (regularized one-vs-rest) agreed on mean held-out
    log-loss to 3 decimal places on the full-exterior model (0.0932 vs
    0.0936-0.0939 across repeated lbfgs runs), but lbfgs took 20-30s per
    20-bird fit at ~1500 training samples / 400 one-hot features -- this
    project's near-fully-aligned interior headings make several birds'
    per-class design matrix close to separable, which is the known slow
    case for lbfgs's line search. liblinear's dual coordinate-descent
    solver was ~40x faster on the identical data (0.6s) with no meaningful
    loss-value difference, so it is used everywhere by default. Both remain
    fully transparent, interpretable, L2-regularized (multi)nomial logistic
    models -- this is a solver/scaling choice, not a change of estimator
    family, and does not touch Part 1.4's "avoid starting with deep
    networks" instruction."""

    def __init__(self, I0: list[int], cond_extra: list[int], C: float = 1.0,
                 penalty: str = "l2", solver: str = "liblinear", max_iter: int = 200):
        self.I0 = sorted(int(i) for i in I0)
        self.cond_extra = sorted(int(b) for b in cond_extra)
        self.cond_set = sorted(set(self.I0) | set(self.cond_extra))
        self.C = C
        self.penalty = penalty
        self.solver = solver
        self.max_iter = max_iter
        self.models_: dict[int, object] = {}

    def fit(self, prev_states: np.ndarray, next_states: np.ndarray) -> "NodewiseModel":
        X = design_matrix(prev_states, self.cond_set)
        for i in self.I0:
            y = next_states[:, i]
            if len(np.unique(y)) < 2:
                self.models_[i] = ("constant", int(y[0]))
                continue
            clf = LogisticRegression(C=self.C, penalty=self.penalty, solver=self.solver,
                                      max_iter=self.max_iter)
            clf.fit(X, y)
            self.models_[i] = clf
        return self

    def _predict_proba_full(self, i: int, X: np.ndarray, n: int, eps: float) -> np.ndarray:
        m = self.models_[i]
        if isinstance(m, tuple) and m[0] == "constant":
            p = np.full((n, NU), eps)
            p[:, m[1]] = 1 - eps * (NU - 1)
            return p
        proba_sparse = m.predict_proba(X)
        p = np.full((n, NU), eps)
        for k, c in enumerate(m.classes_):
            p[:, c] = proba_sparse[:, k]
        return p / p.sum(axis=1, keepdims=True)

    def per_bird_logloss(self, prev_states: np.ndarray, next_states: np.ndarray,
                          eps: float = 1e-9) -> dict[int, float]:
        X = design_matrix(prev_states, self.cond_set)
        out = {}
        for i in self.I0:
            y = next_states[:, i]
            p = self._predict_proba_full(i, X, len(y), eps)
            ll = -np.log(np.clip(p[np.arange(len(y)), y], eps, 1.0))
            out[i] = float(ll.mean())
        return out

    def mean_logloss(self, prev_states: np.ndarray, next_states: np.ndarray) -> float:
        d = self.per_bird_logloss(prev_states, next_states)
        return float(np.mean(list(d.values())))
