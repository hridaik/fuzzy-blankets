"""Predictive boundary CONSTRUCTION (task brief section 13).

INFERENCE-SIDE MODULE. Certification is a separate object -- see
`challenger.py` and task brief section 14: greedy single-node gains are
allowed for construction, but they are explicitly NOT the sufficiency test.

Construction rule: starting from the empty set, greedily add the exterior bird
whose addition most reduces held-out interior log-loss, where the eligible
pool is the exterior birds with *stable positive directed predictive influence*
into the current interior (`heading_stratified.directed_influence` +
`stability.py`-style trajectory bootstrap). Stopping is by natural rule --
excess loss over the full-pool model within `delta_tol`, or best remaining
gain below `min_gain` -- with `K_max` retained only as a computational safety
cap. Where the rule terminated is recorded in the trace for every run, so a
boundary that hit the cap is visibly distinguishable from one that stopped on
its own. The boundary is never padded to `K_max`.

Candidates are NOT restricted to the true FOV shell and no fixed boundary size
is imposed.
"""
from __future__ import annotations

import numpy as np

from heading_stratified import (StratifiedPredictor, directed_influence, source_pool,
                                design, strata, _row_logloss, SHORTLIST_K, R_POOL)

DELTA_TOL = 0.01          # nats/bird-step, same constant Stage 6.5-6.7 froze
MIN_GAIN = 0.002          # nats, same
K_MAX = 12                # computational safety cap only
POOL_CAP = 20             # greedy searches only the top-POOL_CAP pool members by
                          # influence score (disclosed compute restriction)
N_BOOT = 12               # trajectory bootstrap resamples for edge stability
TAU_FREQ = 0.5            # selection frequency threshold (Stage 6.7's frozen value)
MAX_TARGETS = 24          # interior targets actually fitted (disclosed subsample)
PERIPHERY_RADIUS = 1.5    # observed-position radius defining the candidate periphery


def interior_targets(I: np.ndarray, positions: np.ndarray | None = None,
                     max_targets: int = MAX_TARGETS, seed: int = 0,
                     periphery_radius: float = PERIPHERY_RADIUS) -> np.ndarray:
    """Which interior birds are actually fitted as prediction targets.

    Disclosed compute restriction, in two parts:

    1. Only members on the candidate's OBSERVED PERIPHERY are used -- interior
       birds with at least one non-member within `periphery_radius` in observed
       position. A bird buried deep inside a large candidate cannot be
       influenced by anything outside it in one step, so including it adds
       fitting cost and dilutes the mean interior loss without contributing any
       boundary signal. This uses only positions and proposed-set membership,
       both of which the observer is allowed to see (PROTOCOL_6_8.md section 1);
       it does NOT use the FOV rule, the Moore graph, or B^D, and the radius
       (1.5) is deliberately wider than the interaction geometry.
    2. If more peripheral members remain than `max_targets`, a fixed-seed
       UNIFORM subsample of them is taken -- never a structurally biased pick.

    The boundary is still constructed for, and reported against, the FULL
    candidate interior; only the loss average runs over these targets.
    """
    I = np.asarray(sorted(int(x) for x in I))
    cand = I
    if positions is not None and len(I) > max_targets:
        others = np.setdiff1d(np.arange(positions.shape[0]), I)
        if len(others):
            d = np.sqrt(((positions[I][:, None, :] - positions[others][None, :, :]) ** 2).sum(-1))
            peripheral = I[d.min(axis=1) <= periphery_radius]
            if len(peripheral) >= min(max_targets, 4):
                cand = peripheral
    if len(cand) <= max_targets:
        return cand
    rng = np.random.default_rng(seed)
    return np.array(sorted(rng.choice(cand, size=max_targets, replace=False)))


