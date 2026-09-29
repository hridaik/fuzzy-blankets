"""Stage 6.12C visualizations (static matplotlib PNGs, same convention as
stage6_12B_contact_persistence/code/viz_612b.py): per-state candidate
landscape, predictor-vs-held-out-effect scatter (pooled + per-state),
oracle-decomposition bar chart, K=2 pair comparison, duration-safety
paired comparison, state views.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612c as C           # noqa: E402


def plot_state_view(state, out_path):
    r0 = np.array(state["r0"])
    interior = state["interior0"]; pool = state["pool20"]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(r0[:, 0], r0[:, 1], s=8, color="lightgrey", label="all birds")
    ax.scatter(r0[pool, 0], r0[pool, 1], s=22, color="tab:orange", label="nearest-20 exterior pool")
    ax.scatter(r0[interior, 0], r0[interior, 1], s=22, color="tab:blue", label="material target")
    ax.set_title(f"Stage 6.12C state view -- {state['state_id']}\n"
                 f"t0={state['t0']}, |target|={len(interior)}, h*={state['h_star']}")
    ax.set_xlim(0, C.L_BOX); ax.set_ylim(0, C.L_BOX); ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_candidate_landscape(state, cand_rows, oracle_row, out_path):
    r0 = np.array(state["r0"])
    srows = sorted(cand_rows, key=lambda r: -r["kinematic_score"])
    cands = [r["candidate"] for r in srows]
    kin = [r["kinematic_score"] for r in srows]
    eff = [r["mean_confirm_delta_conservative"] for r in srows]
    contact = [r["mean_confirm_forced_contact"] for r in srows]
    dist = [r["static_t0_distance"] for r in srows]

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    x = np.arange(len(cands))
    ax = axes[0, 0]
    ax.bar(x, kin, color="tab:blue")
    ax.set_xticks(x); ax.set_xticklabels(cands, fontsize=6, rotation=90)
    ax.set_ylabel("C_hat_kin (frozen, window=8, R=mf.R)")
    ax.set_title("Kinematic predicted contact, ranked")

    ax = axes[0, 1]
    colors = ["tab:red" if v < 0 else "tab:green" for v in eff]
    ax.bar(x, eff, color=colors)
    ax.set_xticks(x); ax.set_xticklabels(cands, fontsize=6, rotation=90)
    ax.set_ylabel("mean confirmatory ΔJ_conservative")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_title("Realized paired effect (held out, same candidate order as top-left)")

    ax = axes[1, 0]
    ax.bar(x, contact, color="tab:purple")
    ax.set_xticks(x); ax.set_xticklabels(cands, fontsize=6, rotation=90)
    ax.set_ylabel("mean forced-actual contact edges (confirm streams)")
    ax.set_title("Forced-future contact oracle ingredient")

    ax = axes[1, 1]
    ax.scatter(kin, eff, s=30, color="tab:blue")
    for label, role, color in [("predictor-top", "kinematic", "tab:orange"),
                                ("contact-oracle", "contact", "tab:purple"),
                                ("effect-oracle", "effect", "tab:red")]:
        pass
    if oracle_row:
        highlight = {
            "predictor-top": oracle_row.get("kinematic_top_candidate"),
            "contact-oracle": oracle_row.get("contact_oracle_candidate"),
            "effect-oracle": oracle_row.get("effect_oracle_candidate"),
            "search-best": oracle_row.get("search_best_candidate"),
        }
        colors = dict(zip(highlight, ["tab:orange", "tab:purple", "tab:red", "tab:green"]))
        for name, cid in highlight.items():
            if cid is None:
                continue
            row = next((r for r in srows if r["candidate"] == cid), None)
            if row:
                ax.scatter([row["kinematic_score"]], [row["mean_confirm_delta_conservative"]],
                           s=140, facecolors="none", edgecolors=colors[name], linewidths=2, label=name)
    rho, _ = spearmanr(kin, eff)
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_xlabel("C_hat_kin"); ax.set_ylabel("mean confirmatory ΔJ_conservative")
    ax.set_title(f"Rank view, this state: Spearman ρ={rho:.3f}" if rho is not None else "n/a")
    ax.legend(fontsize=7, loc="best")

    fig.suptitle(f"Stage 6.12C candidate landscape -- {state['state_id']} (K=1, d=8, 8 confirmatory streams)")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_pooled_predictor_scatter(cand, out_path):
    kin = [r["kinematic_score"] for r in cand]
    eff = [r["mean_confirm_delta_conservative"] for r in cand]
    rho, _ = spearmanr(kin, eff)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(kin, eff, s=14, alpha=0.4, color="tab:blue")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_xlabel("C_hat_kin (frozen kinematic predictor, window=8, R=mf.R)")
    ax.set_ylabel("mean confirmatory ΔJ_conservative")
    ax.set_title(f"Stage 6.12C K=1 primary: pooled predictor vs. held-out effect\n"
                 f"(CONTEXT ONLY, not the primary claim -- n={len(cand)} candidate-rows, 10 states; "
                 f"pooled Spearman ρ={rho:.3f})")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_state_rho_distribution(rank_rows, out_path):
    rhos = [r["spearman_rho"] for r in rank_rows if r["spearman_rho"] is not None]
    sids = [r["state_id"] for r in rank_rows if r["spearman_rho"] is not None]
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["tab:green" if r > 0 else "tab:red" for r in rhos]
    ax.bar(range(len(rhos)), rhos, color=colors)
    ax.set_xticks(range(len(sids))); ax.set_xticklabels(sids, fontsize=7, rotation=45, ha="right")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_ylabel("state-level Spearman ρ (C_hat_kin vs. held-out ΔJ_conservative)")
    ax.set_title("Stage 6.12C: per-state predictor-ranking correlation (K=1, d=8 primary cell)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_oracle_decomposition(oracle_summary, out_path):
    labels = ["random\n(median)", "kinematic\n(deployable)", "search-best\n(reproducibility)",
              "contact oracle\n(non-deployable)", "effect oracle\n(non-deployable)"]
    means = [oracle_summary["random_median_mean"], oracle_summary["kinematic_top_mean"],
             oracle_summary["search_best_mean"], oracle_summary["contact_oracle_mean"],
             oracle_summary["effect_oracle_mean"]]
    cis = [oracle_summary["random_median_ci90"], oracle_summary["kinematic_top_ci90"],
           oracle_summary["search_best_ci90"], oracle_summary["contact_oracle_ci90"],
           oracle_summary["effect_oracle_ci90"]]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(labels))
    yerr_lo = [m - c[0] for m, c in zip(means, cis)]
    yerr_hi = [c[1] - m for m, c in zip(means, cis)]
    colors = ["tab:grey", "tab:blue", "tab:cyan", "tab:purple", "tab:red"]
    ax.bar(x, means, yerr=[yerr_lo, yerr_hi], capsize=4, color=colors)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_ylabel("mean confirmatory ΔJ_conservative (state-clustered, 90% CI)")
    ax.set_title("Stage 6.12C oracle decomposition: random vs. deployable vs. non-deployable upper bounds\n"
                 "(10 confirmatory states, K=1, d=8)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_k2_comparison(k2_rows, out_path):
    sids = [r["state_id"] for r in k2_rows]
    top = [r["top_delta_conservative"] for r in k2_rows]
    rand = [r["random_median_delta_conservative"] for r in k2_rows]
    low = [r["low_delta_conservative"] for r in k2_rows]
    x = np.arange(len(sids)); w = 0.25
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(x - w, top, width=w, label="top-predicted pair", color="tab:blue")
    ax.bar(x, rand, width=w, label="random pairs (median of 24)", color="tab:grey")
    ax.bar(x + w, low, width=w, label="low-predicted pair", color="tab:red")
    ax.set_xticks(x); ax.set_xticklabels(sids, fontsize=7, rotation=45, ha="right")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_ylabel("mean ΔJ_conservative (6 confirmatory streams)")
    ax.set_title("Stage 6.12C K=2 secondary: top-predicted vs. random vs. low-predicted pairs")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_duration_safety(dur_rows, out_path):
    sids = [r["state_id"] for r in dur_rows]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    x = np.arange(len(sids)); w = 0.2
    ax.bar(x - 1.5 * w, [r["top_d8"] for r in dur_rows], width=w, label="top-kin, d=8", color="tab:blue")
    ax.bar(x - 0.5 * w, [r["top_d24"] for r in dur_rows], width=w, label="top-kin, d=24", color="tab:cyan")
    ax.bar(x + 0.5 * w, [r["rand_d8"] for r in dur_rows], width=w, label="random, d=8", color="tab:red")
    ax.bar(x + 1.5 * w, [r["rand_d24"] for r in dur_rows], width=w, label="random, d=24", color="tab:orange")
    ax.set_xticks(x); ax.set_xticklabels(sids, fontsize=7, rotation=45, ha="right")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_ylabel("mean ΔJ_conservative (6 paired streams)")
    ax.set_title("Duration safety: paired ΔJ, d=8 vs d=24")
    ax.legend(fontsize=7)
    ax = axes[1]
    ax.bar(x - w / 2, [r["top_d24_lost"] for r in dur_rows], width=w, label="top-kin lost/dead @ d=24", color="tab:blue")
    ax.bar(x + w / 2, [r["rand_d24_lost"] for r in dur_rows], width=w, label="random lost/dead @ d=24", color="tab:red")
    ax.set_xticks(x); ax.set_xticklabels(sids, fontsize=7, rotation=45, ha="right")
    ax.set_ylabel("fraction of 6 streams with lost_dead event")
    ax.set_title("Duration safety: target-loss rate at d=24")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def main():
    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.load(open(C.DATA_DIR / "state_manifest_612c.json"))
    for state in manifest["states"]:
        plot_state_view(state, C.FIG_DIR / f"state_view_{state['state_id']}.png")

    cand_path = C.DATA_DIR / "k1_candidates_612c.json"
    an_path = C.DATA_DIR / "analysis_612c.json"
    if cand_path.exists() and an_path.exists():
        cand = json.load(open(cand_path))
        an = json.load(open(an_path))
        oracle_rows = an["oracle_decomposition"]["rows"]
        oracle_by_state = {r["state_id"]: r for r in oracle_rows}
        for state in manifest["states"]:
            srows = [r for r in cand if r["state_id"] == state["state_id"]]
            if srows:
                plot_candidate_landscape(state, srows, oracle_by_state.get(state["state_id"]),
                                          C.FIG_DIR / f"candidate_landscape_{state['state_id']}.png")
        plot_pooled_predictor_scatter(cand, C.FIG_DIR / "pooled_predictor_scatter.png")
        plot_state_rho_distribution(an["predictor_ranking"]["rows"], C.FIG_DIR / "state_rho_distribution.png")
        plot_oracle_decomposition(an["oracle_decomposition"]["summary"], C.FIG_DIR / "oracle_decomposition.png")
        if an["k2_secondary"]["rows"]:
            plot_k2_comparison(an["k2_secondary"]["rows"], C.FIG_DIR / "k2_pair_comparison.png")
        if an["duration_safety"]["rows"]:
            plot_duration_safety(an["duration_safety"]["rows"], C.FIG_DIR / "duration_safety.png")

    print("wrote figures to", C.FIG_DIR)


if __name__ == "__main__":
    main()
