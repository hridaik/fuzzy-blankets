import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_BOUNDARY, COLOR_EXTERIOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")
NODES = [4, 5, 6, 7, 8]
NODE_COLOR = {4: COLOR_BOUNDARY, 5: "#F0A800", 6: COLOR_EXTERIOR, 7: "#00B090", 8: "#00C8A0"}


def best_subset_by_size(rows, size, weight):
    sub = [r for r in rows if int(r["size"]) == size]
    return min(sub, key=lambda r: 0.5 * r["E"] + weight * r["D"])


if __name__ == "__main__":
    rows = []
    with open(os.path.join(DATADIR, "part12_multiactuator_sweep.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: (float(v) if k not in ("S",) else v) for k, v in r.items()})

    q, T = 0.0, 1.0
    lam_levels = [0.0, 1.0, 100.0]
    fig, axes = plt.subplots(1, len(lam_levels), figsize=(5 * len(lam_levels), 5), sharey=True)
    M_all = []
    for ax, lam in zip(axes, lam_levels):
        cell = [r for r in rows if r["q"] == q and r["T"] == T and r["lam"] == lam]
        M = np.zeros((3, len(NODES)))
        labels = []
        for i, sz in enumerate([1, 2, 3]):
            best = best_subset_by_size(cell, sz, lam)
            S = eval(best["S"])
            labels.append(f"|S|={sz}: {S}")
            for node in S:
                M[i, NODES.index(node)] = 1
        im = ax.imshow(M, cmap="Greys", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(NODES))); ax.set_xticklabels(NODES)
        ax.set_yticks(range(3)); ax.set_yticklabels(labels, fontsize=8)
        ax.set_title(f"$\\lambda$={lam:g}")
        for i in range(3):
            for j in range(len(NODES)):
                if M[i, j]:
                    ax.text(j, i, "1", ha="center", va="center", color="white", fontsize=9)
    axes[0].set_ylabel("best subset by cardinality")
    fig.suptitle(f"Stage-4 Figure 10 — Composition of best sparse actuator sets (q={q:g}, T={T:g})",
                 y=1.03, fontsize=12.5)
    save_all(fig, os.path.join(FIGDIR, "fig10_sparse_composition"))
    plt.close(fig)
    print("Figure 10 saved.")
