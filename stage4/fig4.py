import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_BOUNDARY, COLOR_EXTERIOR, COLOR_ACCENT2

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

NODE_COLOR = {4: COLOR_BOUNDARY, 5: "#CC79A7", 6: COLOR_EXTERIOR}

if __name__ == "__main__":
    rows = []
    with open(os.path.join(DATADIR, "part9_single_actuator_sweep.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: (float(v) if k != "k" else int(float(v))) for k, v in r.items()})

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)
    for ax, q in zip(axes, [0.0, 1.0, -1.0]):
        for k in [4, 5, 6]:
            sub = [r for r in rows if r["k"] == k and r["q"] == q and r["T"] == 1.0]
            sub = sorted(sub, key=lambda r: r["lam"])
            E = np.array([r["E"] for r in sub])
            D = np.array([r["D"] for r in sub])
            lam = np.array([r["lam"] for r in sub])
            ax.plot(E, D, "-", color=NODE_COLOR[k], linewidth=1.6, alpha=0.85, label=f"node {k}")
            ax.scatter(E, D, s=14, color=NODE_COLOR[k])
            # mark lambda=0 and high-lambda end
            ax.scatter(E[0], D[0], marker="s", s=70, color=NODE_COLOR[k], edgecolor="black", zorder=5)
            ax.scatter(E[-1], D[-1], marker="^", s=70, color=NODE_COLOR[k], edgecolor="black", zorder=5)
            mid = len(E) // 2
            ax.annotate("", xy=(E[mid + 3], D[mid + 3]), xytext=(E[mid - 3], D[mid - 3]),
                        arrowprops=dict(arrowstyle="->", color=NODE_COLOR[k], alpha=0.6))
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("E (energy)")
        ax.set_title(f"q={q:g}, T=1")
        if q == 0.0:
            ax.set_ylabel("D (excess organizational distortion)")
            ax.legend(fontsize=9)
            ax.text(0.02, 0.02, "square=$\\lambda$=0\ntriangle=high $\\lambda$\narrow: increasing $\\lambda$",
                    transform=ax.transAxes, fontsize=8, va="bottom")

    fig.suptitle("Stage-4 Figure 4 — Energy-organization Pareto fronts", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "fig4_pareto_fronts"))
    plt.close(fig)
    print("Figure 4 saved.")
