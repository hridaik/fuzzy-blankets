import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_BOUNDARY, COLOR_EXTERIOR
from steering_core import eta_k_lyapunov

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

if __name__ == "__main__":
    q_grid = np.linspace(-2, 2, 400)
    T_list = [1e-3, 1e-2, 1e-1]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for T, alpha in zip(T_list, [1.0, 0.7, 0.45]):
        eta4 = np.array([eta_k_lyapunov(T, q, 4)[0] for q in q_grid])
        eta6 = np.array([eta_k_lyapunov(T, q, 6)[0] for q in q_grid])
        ax.plot(q_grid, eta6, color=COLOR_EXTERIOR, alpha=alpha, linewidth=2.0,
                label=f"node 6, T={T:g}")
        ax.plot(q_grid, eta4, color=COLOR_BOUNDARY, alpha=alpha, linewidth=2.0,
                label=f"node 4, T={T:g}")
    ax.set_yscale("log")
    ax.axvline(6/7, color="black", linestyle=":", linewidth=1.3)
    ax.axvline(-6/11, color="black", linestyle=":", linewidth=1.3)
    ax.text(6/7, ax.get_ylim()[1], " q=6/7", rotation=90, va="top", ha="left", fontsize=8)
    ax.text(-6/11, ax.get_ylim()[1], " q=-6/11", rotation=90, va="top", ha="left", fontsize=8)
    ax.set_xlabel("q")
    ax.set_ylabel(r"$\eta_k(T;q)$ (control authority, short T)")
    ax.set_title("Steering Figure 6 — Short-time crossover: node 6 vs. node 4")
    ax.legend(fontsize=7.5, ncol=2)
    save_all(fig, os.path.join(FIGDIR, "sfig6_crossover"))
    plt.close(fig)
    print("Steering Figure 6 saved. Threshold lines fixed at analytic q*=6/7, -6/11 (not fit to data).")
