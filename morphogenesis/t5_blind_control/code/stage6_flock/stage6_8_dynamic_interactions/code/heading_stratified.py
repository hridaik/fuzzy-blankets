"""Heading-stratified predictive models and directed predictive influence
(task brief sections 11-12).

INFERENCE-SIDE MODULE. Sees headings, positions and its own interventions.
Never sees the FOV rule, the effective edges, the gates, or B^D.

Why stratification is necessary here and was not in Stage 6.5-6.7
-----------------------------------------------------------------
Under the FOV rule the set of sources that can influence bird i depends on
i's OWN current heading. A single additive multinomial model pooled over all
of i's headings averages four different conditioning structures together and
washes the dependence out. Stage 6.8 therefore fits, for every target i and
every current heading h,

    P( Z_{i,t+1} | Z_{i,t} = h, Z_{-i,t} )

i.e. the transition data is split into four current-heading strata for i and a
separate regularized multinomial model is fit within each. A source's
predictive relevance is then explicitly conditional on the receiver's
orientation -- which is the structure the FOV model creates.

Estimator: `sklearn.linear_model.LogisticRegression` with the SAME frozen
hyperparameters Stage 6.5-6.7 used (`solver=liblinear, penalty=l2, C=1.0,
max_iter=200`, `stage6_5/boundary_inference/code/nodewise_model.py`), so the
estimator family is unchanged and only the conditioning changes.

Disclosed approximation: source pool
------------------------------------
`source_pool` restricts the candidate sources for target i to birds within
`R_POOL` of i in OBSERVED position. This is a compute-feasibility restriction
of exactly the kind Stage 6.7 disclosed for its `shortlist_k=25` coefficient
shortlist, stated rather than silently applied. It is deliberately much wider
than the interaction range (R_POOL=4.0 admits ~48 birds where the true Moore
neighbourhood has 8 and the live FOV in-set has ~5), so the inference problem
-- which directed subset is live at time t -- is untouched by it. Set
`R_POOL=None` for the full-population pool.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression

NU = 4
C_REG = 1.0
PENALTY = "l2"
SOLVER = "liblinear"
MAX_ITER = 200
R_POOL = 4.0              # observed-position radius for the source pool
SHORTLIST_K = 20          # regularized-coefficient shortlist size
MIN_STRATUM_SAMPLES = 40  # a heading stratum with fewer samples is not fitted


def onehot(z: np.ndarray, nu: int = NU) -> np.ndarray:
    return np.eye(nu)[z]


def design(prev: np.ndarray, sources: list[int], nu: int = NU) -> np.ndarray:
    if len(sources) == 0:
        return np.zeros((prev.shape[0], 0))
    oh = onehot(prev[:, sources], nu=nu)
    return oh.reshape(oh.shape[0], -1)


def source_pool(positions: np.ndarray, i: int, r_pool: float | None = R_POOL) -> list[int]:
    n = positions.shape[0]
    if r_pool is None:
        return [j for j in range(n) if j != i]
    d = np.sqrt(((positions - positions[i]) ** 2).sum(axis=1))
    return [int(j) for j in np.where((d <= r_pool) & (np.arange(n) != i))[0]]


def _fit(X, y):
    if len(np.unique(y)) < 2:
        return ("constant", int(y[0]))
    clf = LogisticRegression(C=C_REG, penalty=PENALTY, solver=SOLVER, max_iter=MAX_ITER)
    clf.fit(X, y)
    return clf


def _row_logloss(model, X, y, eps: float = 1e-9) -> np.ndarray:
    """Per-row negative log-likelihood."""
    n = len(y)
    if isinstance(model, tuple) and model[0] == "constant":
        p = np.full((n, NU), eps)
        p[:, model[1]] = 1 - eps * (NU - 1)
    else:
        ps = model.predict_proba(X)
        p = np.full((n, NU), eps)
        for k, c in enumerate(model.classes_):
            p[:, c] = ps[:, k]
        p = p / p.sum(axis=1, keepdims=True)
    return -np.log(np.clip(p[np.arange(n), y], eps, 1.0))


def _logloss(model, X, y, eps: float = 1e-9) -> float:
    return float(_row_logloss(model, X, y, eps).mean())


def strata(prev: np.ndarray, i: int, nu: int = NU) -> dict:
    """Row indices of each current-heading stratum for target i."""
    return {h: np.where(prev[:, i] == h)[0] for h in range(nu)}


class StratifiedPredictor:
    """One multinomial model per (target, current-heading) stratum, sharing a
    conditioning set of sources."""

    def __init__(self, target: int, sources: list[int]):
        self.target = int(target)
        self.sources = sorted(int(s) for s in sources)
        self.models_: dict[int, object] = {}

    def fit(self, prev: np.ndarray, nxt: np.ndarray) -> "StratifiedPredictor":
        X = design(prev, self.sources)
        for h, idx in strata(prev, self.target).items():
            if len(idx) < MIN_STRATUM_SAMPLES:
                continue
            self.models_[h] = _fit(X[idx], nxt[idx, self.target])
        return self

    def per_stratum_logloss(self, prev: np.ndarray, nxt: np.ndarray) -> dict[int, float]:
        X = design(prev, self.sources)
        out = {}
        for h, idx in strata(prev, self.target).items():
            if h not in self.models_ or len(idx) == 0:
                continue
            out[h] = _logloss(self.models_[h], X[idx], nxt[idx, self.target])
        return out

    def pooled_logloss(self, prev: np.ndarray, nxt: np.ndarray) -> float:
        """Sample-weighted mean over strata (so it is comparable across models
        with different fitted-stratum sets only when those sets match; callers
        always compare within one target)."""
        X = design(prev, self.sources)
        tot, n_tot = 0.0, 0
        for h, idx in strata(prev, self.target).items():
            if h not in self.models_ or len(idx) == 0:
                continue
            tot += _logloss(self.models_[h], X[idx], nxt[idx, self.target]) * len(idx)
            n_tot += len(idx)
        return tot / n_tot if n_tot else float("nan")


def coefficient_shortlist(pred: StratifiedPredictor, h: int, k: int = SHORTLIST_K) -> list[int]:
    """Rank sources by total |coefficient| mass on their nu-column block in the
    stratum-h model. Same ranking rule Stage 6.7 used, applied within a
    stratum."""
    m = pred.models_.get(h)
    if m is None or isinstance(m, tuple):
        return []
    coef = np.abs(m.coef_).sum(axis=0)                     # (len(sources)*NU,)
    mass = coef.reshape(len(pred.sources), NU).sum(axis=1)
    order = np.argsort(-mass)
    return [pred.sources[int(o)] for o in order[:k]]


def directed_influence(target: int, sources: list[int],
                       tr_prev, tr_next, va_prev, va_next,
                       shortlist_k: int = SHORTLIST_K) -> dict:
    """Delta^{(h)}_{i<-j} = ell_i^{(-j,h)} - ell_i^{(full,h)}, held out on the
    validation split. Non-shortlisted sources get Delta = 0 exactly (a
    disclosed approximation, as in Stage 6.7, not a silent omission)."""
    full = StratifiedPredictor(target, sources).fit(tr_prev, tr_next)
    full_ll = full.per_stratum_logloss(va_prev, va_next)
    out = {h: {} for h in full_ll}
    for h in full_ll:
        for j in coefficient_shortlist(full, h, shortlist_k):
            reduced = [s for s in sources if s != j]
            m = StratifiedPredictor(target, reduced).fit(tr_prev, tr_next)
            ll = m.per_stratum_logloss(va_prev, va_next).get(h)
            if ll is None:
                continue
            out[h][j] = float(ll - full_ll[h])
    return dict(full_logloss=full_ll, delta=out,
                fitted_strata=sorted(full_ll.keys()))
