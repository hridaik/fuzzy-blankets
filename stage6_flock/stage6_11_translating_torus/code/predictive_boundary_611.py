"""Stage 6.11 relational passive predictor and predictive-boundary
construction/certification (task brief items 6-7).

INFERENCE-SIDE. The primary moving-world next-heading model is permutation/
translation invariant: one multinomial-logistic coefficient set per
CURRENT-HEADING stratum h_cur, applied identically to every bird and every
neighbour -- never a per-bird-ID coefficient. Its score has exactly the form

    s_h(i,t) = b_h + sum_{j in pool(i,t)} phi_h(z_j(t), dist_bin(i,j,t), bearing_octant(i,j,t))

with a_h(z_i(t)) absorbed into b_h by stratifying on z_i(t) (heading_stratified.py's
established Stage 6.8 pattern, kept here; only the FEATURE representation
changes, from per-source-ID coefficients to a relational category histogram).
Because s_h is linear in the pooled category counts, a specific source's
held-out predictive contribution is measured exactly by ablation (remove its
one category count, re-softmax) -- no per-source coefficient is needed, which
is what makes the relational model (item 6) and per-source boundary
construction (item 7) compatible.

The true interaction radius is never used. Distance bins are equal-frequency
cut points estimated from the TRAINING split's own pooled nearest-neighbour
distances; the observable pool is the nearest M_obs birds (broad, swept over
>=2 sizes per item 6's sensitivity-check requirement).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression

from geometry_611 import torus_delta, torus_distance_matrix, bearing_octant, local_scale

NU = 4
N_DIST_BINS = 3
N_BEARING = 8
N_CATEGORIES = NU * N_DIST_BINS * N_BEARING           # 96
M_OBS_GRID = (12, 20)
C_REG = 1.0
MAX_ITER = 300
MIN_STRATUM_SAMPLES = 40
DELTA_TOL = 0.01          # nats/bird-step excess-over-full-pool stop rule (item 7 construction)
MIN_GAIN = 0.002
K_MAX = 12
N_BOOT_CERT = 300
ALPHA_CERT = 0.05
DELTA_SUFFICIENT = 0.01


def category_index(z_j: np.ndarray, dist_bin: np.ndarray, bearing_oct: np.ndarray) -> np.ndarray:
    return (z_j * N_DIST_BINS + dist_bin) * N_BEARING + bearing_oct


def estimate_distance_cuts(r_hist: np.ndarray, z_hist: np.ndarray, L: float, M_obs: int,
                            rng: np.random.Generator, n_sample_steps: int = 20) -> np.ndarray:
    """Equal-frequency cut points from the TRAINING split's own pooled
    nearest-M_obs distances. Never a function of the true interaction radius."""
    T, N = z_hist.shape[0] - 1, z_hist.shape[1]
    steps = rng.choice(T, size=min(n_sample_steps, T), replace=False)
    pooled = []
    for t in steps:
        D = torus_distance_matrix(r_hist[t], L)
        pooled.append(np.sort(D, axis=1)[:, :M_obs].ravel())
    pooled = np.concatenate(pooled)
    qs = np.linspace(0, 1, N_DIST_BINS + 1)[1:-1]
    return np.quantile(pooled, qs)


def pool_and_histogram(r_t: np.ndarray, z_t: np.ndarray, i: int, L: float,
                        dist_cuts: np.ndarray, M_obs: int):
    """Nearest-M_obs pool for bird i at this snapshot, its per-neighbour
    category, and the aggregated 96-dim histogram."""
    d = torus_delta(r_t, r_t[i], L)
    D = np.sqrt((d ** 2).sum(-1))
    D[i] = np.inf
    pool_idx = np.argsort(D)[:M_obs]
    delta_to_pool = d[pool_idx]
    own_heading_vec = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])[z_t[i]]
    bearing = bearing_octant(delta_to_pool, np.tile(own_heading_vec, (len(pool_idx), 1)))
    dbin = np.digitize(D[pool_idx], dist_cuts)
    cats = category_index(z_t[pool_idx], dbin, bearing)
    hist = np.bincount(cats, minlength=N_CATEGORIES).astype(float)
    return hist, pool_idx, cats


@dataclass
class Row:
    t: int
    i: int
    z_i: int
    hist: np.ndarray
    label: int
    pool_idx: np.ndarray
    pool_cat: np.ndarray


def build_rows(r_hist: np.ndarray, z_hist: np.ndarray, L: float, M_obs: int,
                dist_cuts: np.ndarray, rng: np.random.Generator,
                max_rows_per_episode: int | None = 1500) -> list[Row]:
    T, N = z_hist.shape[0] - 1, z_hist.shape[1]
    pairs = [(t, i) for t in range(T) for i in range(N)]
    if max_rows_per_episode is not None and len(pairs) > max_rows_per_episode:
        sel = rng.choice(len(pairs), size=max_rows_per_episode, replace=False)
        pairs = [pairs[k] for k in sel]
    rows = []
    for t, i in pairs:
        hist, pool_idx, cats = pool_and_histogram(r_hist[t], z_hist[t], i, L, dist_cuts, M_obs)
        rows.append(Row(t=t, i=i, z_i=int(z_hist[t, i]), hist=hist,
                         label=int(z_hist[t + 1, i]), pool_idx=pool_idx, pool_cat=cats))
    return rows


def build_rows_multi(episodes: list[dict], L: float, M_obs: int, dist_cuts: np.ndarray,
                      rng: np.random.Generator, max_rows_per_episode: int | None = 1500) -> list[Row]:
    out = []
    for ep in episodes:
        out.extend(build_rows(ep["r_hist"], ep["z_hist"], L, M_obs, dist_cuts, rng, max_rows_per_episode))
    return out


class RelationalHeadingModel:
    """One multinomial-logistic model per current-heading stratum, sharing
    coefficients across all birds/times/pairs (permutation + translation
    invariant by construction: only relative category features enter)."""

    def __init__(self, M_obs: int, dist_cuts: np.ndarray, L: float):
        self.M_obs = M_obs
        self.dist_cuts = dist_cuts
        self.L = L
        self.models: dict[int, LogisticRegression | tuple] = {}
        self.n_fit_rows = 0

    def fit(self, rows: list[Row]):
        self.n_fit_rows = len(rows)
        for h in range(NU):
            rh = [r for r in rows if r.z_i == h]
            if len(rh) < MIN_STRATUM_SAMPLES or len(set(r.label for r in rh)) < 2:
                self.models[h] = ("constant", max(set(r.label for r in rh), key=lambda c: sum(1 for r in rh if r.label == c))
                                   if rh else 0)
                continue
            X = np.stack([r.hist for r in rh])
            y = np.array([r.label for r in rh])
            prev = self.models.get(h)
            clf = LogisticRegression(multi_class="multinomial", solver="lbfgs", C=C_REG,
                                      max_iter=MAX_ITER, warm_start=isinstance(prev, LogisticRegression))
            if isinstance(prev, LogisticRegression):
                clf.coef_, clf.intercept_, clf.classes_ = prev.coef_, prev.intercept_, prev.classes_
            clf.fit(X, y)
            self.models[h] = clf

    def refit_with_buffer(self, base_rows: list[Row], online_buffer: list[Row]):
        """Periodic warm-started refit on base corpus + everything observed
        so far this episode -- "sequential MAP / online predictive
        estimation" (item 6), not a coefficient posterior."""
        self.fit(base_rows + online_buffer)

    def _score(self, h: int, hist: np.ndarray) -> np.ndarray:
        m = self.models[h]
        if isinstance(m, tuple):
            s = np.full(NU, -np.inf)
            s[m[1]] = 0.0
            return s
        classes = m.classes_
        raw = hist @ m.coef_.T + m.intercept_
        s = np.full(NU, -1e9)
        s[classes] = raw
        return s

    def logloss(self, h: int, hist: np.ndarray, label: int) -> float:
        s = self._score(h, hist)
        s = s - s.max()
        p = np.exp(s)
        p = p / p.sum()
        return float(-np.log(max(p[label], 1e-12)))

    def predict_proba(self, h: int, hist: np.ndarray) -> np.ndarray:
        s = self._score(h, hist)
        s = s - s.max()
        p = np.exp(s)
        return p / p.sum()

    def mean_logloss(self, rows: list[Row]) -> float:
        if not rows:
            return float("nan")
        return float(np.mean([self.logloss(r.z_i, r.hist, r.label) for r in rows]))

    def logloss_batch(self, z_i_arr: np.ndarray, hist_matrix: np.ndarray, label_arr: np.ndarray) -> float:
        """Vectorized mean log-loss over many rows at once -- one matrix pass
        per stratum instead of a Python loop per row. Used by the boundary
        greedy search / certification, which re-score the same row set many
        times (once per candidate x per greedy step)."""
        n = len(z_i_arr)
        if n == 0:
            return float("nan")
        ll = np.empty(n)
        for h in range(NU):
            mask = z_i_arr == h
            if not mask.any():
                continue
            m = self.models[h]
            X = hist_matrix[mask]
            if isinstance(m, tuple):
                s = np.full((mask.sum(), NU), -np.inf)
                s[:, m[1]] = 0.0
            else:
                classes = m.classes_
                raw = X @ m.coef_.T + m.intercept_
                s = np.full((mask.sum(), NU), -1e9)
                s[:, classes] = raw
            s = s - s.max(axis=1, keepdims=True)
            p = np.exp(s)
            p = p / p.sum(axis=1, keepdims=True)
            lab = label_arr[mask]
            ll[mask] = -np.log(np.maximum(p[np.arange(len(lab)), lab], 1e-12))
        return float(ll.mean())


