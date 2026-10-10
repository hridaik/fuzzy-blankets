"""V2 comparison figures."""
from __future__ import annotations

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_v2 import V2_DIR

FIG_DIR = V2_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def main():
    data = json.load(open(V2_DIR / "data" / "replication_results.json"))
    flocks = [f for f in data["flocks"] if "rules" in f]
    seeds = [f["seed"] for f in flocks]
    rule_names = ["A_degree", "B_leverage", "C_patch", "D_random", "reference_full_shell", "reference_baseline"]
    colors = {"A_degree": "#4c72b0", "B_leverage": "#55a868", "C_patch": "#c44e52",
              "D_random": "#8172b2", "reference_full_shell": "#333333", "reference_baseline": "#dddddd"}

    # Figure: grouped bar of P(success) per flock per rule
    fig, ax = plt.subplots(figsize=(13, 5.5))
    x = np.arange(len(seeds))
    w = 0.14
    for i, rn in enumerate(rule_names):
        vals = [f["rules"][rn]["p_success"] for f in flocks]
        ax.bar(x + (i - 2.5) * w, vals, width=w, label=rn, color=colors[rn])
    ax.axhline(0.5, ls="--", c="gray", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"seed {s}" for s in seeds])
    ax.set_ylabel("P(success)  H*(t0+Tu)>=0.8")
    ax.set_title("V2 replication: P(success) by rule, across 10 independently emergent flocks\n"
                  "(k = ceil(0.75 x |B^D_0|), frozen from the canonical-flock mechanism audit)")
    ax.legend(fontsize=8, ncol=3, loc="lower left")
    ax.set_ylim(0, 1.08)
    savefig(fig, "v2_fig1_rule_comparison")

    # Figure: mean across flocks, per rule, with per-flock scatter
    fig, ax = plt.subplots(figsize=(8, 5.5))
    means = []
    for i, rn in enumerate(rule_names[:-1]):
        vals = [f["rules"][rn]["p_success"] for f in flocks]
        means.append(np.mean(vals))
        ax.scatter([i] * len(vals), vals, color=colors[rn], alpha=0.6, zorder=3)
        ax.scatter([i], [np.mean(vals)], color="black", marker="_", s=400, zorder=4)
    ax.set_xticks(range(len(rule_names) - 1))
    ax.set_xticklabels(rule_names[:-1], rotation=15)
    ax.set_ylabel("P(success) per flock (dots), mean (black bar)")
    ax.set_title("V2: actuator-selection rule comparison across 10 flocks")
    ax.set_ylim(0, 1.08)
    savefig(fig, "v2_fig2_rule_means")

    print("V2 figures written to", FIG_DIR)


if __name__ == "__main__":
    main()
