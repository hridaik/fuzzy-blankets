"""Figures R6.5-4, R6.5-5, R6.5-6. Follows the existing Agg-backend,
data-driven, PNG+PDF convention -- reads only from data/, never recomputes."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FIG_DIR = Path(__file__).resolve().parents[1] / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

REP_COLOR = {"M": "#55a868", "L": "#8172b2", "L_reg": "#4c72b0", "F": "#c44e52", "F_guard": "#dd8452"}


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def fig_r6_5_4():
    jitter = json.load(open(DATA_DIR / "jitter_analysis.json"))
    seeds = list(jitter.keys())
    fig, axes = plt.subplots(1, len(seeds), figsize=(3.2 * len(seeds), 3.5), sharey=True)
    for ax, seed in zip(axes, seeds):
        r = jitter[seed]
        D_X, T_I = np.array(r["D_X"]), np.array(r["T_I"])
        low_mask = D_X <= r["D_X_median"]
        colors = np.where((T_I > r["T_I_p90"]) & low_mask, "#c44e52", "#4c72b0")
        ax.scatter(D_X, T_I, c=colors, s=18, alpha=0.8)
        ax.axvline(r["D_X_median"], ls="--", c="gray", lw=0.7)
        ax.axhline(r["T_I_p90"], ls="--", c="gray", lw=0.7)
        ax.set_title(f"seed {seed}\ncorr={r['pearson_corr_DX_TI']:.2f}", fontsize=10)
        ax.set_xlabel(r"$D_X(t)$")
    axes[0].set_ylabel(r"$T_I(t)$")
    fig.suptitle("R6.5-4: detector jitter (red = large turnover during quiet physical state) vs. physical change")
    savefig(fig, "fig_r6_5_4_jitter_vs_physical_change")


def fig_r6_5_5():
    d = json.load(open(DATA_DIR / "closed_loop_stabilized.json"))
    reps = d["representations"]
    seeds = d["flocks"]

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    x = np.arange(len(seeds))
    width = 0.2
    metrics = [("nominal_p_success", "Nominal P(success)"),
               ("identity_valid_p_success", "Identity-valid P(success)"),
               ("mean_final_size", "Mean final size")]
    for ax, (key, label) in zip(axes, metrics):
        for k, rep in enumerate(reps):
            vals = [r["summary"][rep][key] for r in d["results"]]
            ax.bar(x + (k - 1.5) * width, vals, width, label=rep, color=REP_COLOR.get(rep, "gray"))
        ax.set_xticks(x)
        ax.set_xticklabels([str(s) for s in seeds])
        ax.set_xlabel("flock seed")
        ax.set_title(label)
    axes[0].legend(fontsize=8)
    fig.suptitle("R6.5-5: nominal vs. identity-valid success, and final size -- collapse vs. guarded")
    savefig(fig, "fig_r6_5_5_collapse_vs_guarded")


def fig_r6_5_6():
    d = json.load(open(DATA_DIR / "closed_loop_stabilized.json"))
    reps = d["representations"]
    seeds = d["flocks"]

    fig, axes = plt.subplots(2, len(seeds), figsize=(4.2 * len(seeds), 7), sharex=True)
    for col, row in enumerate(d["results"]):
        seed = row["seed"]
        ax = axes[0, col]
        for rep in reps:
            sizes = row["pathwise"][rep]["boundary_sizes"]
            ax.plot(range(len(sizes)), sizes, "o-", label=rep, color=REP_COLOR.get(rep, "gray"))
        ax.set_title(f"seed {seed}")
        ax.set_xlabel("checkpoint index")
        if col == 0:
            ax.set_ylabel(r"$|B_t|$")
            ax.legend(fontsize=8)

        ax = axes[1, col]
        for rep in reps:
            mean_leak = row["pathwise"][rep]["mean_leakage"]
            ax.bar(rep, mean_leak, color=REP_COLOR.get(rep, "gray"))
        ax.axhline(0.02, ls="--", c="gray", lw=0.8)
        ax.set_xlabel("representation")
        if col == 0:
            ax.set_ylabel(r"mean $L_t^{(1)}$ (nats)")
        ax.tick_params(axis="x", labelrotation=30)
    fig.suptitle(r"R6.5-6: boundary size (top) and pathwise leakage $L_t^{(1)}$ (bottom) after stabilization")
    savefig(fig, "fig_r6_5_6_pathwise_boundary_stabilized")


if __name__ == "__main__":
    fig_r6_5_4()
    print("wrote fig_r6_5_4")
    fig_r6_5_5()
    print("wrote fig_r6_5_5")
    fig_r6_5_6()
    print("wrote fig_r6_5_6")
