import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage3"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from figstyle import save_all, COLOR_BOUNDARY, COLOR_EXTERIOR
from riccati_solver import solve_organization_aware

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

EXT_NODES = [4, 5, 6, 7, 8]
TIE_TOL_REL = 1e-3

if __name__ == "__main__":
    T = 1.0
    q_grid = np.linspace(-2, 2, 41)
    lam_grid = np.concatenate([[0.0], np.geomspace(1e-2, 1e5, 35)])

    best_node = np.zeros((len(q_grid), len(lam_grid)))
    log10ratio = np.zeros((len(q_grid), len(lam_grid)))
    n_tied = np.zeros((len(q_grid), len(lam_grid)), dtype=int)

    for iq, q in enumerate(q_grid):
        for il, lam in enumerate(lam_grid):
            Js = {}
            for k in EXT_NODES:
                res = solve_organization_aware(q, T, [k], lam, n_eval=60)
                Js[k] = 0.5 * res["E"] + lam * res["D"]
            best_k = min(Js, key=Js.get)
            sorted_vals = sorted(Js.values())
            ratio = sorted_vals[1] / sorted_vals[0] if sorted_vals[0] > 0 else np.nan
            best_node[iq, il] = best_k
            log10ratio[iq, il] = np.log10(ratio) if ratio > 0 else np.nan
            n_tied[iq, il] = sum(1 for v in Js.values() if abs(v - sorted_vals[0]) / sorted_vals[0] < TIE_TOL_REL)

    np.savez(os.path.join(DATADIR, "fig7_phase_data.npz"), q_grid=q_grid, lam_grid=lam_grid,
             best_node=best_node, log10ratio=log10ratio, n_tied=n_tied)

    node_colors = [COLOR_BOUNDARY, "#F0A800", COLOR_EXTERIOR, "#00B090", "#00C8A0"]
    cmap = ListedColormap(node_colors)
    bounds = np.array(EXT_NODES + [9]) - 0.5
    norm = BoundaryNorm(bounds, cmap.N)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    ax0 = axes[0]
    im0 = ax0.pcolormesh(q_grid, lam_grid, best_node.T, cmap=cmap, norm=norm, shading="nearest")
    tied_mask = (n_tied.T > 1)
    qq, ll = np.meshgrid(q_grid, lam_grid)
    if tied_mask.any():
        ax0.scatter(qq[tied_mask], ll[tied_mask], marker="x", color="black", s=10, linewidths=0.7,
                    label=f"tied (tol={TIE_TOL_REL})")
        ax0.legend(fontsize=8)
    ax0.set_yscale("symlog", linthresh=1e-2)
    ax0.set_xlabel("q"); ax0.set_ylabel(r"$\lambda$ (symlog)")
    ax0.set_title(f"A: best actuator by weighted objective $J_\\lambda$ (T={T:g})")
    cbar = fig.colorbar(im0, ax=ax0, ticks=EXT_NODES)
    cbar.set_label("actuator k")

    ax1 = axes[1]
    im1 = ax1.pcolormesh(q_grid, lam_grid, log10ratio.T, cmap="viridis", shading="nearest")
    ax1.set_yscale("symlog", linthresh=1e-2)
    ax1.set_xlabel("q"); ax1.set_ylabel(r"$\lambda$ (symlog)")
    ax1.set_title("B: decisiveness, $\\log_{10}(J_{2nd}/J_{best})$")
    fig.colorbar(im1, ax=ax1, label=r"$\log_{10}$ ratio")

    fig.suptitle("Stage-4 Figure 7 — Best single actuator depends on what we value", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "fig7_actuator_value_map"))
    plt.close(fig)
    print("Figure 7 saved.")
