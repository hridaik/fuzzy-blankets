import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from scipy.integrate import solve_ivp
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR, COLOR_ACCENT
from steering_core import A_q, e_k, C_VEC, eta_k_lyapunov, N

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

if __name__ == "__main__":
    cases = [(0.0, 4), (0.0, 6), (1.0, 4), (1.0, 6)]
    T = 1.0
    Ystar = 1.0

    fig, axes = plt.subplots(2, 4, figsize=(17, 7.5), height_ratios=[1, 1])
    for col, (q, k) in enumerate(cases):
        Aq = A_q(q)
        ek = e_k(k)
        eta, _, _ = eta_k_lyapunov(T, q, k)
        E_star = Ystar**2 / eta

        def u_star(s):
            return (Ystar / eta) * (C_VEC @ expm(-Aq * (T - s)) @ ek)

        def mdot(t, m):
            return -Aq @ m + ek * u_star(t)

        t_grid = np.linspace(0, T, 600)
        sol = solve_ivp(mdot, [0, T], np.zeros(N), t_eval=t_grid, rtol=1e-10, atol=1e-12)
        Y_traj = C_VEC @ sol.y
        u_vals = np.array([u_star(t) for t in t_grid])
        energy = np.trapezoid(u_vals**2, t_grid)

        ax_top = axes[0, col]
        ax_top.plot(t_grid, u_vals, color=COLOR_ACCENT, linewidth=2.0)
        ax_top.set_title(f"q={q:g}, k={k}\nE*={energy:.3f}", fontsize=10)
        ax_top.set_xlabel("t"); ax_top.set_ylabel(r"$u_k^\star(t)$" if col == 0 else "")

        ax_bot = axes[1, col]
        ax_bot.plot(t_grid, Y_traj, color="black", linewidth=2.2, label="Y(t)")
        for n in [1, 2, 3]:
            ax_bot.plot(t_grid, sol.y[n - 1], color=COLOR_INTERIOR, alpha=0.35, linewidth=1.0)
        for n in [4, 5]:
            ax_bot.plot(t_grid, sol.y[n - 1], color=COLOR_BOUNDARY, alpha=0.5, linewidth=1.0)
        for n in [6, 7, 8]:
            ax_bot.plot(t_grid, sol.y[n - 1], color=COLOR_EXTERIOR, alpha=0.35, linewidth=1.0)
        ax_bot.axhline(1.0, color="gray", linestyle=":", linewidth=1.0)
        ax_bot.set_xlabel("t"); ax_bot.set_ylabel("mean state" if col == 0 else "")
        assert abs(Y_traj[-1] - 1.0) < 1e-3

    fig.suptitle("Steering Figure 9 — Actual minimum-energy steering examples (T=1, Y*=1)", y=1.02, fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    save_all(fig, os.path.join(FIGDIR, "sfig9_steering_examples"))
    plt.close(fig)
    print("Steering Figure 9 saved. All four cases verified to reach Y(T)=1.")
