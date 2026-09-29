"""Stage 6.12C confirmatory analysis. Reads data/{k1_candidates,k1_rollouts,
k2_pairs,duration_substudy}_612c.json and computes every predeclared
statistic from CONFIRMATORY_PROTOCOL.md. State-clustered bootstrap
throughout -- the independent generalization unit is the STATE.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612c as C  # noqa: E402

RNG_BOOT = np.random.default_rng(999_000_001)
N_BOOT = 20000


def state_clustered_bootstrap(state_values, statistic=np.mean, n_boot=N_BOOT, rng=RNG_BOOT):
    """state_values: 1D array, one value per state. Resample STATES with
    replacement (not candidate-rollouts)."""
    vals = np.asarray(state_values, dtype=float)
    n = len(vals)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boots[b] = statistic(vals[idx])
    lo, hi = np.percentile(boots, [5, 95])
    return float(lo), float(hi)


def load():
    cand = json.load(open(C.DATA_DIR / "k1_candidates_612c.json"))
    roll = json.load(open(C.DATA_DIR / "k1_rollouts_612c.json"))
    pairs = json.load(open(C.DATA_DIR / "k2_pairs_612c.json"))
    dur = json.load(open(C.DATA_DIR / "duration_substudy_612c.json"))
    return cand, roll, pairs, dur


def l_pred_analysis(cand):
    """Primary confirmatory estimand: L_pred per state, using ONLY
    confirmatory-stream mean ΔJ."""
    states = sorted(set(r["state_id"] for r in cand))
    rows = []
    for sid in states:
        srows = [r for r in cand if r["state_id"] == sid]
        top = max(srows, key=lambda r: r["kinematic_score"])
        deltas_cons = np.array([r["mean_confirm_delta_conservative"] for r in srows])
        deltas_assoc = np.array([r["mean_confirm_delta_assoc"] for r in srows])
        med_cons = float(np.median(deltas_cons))
        med_assoc = float(np.median(deltas_assoc))
        l_cons = (top["mean_confirm_delta_conservative"] / med_cons) if med_cons not in (0, 0.0) else None
        l_assoc = (top["mean_confirm_delta_assoc"] / med_assoc) if med_assoc not in (0, 0.0) else None
        rows.append(dict(state_id=sid, top_candidate=top["candidate"],
                          top_kinematic_score=top["kinematic_score"],
                          top_mean_confirm_delta_conservative=top["mean_confirm_delta_conservative"],
                          top_mean_confirm_delta_assoc=top["mean_confirm_delta_assoc"],
                          median_delta_conservative=med_cons, median_delta_assoc=med_assoc,
                          L_pred_conservative=l_cons, L_pred_assoc=l_assoc,
                          top_minus_median_conservative=top["mean_confirm_delta_conservative"] - med_cons,
                          top_minus_median_assoc=top["mean_confirm_delta_assoc"] - med_assoc))
    valid_cons = [r["L_pred_conservative"] for r in rows if r["L_pred_conservative"] is not None]
    valid_assoc = [r["L_pred_assoc"] for r in rows if r["L_pred_assoc"] is not None]
    diff_cons = [r["top_minus_median_conservative"] for r in rows]
    diff_assoc = [r["top_minus_median_assoc"] for r in rows]
    summary = dict(
        n_states=len(rows),
        L_pred_conservative_median=float(np.median(valid_cons)) if valid_cons else None,
        L_pred_conservative_mean=float(np.mean(valid_cons)) if valid_cons else None,
        L_pred_conservative_ci90=state_clustered_bootstrap(valid_cons) if valid_cons else None,
        L_pred_assoc_median=float(np.median(valid_assoc)) if valid_assoc else None,
        L_pred_assoc_mean=float(np.mean(valid_assoc)) if valid_assoc else None,
        L_pred_assoc_ci90=state_clustered_bootstrap(valid_assoc) if valid_assoc else None,
        frac_states_L_pred_conservative_gt0=float(np.mean([v > 0 for v in valid_cons])) if valid_cons else None,
        frac_states_L_pred_assoc_gt0=float(np.mean([v > 0 for v in valid_assoc])) if valid_assoc else None,
        top_minus_median_conservative_mean=float(np.mean(diff_cons)),
        top_minus_median_conservative_ci90=state_clustered_bootstrap(diff_cons),
        top_minus_median_assoc_mean=float(np.mean(diff_assoc)),
        top_minus_median_assoc_ci90=state_clustered_bootstrap(diff_assoc),
        frac_states_top_minus_median_conservative_gt0=float(np.mean([v > 0 for v in diff_cons])),
    )
    return rows, summary


def predictor_ranking_analysis(cand):
    states = sorted(set(r["state_id"] for r in cand))
    per_state = []
    for sid in states:
        srows = sorted([r for r in cand if r["state_id"] == sid], key=lambda r: -r["kinematic_score"])
        kin = [r["kinematic_score"] for r in srows]
        eff_cons = [r["mean_confirm_delta_conservative"] for r in srows]
        rho, p = spearmanr(kin, eff_cons)
        n = len(srows)
        q = n // 4
        by_kin_desc = srows
        top_q = by_kin_desc[:q]; bot_q = by_kin_desc[-q:]
        top_q_mean = float(np.mean([r["mean_confirm_delta_conservative"] for r in top_q]))
        bot_q_mean = float(np.mean([r["mean_confirm_delta_conservative"] for r in bot_q]))
        by_effect_desc = sorted(srows, key=lambda r: -r["mean_confirm_delta_conservative"])
        true_best = by_effect_desc[0]
        rank_of_best_in_kin = next(i for i, r in enumerate(by_kin_desc) if r["candidate"] == true_best["candidate"])
        true_top3 = set(r["candidate"] for r in by_effect_desc[:3])
        kin_top3 = set(r["candidate"] for r in by_kin_desc[:3])
        kin_top5 = set(r["candidate"] for r in by_kin_desc[:5])
        recall_top3_in_top3 = len(true_top3 & kin_top3) / 3
        recall_top3_in_top5 = len(true_top3 & kin_top5) / 3
        per_state.append(dict(state_id=sid, spearman_rho=rho, spearman_p=p,
                               top_quartile_mean_delta_conservative=top_q_mean,
                               bottom_quartile_mean_delta_conservative=bot_q_mean,
                               rank_of_true_best_in_kin_ranking=rank_of_best_in_kin,
                               recall_true_top3_in_predictor_top3=recall_top3_in_top3,
                               recall_true_top3_in_predictor_top5=recall_top3_in_top5))
    rhos = [r["spearman_rho"] for r in per_state if r["spearman_rho"] is not None]
    summary = dict(
        n_states=len(per_state), rho_median=float(np.median(rhos)) if rhos else None,
        rho_mean=float(np.mean(rhos)) if rhos else None,
        rho_ci90=state_clustered_bootstrap(rhos) if rhos else None,
        frac_states_rho_gt0=float(np.mean([r > 0 for r in rhos])) if rhos else None,
        mean_rank_of_true_best=float(np.mean([r["rank_of_true_best_in_kin_ranking"] for r in per_state])),
        mean_recall_top3_in_top3=float(np.mean([r["recall_true_top3_in_predictor_top3"] for r in per_state])),
        mean_recall_top3_in_top5=float(np.mean([r["recall_true_top3_in_predictor_top5"] for r in per_state])),
        mean_top_quartile_delta=float(np.mean([r["top_quartile_mean_delta_conservative"] for r in per_state])),
        mean_bottom_quartile_delta=float(np.mean([r["bottom_quartile_mean_delta_conservative"] for r in per_state])),
    )
    # pooled correlation for reference/context only (not the primary claim)
    all_kin = [r["kinematic_score"] for r in cand]
    all_eff = [r["mean_confirm_delta_conservative"] for r in cand]
    pooled_rho, pooled_p = spearmanr(all_kin, all_eff)
    summary["pooled_rho_CONTEXT_ONLY_not_primary"] = float(pooled_rho)
    return per_state, summary


def oracle_decomposition(cand):
    states = sorted(set(r["state_id"] for r in cand))
    rows = []
    for sid in states:
        srows = [r for r in cand if r["state_id"] == sid]
        n_streams = len(srows[0]["confirm_delta_conservative_all"])
        by_cand = {r["candidate"]: r for r in srows}

        random_median = float(np.median([r["mean_confirm_delta_conservative"] for r in srows]))
        kin_top = max(srows, key=lambda r: r["kinematic_score"])
        contact_oracle_top = max(srows, key=lambda r: r["mean_confirm_forced_contact"])
        effect_oracle_top = max(srows, key=lambda r: r["mean_confirm_delta_conservative"])
        search_best = max(srows, key=lambda r: r["mean_search_delta_conservative"])

        rows.append(dict(
            state_id=sid, n_streams=n_streams,
            random_median_delta_conservative=random_median,
            kinematic_top_candidate=kin_top["candidate"], kinematic_top_delta_conservative=kin_top["mean_confirm_delta_conservative"],
            contact_oracle_candidate=contact_oracle_top["candidate"], contact_oracle_delta_conservative=contact_oracle_top["mean_confirm_delta_conservative"],
            effect_oracle_candidate=effect_oracle_top["candidate"], effect_oracle_delta_conservative=effect_oracle_top["mean_confirm_delta_conservative"],
            search_best_candidate=search_best["candidate"], search_best_delta_conservative=search_best["mean_confirm_delta_conservative"],
        ))
    def col(k):
        return [r[k] for r in rows]
    summary = dict(
        n_states=len(rows),
        random_median_mean=float(np.mean(col("random_median_delta_conservative"))),
        random_median_ci90=state_clustered_bootstrap(col("random_median_delta_conservative")),
        kinematic_top_mean=float(np.mean(col("kinematic_top_delta_conservative"))),
        kinematic_top_ci90=state_clustered_bootstrap(col("kinematic_top_delta_conservative")),
        search_best_mean=float(np.mean(col("search_best_delta_conservative"))),
        search_best_ci90=state_clustered_bootstrap(col("search_best_delta_conservative")),
        contact_oracle_mean=float(np.mean(col("contact_oracle_delta_conservative"))),
        contact_oracle_ci90=state_clustered_bootstrap(col("contact_oracle_delta_conservative")),
        effect_oracle_mean=float(np.mean(col("effect_oracle_delta_conservative"))),
        effect_oracle_ci90=state_clustered_bootstrap(col("effect_oracle_delta_conservative")),
        frac_kinematic_top_eq_contact_oracle=float(np.mean([r["kinematic_top_candidate"] == r["contact_oracle_candidate"] for r in rows])),
        frac_kinematic_top_eq_effect_oracle=float(np.mean([r["kinematic_top_candidate"] == r["effect_oracle_candidate"] for r in rows])),
        frac_contact_oracle_eq_effect_oracle=float(np.mean([r["contact_oracle_candidate"] == r["effect_oracle_candidate"] for r in rows])),
    )
    return rows, summary


def incremental_value_analysis(cand):
    """Predeclared, non-ML: (1) within-state rank association stratified by
    direct-contact-at-t0 status; (2) simple rank regression of
    ΔJ_conservative on [direct_contact_t0, static_distance, kinematic_score]."""
    contact_rows = [r for r in cand if r["direct_contact_t0"] == 1]
    nocontact_rows = [r for r in cand if r["direct_contact_t0"] == 0]

    def strat_rho(rows):
        states = sorted(set(r["state_id"] for r in rows))
        rhos = []
        for sid in states:
            srows = [r for r in rows if r["state_id"] == sid]
            if len(srows) < 4:
                continue
            rho, _ = spearmanr([r["kinematic_score"] for r in srows], [r["mean_confirm_delta_conservative"] for r in srows])
            if rho is not None and not np.isnan(rho):
                rhos.append(rho)
        return rhos

    rhos_contact = strat_rho(contact_rows)
    rhos_nocontact = strat_rho(nocontact_rows)

    # simple rank regression: rank-transform each predictor and the outcome
    # WITHIN state, pool ranks across states, OLS with state fixed effects
    # approximated by within-state demeaning (a simple, predeclared,
    # non-ML analysis).
    states = sorted(set(r["state_id"] for r in cand))
    X_rows, y_rows = [], []
    for sid in states:
        srows = [r for r in cand if r["state_id"] == sid]
        n = len(srows)
        def rank(vals):
            order = np.argsort(np.argsort(vals))
            return (order - (n - 1) / 2) / n
        contact = rank([r["direct_contact_t0"] for r in srows])
        dist = rank([-r["static_t0_distance"] for r in srows])
        kin = rank([r["kinematic_score"] for r in srows])
        y = rank([r["mean_confirm_delta_conservative"] for r in srows])
        for i in range(n):
            X_rows.append([contact[i], dist[i], kin[i]])
            y_rows.append(y[i])
    X = np.array(X_rows); y = np.array(y_rows)
    X1 = np.hstack([np.ones((len(X), 1)), X])
    coef, *_ = np.linalg.lstsq(X1, y, rcond=None)

    # state-clustered SE via cluster bootstrap over states (resample states,
    # refit)
    boots = []
    for b in range(2000):
        idx = RNG_BOOT.choice(len(states), size=len(states), replace=True)
        Xb, yb = [], []
        for i in idx:
            sid = states[i]
            srows = [r for r in cand if r["state_id"] == sid]
            n = len(srows)
            def rank(vals):
                order = np.argsort(np.argsort(vals))
                return (order - (n - 1) / 2) / n
            contact = rank([r["direct_contact_t0"] for r in srows])
            dist = rank([-r["static_t0_distance"] for r in srows])
            kin = rank([r["kinematic_score"] for r in srows])
            y_ = rank([r["mean_confirm_delta_conservative"] for r in srows])
            for k in range(n):
                Xb.append([contact[k], dist[k], kin[k]])
                yb.append(y_[k])
        Xb = np.hstack([np.ones((len(Xb), 1)), np.array(Xb)])
        cb, *_ = np.linalg.lstsq(Xb, np.array(yb), rcond=None)
        boots.append(cb)
    boots = np.array(boots)
    ci = {name: (float(np.percentile(boots[:, i], 5)), float(np.percentile(boots[:, i], 95)))
          for i, name in enumerate(["intercept", "direct_contact_t0", "static_distance", "kinematic_score"])}

    return dict(
        n_contact_states_with_ge4=len(rhos_contact), n_nocontact_states_with_ge4=len(rhos_nocontact),
        rho_contact_at_t0=dict(mean=float(np.mean(rhos_contact)) if rhos_contact else None,
                                median=float(np.median(rhos_contact)) if rhos_contact else None),
        rho_no_contact_at_t0=dict(mean=float(np.mean(rhos_nocontact)) if rhos_nocontact else None,
                                   median=float(np.median(rhos_nocontact)) if rhos_nocontact else None),
        rank_regression_coef=dict(intercept=float(coef[0]), direct_contact_t0=float(coef[1]),
                                   static_distance=float(coef[2]), kinematic_score=float(coef[3])),
        rank_regression_coef_ci90_state_clustered=ci,
        n_rows=len(X), n_states=len(states),
    )


def k2_analysis(pairs):
    states = sorted(set(r["state_id"] for r in pairs))
    rows = []
    for sid in states:
        srows = [r for r in pairs if r["state_id"] == sid]
        top = next(r for r in srows if r["role"] == "top_predicted")
        low = next(r for r in srows if r["role"] == "low_predicted")
        randoms = [r for r in srows if r["role"] == "random"]
        rand_median = float(np.median([r["mean_delta_conservative"] for r in randoms]))
        rows.append(dict(state_id=sid, top_pair=top["S"], top_delta_conservative=top["mean_delta_conservative"],
                          low_pair=low["S"], low_delta_conservative=low["mean_delta_conservative"],
                          random_median_delta_conservative=rand_median, n_random=len(randoms),
                          top_minus_random_median=top["mean_delta_conservative"] - rand_median))
    diffs = [r["top_minus_random_median"] for r in rows]
    summary = dict(n_states=len(rows), top_minus_random_median_mean=float(np.mean(diffs)),
                   top_minus_random_median_ci90=state_clustered_bootstrap(diffs),
                   frac_states_top_beats_random_median=float(np.mean([d > 0 for d in diffs])),
                   top_pair_mean=float(np.mean([r["top_delta_conservative"] for r in rows])),
                   random_median_mean=float(np.mean([r["random_median_delta_conservative"] for r in rows])),
                   low_pair_mean=float(np.mean([r["low_delta_conservative"] for r in rows])))
    return rows, summary


def duration_analysis(dur):
    states = sorted(set(r["state_id"] for r in dur))
    rows = []
    for sid in states:
        srows = [r for r in dur if r["state_id"] == sid]
        top = next(r for r in srows if r["label"] == "top_kinematic")
        rand = next(r for r in srows if r["label"] == "matched_random")
        rows.append(dict(state_id=sid,
                          top_d8=top["d8_mean_delta_conservative"], top_d24=top["d24_mean_delta_conservative"],
                          top_d24_lost=top["d24_lost_dead_rate"], top_d24_vcons=top["d24_v_conservative_rate"],
                          rand_d8=rand["d8_mean_delta_conservative"], rand_d24=rand["d24_mean_delta_conservative"],
                          rand_d24_lost=rand["d24_lost_dead_rate"], rand_d24_vcons=rand["d24_v_conservative_rate"]))
    summary = dict(
        n_states=len(rows),
        top_d8_mean=float(np.mean([r["top_d8"] for r in rows])), top_d24_mean=float(np.mean([r["top_d24"] for r in rows])),
        rand_d8_mean=float(np.mean([r["rand_d8"] for r in rows])), rand_d24_mean=float(np.mean([r["rand_d24"] for r in rows])),
        top_lost_dead_rate_d24=float(np.mean([r["top_d24_lost"] for r in rows])),
        rand_lost_dead_rate_d24=float(np.mean([r["rand_d24_lost"] for r in rows])),
        top_v_conservative_rate_d24=float(np.mean([r["top_d24_vcons"] for r in rows])),
        rand_v_conservative_rate_d24=float(np.mean([r["rand_d24_vcons"] for r in rows])),
    )
    return rows, summary


def main():
    cand, roll, pairs, dur = load()
    lpred_rows, lpred_summary = l_pred_analysis(cand)
    rank_rows, rank_summary = predictor_ranking_analysis(cand)
    oracle_rows, oracle_summary = oracle_decomposition(cand)
    incr_summary = incremental_value_analysis(cand)
    k2_rows, k2_summary = k2_analysis(pairs)
    dur_rows, dur_summary = duration_analysis(dur)

    out = dict(
        n_candidate_rows=len(cand), n_rollout_rows=len(roll), n_pair_rows=len(pairs), n_duration_rows=len(dur),
        l_pred=dict(rows=lpred_rows, summary=lpred_summary),
        predictor_ranking=dict(rows=rank_rows, summary=rank_summary),
        oracle_decomposition=dict(rows=oracle_rows, summary=oracle_summary),
        incremental_value=incr_summary,
        k2_secondary=dict(rows=k2_rows, summary=k2_summary),
        duration_safety=dict(rows=dur_rows, summary=dur_summary),
    )
    json.dump(out, open(C.DATA_DIR / "analysis_612c.json", "w"), indent=1, default=str)
    print(json.dumps(dict(l_pred=lpred_summary, predictor_ranking=rank_summary, oracle_decomposition=oracle_summary,
                           incremental_value=incr_summary, k2_secondary=k2_summary, duration_safety=dur_summary),
                      indent=1, default=str))
    print("wrote", C.DATA_DIR / "analysis_612c.json")


if __name__ == "__main__":
    main()