# ------------------------------------------------------- item 7: boundary --
def interior_periphery_targets(members: np.ndarray, r_t: np.ndarray, L: float,
                                periphery_radius: float, max_targets: int = 24,
                                rng: np.random.Generator | None = None) -> np.ndarray:
    """Interior members within `periphery_radius` of some non-member -- the
    "observable periphery" item 7 restricts prediction evaluation to."""
    member_set = set(int(m) for m in members)
    non_members = np.array([i for i in range(len(r_t)) if i not in member_set])
    if len(non_members) == 0:
        return np.array([], dtype=int)
    d = torus_delta(r_t[members][:, None, :], r_t[non_members][None, :, :], L)
    D = np.sqrt((d ** 2).sum(-1))
    near = (D <= periphery_radius).any(axis=1)
    targets = members[near]
    if rng is not None and len(targets) > max_targets:
        targets = rng.choice(targets, size=max_targets, replace=False)
    return targets


def rows_for_targets(episodes: list[dict], members: np.ndarray, L: float, M_obs: int,
                      dist_cuts: np.ndarray, periphery_radius: float,
                      rng: np.random.Generator, max_targets_per_step: int = 24,
                      max_rows_total: int | None = 6000) -> list[Row]:
    """Build rows only for the interior's own observable periphery, across
    all provided episodes (used as either dev/val or held-out/test data).
    `max_rows_total` subsamples uniformly across all (episode, step, target)
    instances -- a disclosed tractability bound, not a selection bias (every
    instance is equally likely to be kept)."""
    out = []
    for ep in episodes:
        r_hist, z_hist = ep["r_hist"], ep["z_hist"]
        T = z_hist.shape[0] - 1
        for t in range(T):
            targets = interior_periphery_targets(members, r_hist[t], L, periphery_radius,
                                                   max_targets_per_step, rng)
            for i in targets:
                hist, pool_idx, cats = pool_and_histogram(r_hist[t], z_hist[t], int(i), L, dist_cuts, M_obs)
                out.append(Row(t=t, i=int(i), z_i=int(z_hist[t, i]), hist=hist,
                                label=int(z_hist[t + 1, i]), pool_idx=pool_idx, pool_cat=cats))
    if max_rows_total is not None and len(out) > max_rows_total:
        sel = rng.choice(len(out), size=max_rows_total, replace=False)
        out = [out[k] for k in sel]
    return out


