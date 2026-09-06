"""Figure R6.5-1. Follows the existing Agg-backend, data-driven, PNG+PDF
convention -- reads only from data/, never recomputes."""
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

CLASS_ORDER = ["included_shell", "omitted_shell", "non_shell_sample"]
CLASS_LABEL = {"included_shell": r"included shell ($\hat B$)",
               "omitted_shell": r"omitted shell ($B^D \setminus \hat B$)",
               "non_shell_sample": r"non-shell ($E^D$ sample)"}
CLASS_COLOR = {"included_shell": "#4c72b0", "omitted_shell": "#dd8452", "non_shell_sample": "#8172b2"}


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def fig_r6_5_1():
    d = json.load(open(DATA_DIR / "causal_redundancy.json"))
    seeds = d["seeds"]

    fig, axes = plt.subplots(2, len(seeds), figsize=(4.2 * len(seeds), 7.5), sharey="row")
    for col, seed in enumerate(seeds):
        res = d["results"][str(seed)]
        ax = axes[0, col]
        data = []
        for cls in CLASS_ORDER:
            samples = []
            for bird_res in res["perturbation"][cls].values():
                samples.extend(bird_res["D_do_joint_samples"])
            data.append(np.array(samples) + 1e-6)  # log-scale floor
        parts = ax.violinplot(data, showmedians=True, showextrema=True)
        for i, pc in enumerate(parts["bodies"]):
            pc.set_facecolor(CLASS_COLOR[CLASS_ORDER[i]])
            pc.set_alpha(0.7)
        ax.set_yscale("log")
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels(["included\nshell", "omitted\nshell", "non-shell\n(sample)"], fontsize=8)
        ax.set_title(f"seed {seed}")
        if col == 0:
            ax.set_ylabel(r"$D_j^{\rm do}$ (nats, log scale)")

        ax = axes[1, col]
        classes = ["included_shell", "omitted_shell", "non_shell_sample"]
        shift_means = []
        for cls in classes:
            shift = res["delta_shift_by_class"].get(cls, {})
            vals = [v["B_hat"] for v in shift.values()]
            shift_means.append(np.mean(vals) if vals else 0.0)
        ax.bar(range(3), shift_means, color=[CLASS_COLOR[c] for c in classes])
        ax.axhline(0, color="gray", lw=0.8)
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(["included\nshell", "omitted\nshell", "non-shell\n(sample)"], fontsize=8)
        if col == 0:
            ax.set_ylabel(r"mean $\Delta_{\rm shift}(\hat B)$ (nats)")

    fig.suptitle(r"R6.5-1: interventional effect $D_j^{\rm do}$ (top) and predictive-loss shift under"
                 "\nintervention, " r"$\Delta_{\rm shift}(\hat B)$ (bottom), by exterior class")
    savefig(fig, "fig_r6_5_1_causal_redundancy")


if __name__ == "__main__":
    fig_r6_5_1()
    print("wrote fig_r6_5_1")
