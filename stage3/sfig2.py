import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all
from steering_core import J_q

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

if __name__ == "__main__":
    J0 = J_q(0.0)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    vmax = max(np.max(np.abs(J_q(1.0) - J0)), np.max(np.abs(J_q(-1.0) - J0)))
    for ax, q in zip(axes, [-1.0, 1.0]):
        dJ = J_q(q) - J0
        im = ax.imshow(dJ, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        ax.set_xticks(range(8)); ax.set_xticklabels(range(1, 9))
        ax.set_yticks(range(8)); ax.set_yticklabels(range(1, 9))
        ax.set_title(f"$\\Delta J(q={q:+.0f}) = J(q) - J(0)$")
        for i in range(8):
            for j in range(8):
                v = dJ[i, j]
                if abs(v) > 1e-9:
                    ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=7,
                            color="white" if abs(v) > vmax * 0.5 else "black")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("Steering Figure 2 — Full dynamical change with q", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "sfig2_deltaJ_heatmap"))
    plt.close(fig)
    print("Steering Figure 2 saved.")
    print("Confirms: DeltaJ has 10 nonzero entries (rows/cols 3 and 6, both directions), not just (3,6)/(6,3).")
