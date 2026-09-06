import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage2"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import core
from figstyle import draw_graph, save_all, COLOR_ACCENT, NODE_POS, NODE_COLOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")


def edges_from_omega(Omega):
    edges = []
    for i in range(8):
        for j in range(i + 1, 8):
            w = -Omega[i, j]
            if abs(w) > 1e-9:
                edges.append((i + 1, j + 1, w))
    return edges


if __name__ == "__main__":
    edges0 = edges_from_omega(core.Omega0)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), width_ratios=[1.6, 1])

    ax = axes[0]
    draw_graph(ax, edges0, title="What we are steering")
    ax.annotate("", xy=(0.0, 0.85), xytext=(0.7, 0.85),
                arrowprops=dict(arrowstyle="-|>", color=COLOR_ACCENT, lw=2.5))
    ax.text(0.35, 1.05, r"$u_k(t)$ actuator", color=COLOR_ACCENT, ha="center", fontsize=10)
    ax.scatter([NODE_POS[4][0]], [NODE_POS[4][1]], s=900, facecolors="none",
               edgecolors=COLOR_ACCENT, linewidth=2.5, zorder=4)
    ax.text(-2.9, 1.55, r"$Y=\frac{1}{3}(x_1+x_2+x_3)$" + "\n(target: mean of interior)",
            fontsize=10, ha="left", va="top", color=NODE_COLOR[1])
    for n in [1, 2, 3]:
        x, y = NODE_POS[n]
        ax.scatter([x], [y], s=900, facecolors="none", edgecolors=NODE_COLOR[1], linewidth=2.0, zorder=4)

    ax2 = axes[1]
    ax2.axis("off")
    txt = (
        "Controlled dynamics:\n"
        r"$dX_t = -A_q X_t\,dt + e_k u(t)\,dt + \sqrt{2}\,dW_t$" + "\n\n"
        r"$A_q = (I+Q_q)\,\Omega_0$" + "\n\n"
        "Key fact (verified, Part 2B):\n"
        r"$\Sigma(t) \equiv \Sigma_0$ for ANY open-loop $u(t)$" + "\n"
        "so the instantaneous Gaussian blanket\n"
        r"$I(X_{1:3};X_{6:8}\mid X_{4,5}) = 0$" + "\n"
        "stays exactly zero while the MEAN is\n"
        "being steered toward a target $Y^\\star$.\n\n"
        "Only the mean trajectory is driven;\n"
        "individual stochastic realizations are\n"
        "NOT claimed to hit the target exactly."
    )
    ax2.text(0.02, 0.98, txt, fontsize=10.5, va="top", ha="left", family="monospace",
             transform=ax2.transAxes)

    fig.suptitle("Steering Figure 1 — What are we controlling?", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "sfig1_control_setup"))
    plt.close(fig)
    print("Steering Figure 1 saved.")
