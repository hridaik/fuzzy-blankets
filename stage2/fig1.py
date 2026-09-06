import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import core
from figstyle import draw_graph, save_all, COLOR_ACCENT, NODE_POS

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")


def edges_from_omega(Omega):
    """Recover the (undirected) weighted edge list from Omega = I + L (off-diagonal -L entries)."""
    edges = []
    for i in range(8):
        for j in range(i + 1, 8):
            w = -Omega[i, j]
            if abs(w) > 1e-9:
                edges.append((i + 1, j + 1, w))
    return edges


if __name__ == "__main__":
    edges0 = edges_from_omega(core.Omega0)
    edges_eps = edges_from_omega(core.Omega_eps(1.0))
    edges_amb = edges_from_omega(core.Omega_amb)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

    draw_graph(axes[0], edges0, title="A: base graph ($\\varepsilon=0$)\nplanted $I=\\{1,2,3\\}, B=\\{4,5\\}, E=\\{6,7,8\\}$")
    added_edge = frozenset((3, 6))
    draw_graph(axes[1], edges_eps, highlight_edges={added_edge},
               title="B: perturbed graph ($\\varepsilon=1$)\ndashed = added 3–6 leakage edge")
    draw_graph(axes[2], edges_amb, title="C: ambiguity graph\nsparse interface: 3–4, 4–6, 2–5, 5–7")

    fig.suptitle("Figure 1 — Benchmark anatomy", fontsize=13, y=1.02)
    save_all(fig, os.path.join(FIGDIR, "fig1_anatomy"))
    plt.close(fig)

    # underlying data
    np.savez(os.path.join(DATADIR, "fig1_data.npz"),
             Omega0=core.Omega0, Omega_eps1=core.Omega_eps(1.0), Omega_amb=core.Omega_amb,
             edges0=np.array(edges0), edges_eps=np.array(edges_eps), edges_amb=np.array(edges_amb))
    print("Figure 1 saved.")
    print("Caption: Panel A shows the base graph testing the population-exact Markov blanket")
    print("{4,5} between I={1,2,3} and E={6,7,8}. Panel B shows the same graph with a single")
    print("epsilon=1 leakage edge (3-6, dashed) added, testing graded (non-exact) blanket violation.")
    print("Panel C shows the sparse-interface ambiguity graph, testing structural non-identifiability")
    print("of the minimal separator under anchored I/E endpoints.")
