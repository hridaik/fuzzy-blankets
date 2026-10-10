"""Stage 6.12C follow-up: stable-selectivity decomposition of the K=1,d=8
exhaustive candidate x stream data. Analysis-only -- no new simulation.
Reads data/k1_candidates_612c.json and data/k1_rollouts_612c.json from
../ (the frozen Stage 6.12C outputs) and writes derivative results into
stable_selectivity_analysis/data/stable_selectivity_results.json plus
figures into stable_selectivity_analysis/figures/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr, pearsonr

HERE = Path(__file__).resolve().parent
SSA_DIR = HERE.parent
S612C_DIR = SSA_DIR.parent
DATA_612C = S612C_DIR / "data"
OUT_DATA = SSA_DIR / "data"
OUT_FIG = SSA_DIR / "figures"
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_FIG.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(555_000_111)
N_PERM = 2000
N_CV_REPS = 500

CAND = json.load(open(DATA_612C / "k1_candidates_612c.json"))
ROLL = json.load(open(DATA_612C / "k1_rollouts_612c.json"))
STATES = sorted(set(r["state_id"] for r in CAND))


def state_matrix(sid, key="confirm_delta_conservative_all", cand_field="candidate"):
    srows = sorted([r for r in CAND if r["state_id"] == sid], key=lambda r: r[cand_field])
    cands = [r[cand_field] for r in srows]
    X = np.array([r[key] for r in srows], dtype=float)  # (n_cand, n_streams)
    return cands, X


def full_matrix(sid):
    """12-stream matrix: 4 search + 8 confirm, columns in a fixed order
    (search 0-3, confirm 0-7), using the SAME physics-seed-defined streams
    already present in the frozen candidate JSON. No new streams."""
    cands, Xs = state_matrix(sid, "search_delta_conservative_all")
    _, Xc = state_matrix(sid, "confirm_delta_conservative_all")
    return cands, np.hstack([Xs, Xc])


def full_matrix_assoc(sid):
    cands, Xs = state_matrix(sid, "search_delta_assoc_all")
    _, Xc = state_matrix(sid, "confirm_delta_assoc_all")
    return cands, np.hstack([Xs, Xc])


# ---------------------------------------------------------------- section 4
def data_design_audit():
    audit = {}
    n_cand_per_state = {}
    n_search = {}
    n_confirm = {}
    crossed_ok = {}
    for sid in STATES:
        cands, X = full_matrix(sid)
        n_cand_per_state[sid] = len(cands)
        _, Xs = state_matrix(sid, "search_delta_conservative_all")
        _, Xc = state_matrix(sid, "confirm_delta_conservative_all")
        n_search[sid] = Xs.shape[1]
        n_confirm[sid] = Xc.shape[1]
        # crossed design check: every candidate has the same number of stream
        # entries (no missing cells) -- already true by construction of
        # state_matrix (fixed-width arrays), so check for NaN/inconsistent
        # lengths across candidates directly from raw json.
        srows = [r for r in CAND if r["state_id"] == sid]
        lens_search = set(len(r["search_delta_conservative_all"]) for r in srows)
        lens_confirm = set(len(r["confirm_delta_conservative_all"]) for r in srows)
        crossed_ok[sid] = (len(lens_search) == 1 and len(lens_confirm) == 1
                            and list(lens_search)[0] == Xs.shape[1]
                            and list(lens_confirm)[0] == Xc.shape[1])
    # paired no-control: by construction (CONFIRMATORY_PROTOCOL.md), the same
    # physics_seed per (state, stream_role, stream_idx) is reused across all
    # 20 candidates -- verify directly from the rollout-level file.
    paired_shared = {}
    for sid in STATES:
        srows = [r for r in ROLL if r["state_id"] == sid]
        by_role_idx = {}
        for r in srows:
            key = (r["stream_role"], r["stream_idx"])
            by_role_idx.setdefault(key, set()).add(r["physics_seed"])
        paired_shared[sid] = all(len(v) == 1 for v in by_role_idx.values())
    both_metrics_available = all(
        "confirm_delta_conservative_all" in r and "confirm_delta_assoc_all" in r for r in CAND
    )
    audit = dict(
        n_states=len(STATES),
        n_candidates_per_state=n_cand_per_state,
        n_candidates_uniform=len(set(n_cand_per_state.values())) == 1,
        n_search_streams_per_state=n_search,
        n_confirm_streams_per_state=n_confirm,
        n_search_uniform=len(set(n_search.values())) == 1,
        n_confirm_uniform=len(set(n_confirm.values())) == 1,
        crossed_design_complete_per_state=crossed_ok,
        crossed_design_complete_all_states=all(crossed_ok.values()),
        same_physics_seed_per_stream_across_candidates=paired_shared,
        same_physics_seed_all_states=all(paired_shared.values()),
        delta_conservative_and_delta_assoc_both_available=both_metrics_available,
        n_candidate_rows=len(CAND),
        n_rollout_rows=len(ROLL),
    )
    return audit


# ---------------------------------------------------------------- section 5
def actuator_mean_stats(metric_all_key_search, metric_all_key_confirm):
    out = {}
    for sid in STATES:
        cands, Xc = state_matrix(sid, metric_all_key_confirm)
        n_cand, n_r = Xc.shape
        mean_ = Xc.mean(axis=1)
        median_ = np.median(Xc, axis=1)
        sd_ = Xc.std(axis=1, ddof=1)
        se_ = sd_ / np.sqrt(n_r)
        frac_pos = (Xc > 0).mean(axis=1)
        out[sid] = dict(
            candidates=cands, mean=mean_.tolist(), median=median_.tolist(),
            sd=sd_.tolist(), se=se_.tolist(), frac_positive=frac_pos.tolist(),
            grand_mean_of_means=float(mean_.mean()),
            sd_of_means_across_candidates=float(mean_.std(ddof=1)),
            mean_within_candidate_sd=float(sd_.mean()),
        )
    return out


# ---------------------------------------------------------------- section 6
def variance_decomposition(matrix_fn=full_matrix):
    """Two-way random-effects, no-replication method-of-moments ANOVA
    decomposition per state. Cannot separate interaction from residual
    noise with one obs/cell -- reported as a single combined term."""
    out = {}
    for sid in STATES:
        cands, X = matrix_fn(sid)
        J, R = X.shape
        mu = X.mean()
        row_means = X.mean(axis=1)   # per actuator
        col_means = X.mean(axis=0)   # per stream
        SS_a = R * np.sum((row_means - mu) ** 2)
        SS_r = J * np.sum((col_means - mu) ** 2)
        SS_tot = np.sum((X - mu) ** 2)
        SS_res = SS_tot - SS_a - SS_r
        df_a, df_r = J - 1, R - 1
        df_res = df_a * df_r
        MS_a = SS_a / df_a
        MS_r = SS_r / df_r
        MS_res = SS_res / df_res if df_res > 0 else np.nan
        var_a_raw = (MS_a - MS_res) / R
        var_r_raw = (MS_r - MS_res) / J
        var_res = MS_res
        var_a = max(0.0, var_a_raw)
        var_r = max(0.0, var_r_raw)
        total = var_a + var_r + var_res if (var_a + var_r + var_res) > 0 else np.nan
        out[sid] = dict(
            n_actuators=J, n_streams=R, grand_mean=float(mu),
            MS_actuator=float(MS_a), MS_stream=float(MS_r), MS_residual=float(MS_res),
            var_actuator_raw=float(var_a_raw), var_stream_raw=float(var_r_raw),
            var_actuator=float(var_a), var_stream=float(var_r), var_residual_or_interaction=float(var_res),
            var_actuator_frac=float(var_a / total) if total and total > 0 else None,
            var_stream_frac=float(var_r / total) if total and total > 0 else None,
            var_residual_frac=float(var_res / total) if total and total > 0 else None,
        )
    fracs_a = [v["var_actuator_frac"] for v in out.values() if v["var_actuator_frac"] is not None]
    fracs_r = [v["var_stream_frac"] for v in out.values() if v["var_stream_frac"] is not None]
    fracs_res = [v["var_residual_frac"] for v in out.values() if v["var_residual_frac"] is not None]
    aggregate = dict(
        mean_var_actuator_frac=float(np.mean(fracs_a)) if fracs_a else None,
        median_var_actuator_frac=float(np.median(fracs_a)) if fracs_a else None,
        mean_var_stream_frac=float(np.mean(fracs_r)) if fracs_r else None,
        mean_var_residual_frac=float(np.mean(fracs_res)) if fracs_res else None,
        n_states_with_positive_raw_var_actuator=int(sum(1 for v in out.values() if v["var_actuator_raw"] > 0)),
        n_states=len(out),
        note="one observation per actuator x stream cell: var_residual_or_interaction "
             "CANNOT be split further into interaction vs measurement noise from this "
             "design alone; reported as a single combined term throughout.",
    )
    return out, aggregate


# ---------------------------------------------------------------- section 7
def reliability_curve(matrix_fn=full_matrix, m_values=(1, 2, 4, 6), n_splits=300):
    out = {}
    for sid in STATES:
        cands, X = matrix_fn(sid)
        J, R = X.shape
        cands = np.array(cands)
        by_m = {}
        for m in m_values:
            if m >= R:
                continue
            pearsons, spearmans, top1_hits, top3_overlaps = [], [], [], []
            for _ in range(n_splits):
                perm = RNG.permutation(R)
                train_idx, test_idx = perm[:m], perm[m:]
                train_mean = X[:, train_idx].mean(axis=1)
                test_mean = X[:, test_idx].mean(axis=1)
                if np.std(train_mean) == 0 or np.std(test_mean) == 0:
                    continue
                pr, _ = pearsonr(train_mean, test_mean)
                sr, _ = spearmanr(train_mean, test_mean)
                pearsons.append(pr); spearmans.append(sr)
                top1_hits.append(int(np.argmax(train_mean) == np.argmax(test_mean)))
                train_top3 = set(np.argsort(-train_mean)[:3])
                test_top3 = set(np.argsort(-test_mean)[:3])
                top3_overlaps.append(len(train_top3 & test_top3))
            by_m[m] = dict(
                n_valid_splits=len(pearsons),
                mean_pearson=float(np.mean(pearsons)) if pearsons else None,
                mean_spearman=float(np.mean(spearmans)) if spearmans else None,
                frac_top1_stable=float(np.mean(top1_hits)) if top1_hits else None,
                mean_top3_overlap=float(np.mean(top3_overlaps)) if top3_overlaps else None,
            )
        out[sid] = by_m
    # aggregate across states, per m
    agg = {}
    for m in m_values:
        vals_p = [out[sid][m]["mean_pearson"] for sid in STATES if m in out[sid] and out[sid][m]["mean_pearson"] is not None]
        vals_s = [out[sid][m]["mean_spearman"] for sid in STATES if m in out[sid] and out[sid][m]["mean_spearman"] is not None]
        vals_t1 = [out[sid][m]["frac_top1_stable"] for sid in STATES if m in out[sid] and out[sid][m]["frac_top1_stable"] is not None]
        vals_t3 = [out[sid][m]["mean_top3_overlap"] for sid in STATES if m in out[sid] and out[sid][m]["mean_top3_overlap"] is not None]
        agg[m] = dict(
            mean_pearson_across_states=float(np.mean(vals_p)) if vals_p else None,
            mean_spearman_across_states=float(np.mean(vals_s)) if vals_s else None,
            mean_frac_top1_stable_across_states=float(np.mean(vals_t1)) if vals_t1 else None,
            mean_top3_overlap_across_states=float(np.mean(vals_t3)) if vals_t3 else None,
        )
    return out, agg


# ---------------------------------------------------------------- section 8
def cv_stable_oracle(matrix_fn=full_matrix, m_train=6, n_reps=N_CV_REPS):
    out = {}
    for sid in STATES:
        cands, X = matrix_fn(sid)
        J, R = X.shape
        lifts, test_best_lifts, j_star_test_deltas = [], [], []
        for _ in range(n_reps):
            perm = RNG.permutation(R)
            train_idx, test_idx = perm[:m_train], perm[m_train:]
            train_mean = X[:, train_idx].mean(axis=1)
            test_mean = X[:, test_idx].mean(axis=1)
            j_star = np.argmax(train_mean)
            median_test = np.median(test_mean)
            test_best = np.max(test_mean)
            denom = median_test if median_test != 0 else np.nan
            lift = test_mean[j_star] / denom if denom and not np.isnan(denom) else np.nan
            lifts.append(lift)
            test_best_lifts.append(test_best / denom if denom and not np.isnan(denom) else np.nan)
            j_star_test_deltas.append(test_mean[j_star] - median_test)
        lifts = np.array(lifts, dtype=float)
        valid = lifts[~np.isnan(lifts)]
        deltas = np.array(j_star_test_deltas, dtype=float)
        out[sid] = dict(
            n_reps=n_reps, m_train=m_train, m_test=R - m_train,
            mean_CV_stable_lift=float(np.mean(valid)) if len(valid) else None,
            median_CV_stable_lift=float(np.median(valid)) if len(valid) else None,
            mean_test_best_reference_lift=float(np.nanmean(test_best_lifts)),
            mean_j_star_test_minus_median=float(np.mean(deltas)),
            frac_valid_reps=float(len(valid) / n_reps),
        )
    all_lifts = [out[sid]["mean_CV_stable_lift"] for sid in STATES if out[sid]["mean_CV_stable_lift"] is not None]
    all_deltas = [out[sid]["mean_j_star_test_minus_median"] for sid in STATES]
    agg = dict(
        mean_CV_stable_lift_across_states=float(np.mean(all_lifts)) if all_lifts else None,
        median_CV_stable_lift_across_states=float(np.median(all_lifts)) if all_lifts else None,
        mean_j_star_test_minus_median_across_states=float(np.mean(all_deltas)),
        n_states=len(STATES),
    )
    return out, agg


def historical_search_train_confirm_test():
    """The ALREADY-COMPUTED, protocol-frozen search(4)->confirm(8) split
    (Stage 6.12C's 'search-selected best' row in ORACLE_DECOMPOSITION.md),
    reproduced here from the candidate JSON for direct comparison with the
    repeated-CV numbers above, not recomputed with different logic."""
    out = {}
    for sid in STATES:
        srows = [r for r in CAND if r["state_id"] == sid]
        j_star = max(srows, key=lambda r: r["mean_search_delta_conservative"])
        confirm_means = np.array([r["mean_confirm_delta_conservative"] for r in srows])
        median_confirm = float(np.median(confirm_means))
        lift = (j_star["mean_confirm_delta_conservative"] / median_confirm) if median_confirm != 0 else None
        out[sid] = dict(
            j_star_candidate=j_star["candidate"],
            j_star_confirm_mean=j_star["mean_confirm_delta_conservative"],
            median_confirm_mean=median_confirm,
            lift=lift,
            j_star_minus_median=j_star["mean_confirm_delta_conservative"] - median_confirm,
        )
    return out


# ---------------------------------------------------------------- section 9
def three_oracles(matrix_fn=full_matrix):
    out = {}
    for sid in STATES:
        cands, X = matrix_fn(sid)
        J, R = X.shape
        means = X.mean(axis=1)
        median_val = float(np.median(means))
        random_baseline = median_val
        per_stream_clairvoyant = float(X.max(axis=0).mean())
        state_stable_mean = float(means.max())
        # CV stable (use same m_train=6 default, mean over reps, already computed
        # in cv_stable_oracle but recompute the raw ΔJ value here, not the ratio)
        lifts = []
        for _ in range(N_CV_REPS):
            perm = RNG.permutation(R)
            train_idx, test_idx = perm[:R // 2], perm[R // 2:]
            train_mean = X[:, train_idx].mean(axis=1)
            test_mean = X[:, test_idx].mean(axis=1)
            j_star = np.argmax(train_mean)
            lifts.append(test_mean[j_star])
        cv_stable_value = float(np.mean(lifts))
        out[sid] = dict(
            random_median=random_baseline,
            A_per_stream_clairvoyant_oracle=per_stream_clairvoyant,
            B_state_stable_mean_oracle=state_stable_mean,
            C_cross_validated_stable_oracle=cv_stable_value,
        )
    agg = dict(
        mean_random_median=float(np.mean([v["random_median"] for v in out.values()])),
        mean_A_per_stream_clairvoyant=float(np.mean([v["A_per_stream_clairvoyant_oracle"] for v in out.values()])),
        mean_B_state_stable_mean=float(np.mean([v["B_state_stable_mean_oracle"] for v in out.values()])),
        mean_C_cv_stable=float(np.mean([v["C_cross_validated_stable_oracle"] for v in out.values()])),
    )
    agg["ratio_A_to_random"] = agg["mean_A_per_stream_clairvoyant"] / agg["mean_random_median"] if agg["mean_random_median"] else None
    agg["ratio_B_to_random"] = agg["mean_B_state_stable_mean"] / agg["mean_random_median"] if agg["mean_random_median"] else None
    agg["ratio_C_to_random"] = agg["mean_C_cv_stable"] / agg["mean_random_median"] if agg["mean_random_median"] else None
    return out, agg


# --------------------------------------------------------------- section 10
def permutation_null(matrix_fn=full_matrix, n_perm=N_PERM):
    out = {}
    for sid in STATES:
        cands, X = matrix_fn(sid)
        J, R = X.shape
        obs_means = X.mean(axis=1)
        obs_median = float(np.median(obs_means))
        obs_A = float(X.max(axis=0).mean())
        obs_B = float(obs_means.max())
        # CV-stable under observed data (m_train = R//2, many reps, reuse logic)
        def cv_stable_value(mat):
            lifts = []
            for _ in range(150):
                perm = RNG.permutation(R)
                tr, te = perm[:R // 2], perm[R // 2:]
                trm = mat[:, tr].mean(axis=1)
                tem = mat[:, te].mean(axis=1)
                j_star = np.argmax(trm)
                lifts.append(tem[j_star])
            return float(np.mean(lifts))
        obs_C = cv_stable_value(X)

        null_A, null_B, null_C, null_median = [], [], [], []
        for _ in range(n_perm):
            Xp = X.copy()
            for r in range(R):
                Xp[:, r] = Xp[RNG.permutation(J), r]
            means_p = Xp.mean(axis=1)
            null_A.append(float(Xp.max(axis=0).mean()))
            null_B.append(float(means_p.max()))
            null_median.append(float(np.median(means_p)))
        null_A = np.array(null_A); null_B = np.array(null_B); null_median = np.array(null_median)
        # CV-stable null: computed on a SUBSET of permutations (expensive); use 200
        null_C_vals = []
        for _ in range(200):
            Xp = X.copy()
            for r in range(R):
                Xp[:, r] = Xp[RNG.permutation(J), r]
            null_C_vals.append(cv_stable_value(Xp))
        null_C_vals = np.array(null_C_vals)

        out[sid] = dict(
            n_perm=n_perm,
            observed=dict(median=obs_median, A_per_stream=obs_A, B_state_stable=obs_B, C_cv_stable=obs_C),
            null_median=dict(mean=float(null_median.mean()), ci90=[float(np.percentile(null_median, 5)), float(np.percentile(null_median, 95))]),
            null_A=dict(mean=float(null_A.mean()), ci90=[float(np.percentile(null_A, 5)), float(np.percentile(null_A, 95))]),
            null_B=dict(mean=float(null_B.mean()), ci90=[float(np.percentile(null_B, 5)), float(np.percentile(null_B, 95))]),
            null_C=dict(mean=float(null_C_vals.mean()), ci90=[float(np.percentile(null_C_vals, 5)), float(np.percentile(null_C_vals, 95))]),
            excess_A=obs_A - float(null_A.mean()),
            excess_B=obs_B - float(null_B.mean()),
            excess_C=obs_C - float(null_C_vals.mean()),
        )
    agg = dict(
        mean_observed_A=float(np.mean([v["observed"]["A_per_stream"] for v in out.values()])),
        mean_null_A=float(np.mean([v["null_A"]["mean"] for v in out.values()])),
        mean_excess_A=float(np.mean([v["excess_A"] for v in out.values()])),
        mean_observed_B=float(np.mean([v["observed"]["B_state_stable"] for v in out.values()])),
        mean_null_B=float(np.mean([v["null_B"]["mean"] for v in out.values()])),
        mean_excess_B=float(np.mean([v["excess_B"] for v in out.values()])),
        mean_observed_C=float(np.mean([v["observed"]["C_cv_stable"] for v in out.values()])),
        mean_null_C=float(np.mean([v["null_C"]["mean"] for v in out.values()])),
        mean_excess_C=float(np.mean([v["excess_C"] for v in out.values()])),
    )
    return out, agg


# --------------------------------------------------------------- section 11
def candidate_recurrence(matrix_fn=full_matrix):
    out = {}
    for sid in STATES:
        cands, X = matrix_fn(sid)
        cands = np.array(cands)
        J, R = X.shape
        winners = cands[np.argmax(X, axis=0)]
        vals, counts = np.unique(winners, return_counts=True)
        p = counts / counts.sum()
        entropy = float(-(p * np.log(p)).sum())
        max_entropy = float(np.log(len(vals))) if len(vals) > 1 else 0.0
        top1_sets = [set(cands[np.argsort(-X[:, r])[:1]]) for r in range(R)]
        top3_sets = [set(cands[np.argsort(-X[:, r])[:3]]) for r in range(R)]
        top5_sets = [set(cands[np.argsort(-X[:, r])[:5]]) for r in range(R)]
        uniq_top1 = len(set.union(*top1_sets))
        uniq_top3 = len(set.union(*top3_sets))
        uniq_top5 = len(set.union(*top5_sets))
        out[sid] = dict(
            n_streams=R, n_unique_winners=int(len(vals)), max_win_count=int(counts.max()),
            max_win_frequency=float(counts.max() / R), winner_entropy=entropy,
            winner_entropy_normalized=float(entropy / max_entropy) if max_entropy > 0 else None,
            n_unique_candidates_in_top1_any_stream=int(uniq_top1),
            n_unique_candidates_in_top3_any_stream=int(uniq_top3),
            n_unique_candidates_in_top5_any_stream=int(uniq_top5),
        )
    agg = dict(
        mean_max_win_frequency=float(np.mean([v["max_win_frequency"] for v in out.values()])),
        mean_winner_entropy_normalized=float(np.mean([v["winner_entropy_normalized"] for v in out.values() if v["winner_entropy_normalized"] is not None])),
        mean_n_unique_winners=float(np.mean([v["n_unique_winners"] for v in out.values()])),
    )
    return out, agg


# --------------------------------------------------------------- section 12
def pairwise_stability(matrix_fn=full_matrix):
    out = {}
    for sid in STATES:
        cands, X = matrix_fn(sid)
        cands = np.array(cands)
        J, R = X.shape
        P = np.zeros((J, J))
        for a in range(J):
            for b in range(J):
                if a == b:
                    continue
                P[a, b] = float((X[a] > X[b]).mean())
        iu = np.triu_indices(J, k=1)
        strong = [(int(cands[a]), int(cands[b]), float(P[a, b])) for a, b in zip(*iu) if max(P[a, b], 1 - P[a, b]) > 0.8]
        frac_stable = len(strong) / len(iu[0])
        means = X.mean(axis=1)
        best = int(np.argmax(means))
        beats_frac = float((X[best] > X).mean())  # over all (candidate,stream) comparisons pooled
        strong.sort(key=lambda t: -max(t[2], 1 - t[2]))
        out[sid] = dict(
            n_pairs=int(len(iu[0])), n_pairs_stable_gt0p8=int(len(strong)),
            frac_pairs_stable=float(frac_stable),
            top_strong_pairs=strong[:5],
            global_best_mean_candidate=cands[best].item() if hasattr(cands[best], "item") else int(cands[best]),
            global_best_beats_frac_pooled=beats_frac,
        )
    agg = dict(
        mean_frac_pairs_stable=float(np.mean([v["frac_pairs_stable"] for v in out.values()])),
        mean_global_best_beats_frac=float(np.mean([v["global_best_beats_frac_pooled"] for v in out.values()])),
    )
    return out, agg


# --------------------------------------------------------------- section 13
def state_taxonomy(oracle3, var_decomp, reliability_agg_by_state, cv_agg_by_state, recurrence):
    rows = []
    for sid in STATES:
        o = oracle3[sid]
        vd = var_decomp[sid]
        rel = reliability_agg_by_state.get(sid, {})
        rel6 = rel.get(6, {}) if isinstance(rel, dict) else {}
        cv = cv_agg_by_state[sid]
        rec = recurrence[sid]
        random_ = o["random_median"]
        per_stream = o["A_per_stream_clairvoyant_oracle"]
        stable_mean = o["B_state_stable_mean_oracle"]
        cv_val = o["C_cross_validated_stable_oracle"]
        var_a_frac = vd["var_actuator_frac"]
        reliability = rel6.get("mean_spearman") if rel6 else None
        identity_valid_frac = None  # placeholder, filled from separate pass in main()
        # classification heuristic (continuous quantities, thresholds stated explicitly)
        clairvoyant_headroom = per_stream - random_
        cv_headroom = cv_val - random_
        if clairvoyant_headroom > 0 and cv_headroom > 0.5 * clairvoyant_headroom and (var_a_frac or 0) > 0.3:
            label = "stable-selective"
        elif clairvoyant_headroom > 0 and (cv_headroom <= 0.3 * clairvoyant_headroom or (var_a_frac or 0) < 0.15):
            label = "stochastic-opportunity"
        elif clairvoyant_headroom <= 0.3 * random_ if random_ else clairvoyant_headroom <= 0:
            label = "low-headroom"
        else:
            label = "mixed/ambiguous"
        rows.append(dict(
            state_id=sid, random_median=random_, per_stream_clairvoyant_oracle=per_stream,
            state_stable_mean_oracle=stable_mean, cv_stable_oracle=cv_val,
            var_actuator_frac=var_a_frac, ranking_reliability_spearman_m6=reliability,
            max_win_frequency=rec["max_win_frequency"], winner_entropy_normalized=rec["winner_entropy_normalized"],
            label=label,
        ))
    counts = {}
    for r in rows:
        counts[r["label"]] = counts.get(r["label"], 0) + 1
    return rows, counts


def main():
    print("Loaded", len(CAND), "candidate rows,", len(ROLL), "rollout rows across", len(STATES), "states")

    audit = data_design_audit()
    print("audit ok:", audit["crossed_design_complete_all_states"], audit["same_physics_seed_all_states"])

    stats_cons = actuator_mean_stats("search_delta_conservative_all", "confirm_delta_conservative_all")
    stats_assoc = actuator_mean_stats("search_delta_assoc_all", "confirm_delta_assoc_all")

    var_decomp_confirm, var_decomp_confirm_agg = variance_decomposition(matrix_fn=lambda sid: state_matrix(sid, "confirm_delta_conservative_all"))
    var_decomp_full, var_decomp_full_agg = variance_decomposition(matrix_fn=full_matrix)
    var_decomp_assoc_full, var_decomp_assoc_full_agg = variance_decomposition(matrix_fn=full_matrix_assoc)

    rel_by_state, rel_agg = reliability_curve(matrix_fn=full_matrix)

    cv_by_state, cv_agg = cv_stable_oracle(matrix_fn=full_matrix, m_train=6)
    cv_by_state_confirmonly, cv_agg_confirmonly = cv_stable_oracle(
        matrix_fn=lambda sid: state_matrix(sid, "confirm_delta_conservative_all"), m_train=4)
    hist_split = historical_search_train_confirm_test()

    oracle3_by_state, oracle3_agg = three_oracles(matrix_fn=full_matrix)
    oracle3_confirm_by_state, oracle3_confirm_agg = three_oracles(matrix_fn=lambda sid: state_matrix(sid, "confirm_delta_conservative_all"))

    perm_by_state, perm_agg = permutation_null(matrix_fn=full_matrix)
    perm_confirm_by_state, perm_confirm_agg = permutation_null(matrix_fn=lambda sid: state_matrix(sid, "confirm_delta_conservative_all"))

    recurrence_by_state, recurrence_agg = candidate_recurrence(matrix_fn=full_matrix)
    pairwise_by_state, pairwise_agg = pairwise_stability(matrix_fn=full_matrix)

    taxonomy_rows, taxonomy_counts = state_taxonomy(
        oracle3_by_state, var_decomp_full,
        {sid: rel_by_state[sid] for sid in STATES}, cv_by_state, recurrence_by_state)

    results = dict(
        data_design_audit=audit,
        actuator_stats_conservative=stats_cons,
        actuator_stats_assoc=stats_assoc,
        variance_decomposition=dict(
            confirm_only=dict(per_state=var_decomp_confirm, aggregate=var_decomp_confirm_agg),
            full_12stream=dict(per_state=var_decomp_full, aggregate=var_decomp_full_agg),
            full_12stream_assoc=dict(per_state=var_decomp_assoc_full, aggregate=var_decomp_assoc_full_agg),
        ),
        reliability=dict(per_state=rel_by_state, aggregate=rel_agg),
        cv_stable_oracle=dict(
            full_12stream_m6=dict(per_state=cv_by_state, aggregate=cv_agg),
            confirm_only_m4=dict(per_state=cv_by_state_confirmonly, aggregate=cv_agg_confirmonly),
            historical_search_train_confirm_test=hist_split,
        ),
        three_oracles=dict(
            full_12stream=dict(per_state=oracle3_by_state, aggregate=oracle3_agg),
            confirm_only=dict(per_state=oracle3_confirm_by_state, aggregate=oracle3_confirm_agg),
        ),
        permutation_null=dict(
            full_12stream=dict(per_state=perm_by_state, aggregate=perm_agg),
            confirm_only=dict(per_state=perm_confirm_by_state, aggregate=perm_confirm_agg),
        ),
        candidate_recurrence=dict(per_state=recurrence_by_state, aggregate=recurrence_agg),
        pairwise_stability=dict(per_state=pairwise_by_state, aggregate=pairwise_agg),
        state_taxonomy=dict(rows=taxonomy_rows, counts=taxonomy_counts),
    )

    with open(OUT_DATA / "stable_selectivity_results.json", "w") as f:
        json.dump(results, f, indent=1, default=str)
    print("wrote", OUT_DATA / "stable_selectivity_results.json")

    print("\n=== KEY NUMBERS ===")
    print("Var_actuator_frac (full 12-stream, mean across states):", var_decomp_full_agg["mean_var_actuator_frac"])
    print("Var_actuator_frac (confirm-only, mean across states):", var_decomp_confirm_agg["mean_var_actuator_frac"])
    print("CV_stable_lift (full, m_train=6, mean across states):", cv_agg["mean_CV_stable_lift_across_states"])
    print("Three oracles (full, aggregate):", oracle3_agg)
    print("Permutation excess (full):", perm_agg)
    print("Taxonomy counts:", taxonomy_counts)


if __name__ == "__main__":
    main()
