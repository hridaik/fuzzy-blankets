import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR, COLOR_ACCENT
from steering_core import eta_k_lyapunov

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

NODES = [1, 4, 5, 6]
LABELS = {1: "internal (1)", 4: "blanket, strong (4)", 5: "blanket, weak (5)", 6: "exterior (6)"}
COLOR = {1: COLOR_INTERIOR, 4: COLOR_BOUNDARY, 5: COLOR_ACCENT, 6: COLOR_EXTERIOR}

if __name__ == "__main__":
    T_grid = np.geomspace(1e-3, 10, 120)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)

    for ax, q, title in zip(axes, [0.0, 1.0], ["A: q=0 (equilibrium)", "B: q=1 (driven)"]):
        for k in NODES:
            E = np.array([1.0 / eta_k_lyapunov(T, q, k)[0] for T in T_grid])
            ax.plot(T_grid, E, color=COLOR[k], linewidth=2.0, label=LABELS[k])
        if q == 0.0:
            ax.plot(T_grid, 9 / T_grid, "k:", linewidth=1.2, label=r"$9/T$")
            ax.plot(T_grid, 3 / T_grid**3, "k--", linewidth=1.0, alpha=0.7)
            ax.plot(T_grid, 12 / T_grid**3, "k--", linewidth=1.0, alpha=0.7, label=r"$3/T^3$, $12/T^3$")
            ax.plot(T_grid, 64 / (5 * T_grid**5), "k-.", linewidth=1.2, label=r"$64/(5T^5)$")
        else:
            ax.plot(T_grid, 4 / (3 * 1.0**2 * T_grid**3), "k--", linewidth=1.2,
                    label=r"$4/(3q^2T^3)$ (node 6, driven)")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("T")
        ax.set_title(title)
        ax.legend(fontsize=7.5)
    axes[0].set_ylabel(r"$E_k^\star(T)$ [energy units]")
    fig.suptitle("Steering Figure 5 — Minimum energy vs. time horizon", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "sfig5_energy_vs_horizon"))
    plt.close(fig)
    print("Steering Figure 5 saved.")
