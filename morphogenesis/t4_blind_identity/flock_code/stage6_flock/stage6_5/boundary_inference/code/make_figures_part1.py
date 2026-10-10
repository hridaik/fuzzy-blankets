"""Figures 6.5A-C. Follows the existing Agg-backend, data-driven, PNG+PDF
convention (v1_mechanism_audit/code/make_figures.py,
v2_interface_control/code/make_v2_figures.py, v3_refinement/code/make_v3_figures.py)
-- reads only from data/, never re-runs the simulator."""
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


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def fig_6_5a():
    """Infer the hidden interface: membership score m_j for every non-core
    bird on the canonical flock, true B^D revealed only in the right panel."""
    boot = json.load(open(DATA_DIR / "bootstrap_membership.json"))
    I0 = set(boot["I0"])
    B_D = set(boot["B_D"])
    membership = {int(k): v for k, v in boot["membership"].items()}
    exterior = sorted(j for j in range(100) if j not in I0)
    m = np.array([membership.get(j, 0.0) for j in exterior])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    order = np.argsort(-m)
    ax = axes[0]
    ax.bar(range(len(exterior)), m[order], color="#4c72b0")
    ax.set_xlabel("exterior bird (ranked by inferred membership score)")
    ax.set_ylabel(r"$m_j$ = P(bird $j$ in bootstrap $\hat B$)")
    ax.set_title("Inferred boundary membership (no source graph used)")
    ax.axhline(0.5, ls="--", c="gray", lw=0.8)

    ax = axes[1]
    colors = ["#c44e52" if exterior[i] in B_D else "#8172b2" for i in order]
    ax.bar(range(len(exterior)), m[order], color=colors)
    ax.set_xlabel("exterior bird (same order)")
    ax.set_title(r"Revealed: red = true $B^D$ member")
    handles = [plt.Rectangle((0, 0), 1, 1, color="#c44e52", label=r"in $B^D$"),
               plt.Rectangle((0, 0), 1, 1, color="#8172b2", label=r"not in $B^D$")]
    ax.legend(handles=handles, fontsize=9)
    savefig(fig, "fig_6_5a_infer_hidden_interface")


def fig_6_5b():
    """Boundary recovery vs. number of training trajectories."""
    d = json.load(open(DATA_DIR / "sample_efficiency.json"))
    rows = d["rows"]
    n = [r["n_traj"] for r in rows]
    jac = [r["jaccard"] for r in rows]
    excess = [r["excess_loss_B_hat"] for r in rows]
    size = [r["size_hat"] for r in rows]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    axes[0].plot(n, jac, "o-", color="#4c72b0")
    axes[0].set_xscale("log")
    axes[0].set_xlabel(r"$N_{\rm traj}$ (training trajectories)")
    axes[0].set_ylabel(r"Jaccard($\hat B$, $B^D$)")
    axes[0].set_ylim(-0.05, 1.05)

    axes[1].plot(n, excess, "o-", color="#dd8452")
    axes[1].axhline(0, ls="--", c="gray", lw=0.8)
    axes[1].set_xscale("log")
    axes[1].set_xlabel(r"$N_{\rm traj}$")
    axes[1].set_ylabel(r"$\Delta\ell(\hat B)$ (nats)")

    axes[2].plot(n, size, "o-", color="#55a868")
    axes[2].set_xscale("log")
    axes[2].set_xlabel(r"$N_{\rm traj}$")
    axes[2].set_ylabel(r"$|\hat B|$")
    savefig(fig, "fig_6_5b_recovery_vs_data")


def fig_6_5c():
    """Does inferred-boundary control work? Oracle vs. inferred vs. Fiedler
    vs. random-matched, across held-out flocks."""
    d = json.load(open(DATA_DIR / "control_comparison.json"))
    rows = d["rows"]
    arms = ["oracle", "inferred", "fiedler", "random_matched"]
    colors = {"oracle": "#55a868", "inferred": "#4c72b0", "fiedler": "#c44e52", "random_matched": "#8172b2"}
    seeds = [r["seed"] for r in rows]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    x = np.arange(len(seeds))
    width = 0.2
    for k, arm in enumerate(arms):
        p = [r[arm]["p_success"] for r in rows]
        axes[0].bar(x + (k - 1.5) * width, p, width, label=arm, color=colors[arm])
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([str(s) for s in seeds])
    axes[0].set_xlabel("held-out flock seed")
    axes[0].set_ylabel("P(success)")
    axes[0].axhline(0.8, ls="--", c="gray", lw=0.8)
    axes[0].legend(fontsize=8)

    for k, arm in enumerate(arms):
        n_act = [r[arm]["n_actuators"] for r in rows]
        axes[1].bar(x + (k - 1.5) * width, n_act, width, color=colors[arm])
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([str(s) for s in seeds])
    axes[1].set_xlabel("held-out flock seed")
    axes[1].set_ylabel("actuator count |A|")

    for k, arm in enumerate(arms):
        hstar = [r[arm]["mean_Hstar_end"] for r in rows]
        axes[2].bar(x + (k - 1.5) * width, hstar, width, color=colors[arm])
    axes[2].set_xticks(x)
    axes[2].set_xticklabels([str(s) for s in seeds])
    axes[2].set_xlabel("held-out flock seed")
    axes[2].set_ylabel(r"mean $H^\star$ at $t_0+T_u$")
    axes[2].axhline(0.8, ls="--", c="gray", lw=0.8)
    savefig(fig, "fig_6_5c_inferred_boundary_control")


if __name__ == "__main__":
    fig_6_5a()
    print("wrote fig_6_5a")
    fig_6_5b()
    print("wrote fig_6_5b")
    fig_6_5c()
    print("wrote fig_6_5c")
