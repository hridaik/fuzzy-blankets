import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_BOUNDARY, COLOR_EXTERIOR, NODE_COLOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

if __name__ == "__main__":
    rows = []
    with open(os.path.join(DATADIR, "part2k_comparison.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({kk: (float(vv) if kk != "k" else int(float(vv))) for kk, vv in r.items()})

    nodes = [4, 5, 6, 7, 8]
    delta_k = {r["k"]: r["delta_k_static"] for r in rows}

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    ax0 = axes[0]
    ax0.bar([str(k) for k in nodes], [delta_k[k] for k in nodes],
            color=[NODE_COLOR[k] for k in nodes], edgecolor="black")
    ax0.set_ylabel(r"$\Delta_k(\varnothing) = L(\varnothing)-L(\{k\})$ [nats]")
    ax0.set_title("A: fixed statistical leakage reduction\n(does NOT change with q)")
    ax0.set_xlabel("node k")

    ax1 = axes[1]
    combos = [(0.0, 1.0), (1.0, 1.0)]
    width = 0.35
    x = np.arange(len(nodes))
    for i, (q, T) in enumerate(combos):
        vals = []
        for k in nodes:
            match = [r for r in rows if r["k"] == k and r["q"] == q and r["T"] == T][0]
            vals.append(match["eta"])
        ax1.bar(x + (i - 0.5) * width, vals, width, label=f"q={q:g}, T={T:g}",
                color=[NODE_COLOR[k] for k in nodes], alpha=1.0 if i == 0 else 0.55,
                edgecolor="black")
    ax1.set_yscale("log")
    ax1.set_xticks(x); ax1.set_xticklabels([str(k) for k in nodes])
    ax1.set_ylabel(r"$\eta_k(T;q)$ (control authority)")
    ax1.set_xlabel("node k")
    ax1.set_title("B: control authority (changes with q)")
    ax1.legend(fontsize=8)

    fig.suptitle("Steering Figure 8 — Statistical boundary vs. control interface", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "sfig8_statistical_vs_control"))
    plt.close(fig)
    print("Steering Figure 8 saved.")
    print("Note: no universal correlation/anticorrelation claimed -- panel A is q-invariant, panel B is not.")
