import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_EDGE

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

MARKERS = {1: "o", 2: "s", 3: "^", 4: "D", 5: "P"}


def pareto_mask(E, D):
    n = len(E)
    mask = np.ones(n, dtype=bool)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if E[j] <= E[i] and D[j] <= D[i] and (E[j] < E[i] or D[j] < D[i]):
                mask[i] = False
                break
    return mask


if __name__ == "__main__":
    rows = []
    with open(os.path.join(DATADIR, "part12_multiactuator_sweep.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: (float(v) if k not in ("S",) else v) for k, v in r.items()})

    q, T = 0.0, 1.0
    sub = [r for r in rows if r["q"] == q and r["T"] == T]
    E = np.array([r["E"] for r in sub])
    D = np.array([r["D"] for r in sub])
    size = np.array([int(r["size"]) for r in sub])
    Slabel = [r["S"] for r in sub]

    fig, ax = plt.subplots(figsize=(10, 7))
    for sz in range(1, 6):
        m = size == sz
        ax.scatter(E[m], D[m], marker=MARKERS[sz], s=30 + sz * 10, color=COLOR_EDGE, alpha=0.5,
                   label=f"|S|={sz}")

    mask = pareto_mask(E, D)
    order = np.argsort(E[mask])
    E_p, D_p = E[mask][order], D[mask][order]
    S_p = np.array(Slabel)[mask][order]
    ax.plot(E_p, D_p, "-", color="red", linewidth=1.5, zorder=3)
    ax.scatter(E_p, D_p, color="red", s=40, zorder=4, label="nondominated (all sizes)")
    # label only a legible, evenly-spaced subsample of the (possibly dense) nondominated set,
    # per instructions not to label every dominated/crowded point
    n_labels = min(10, len(E_p))
    label_idx = np.unique(np.linspace(0, len(E_p) - 1, n_labels).astype(int))
    for i in label_idx:
        ax.annotate(S_p[i], (E_p[i], D_p[i]), fontsize=7, xytext=(5, 5), textcoords="offset points",
                    rotation=25, ha="left")

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("E"); ax.set_ylabel("D")
    ax.set_title(f"Stage-4 Figure 9 — All 31 actuator subsets, E-D Pareto (q={q:g}, T={T:g})")
    ax.legend(fontsize=8)
    save_all(fig, os.path.join(FIGDIR, "fig9_multiactuator_pareto"))
    plt.close(fig)
    print("Figure 9 saved.")
