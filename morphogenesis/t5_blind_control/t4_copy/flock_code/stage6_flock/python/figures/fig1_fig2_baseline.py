"""Figure 1 (baseline emergent macro-agent) and Figure 2 (spectral identification)."""
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
UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])
HEADING_NAMES = ["up", "down", "left", "right"]


def load_canonical():
    d = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    data = np.load(d / "canonical_snapshot.npz")
    meta = json.load(open(d / "canonical_snapshot_meta.json"))
    return data, meta


def main():
    data, meta = load_canonical()
    I0 = np.array(meta["I0"])
    t0 = meta["t0"]
    h0 = meta["h0"]
    h_star = meta["h_star"]
    z_hist = data["z_hist_full"]
    z_t0 = z_hist[t0]
    L = 10
    lattice = Lattice(nn=100, nh=8)

    window = z_hist[t0 - TW + 1: t0 + 1]
    sr = analyze_window(window, refclust=I0)

    row, col = bird_to_rowcol(np.arange(100), L)
    interior_mask = np.isin(np.arange(100), I0)
    boundary_mask = np.isin(np.arange(100), sr.boundary_nodes)
    exterior_mask = ~interior_mask & ~boundary_mask

    fig_dir = Path(__file__).resolve().parents[2] / "figures"
    fig_dir.mkdir(exist_ok=True)

    # ---------------- Figure 1 ----------------
    fig, ax = plt.subplots(figsize=(7, 7))
    colors = np.where(interior_mask, "#1f77b4", np.where(boundary_mask, "#ff7f0e", "#cccccc"))
    vecs = UV4[z_t0]
    ax.quiver(col, row, vecs[:, 0], vecs[:, 1], color=colors, scale=18, width=0.008)
    ax.scatter(col[interior_mask], row[interior_mask], s=120, facecolors='none',
               edgecolors='#1f77b4', linewidths=1.5, label=f"frozen core I0 (n={len(I0)})")
    ax.scatter(col[boundary_mask], row[boundary_mask], s=120, facecolors='none',
               edgecolors='#ff7f0e', linewidths=1.5, label=f"spectral boundary (n={boundary_mask.sum()})")
    ax.invert_yaxis()
    ax.set_xlim(-1, L)
    ax.set_ylim(L, -1)
    ax.set_aspect("equal")
    ax.set_title(f"Canonical emergent macro-agent at t0={t0}\n"
                 f"h0={HEADING_NAMES[h0]} -> target h*={HEADING_NAMES[h_star]} (90-deg turn)")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(fig_dir / "fig01_baseline_macroagent.png", dpi=150)
    fig.savefig(fig_dir / "fig01_baseline_macroagent.pdf")
    plt.close(fig)

    # ---------------- Figure 2 ----------------
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    y2 = sr.fiedler_norm
    order = np.argsort(y2)
    axes[0].plot(y2[order], marker='.', linestyle='none', markersize=4, color='gray')
    axes[0].scatter(np.where(np.isin(order, I0))[0], y2[order][np.isin(order, I0)],
                     color='#1f77b4', s=25, label='I0 members', zorder=3)
    axes[0].axhspan(-0.05, 0.05, color='#ff7f0e', alpha=0.2, label='boundary band |y2|<0.05')
    axes[0].set_title("Fiedler vector (sorted, max-abs normalized)")
    axes[0].set_xlabel("node rank"); axes[0].set_ylabel("y2 (normalized)")
    axes[0].legend(fontsize=8)

    eigs = sr.eigvals[:10]
    axes[1].bar(range(len(eigs)), eigs, color=['#d62728' if i in (1, 2) else '#7f7f7f' for i in range(len(eigs))])
    axes[1].set_xlabel("eigenvalue rank (ascending)")
    axes[1].set_ylabel("eigenvalue")
    axes[1].set_title(f"lambda2={sr.lambda2:.3f}, lambda3={sr.lambda3:.3f}\neigengap={sr.eigengap:.3f}")
    fig.suptitle(f"Spectral identification at t0={t0} (window [{t0-TW+1},{t0}], TW={TW})")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig02_spectral_identification.png", dpi=150)
    fig.savefig(fig_dir / "fig02_spectral_identification.pdf")
    plt.close(fig)
    print("Figures 1 and 2 written to", fig_dir)


if __name__ == "__main__":
    main()
