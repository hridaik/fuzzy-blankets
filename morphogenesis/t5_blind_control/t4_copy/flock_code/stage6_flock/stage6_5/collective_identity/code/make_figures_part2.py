"""Figures 6.5D-G. Same Agg-backend, data-driven, PNG+PDF convention as the
rest of this project -- reads only from data/."""
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
REP_COLORS = {"M": "#4c72b0", "L": "#dd8452", "F": "#55a868"}
REP_LABELS = {"M": r"$I^M$ (material)", "L": r"$I^L$ (lineage)", "F": r"$I^F$ (functional)"}


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def fig_6_5d():
    """Three definitions of the same collective, over time, on one
    representative flock/replicate -- selected timesteps, not a movie."""
    d = json.load(open(DATA_DIR / "identity_evaluation.json"))
    flock = next(r for r in d["results"] if r["flock_seed"] == 2)
    ep = flock["episodes"][0]
    t_show = [0, 5, 10, 20, 30, 40]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for rep in ("M", "L", "F"):
        sizes = ep["per_representation"][rep]["size_series"]
        r0 = ep["per_representation"][rep]["R0_series"]
        t = list(range(len(sizes)))
        ax.plot(t, sizes, "-", color=REP_COLORS[rep], label=f"{REP_LABELS[rep]} size")
    ax.axvline(20, ls="--", c="gray", lw=0.8, label=r"$t_0+T_u$ (release)")
    ax.set_xlabel("t (steps into episode)")
    ax.set_ylabel(r"$|I_t^r|$")
    ax.set_title("Flock 2, replicate 0: collective size under three definitions")
    ax.legend(fontsize=8)
    savefig(fig, "fig_6_5d_three_definitions_over_time")


def fig_6_5e():
    """Membership and boundary turnover: |I_t|, R0(t), |B_t|, |B_t triangle B_{t-1}|."""
    d = json.load(open(DATA_DIR / "identity_evaluation.json"))
    flock = next(r for r in d["results"] if r["flock_seed"] == 2)
    ep = flock["episodes"][0]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for rep in ("M", "L", "F"):
        pm = ep["per_representation"][rep]
        t = list(range(len(pm["size_series"])))
        axes[0, 0].plot(t, pm["size_series"], color=REP_COLORS[rep], label=REP_LABELS[rep])
        axes[0, 1].plot(t, pm["R0_series"], color=REP_COLORS[rep])
        axes[1, 0].plot(t, pm["boundary_size_series"], color=REP_COLORS[rep])
        axes[1, 1].plot(t, pm["boundary_turnover_series"], color=REP_COLORS[rep])
    axes[0, 0].set_ylabel(r"$|I_t|$")
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].set_ylabel(r"$R_0(t)$")
    axes[1, 0].set_ylabel(r"$|B_t^{D,r}|$")
    axes[1, 0].set_xlabel("t")
    axes[1, 1].set_ylabel(r"$|B_t \triangle B_{t-1}|$")
    axes[1, 1].set_xlabel("t")
    savefig(fig, "fig_6_5e_membership_boundary_turnover")


def fig_6_5f():
    """Representation changes the control assessment: success / retention /
    coherence / persistence, aggregated over dev-flock replicates, per
    representation -- highlighting disagreements."""
    d = json.load(open(DATA_DIR / "identity_evaluation.json"))
    reps = ("M", "L", "F")
    flocks = [r["flock_seed"] for r in d["results"]]

    metrics = {"success": [], "persistence": [], "final_R0": [], "min_coherence": []}
    for r in d["results"]:
        for rep in reps:
            eps = [e["per_representation"][rep] for e in r["episodes"]]
            metrics["success"].append(np.mean([e["success"] for e in eps]))
            metrics["persistence"].append(np.mean([e["persistence"] for e in eps]))
            metrics["final_R0"].append(np.mean([e["final_R0"] for e in eps]))
            metrics["min_coherence"].append(np.mean([e["min_coherence"] for e in eps]))

    fig, axes = plt.subplots(1, 4, figsize=(15, 4))
    x = np.arange(len(flocks))
    width = 0.25
    titles = ["P(success)", "P(persistence)", r"final $R_0$", "mean min coherence"]
    for ax, key, title in zip(axes, metrics, titles):
        vals = np.array(metrics[key]).reshape(len(flocks), len(reps))
        for k, rep in enumerate(reps):
            ax.bar(x + (k - 1) * width, vals[:, k], width, color=REP_COLORS[rep], label=REP_LABELS[rep])
        ax.set_xticks(x)
        ax.set_xticklabels([str(s) for s in flocks])
        ax.set_xlabel("flock seed")
        ax.set_title(title)
    axes[0].legend(fontsize=7)
    savefig(fig, "fig_6_5f_representation_changes_assessment")


def fig_6_5g():
    """Adaptive-control proof of concept: fixed-material vs. lineage-adaptive
    vs. functional-adaptive control."""
    d = json.load(open(DATA_DIR / "adaptive_control.json"))
    reps = d["representations"]
    flocks = [r["flock_seed"] for r in d["results"]]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    x = np.arange(len(flocks))
    width = 0.25
    for k, rep in enumerate(reps):
        succ = [r["per_representation"][rep]["p_success"] for r in d["results"]]
        succ_ret = [r["per_representation"][rep]["p_success_retained_only"] for r in d["results"]]
        axes[0].bar(x + (k - 1) * width, succ, width, color=REP_COLORS[rep], label=REP_LABELS[rep])
        axes[0].bar(x + (k - 1) * width, succ_ret, width, color=REP_COLORS[rep], alpha=0.4, hatch="//")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([str(s) for s in flocks])
    axes[0].set_ylabel("P(success): solid=full I_t, hatched=retained-only")
    axes[0].set_xlabel("flock seed")
    axes[0].legend(fontsize=7)

    for k, rep in enumerate(reps):
        n_act = [r["per_representation"][rep]["mean_n_actuators"] for r in d["results"]]
        axes[1].bar(x + (k - 1) * width, n_act, width, color=REP_COLORS[rep])
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([str(s) for s in flocks])
    axes[1].set_ylabel("mean actuator count")
    axes[1].set_xlabel("flock seed")

    for k, rep in enumerate(reps):
        ret = [r["per_representation"][rep]["mean_final_retention"] for r in d["results"]]
        turn = [r["per_representation"][rep]["mean_membership_turnover"] for r in d["results"]]
        axes[2].scatter(turn, ret, color=REP_COLORS[rep], label=REP_LABELS[rep], s=60)
    axes[2].set_xlabel("mean total membership turnover")
    axes[2].set_ylabel(r"mean final retention $R_0(T_u)$")
    axes[2].legend(fontsize=7)
    savefig(fig, "fig_6_5g_adaptive_control_proof_of_concept")


if __name__ == "__main__":
    fig_6_5d()
    print("wrote fig_6_5d")
    fig_6_5e()
    print("wrote fig_6_5e")
    fig_6_5f()
    print("wrote fig_6_5f")
    fig_6_5g()
    print("wrote fig_6_5g")
