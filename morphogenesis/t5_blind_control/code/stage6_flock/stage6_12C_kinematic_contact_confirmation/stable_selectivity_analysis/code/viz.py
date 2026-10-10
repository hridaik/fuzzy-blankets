"""Figures for the stable-selectivity follow-up. Reads
stable_selectivity_results.json (written by analysis.py) plus the raw
candidate JSON, matches the plotting style of
stage6_12C_kinematic_contact_confirmation/figures/ (plain matplotlib, no
seaborn, one PNG per state per plot type, plus pooled summary plots)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
SSA_DIR = HERE.parent
S612C_DIR = SSA_DIR.parent
DATA_612C = S612C_DIR / "data"
OUT_DATA = SSA_DIR / "data"
OUT_FIG = SSA_DIR / "figures"

CAND = json.load(open(DATA_612C / "k1_candidates_612c.json"))
RES = json.load(open(OUT_DATA / "stable_selectivity_results.json"))
STATES = sorted(set(r["state_id"] for r in CAND))
RNG = np.random.default_rng(777_222_333)


def full_matrix(sid):
    srows = sorted([r for r in CAND if r["state_id"] == sid], key=lambda r: r["candidate"])
    cands = [r["candidate"] for r in srows]
    Xs = np.array([r["search_delta_conservative_all"] for r in srows])
    Xc = np.array([r["confirm_delta_conservative_all"] for r in srows])
    return cands, np.hstack([Xs, Xc])


def short(sid):
    return sid.replace("s612c_", "").replace("_seed", " seed=")


def fig_heatmap(sid):
    cands, X = full_matrix(sid)
    means = X.mean(axis=1)
    order = np.argsort(-means)
    Xs = X[order]
    cands_s = np.array(cands)[order]
    fig, ax = plt.subplots(figsize=(7, 8))
    vmax = np.abs(X).max() or 1e-6
    im = ax.imshow(Xs, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_yticks(range(len(cands_s)))
    ax.set_yticklabels(cands_s, fontsize=6)
    ax.set_xticks(range(X.shape[1]))
    labels = [f"s{i}" for i in range(4)] + [f"c{i}" for i in range(8)]
    ax.set_xticklabels(labels, fontsize=7, rotation=45)
    ax.set_xlabel("physics stream (s=search, c=confirm)")
    ax.set_ylabel("candidate (rows sorted ONCE by overall mean, descending)")
    ax.set_title(f"{short(sid)} - candidate x stream ΔJ_conservative")
    plt.colorbar(im, ax=ax, label="ΔJ_conservative")
    plt.tight_layout()
    plt.savefig(OUT_FIG / f"heatmap_{sid}.png", dpi=130)
    plt.close(fig)


def fig_mean_uncertainty(sid):
    cands, X = full_matrix(sid)
    means = X.mean(axis=1)
    se = X.std(axis=1, ddof=1) / np.sqrt(X.shape[1])
    order = np.argsort(-means)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    xs = np.arange(len(cands))
    ax.errorbar(xs, means[order], yerr=1.96 * se[order], fmt="o", ms=3, capsize=2, color="#2b6cb0")
    ax.axhline(0, color="gray", lw=0.8, ls="--")
    ax.set_xlabel("candidate (sorted by mean ΔJ_conservative, descending)")
    ax.set_ylabel("mean ΔJ_conservative ± 95% CI (across 12 streams)")
    ax.set_title(f"{short(sid)} - actuator mean effect with uncertainty")
    plt.tight_layout()
    plt.savefig(OUT_FIG / f"mean_uncertainty_{sid}.png", dpi=130)
    plt.close(fig)


def fig_winner_recurrence(sid):
    cands, X = full_matrix(sid)
    cands = np.array(cands)
    winners = cands[np.argmax(X, axis=0)]
    vals, counts = np.unique(winners, return_counts=True)
    order = np.argsort(-counts)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(range(len(vals)), counts[order], color="#805ad5")
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(vals[order], rotation=90, fontsize=7)
    ax.set_xlabel("candidate (only candidates that won >=1 stream)")
    ax.set_ylabel(f"# streams won (out of {X.shape[1]})")
    ax.set_title(f"{short(sid)} - per-stream winner recurrence")
    plt.tight_layout()
    plt.savefig(OUT_FIG / f"winner_recurrence_{sid}.png", dpi=130)
    plt.close(fig)


def fig_train_test_stability(sid, m=6):
    cands, X = full_matrix(sid)
    R = X.shape[1]
    perm = RNG.permutation(R)
    train_idx, test_idx = perm[:m], perm[m:]
    train_mean = X[:, train_idx].mean(axis=1)
    test_mean = X[:, test_idx].mean(axis=1)
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.scatter(train_mean, test_mean, s=18, color="#dd6b20")
    lo = min(train_mean.min(), test_mean.min())
    hi = max(train_mean.max(), test_mean.max())
    ax.plot([lo, hi], [lo, hi], color="gray", ls="--", lw=0.8)
    ax.axhline(0, color="gray", lw=0.5)
    ax.axvline(0, color="gray", lw=0.5)
    from scipy.stats import spearmanr
    rho, _ = spearmanr(train_mean, test_mean)
    ax.set_xlabel(f"mean ΔJ_conservative, {m} TRAIN streams")
    ax.set_ylabel(f"mean ΔJ_conservative, {R - m} TEST streams")
    ax.set_title(f"{short(sid)} - train/test ranking stability (ρ={rho:.2f}, one split)")
    plt.tight_layout()
    plt.savefig(OUT_FIG / f"train_test_stability_{sid}.png", dpi=130)
    plt.close(fig)


def fig_oracle_comparison(sid):
    o = RES["three_oracles"]["full_12stream"]["per_state"][sid]
    perm = RES["permutation_null"]["full_12stream"]["per_state"][sid]
    labels = ["random\n/median", "per-stream\nclairvoyant (A)", "state-stable\nmean (B)", "CV-stable\n(C)"]
    vals = [o["random_median"], o["A_per_stream_clairvoyant_oracle"], o["B_state_stable_mean_oracle"], o["C_cross_validated_stable_oracle"]]
    null_means = [perm["null_median"]["mean"], perm["null_A"]["mean"], perm["null_B"]["mean"], perm["null_C"]["mean"]]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    xs = np.arange(len(labels))
    ax.bar(xs - 0.18, vals, width=0.36, label="observed", color="#2f855a")
    ax.bar(xs + 0.18, null_means, width=0.36, label="permutation-null mean\n(no stable identity)", color="#a0aec0")
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("mean ΔJ_conservative")
    ax.set_title(f"{short(sid)} - oracle comparison: observed vs. no-stable-identity null")
    ax.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(OUT_FIG / f"oracle_comparison_{sid}.png", dpi=130)
    plt.close(fig)


def fig_aggregate_oracle_comparison():
    agg = RES["three_oracles"]["full_12stream"]["aggregate"]
    perm_agg = RES["permutation_null"]["full_12stream"]["aggregate"]
    labels = ["random\n/median", "per-stream\nclairvoyant (A)", "state-stable\nmean (B)", "CV-stable\n(C)"]
    vals = [agg["mean_random_median"], agg["mean_A_per_stream_clairvoyant"], agg["mean_B_state_stable_mean"], agg["mean_C_cv_stable"]]
    nulls = [None, perm_agg["mean_null_A"], perm_agg["mean_null_B"], perm_agg["mean_null_C"]]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    xs = np.arange(len(labels))
    ax.bar(xs - 0.18, vals, width=0.36, color="#2f855a", label="observed (mean across 10 states)")
    ax.bar(xs + 0.18, [n if n is not None else 0 for n in nulls], width=0.36, color="#a0aec0",
           label="permutation-null mean")
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_ylabel("mean ΔJ_conservative (pooled across 10 states)")
    ax.set_title("Aggregate oracle comparison: observed vs. no-stable-actuator-identity null")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT_FIG / "aggregate_oracle_comparison.png", dpi=140)
    plt.close(fig)


def fig_var_actuator_frac_by_state():
    vd = RES["variance_decomposition"]["full_12stream"]["per_state"]
    sids = STATES
    fracs = [vd[s]["var_actuator_frac"] for s in sids]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(range(len(sids)), fracs, color="#3182ce")
    ax.set_xticks(range(len(sids)))
    ax.set_xticklabels([short(s) for s in sids], rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("Var_actuator / Var_total (method-of-moments, clipped >=0)")
    ax.set_title("Stable-actuator variance fraction by state (12-stream)")
    plt.tight_layout()
    plt.savefig(OUT_FIG / "var_actuator_frac_by_state.png", dpi=140)
    plt.close(fig)


def fig_reliability_curve():
    agg = RES["reliability"]["aggregate"]
    ms = sorted(int(k) for k in agg.keys())
    spear = [agg[str(m)]["mean_spearman_across_states"] for m in ms]
    pear = [agg[str(m)]["mean_pearson_across_states"] for m in ms]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(ms, spear, "o-", label="mean Spearman ρ (train vs test candidate means)", color="#c53030")
    ax.plot(ms, pear, "s--", label="mean Pearson r", color="#2b6cb0")
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_xlabel("# training streams (m)")
    ax.set_ylabel("train-vs-test ranking correlation (mean across states)")
    ax.set_title("Sample-efficiency curve: does ranking reliability improve with more streams?")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT_FIG / "reliability_sample_efficiency_curve.png", dpi=140)
    plt.close(fig)


def main():
    for sid in STATES:
        fig_heatmap(sid)
        fig_mean_uncertainty(sid)
        fig_winner_recurrence(sid)
        fig_train_test_stability(sid)
        fig_oracle_comparison(sid)
    fig_aggregate_oracle_comparison()
    fig_var_actuator_frac_by_state()
    fig_reliability_curve()
    print("wrote figures to", OUT_FIG)


if __name__ == "__main__":
    main()