class InteriorModel:
    """p(X_{I,t+1} | X_{I,t}, X_{B,t}) as one heading-stratified multinomial
    per interior target, conditioned on (I u B) \\ {i}.

    Disclosed compute restriction (the same one `heading_stratified.source_pool`
    already applies, extended to the interior side): when `positions` is given,
    target i conditions only on members of (I u B) within `r_pool` in OBSERVED
    position. Conditioning a peripheral bird on all ~130 members of a large
    candidate costs hundreds of one-hot features per fit and buys nothing -- a
    bird cannot be influenced in one step by a member ten lattice units away.
    `r_pool = 3.5` is ~2.5x the interaction geometry, so no live source is
    excluded by it, and it uses positions only -- never the FOV rule, the Moore
    graph or B^D.
    """

    def __init__(self, targets, I, B: list[int], positions=None,
                 r_pool: float | None = R_POOL):
        self.targets = np.asarray(targets)
        self.full_cond = sorted(set(int(x) for x in I) | set(int(x) for x in B))
        self.positions = positions
        self.r_pool = r_pool
        self.models_: dict[int, StratifiedPredictor] = {}

    def _cond_for(self, i: int) -> list[int]:
        src = [s for s in self.full_cond if s != int(i)]
        if self.positions is None or self.r_pool is None or not src:
            return sorted(src)
        d = np.sqrt(((self.positions[src] - self.positions[int(i)]) ** 2).sum(axis=1))
        return sorted(s for s, dd in zip(src, d) if dd <= self.r_pool)

    def fit(self, prev, nxt):
        for i in self.targets:
            self.models_[int(i)] = StratifiedPredictor(int(i), self._cond_for(int(i))).fit(prev, nxt)
        return self

    def fit_reusing(self, base: "InteriorModel", prev, nxt) -> "InteriorModel":
        """Fit, but copy `base`'s per-target model wherever this model's
        conditioning set for that target is IDENTICAL to base's.

        Exact, not an approximation: target i conditions on
        (I u B) intersect ball(i, r_pool), so adding a source j outside that
        ball leaves i's conditioning set -- and hence i's fitted model and every
        loss derived from it -- unchanged. Adding one candidate to a 24-target
        interior typically touches a handful of targets, so the challenger's
        scan over every residual exterior source costs several times less
        without changing a single number. Asserted in
        tests/test_challenger_reuse_is_exact.py.
        """
        for i in self.targets:
            i = int(i)
            cond = self._cond_for(i)
            b = base.models_.get(i)
            self.models_[i] = b if (b is not None and b.sources == cond) \
                else StratifiedPredictor(i, cond).fit(prev, nxt)
        return self

    def mean_logloss(self, prev, nxt) -> float:
        v = [self.models_[int(i)].pooled_logloss(prev, nxt) for i in self.targets]
        v = [x for x in v if x == x]
        return float(np.mean(v)) if v else float("nan")

    def per_row_logloss(self, prev, nxt) -> np.ndarray:
        """(n_rows,) mean over targets of the per-row negative log-likelihood,
        NaN where no target has a fitted stratum for that row. Computing this
        once and grouping afterwards avoids rebuilding one design matrix per
        (trajectory, target) in the challenger's trajectory-level bootstrap."""
        M = np.full((prev.shape[0], len(self.targets)), np.nan)
        for c, i in enumerate(self.targets):
            i = int(i)
            sp = self.models_[i]
            X = design(prev, sp.sources)
            for h, idx in strata(prev, i).items():
                if h not in sp.models_ or len(idx) == 0:
                    continue
                M[idx, c] = _row_logloss(sp.models_[h], X[idx], nxt[idx, i])
        with np.errstate(invalid="ignore"):
            return np.nanmean(M, axis=1)


def fit_eval(targets, I, B, tr_prev, tr_next, va_prev, va_next, positions=None) -> float:
    return InteriorModel(targets, I, B, positions).fit(tr_prev, tr_next) \
                                                  .mean_logloss(va_prev, va_next)


