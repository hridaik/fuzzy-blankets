import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage3"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_ACCENT, COLOR_ACCENT2, COLOR_INTERIOR
from riccati_solver import solve_organization_aware

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

if __name__ == "__main__":
    q, k, T = 1.0, 6, 1.0
    lambdas = [0.0, 10.0, 1000.0]
    lam_colors = [COLOR_INTERIOR, COLOR_ACCENT2, COLOR_ACCENT]
    lam_labels = [r"$\lambda=0$ (energy-optimal)", r"$\lambda=10$ (moderate)", r"$\lambda=1000$ (high)"]

    fig, axes = plt.subplots(3, 1, figsize=(8, 9.5), sharex=True)
    for lam, c, lab in zip(lambdas, lam_colors, lam_labels):
        res = solve_organization_aware(q, T, [k], lam, n_eval=400)
        axes[0].plot(res["t"], res["u"][0], color=c, linewidth=1.8, label=lab)
        Y_t = np.array([0.0]) if False else None
        from steering_core import C_VEC
        Y_t = C_VEC @ res["m"]
        axes[1].plot(res["t"], Y_t, color=c, linewidth=1.8, label=lab)
        axes[2].plot(res["t"], res["dperp_t"], color=c, linewidth=1.8, label=lab)
        print(f"lambda={lam}: E={res['E']:.4f}  D={res['D']:.4f}")

    axes[0].set_ylabel(r"$u(t)$")
    axes[0].set_title(f"Stage-4 Figure 5 — Organization-aware control, node {k}, q={q:g}, T={T:g}")
    axes[0].legend(fontsize=9)
    axes[1].set_ylabel("Y(t)")
    axes[1].axhline(1.0, color="gray", linestyle=":", linewidth=1.0)
    axes[2].set_ylabel(r"$d_\perp(t)$")
    axes[2].set_xlabel("t")

    save_all(fig, os.path.join(FIGDIR, "fig5_organization_aware_control"))
    plt.close(fig)
    print("Figure 5 saved.")
