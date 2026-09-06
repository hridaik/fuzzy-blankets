"""Figure 1: One collective, changing interface. Three network panels at z=-1,0,+1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import core5

PANELS = [(-1.0, "z = -1  (boundary {4,5})", {4, 5}),
          (0.0, "z = 0  (boundary {4,5,6})", {4, 5, 6}),
          (1.0, "z = +1  (boundary {5,6})", {5, 6})]

if __name__ == "__main__":
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    for ax, (z, title, B) in zip(axes, PANELS):
        W = core5.W_of_z(z)
        edges = [(a, b, W[core5.idx[a], core5.idx[b]])
                 for a in range(1, 9) for b in range(a + 1, 9) if W[core5.idx[a], core5.idx[b]] > 1e-9]
        node_color = {n: (fs.COLOR_BOUNDARY if n in B else
                           (fs.COLOR_INTERIOR if n in (1, 2, 3) else fs.COLOR_EXTERIOR))
                      for n in range(1, 9)}
        highlight = {frozenset((a, b)) for a in (1, 2, 3) for b in B if W[core5.idx[a], core5.idx[b]] > 1e-9}
        highlight |= {frozenset((a, b)) for a in B for b in (6, 7, 8) if W[core5.idx[a], core5.idx[b]] > 1e-9}
        fs.draw_graph(ax, edges, node_color=node_color, highlight_edges=highlight, title=title)
        for n in (1, 2, 3):
            x, y = fs.NODE_POS[n]
            ax.add_patch(plt.Circle((x, y), 0.32, fill=False, edgecolor="black", linewidth=2.2, zorder=4))
    fig.suptitle("The collective is identified with the persistent interior, not a frozen set of\n"
                 "boundary variables. Interior nodes {1,2,3} (blue, ringed) are fixed throughout; the\n"
                 "screening boundary (orange) is re-inferred and changes identity as z sweeps -1 -> +1.",
                 fontsize=10.5, y=1.10)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig1_changing_interface")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
