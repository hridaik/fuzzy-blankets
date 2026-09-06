import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_BOUNDARY, COLOR_EXTERIOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")
NODE_COLOR = {4: COLOR_BOUNDARY, 5: "#CC79A7", 6: COLOR_EXTERIOR}

if __name__ == "__main__":
    rows = []
    with open(os.path.join(DATADIR, "part9_single_actuator_sweep.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: (float(v) if k != "k" else int(float(v))) for k, v in r.items()})

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    q, T = 1.0, 1.0
    for k in [4, 5, 6]:
        sub = sorted([r for r in rows if r["k"] == k and r["q"] == q and r["T"] == T], key=lambda r: r["lam"])
        E = np.array([r["E"] for r in sub])
        D = np.array([r["D"] for r in sub])
        # min D achievable as function of allowed E budget = the Pareto front itself (E,D) sorted by E
        order = np.argsort(E)
        axes[0].plot(E[order], D[order], "-o", color=NODE_COLOR[k], markersize=3, label=f"node {k}")
        # min E as function of allowed D budget: sort by D
        orderD = np.argsort(D)
        axes[1].plot(D[orderD], E[orderD], "-o", color=NODE_COLOR[k], markersize=3, label=f"node {k}")

    axes[0].set_xscale("log"); axes[0].set_yscale("log")
    axes[0].set_xlabel("allowed energy budget E"); axes[0].set_ylabel("minimum achievable D")
    axes[0].set_title(f"A: min D vs. E budget (q={q:g}, T={T:g})")
    axes[0].legend(fontsize=9)

    axes[1].set_xscale("log"); axes[1].set_yscale("log")
    axes[1].set_xlabel("allowed distortion budget D"); axes[1].set_ylabel("minimum required energy E")
    axes[1].set_title(f"B: min E vs. D budget (q={q:g}, T={T:g})")

    fig.suptitle("Stage-4 Figure 8 — Energy budget vs. disruption budget", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "fig8_budget_tradeoff"))
    plt.close(fig)
    print("Figure 8 saved.")
