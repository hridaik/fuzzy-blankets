"""Blind predictive-sufficiency CERTIFICATION (task brief sections 14-15).

INFERENCE-SIDE MODULE.

Why this exists
---------------
Stage 6.7 stopped greedy selection when no single remaining source helped, and
treated that as evidence of sufficiency. It is not: a set of residual sources
can be jointly informative about the interior's next state even when every one
of them is individually useless. Stage 6.8 therefore separates

    boundary CONSTRUCTION   (predictive_boundary_68.construct, greedy, single-node)
    boundary CERTIFICATION  (this module, joint, adversarial)

For a proposed B, a base predictor M_B is fit, then INDEPENDENT residual
challengers are fit from the remaining exterior E = everything outside I u B:

    C1  best remaining single source
    C2  best pair from a small residual shortlist
    C3  a strongly L1-regularized sparse multivariate multinomial challenger
        using ALL residual exterior sources at once

Every challenger is *selected* on training/validation trajectories. The test
split is touched exactly ONCE, at the end, to evaluate the already-chosen
challengers:

    Lhat_challenge(B) = ell_test(M_B) - min_c ell_test(M_{B+c})

bootstrapped across test TRAJECTORIES (not rows -- resampling rows would break
the within-trajectory dependence and understate the interval). B is called

    "predictively sufficient relative to the challenger class"

iff the (1-alpha) bootstrap UPPER bound U_{1-alpha}(Lhat_challenge) <= delta.

This is NOT a test of exact conditional independence and is never described as
one. The wording above is the wording used in RESULTS_6_8.md and in every
figure caption.
"""
from __future__ import annotations

import itertools

import numpy as np
from sklearn.linear_model import LogisticRegression

from heading_stratified import StratifiedPredictor, design, strata, _logloss, _row_logloss, NU
from predictive_boundary_68 import InteriorModel

DELTA_SUFFICIENT = 0.01     # nats/bird-step, same constant as construction
ALPHA = 0.05                # one-sided 95% upper bound
N_BOOT_TEST = 500
PAIR_SHORTLIST = 8          # residual shortlist size for the C2 pair search
C_SPARSE = 0.05             # strong L1 regularization for the C3 challenger


class SparseChallenger:
    """C3: one strongly L1-regularized multinomial per (target, stratum) using
    ALL residual exterior sources simultaneously, on top of the base
    conditioning set."""

    def __init__(self, targets, cond: list[int], residual: list[int], C: float = C_SPARSE,
                 positions=None, r_pool: float | None = 3.5):
        self.targets = np.asarray(targets)
        self.cond = sorted(set(int(x) for x in cond))
        self.residual = sorted(set(int(x) for x in residual))
        self.C = C
        self.positions = positions
        self.r_pool = r_pool
        self.models_: dict = {}

    def _restrict(self, i: int, src: list[int]) -> list[int]:
        """Same disclosed spatial restriction as `InteriorModel`, applied to the
        BASE conditioning set only -- the residual exterior sources this
        challenger is testing are never restricted, so the challenge remains a
        challenge over all of them."""
        if self.positions is None or self.r_pool is None or not src:
            return src
        d = np.sqrt(((self.positions[src] - self.positions[int(i)]) ** 2).sum(axis=1))
        return [s for s, dd in zip(src, d) if dd <= self.r_pool]

    def fit(self, prev, nxt):
        for i in self.targets:
            i = int(i)
            src = self._restrict(i, [s for s in self.cond if s != i]) + \
                  [s for s in self.residual if s != i]
            self.models_[i] = (src, {})
            X = design(prev, src)
            for h, idx in strata(prev, i).items():
                if len(idx) < 40:
                    continue
                y = nxt[idx, i]
                if len(np.unique(y)) < 2:
                    self.models_[i][1][h] = ("constant", int(y[0]))
                    continue
                clf = LogisticRegression(C=self.C, penalty="l1", solver="liblinear",
                                         max_iter=200)
                clf.fit(X[idx], y)
                self.models_[i][1][h] = clf
        return self

    def mean_logloss(self, prev, nxt) -> float:
        with np.errstate(invalid="ignore"):
            v = np.nanmean(self.per_row_logloss(prev, nxt))
        return float(v)

    def per_row_logloss(self, prev, nxt) -> np.ndarray:
        M = np.full((prev.shape[0], len(self.targets)), np.nan)
        for c, i in enumerate(self.targets):
            i = int(i)
            src, ms = self.models_[i]
            X = design(prev, src)
            for h, idx in strata(prev, i).items():
                if h not in ms or len(idx) == 0:
                    continue
                M[idx, c] = _row_logloss(ms[h], X[idx], nxt[idx, i])
        with np.errstate(invalid="ignore"):
            return np.nanmean(M, axis=1)


