import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from figstyle import save_all, COLOR_BOUNDARY, COLOR_EXTERIOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

if __name__ == "__main__":
    d = np.load(os.path.join(DATADIR, "part2j_actuator_grid.npz"))
    q_grid = d["q_grid"]; T_grid = d["T_grid"]
    best_node = d["best_node_ext"]  # (nq, nT), values in {4,5,6,7,8}
    log10ratio = d["log10ratio_ext"]
    n_tied = d["n_tied_ext"]
    tie_tol = float(d["tie_tol_rel"])

    ext_nodes = [4, 5, 6, 7, 8]
    node_colors = [COLOR_BOUNDARY, "#F0A800", COLOR_EXTERIOR, "#00B090", "#00C8A0"]
    cmap = ListedColormap(node_colors)
    bounds = np.array(ext_nodes + [9]) - 0.5
    norm = BoundaryNorm(bounds, cmap.N)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    ax0 = axes[0]
    # display: best_node is (nq,nT); imshow expects (rows=T, cols=q) with origin lower for log T on y
    im0 = ax0.pcolormesh(q_grid, T_grid, best_node.T, cmap=cmap, norm=norm, shading="nearest")
    tied_mask = (n_tied.T > 1)
    qq, TT = np.meshgrid(q_grid, T_grid)
    ax0.scatter(qq[tied_mask], TT[tied_mask], marker="x", color="black", s=14, linewidths=0.8,
                label=f"tied (tol={tie_tol})")
    ax0.set_yscale("log")
    ax0.set_xlabel("q"); ax0.set_ylabel("T (log scale)")
    ax0.set_title("A: best-accessible actuator (k in {4..8})")
    cbar0 = fig.colorbar(im0, ax=ax0, ticks=ext_nodes)
    cbar0.set_label("actuator k")
    if tied_mask.any():
        ax0.legend(fontsize=8, loc="upper right")

    ax1 = axes[1]
    im1 = ax1.pcolormesh(q_grid, T_grid, log10ratio.T, cmap="viridis", shading="nearest")
    ax1.set_yscale("log")
    ax1.set_xlabel("q"); ax1.set_ylabel("T (log scale)")
    ax1.set_title(r"B: decisiveness, $\log_{10}(E_{2nd}/E_{best})$")
    fig.colorbar(im1, ax=ax1, label=r"$\log_{10}$ ratio")

    fig.suptitle("Steering Figure 7 — Best accessible actuator phase diagram", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "sfig7_actuator_phase_diagram"))
    plt.close(fig)
    print("Steering Figure 7 saved.")
