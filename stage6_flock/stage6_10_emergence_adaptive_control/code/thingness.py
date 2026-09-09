"""Stage 6.10 Part E -- the thingness profile (C, G, L, D).

Computed for detected candidate lineages from OBSERVED trajectories. The four
axes are deliberately different kinds of evidence:

  C  heading coherence            -- is it doing one thing?
  G  internal predictive integration -- do its members predict each other
                                     better than the exterior predicts them?
  L  residual predictive leakage  -- challenger-certified: how much does the
                                     exterior still explain once the interior
                                     and its inferred boundary are conditioned
                                     on? (LOW is thing-like)
  D  exterior heading-distribution contrast -- is it distinguishable from the
                                     medium it sits in?

Percentile ranks are taken against COMPARABLE candidates: connected, of similar
size, in the same uncontrolled regime. Absolute values of G and L depend on
size and regime, so a raw threshold would silently select for size; the rank is
the comparable quantity.

The thing-like stratum's thresholds are frozen on development/uncontrolled data
only. Control success is not computed in this module and is not importable from
it -- see PROTOCOL_6_10.md.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression

NU = 4
C_REG, MAX_ITER = 1.0, 200

# Disclosed conditioning restriction, identical to Stage 6.8's
# `predictive_boundary_68.R_POOL`: a target conditions only on sources within
# this observed-position radius. ~2.5x the interaction geometry, so no source
# that can influence the target in one step is excluded. Without it, a 70-member
# interior contributes 280 one-hot features and the interior-only model loses to
# the marginal base rate on held-out data purely from variance, making G
# negative for most candidates -- an artefact of the estimator, not a fact about
# the collective.
R_POOL = 3.5


def coherence(z_window, I) -> float:
    """C: mean fraction of the collective sharing its modal heading."""
    I = np.asarray(sorted(int(x) for x in I))
    if len(I) == 0:
        return float("nan")
    vals = [np.bincount(np.asarray(z)[I], minlength=NU).max() / len(I) for z in z_window]
    return float(np.mean(vals))


def _fit_logloss(tr_prev, tr_nxt, te_prev, te_nxt, target, sources, eps=1e-9):
    """HELD-OUT mean log-loss for predicting `target`'s next heading from
    `sources`' current headings. Fitted on the train replicates and scored on
    the test replicates: an in-sample score would make G and L grow with the
    number of conditioning sources regardless of any real dependence, so the
    interior (large source set) would always look integrated."""
    y_te = te_nxt[:, target]
    if len(sources) == 0:
        p = np.bincount(tr_nxt[:, target], minlength=NU) + 1.0
        p = p / p.sum()
        return float(-np.log(np.clip(p[y_te], eps, 1)).mean())
    Xtr = np.eye(NU)[tr_prev[:, sources]].reshape(tr_prev.shape[0], -1)
    Xte = np.eye(NU)[te_prev[:, sources]].reshape(te_prev.shape[0], -1)
    y_tr = tr_nxt[:, target]
    if len(np.unique(y_tr)) < 2:
        c = int(y_tr[0])
        p = np.full(NU, eps); p[c] = 1.0 - (NU - 1) * eps
        return float(-np.log(np.clip(p[y_te], eps, 1)).mean())
    clf = LogisticRegression(C=C_REG, penalty="l2", solver="liblinear", max_iter=MAX_ITER)
    clf.fit(Xtr, y_tr)
    pr = clf.predict_proba(Xte)
    p = np.full((len(y_te), NU), eps)
    for k, c in enumerate(clf.classes_):
        p[:, c] = pr[:, k]
    p /= p.sum(1, keepdims=True)
    return float(-np.log(np.clip(p[np.arange(len(y_te)), y_te], eps, 1)).mean())


def _restrict(sources, target, positions, r_pool):
    src = [int(s) for s in sources if int(s) != int(target)]
    if positions is None or r_pool is None or not src:
        return sorted(src)
    d = np.sqrt(((positions[src] - positions[int(target)]) ** 2).sum(axis=1))
    return sorted(s for s, dd in zip(src, d) if dd <= r_pool)


def integration_and_leakage(tr_prev, tr_nxt, te_prev, te_nxt, I, boundary,
                            exterior, targets=None, max_targets=10,
                            max_challengers=24, seed=0, positions=None,
                            r_pool=R_POOL):
    """G and L, both as HELD-OUT log-loss reductions.

    G = ell(marginal) - ell(interior-only)      -- how much the collective's own
                                                   members explain each other
    L = ell(interior+boundary) - ell(interior+boundary+challenger)
                                                -- what the exterior still adds
                                                   once the inferred boundary is
                                                   conditioned on (low = closed)
    The challenger is the strongest residual exterior source, selected on the
    training replicates and scored on the held-out ones (the multi-source
    certified version lives in Stage 6.8's `challenger.py`). Both are
    differences of held-out losses, so adding useless sources costs rather than
    pays, and a size-driven G is not manufactured by the estimator.
    """
    I = sorted(int(x) for x in I)
    B = sorted(int(x) for x in boundary)
    E = [int(x) for x in exterior if int(x) not in set(I) | set(B)]
    rng = np.random.default_rng(seed)
    tg = I if targets is None else list(targets)
    if len(tg) > max_targets:
        tg = sorted(rng.choice(tg, size=max_targets, replace=False).tolist())
    gs, ls = [], []
    for i in tg:
        others = _restrict(I, i, positions, r_pool)
        l_marg = _fit_logloss(tr_prev, tr_nxt, te_prev, te_nxt, i, [])
        l_int = _fit_logloss(tr_prev, tr_nxt, te_prev, te_nxt, i, others)
        gs.append(l_marg - l_int)
        cond = sorted(set(others) | set(_restrict(B, i, positions, r_pool)))
        l_ib = _fit_logloss(tr_prev, tr_nxt, te_prev, te_nxt, i, cond)
        best = 0.0
        for j in _restrict(E, i, positions, r_pool)[:max_challengers]:
            l_c = _fit_logloss(tr_prev, tr_nxt, te_prev, te_nxt, i, sorted(set(cond) | {j}))
            best = max(best, l_ib - l_c)
        ls.append(best)
    return float(np.mean(gs)) if gs else float("nan"), float(np.mean(ls)) if ls else float("nan")


def exterior_contrast(z, I, exterior_ring) -> float:
    """D: total-variation distance between the collective's heading histogram
    and its local exterior's. High = it stands out from its medium."""
    z = np.asarray(z)
    I = np.asarray(sorted(int(x) for x in I))
    E = np.asarray(sorted(int(x) for x in exterior_ring))
    if len(I) == 0 or len(E) == 0:
        return float("nan")
    pi = np.bincount(z[I], minlength=NU) / len(I)
    pe = np.bincount(z[E], minlength=NU) / len(E)
    return float(0.5 * np.abs(pi - pe).sum())


def percentile_ranks(value, reference) -> float:
    """Rank of `value` within `reference` (both same axis), in [0, 1]."""
    ref = np.asarray([r for r in reference if r == r], float)
    if len(ref) == 0 or value != value:
        return float("nan")
    return float((ref < value).mean() + 0.5 * (ref == value).mean())


# --------------------------------------------------------- percentile ranks --
SIZE_TOL = 0.25          # a "comparable" candidate is within +-25% in area


def comparable_mask(cands, i, size_tol=SIZE_TOL):
    """Which candidates candidate `i` should be ranked against.

    Comparable means: same number of cardinal components, and within `size_tol`
    in area. Absolute values of G and D depend strongly on both, so a raw
    percentile over the whole landscape would rank candidates by size rather
    than by how thing-like they are. Snake-like candidates are NOT excluded --
    shape is a separate axis (Part F) and is deliberately not folded in here.
    """
    a = cands[i]
    lo, hi = a["size"] * (1 - size_tol), a["size"] * (1 + size_tol)
    return [j for j, b in enumerate(cands)
            if lo <= b["size"] <= hi and b["n_components"] == a["n_components"]]


def add_percentile_ranks(cands, axes=("C", "G", "L", "D"), size_tol=SIZE_TOL):
    """Attach `rank_<axis>` to each candidate, in place.

    Ranks are within the comparable set, so they are only interpretable against
    candidates of similar size and connectivity. `n_comparable` is stored with
    them: a rank taken against three peers is not the same evidence as one taken
    against forty, and the reader needs to see which they have.
    """
    for i, c in enumerate(cands):
        idx = comparable_mask(cands, i, size_tol)
        c["n_comparable"] = len(idx)
        for ax in axes:
            ref = [cands[j][ax] for j in idx if j != i]
            c[f"rank_{ax}"] = percentile_ranks(c[ax], ref) if ref else float("nan")
    return cands
