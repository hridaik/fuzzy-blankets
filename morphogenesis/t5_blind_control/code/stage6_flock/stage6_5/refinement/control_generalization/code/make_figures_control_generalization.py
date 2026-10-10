"""Figures R6.5-2, R6.5-3. Follows the existing Agg-backend, data-driven,
PNG+PDF convention -- reads only from data/, never recomputes."""
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

ARM_COLOR = {"oracle": "#55a868", "inferred": "#4c72b0", "fiedler": "#c44e52", "random_matched": "#8172b2"}


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def fig_r6_5_2():
    d = json.load(open(DATA_DIR / "four_controller_comparison.json"))
    agg = json.load(open(DATA_DIR / "aggregate_summary.json"))
    rows = d["rows"]
    seeds = [r["seed"] for r in rows]
    arms = ["oracle", "inferred", "fiedler", "random_matched"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    ax = axes[0]
    x = np.arange(len(seeds))
    width = 0.2
    for k, arm in enumerate(arms):
        p = [r[arm]["p_success"] for r in rows]
        ax.bar(x + (k - 1.5) * width, p, width, label=arm, color=ARM_COLOR[arm])
    ax.set_xticks(x)
    ax.set_xticklabels([str(s) for s in seeds], fontsize=8)
    ax.set_xlabel("discriminating flock seed")
    ax.set_ylabel("P(success)")
    ax.axhline(0.7, ls="--", c="gray", lw=0.8)
    ax.set_title("Per-flock controller success, 12 discriminating flocks")
    ax.legend(fontsize=8)

    ax = axes[1]
    deltas = agg["summary"]["per_flock_delta"]
    seed_ids = sorted(deltas, key=lambda s: deltas[s])
    vals = [deltas[s] for s in seed_ids]
    colors = ["#55a868" if v > 0 else "#c44e52" if v < 0 else "#8172b2" for v in vals]
    ax.barh(range(len(seed_ids)), vals, color=colors)
    ax.set_yticks(range(len(seed_ids)))
    ax.set_yticklabels(seed_ids, fontsize=9)
    ax.tick_params(axis="y", which="both", length=0)
    ax.set_ylim(-0.7, len(seed_ids) - 0.3)
    ax.axvline(0, color="black", lw=0.8)
    ci = agg["summary"]["bootstrap"]
    ax.axvline(ci["mean"], color="#4c72b0", lw=1.5, label=f"mean={ci['mean']:.3f}")
    ax.axvspan(ci["ci_lo"], ci["ci_hi"], color="#4c72b0", alpha=0.15,
               label=f"95% CI [{ci['ci_lo']:.3f}, {ci['ci_hi']:.3f}]")
    ax.set_xlabel(r"$\Delta_s^{(f)} = P_{\hat B} - P_{\rm random}$")
    ax.set_title("Flock-level paired effect (bootstrap over flocks)")
    ax.legend(fontsize=8)
    savefig(fig, "fig_r6_5_2_control_generalization")


def fig_r6_5_3():
    d = json.load(open(DATA_DIR / "aggregate_summary.json"))
    q = d["quality_vs_control"]["raw"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    panels = [("recall", "recall(B_hat)"), ("excess_loss", r"$\Delta\ell(\hat B)$ (nats)"),
              ("actuator_budget", r"actuator budget $|\hat B|$")]
    for ax, (key, label) in zip(axes, panels):
        ax.scatter(q[key], q["p_success"], c="#4c72b0")
        for x, y, s in zip(q[key], q["p_success"], q["seed"]):
            ax.annotate(str(s), (x, y), fontsize=7, alpha=0.7)
        ax.set_xlabel(label)
        ax.set_ylabel("P(success), inferred controller")
        ax.set_ylim(-0.05, 1.05)
    fig.suptitle("R6.5-3 (exploratory): inference quality vs. control success, 12 discriminating flocks")
    savefig(fig, "fig_r6_5_3_inference_quality_vs_control")


if __name__ == "__main__":
    fig_r6_5_2()
    print("wrote fig_r6_5_2")
    fig_r6_5_3()
    print("wrote fig_r6_5_3")
