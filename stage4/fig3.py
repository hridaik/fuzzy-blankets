import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage3"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR, COLOR_ACCENT
from steering_core import C_VEC
from organization_core import v_vec
from riccati_solver import solve_organization_aware

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

if __name__ == "__main__":
    cases = [(0.0, 4, "node 4"), (0.0, 6, "node 6")]
    T = 1.0
    fig, axes = plt.subplots(3, 2, figsize=(11, 9.5), sharex=True)
    for col, (q, k, label) in enumerate(cases):
        res = solve_organization_aware(q, T, [k], lam=0.0, n_eval=400)
        t = res["t"]; m = res["m"]
        Y_t = C_VEC @ m
        m_nat_t = np.outer(v_vec, Y_t)

        ax0 = axes[0, col]
        ax0.plot(t, Y_t, color="black", linewidth=2.0)
        ax0.set_title(f"{label} (q={q:g}, T={T:g}, $\\lambda$=0)")
        ax0.set_ylabel("Y(t)" if col == 0 else "")

        ax1 = axes[1, col]
        for n, c in [(1, COLOR_INTERIOR), (4, COLOR_BOUNDARY), (6, COLOR_EXTERIOR)]:
            ax1.plot(t, m[n - 1], color=c, linewidth=1.8, label=f"node {n}")
            ax1.plot(t, m_nat_t[n - 1], color=c, linestyle=":", linewidth=1.3, alpha=0.7)
        ax1.set_ylabel("mean states\n(solid=actual, dotted=natural)" if col == 0 else "")
        if col == 0:
            ax1.legend(fontsize=7.5)

        ax2 = axes[2, col]
        ax2.plot(t, res["dperp_t"], color=COLOR_ACCENT, linewidth=2.0)
        ax2.set_ylabel(r"$d_\perp(t)$" if col == 0 else "")
        ax2.set_xlabel("t")

    fig.suptitle("Stage-4 Figure 3 — Same target, different microscopic trajectories", y=1.02, fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save_all(fig, os.path.join(FIGDIR, "fig3_same_target_diff_trajectory"))
    plt.close(fig)
    print("Figure 3 saved.")