def _per_traj_logloss(model, prev, nxt, traj_id) -> dict:
    """Mean interior log-loss per test trajectory, for the trajectory-level
    bootstrap. The per-row losses are computed ONCE for the whole test split
    and then grouped, rather than refitting a design matrix per trajectory."""
    rows = model.per_row_logloss(prev, nxt)
    out = {}
    for tid in np.unique(traj_id):
        m = traj_id == tid
        with np.errstate(invalid="ignore"):
            out[int(tid)] = float(np.nanmean(rows[m]))
    return out


def certify(targets, I, B, exterior, tr_prev, tr_next, va_prev, va_next,
            te_prev, te_next, te_traj, delta: float = DELTA_SUFFICIENT,
            alpha: float = ALPHA, n_boot: int = N_BOOT_TEST,
            pair_shortlist: int = PAIR_SHORTLIST, rng=None, positions=None) -> dict:
    """Blind predictive-sufficiency challenge of a proposed boundary `B`."""
    rng = rng or np.random.default_rng(0)
    I = sorted(int(x) for x in I)
    B = sorted(int(x) for x in B)
    base_set = set(I) | set(B)
    E = sorted(int(j) for j in exterior if int(j) not in base_set)

    base = InteriorModel(targets, I, B, positions).fit(tr_prev, tr_next)

    # ---- challenger SELECTION: train/val only, test never touched -----------
    singles = {}
    for j in E:
        singles[j] = InteriorModel(targets, I, B + [j], positions) \
            .fit_reusing(base, tr_prev, tr_next).mean_logloss(va_prev, va_next)
    ranked = sorted(singles, key=lambda j: singles[j])
    c1 = [ranked[0]] if ranked else []

    c2, best_pair_loss = [], np.inf
    for a, b in itertools.combinations(ranked[:pair_shortlist], 2):
        l = InteriorModel(targets, I, B + [a, b], positions) \
            .fit_reusing(base, tr_prev, tr_next).mean_logloss(va_prev, va_next)
        if l < best_pair_loss:
            best_pair_loss, c2 = l, [a, b]

    challengers = {}
    if c1:
        challengers["C1_best_single"] = InteriorModel(targets, I, B + c1, positions).fit_reusing(base, tr_prev, tr_next)
    if c2:
        challengers["C2_best_pair"] = InteriorModel(targets, I, B + c2, positions).fit_reusing(base, tr_prev, tr_next)
    if E:
        challengers["C3_sparse_all_residual"] = SparseChallenger(targets, I + B, E, positions=positions).fit(tr_prev, tr_next)

    # ---- EVALUATION: the test split is touched exactly once ----------------
    base_per = _per_traj_logloss(base, te_prev, te_next, te_traj)
    chal_per = {k: _per_traj_logloss(m, te_prev, te_next, te_traj) for k, m in challengers.items()}
    tids = sorted(base_per)

    base_test = float(np.mean([base_per[t] for t in tids]))
    chal_test = {k: float(np.mean([v[t] for t in tids])) for k, v in chal_per.items()}
    L_point = base_test - min(chal_test.values()) if chal_test else 0.0

    boots = []
    for _ in range(n_boot):
        pick = rng.choice(tids, size=len(tids), replace=True)
        b = np.mean([base_per[t] for t in pick])
        c = min(np.mean([v[t] for t in pick]) for v in chal_per.values()) if chal_per else b
        boots.append(b - c)
    boots = np.asarray(boots)
    upper = float(np.quantile(boots, 1 - alpha))

    return dict(
        B=B, n_residual_exterior=len(E),
        base_test_logloss=base_test, challenger_test_logloss=chal_test,
        challenger_sets=dict(C1_best_single=c1, C2_best_pair=c2,
                             C3_sparse_all_residual=E),
        L_challenge_point=float(L_point),
        L_challenge_upper=upper, alpha=alpha, delta=delta,
        predictively_sufficient_rel_challenger_class=bool(upper <= delta),
        wording="predictively sufficient relative to the challenger class "
                "(NOT exact conditional independence)",
        n_boot=n_boot, n_test_trajectories=len(tids),
    )
