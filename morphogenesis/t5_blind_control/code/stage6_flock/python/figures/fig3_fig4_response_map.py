"""Figure 3 (actuator-response map on the lattice) and Figure 4 (statistical
comparison of control leverage by Fiedler role)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flock_sim.lattice import Lattice, bird_to_rowcol
from flock_sim.spectral import analyze_window

TW = 5


def main():
    d = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    rm = json.load(open(d / "phase4_5_response_map.json"))
    meta = json.load(open(d / "canonical_snapshot_meta.json"))
    data = np.load(d / "canonical_snapshot.npz")
    I0 = np.array(rm["I0"])
    t0 = meta["t0"]
    z_hist = data["z_hist_full"]
    window = z_hist[t0 - TW + 1: t0 + 1]
    sr = analyze_window(window, refclust=I0)

    results = {int(k): v for k, v in rm["results"].items()}
    non_interior = sorted(results.keys())
    p_success = np.array([results[k]["p_success"] for k in non_interior])
    mean_end = np.array([results[k]["mean_Hstar_end"] for k in non_interior])
    y2 = sr.fiedler_norm
    is_boundary = np.isin(non_interior, sr.boundary_nodes)

    L = 10
    row, col = bird_to_rowcol(np.array(non_interior), L)
    row_I0, col_I0 = bird_to_rowcol(I0, L)

    fig_dir = Path(__file__).resolve().parents[2] / "figures"

    # ---------------- Figure 3 ----------------
    fig, ax = plt.subplots(figsize=(7.5, 7))
    sizes = 40 + 260 * p_success
    sc = ax.scatter(col, row, c=mean_end, cmap="viridis", s=sizes,
                     edgecolors=np.where(is_boundary, "red", "none"), linewidths=1.8, vmin=0, vmax=1)
    ax.scatter(col_I0, row_I0, marker='s', s=80, facecolors='none', edgecolors='black',
               linewidths=1.2, label=f"frozen core I0 (n={len(I0)})")
    cbar = fig.colorbar(sc, ax=ax, shrink=0.8)
    cbar.set_label("mean H*(t0+Tu) under single-actuator forcing")
    ax.invert_yaxis()
    ax.set_xlim(-1, L); ax.set_ylim(L, -1)
    ax.set_aspect("equal")
    ax.set_title("Actuator-response map (marker size ~ P(success), red outline = spectral boundary)")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(fig_dir / "fig03_actuator_response_map.png", dpi=150)
    fig.savefig(fig_dir / "fig03_actuator_response_map.pdf")
    plt.close(fig)

    # ---------------- Figure 4 ----------------
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    role = np.where(is_boundary, "boundary", "exterior")
    for grp, color in [("boundary", "#d62728"), ("exterior", "#1f77b4")]:
        mask = role == grp
        axes[0].scatter(np.random.default_rng(0).normal(0 if grp == "boundary" else 1, 0.05, mask.sum()),
                         p_success[mask], color=color, alpha=0.6, label=f"{grp} (n={mask.sum()})")
    axes[0].set_xticks([0, 1]); axes[0].set_xticklabels(["boundary", "exterior"])
    axes[0].set_ylabel("P(success) at Tu=20")
    axes[0].set_title("Control leverage by Fiedler role")
    axes[0].legend(fontsize=8)

    axes[1].scatter(np.abs(y2[non_interior]), p_success, alpha=0.6, color="#2ca02c")
    axes[1].set_xlabel("|y2| (Fiedler coordinate, max-abs normalized)")
    axes[1].set_ylabel("P(success) at Tu=20")
    axes[1].set_title("Control leverage vs. Fiedler coordinate")
    fig.suptitle(f"Statistical comparison of single-actuator control leverage (n={rm['n_replicates']} reps/bird)")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig04_leverage_comparison.png", dpi=150)
    fig.savefig(fig_dir / "fig04_leverage_comparison.pdf")
    plt.close(fig)
    print("Figures 3 and 4 written to", fig_dir)
    print(f"boundary birds: {is_boundary.sum()}, exterior birds: {(~is_boundary).sum()}")
    print(f"mean p_success boundary={p_success[is_boundary].mean() if is_boundary.any() else float('nan'):.3f} "
          f"exterior={p_success[~is_boundary].mean():.3f}")


if __name__ == "__main__":
    main()