def stable_influence_pool(targets, I, positions, tr_prev, tr_next, va_prev, va_next,
                          n_boot: int = N_BOOT, tau_freq: float = TAU_FREQ,
                          shortlist_k: int = SHORTLIST_K, r_pool: float | None = R_POOL,
                          rng: np.random.Generator | None = None) -> dict:
    """Directed, heading-conditioned predictive influence of every exterior
    source j on the interior, plus trajectory-bootstrap selection frequency.

    Returns the state-conditioned directed predictive graph `Ghat^pred_t`
    (per-(target, stratum, source) Delta values) and the node-level pool of
    exterior sources with `selection_frequency >= tau_freq`. This is written to
    disk BEFORE any oracle comparison (task brief section 12).
    """
    rng = rng or np.random.default_rng(0)
    Iset = set(int(x) for x in I)
    n_tr = tr_prev.shape[0]

    def _one(prev, nxt):
        g = {}
        for i in targets:
            pool = [j for j in source_pool(positions, int(i), r_pool)]
            res = directed_influence(int(i), pool, prev, nxt, va_prev, va_next,
                                     shortlist_k=shortlist_k)
            g[int(i)] = res
        return g

    base = _one(tr_prev, tr_next)

    # node-level score: total positive influence into the interior, summed over
    # targets and strata, weighted by how often that stratum actually occurs
    score, per_edge = {}, {}
    for i, res in base.items():
        strat_w = {}
        for h in res["fitted_strata"]:
            strat_w[h] = float(np.mean(va_prev[:, i] == h))
        tot_w = sum(strat_w.values()) or 1.0
        for h, dd in res["delta"].items():
            for j, d in dd.items():
                if j in Iset or d <= 0:
                    continue
                w = strat_w.get(h, 0.0) / tot_w
                score[j] = score.get(j, 0.0) + w * d
                per_edge.setdefault((i, h), {})[j] = d

    sel_count = {j: 0 for j in score}
    for _ in range(n_boot):
        idx = rng.integers(0, n_tr, n_tr)
        g = _one(tr_prev[idx], tr_next[idx])
        picked = set()
        for i, res in g.items():
            for h, dd in res["delta"].items():
                for j, d in dd.items():
                    if j not in Iset and d > 0:
                        picked.add(j)
        for j in sel_count:
            if j in picked:
                sel_count[j] += 1

    freq = {j: sel_count[j] / max(1, n_boot) for j in score}
    pool = sorted([j for j in score if freq[j] >= tau_freq], key=lambda j: -score[j])
    return dict(score=score, selection_frequency=freq, pool=pool,
                directed_graph={f"{i}|{h}": v for (i, h), v in per_edge.items()})


def construct(targets, I, pool, tr_prev, tr_next, va_prev, va_next,
              full_pool_loss: float, delta_tol: float = DELTA_TOL,
              min_gain: float = MIN_GAIN, k_max: int = K_MAX, positions=None):
    """Greedy forward construction of `Bhat^pred`. Same stopping logic as
    Stage 6.5's frozen `greedy_forward_select`, restated here because that
    module's model class is not heading-stratified."""
    remaining = list(pool)
    B: list[int] = []
    cur = fit_eval(targets, I, B, tr_prev, tr_next, va_prev, va_next, positions)
    trace = [dict(step=0, added=None, B=[], loss=cur, excess_over_full=cur - full_pool_loss)]
    stop = "exhausted_pool"
    while remaining:
        if cur - full_pool_loss <= delta_tol:
            stop = "delta_tol_reached"
            break
        if len(B) >= k_max:
            stop = "k_max_cap"
            break
        best_j, best_loss, best_gain = None, None, -np.inf
        for j in remaining:
            lj = fit_eval(targets, I, B + [j], tr_prev, tr_next, va_prev, va_next, positions)
            if cur - lj > best_gain:
                best_j, best_loss, best_gain = j, lj, cur - lj
        if best_gain <= min_gain:
            stop = "no_candidate_above_min_gain"
            break
        B.append(int(best_j)); remaining.remove(best_j); cur = best_loss
        trace.append(dict(step=len(B), added=int(best_j), B=list(B), loss=cur,
                          gain=float(best_gain), excess_over_full=cur - full_pool_loss))
    trace[-1]["stop_reason"] = stop
    return sorted(B), trace, stop
