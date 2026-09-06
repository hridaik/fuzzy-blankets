import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import core
from figstyle import save_all, COLOR_ACCENT, COLOR_INTERIOR, COLOR_EXTERIOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

I_idx = core.I_IDX
B_idx = [core.idx[4], core.idx[5]]
E_idx = [core.idx[6], core.idx[7], core.idx[8]]


def L_H_of_eps(eps):
    H = -core.Omega_eps(eps)
    IE = I_idx + E_idx
    K = H[np.ix_(IE, IE)]
    nI = len(I_idx)
    A = K[:nI, :nI]; G = K[nI:, nI:]; C = K[:nI, nI:]
    def inv_sqrt(M):
        w, V = np.linalg.eigh(M)
        return V @ np.diag(1.0 / np.sqrt(np.abs(w))) @ V.T
    M = inv_sqrt(A) @ C @ inv_sqrt(G)
    return np.sum(M**2)


if __name__ == "__main__":
    eps_grid = np.concatenate([np.array([0.0]), np.geomspace(1e-4, 1.0, 200)])
    eps_grid = np.sort(eps_grid)
    L_exact = np.array([core.L_cmi_precision(core.Omega_eps(e), I_idx, B_idx, E_idx) for e in eps_grid])
    LH = np.array([L_H_of_eps(e) for e in eps_grid])
    r_formula = 14 * eps_grid / (55 + 14 * eps_grid)
    L_analytic = -0.5 * np.log(1 - r_formula**2)

    assert np.max(np.abs(L_exact - L_analytic)) < 1e-9, "analytic r(eps) formula mismatch!"
    assert np.max(np.abs(LH - r_formula**2)) < 1e-9, "L_H = r^2 identity mismatch!"

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    ax = axes[0]
    ax.plot(eps_grid, L_exact, color=COLOR_INTERIOR, linewidth=2.2, label=r"exact $L_{\{4,5\}}(\varepsilon)$")
    ax.plot(eps_grid, 0.5 * LH, color=COLOR_ACCENT, linewidth=2.0, linestyle="--",
            label=r"weak-leak approx $\frac{1}{2}L_H$")
    ax.set_xlabel(r"$\varepsilon$")
    ax.set_ylabel("nats")
    ax.set_title("A: exact CMI vs. Hessian (weak-leak) approximation")
    ax.legend(fontsize=9)

    ax2 = axes[1]
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = 2 * L_exact / LH
    mask = eps_grid > 0
    ax2.plot(eps_grid[mask], ratio[mask], color=COLOR_EXTERIOR, linewidth=2.0)
    ax2.axhline(1.0, color="gray", linestyle=":", linewidth=1.0)
    ax2.set_xscale("log")
    ax2.set_xlabel(r"$\varepsilon$ (log scale)")
    ax2.set_ylabel(r"$2L/L_H$")
    ax2.set_title(r"B: departure of $2L/L_H$ from unity")

    fig.suptitle("Figure 3 — Exact vs. Hessian-approximate blanket leakage", y=1.02, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "fig3_epsilon_curve"))
    plt.close(fig)

    with open(os.path.join(DATADIR, "fig3_data.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["eps", "L_exact", "L_H", "half_L_H", "ratio_2L_over_LH"])
        for e, le, lh, rt in zip(eps_grid, L_exact, LH, ratio):
            w.writerow([e, le, lh, 0.5*lh, rt])
    print("Figure 3 saved. Analytic identities verified to <1e-9.")
    print(f"L_{{4,5}}(eps=1) = {L_exact[-1]:.11f} (expected 0.02101960808)")
