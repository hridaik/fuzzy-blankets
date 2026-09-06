import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import core
from figstyle import draw_graph, save_all, NODE_COLOR
from organization_core import v_vec

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
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), width_ratios=[1, 1, 1.1])

    ax0 = axes[0]
    draw_graph(ax0, edges_from_omega(core.Omega0), title="A: target $Y=(x_1+x_2+x_3)/3$")

    ax1 = axes[1]
    nodes = list(range(1, 9))
    ax1.bar([str(n) for n in nodes], v_vec, color=[NODE_COLOR[n] for n in nodes], edgecolor="black")
    ax1.set_ylabel(r"$m_{\rm nat}(1)_i = v_i$")
    ax1.set_xlabel("node")
    ax1.set_title("B: natural mean profile at Y=1")
    ax1.axhline(0, color="gray", linewidth=0.6)

    ax2 = axes[2]
    ax2.axis("off")
    txt = (
        r"$m = m_{\rm nat}(Y) + r$" + "\n\n"
        r"$m_{\rm nat}(Y) = v\,Y$" + "\n"
        "  the microstate the system would\n"
        "  naturally adopt to have this Y,\n"
        "  under its OWN endogenous coupling\n\n"
        r"$r = m - v Y,\qquad c^\top r = 0$" + "\n"
        "  r changes microscopic organization\n"
        "  WITHOUT changing the macro-target Y\n\n"
        r"$d_\perp = \frac{1}{2} m^\top Q_\perp m = \frac{1}{2} r^\top\Omega_0 r$" + "\n"
        "  excess distortion beyond what Y alone\n"
        "  requires -- the Stage-4 disruption metric"
    )
    ax2.text(0.02, 0.98, txt, fontsize=10.5, va="top", ha="left", family="monospace",
             transform=ax2.transAxes)
    ax2.set_title("C: decomposition $m=m_{\\rm nat}(Y)+r$")

    fig.suptitle("Stage-4 Figure 1 — What does \"natural organization at the same target\" mean?",
                 y=1.03, fontsize=12.5)
    save_all(fig, os.path.join(FIGDIR, "fig1_natural_organization"))
    plt.close(fig)
    print("Figure 1 saved.")