def _rows_to_matrix(rows: list[Row]):
    n = len(rows)
    hist_matrix = np.stack([r.hist for r in rows]) if n else np.zeros((0, N_CATEGORIES))
    z_i_arr = np.array([r.z_i for r in rows], dtype=int)
    label_arr = np.array([r.label for r in rows], dtype=int)
    return hist_matrix, z_i_arr, label_arr


def _exterior_occurrences(rows: list[Row], exclude: set[int]) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """{bird: (row_index_array, category_array)} for every bird appearing in
    any row's observed pool and not in `exclude` -- precomputed once so the
    greedy search / certification never re-scans row pools per candidate."""
    occ: dict[int, list] = {}
    for ridx, r in enumerate(rows):
        for pj, pc in zip(r.pool_idx, r.pool_cat):
            pj = int(pj)
            if pj in exclude:
                continue
            occ.setdefault(pj, []).append((ridx, int(pc)))
    return {j: (np.array([x[0] for x in v]), np.array([x[1] for x in v])) for j, v in occ.items()}


def construct_boundary(model: RelationalHeadingModel, members: np.ndarray, rows: list[Row],
                        delta_tol: float = DELTA_TOL, min_gain: float = MIN_GAIN,
                        k_max: int = K_MAX) -> dict:
    """Greedy conditional construction, fully vectorized: start from the
    INTERIOR-ONLY conditioning set (all exterior-sourced pool categories
    ablated out of every target row's histogram), then iteratively add the
    single exterior source bird whose reinclusion most reduces mean log-loss
    on `rows`, stopping by the predeclared tolerance/cap. `rows` should be
    interior-periphery rows from a split NOT used for later certification
    (item 7's construction/certification separation)."""
    member_set = set(int(m) for m in members)
    hist_matrix, z_i_arr, label_arr = _rows_to_matrix(rows)
    if len(rows) == 0:
        return dict(B=[], full_pool_loss=float("nan"), interior_only_loss=float("nan"),
                    final_loss=float("nan"), trace=[])

    occ = _exterior_occurrences(rows, member_set)
    baseline = hist_matrix.copy()
    for ridx, cat in occ.values():
        np.subtract.at(baseline, (ridx, cat), 1.0)
    np.clip(baseline, 0.0, None, out=baseline)

    full_pool_loss = model.logloss_batch(z_i_arr, hist_matrix, label_arr)
    interior_only_loss = model.logloss_batch(z_i_arr, baseline, label_arr)
    cur, cur_loss = baseline, interior_only_loss
    B: list[int] = []
    trace = [dict(step=0, added=None, mean_logloss=cur_loss)]
    candidates = sorted(occ.keys())

    for step in range(1, k_max + 1):
        best_j, best_loss, best_mat = None, cur_loss, cur
        for j in candidates:
            if j in B:
                continue
            ridx, cat = occ[j]
            trial = cur.copy()
            np.add.at(trial, (ridx, cat), 1.0)
            loss = model.logloss_batch(z_i_arr, trial, label_arr)
            if loss < best_loss:
                best_j, best_loss, best_mat = j, loss, trial
        gain = cur_loss - best_loss
        if best_j is None or gain < min_gain or (best_loss - full_pool_loss) <= delta_tol:
            trace.append(dict(step=step, added=None, mean_logloss=cur_loss, stop_reason="tol_or_no_gain"))
            break
        B.append(best_j)
        cur, cur_loss = best_mat, best_loss
        trace.append(dict(step=step, added=best_j, mean_logloss=cur_loss, gain=gain))
    else:
        trace.append(dict(step=k_max, added=None, mean_logloss=cur_loss, stop_reason="k_max"))

    return dict(B=sorted(B), full_pool_loss=full_pool_loss, interior_only_loss=interior_only_loss,
                final_loss=cur_loss, trace=trace)


