import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")
LS = {1: "-", 2: "--", 3: ":", 4: "-", 5: "--", 6: "-", 7: "--", 8: ":"}
COLOR = {1: COLOR_INTERIOR, 2: COLOR_INTERIOR, 3: COLOR_INTERIOR,
         4: COLOR_BOUNDARY, 5: COLOR_BOUNDARY,
         6: COLOR_EXTERIOR, 7: COLOR_EXTERIOR, 8: COLOR_EXTERIOR}

if __name__ == "__main__":
    rows = []
    with open(os.path.join(DATADIR, "part2e_static_gain.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: float(v) for k, v in r.items()})
    rows = sorted(rows, key=lambda r: r["q"])
    qs = [r["q"] for r in rows]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for k in range(1, 9):
        vals = [r[f"g{k}"] for r in rows]
        ax.plot(qs, vals, color=COLOR[k], linestyle=LS[k], linewidth=2.0, label=f"$g_{k}(q)$")
    ax.set_xlabel("q")
    ax.set_ylabel(r"$g_k(q) = c^\top A_q^{-1} e_k$")
    ax.set_title("Steering Figure 4 — Static leverage vs. circulation")
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    ax.text(0.98, 0.98, "flat (q-invariant): k=1,2,4,5,7,8\ncurved (q-dependent): k=3,6",
            transform=ax.transAxes, fontsize=9, va="top", ha="right",
            bbox=dict(boxstyle="round", facecolor="white", edgecolor="gray", alpha=0.9))
    save_all(fig, os.path.join(FIGDIR, "sfig4_static_leverage"))
    plt.close(fig)
    print("Steering Figure 4 saved.")
