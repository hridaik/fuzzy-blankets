import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR
from steering_core import h_k

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
LS = {1: "-", 2: "--", 3: ":", 4: "-", 5: "--", 6: "-", 7: "--", 8: ":"}
COLOR = {1: COLOR_INTERIOR, 2: COLOR_INTERIOR, 3: COLOR_INTERIOR,
         4: COLOR_BOUNDARY, 5: COLOR_BOUNDARY,
         6: COLOR_EXTERIOR, 7: COLOR_EXTERIOR, 8: COLOR_EXTERIOR}

if __name__ == "__main__":
    t_grid = np.linspace(0, 4, 500)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for ax, q, label in zip(axes, [0.0, 1.0, -1.0], ["A: q=0", "B: q=1", "C: q=-1"]):
        for k in range(1, 9):
            hk = h_k(t_grid, q, k)
            ax.plot(t_grid, hk, color=COLOR[k], linestyle=LS[k], linewidth=1.8, label=f"k={k}")
        ax.axhline(0, color="gray", linewidth=0.6)
        ax.set_xlabel("t")
        ax.set_title(label)
    axes[0].set_ylabel(r"$h_k(t;q) = c^\top e^{-A_q t} e_k$")
    axes[-1].legend(fontsize=7.5, ncol=2, loc="upper right")
    fig.suptitle("Steering Figure 3 — Impulse-response atlas", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "sfig3_impulse_atlas"))
    plt.close(fig)
    print("Steering Figure 3 saved.")