def certify(model: RelationalHeadingModel, members: np.ndarray, B: list[int],
            test_episodes: list[dict], L: float, M_obs: int, dist_cuts: np.ndarray,
            periphery_radius: float, rng: np.random.Generator,
            n_boot: int = N_BOOT_CERT, alpha: float = ALPHA_CERT,
            delta: float = DELTA_SUFFICIENT, max_rows_per_episode: int = 800) -> dict:
    """Single-challenger certification on TEST data never used for
    construction. Per-episode, per-candidate log-loss is precomputed ONCE
    (one vectorized pass each); the bootstrap then only resamples EPISODES
    over those precomputed scalars, never re-scores rows inside the bootstrap
    loop. B is "predictively sufficient relative to the single-source
    challenger class" iff the 95% bootstrap upper bound of the challenge gap
    <= delta (item 7's wording; a disclosed single-challenger simplification
    of Stage 6.8's 3-challenger battery)."""
    member_set = set(int(m) for m in members)
    keep_B = member_set | set(B)

    base_losses, cand_losses = [], {}
    for ep in test_episodes:
        rows = rows_for_targets([ep], members, L, M_obs, dist_cuts, periphery_radius, rng,
                                 max_rows_total=max_rows_per_episode)
        hist_matrix, z_i_arr, label_arr = _rows_to_matrix(rows)
        if len(rows) == 0:
            base_losses.append(float("nan"))
            continue
        occ = _exterior_occurrences(rows, keep_B)
        base_mat = hist_matrix.copy()
        for ridx, cat in occ.values():
            np.subtract.at(base_mat, (ridx, cat), 1.0)
        np.clip(base_mat, 0.0, None, out=base_mat)
        base_losses.append(model.logloss_batch(z_i_arr, base_mat, label_arr))
        for j, (ridx, cat) in occ.items():
            trial = base_mat.copy()
            np.add.at(trial, (ridx, cat), 1.0)
            cand_losses.setdefault(j, []).append(model.logloss_batch(z_i_arr, trial, label_arr))
        for j in cand_losses:
            if len(cand_losses[j]) < len(base_losses):
                cand_losses[j].append(base_losses[-1])   # candidate absent this episode -> no effect

    base_arr = np.array(base_losses)
    cand_arr = {j: np.array(v) for j, v in cand_losses.items()}
    valid = np.where(~np.isnan(base_arr))[0]

    challenge_gaps = np.zeros(n_boot)
    for b in range(n_boot):
        idx = rng.choice(valid, size=len(valid), replace=True) if len(valid) else valid
        boot_base = float(np.mean(base_arr[idx])) if len(idx) else float("nan")
        best = boot_base
        for arr in cand_arr.values():
            best = min(best, float(np.mean(arr[idx]))) if len(idx) else best
        challenge_gaps[b] = boot_base - best if len(idx) else 0.0

    upper = float(np.quantile(challenge_gaps, 1 - alpha)) if n_boot else float("nan")
    return dict(B=sorted(B), base_test_logloss=float(np.nanmean(base_arr)) if len(base_arr) else None,
                L_challenge_point=float(np.mean(challenge_gaps)) if n_boot else None, L_challenge_upper=upper,
                delta=delta, alpha=alpha, n_boot=n_boot,
                predictively_sufficient_rel_challenger_class=bool(upper <= delta) if n_boot else None,
                n_exterior_challengers_tested=len(cand_arr),
                wording="predictively sufficient relative to the single-source challenger class -- "
                        "NOT a conditional-independence claim")
