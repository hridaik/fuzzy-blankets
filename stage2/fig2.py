import sys, os, itertools, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import core
from figstyle import save_all, COLOR_ACCENT, COLOR_EDGE

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

rest_nodes = core.REST_NODES
I_idx = core.I_IDX


def all_candidates_L(Sigma):
    rows = []
    for rr in range(len(rest_nodes) + 1):
        for Bc in itertools.combinations(rest_nodes, rr):
            B_idx = [core.idx[nn] for nn in Bc]
            E_idx = [core.idx[nn] for nn in rest_nodes if nn not in Bc]
            L = core.L_cmi_cov_joint(Sigma, I_idx, B_idx, E_idx)
            rows.append((Bc, len(Bc), L))
    return rows


def pareto_mask(rows, tol=core.TOL):
    def snap(v):
        return 0.0 if abs(v) < tol else v
    mask = []
    for i, (B, s, L) in enumerate(rows):
        Ls = snap(L)
        dominated = False
        for j, (B2, s2, L2) in enumerate(rows):
            if i == j:
                continue
            L2s = snap(L2)
            if s2 <= s and L2s <= Ls and (s2 < s or L2s < Ls):
                dominated = True
                break
        mask.append(not dominated)
    return mask


if __name__ == "__main__":
    rows0 = all_candidates_L(core.Sigma0)
    Sigma_eps1 = np.linalg.inv(core.Omega_eps(1.0))
    rows1 = all_candidates_L(Sigma_eps1)

    mask0 = pareto_mask(rows0)
    mask1 = pareto_mask(rows1)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=False)
    rng = np.random.default_rng(0)

    for ax, rows, mask, title, labelset in [
        (axes[0], rows0, mask0, r"A: $\varepsilon=0$", [(), (4,), (5,), (4, 5)]),
        (axes[1], rows1, mask1, r"B: $\varepsilon=1$", [(), (4,), (4, 5), (4, 5, 6)]),
    ]:
        xs = np.array([s for _, s, _ in rows], dtype=float)
        ys = np.array([L for _, _, L in rows])
        jitter = rng.uniform(-0.08, 0.08, size=len(xs))
        ax.scatter(xs + jitter, ys, s=28, color=COLOR_EDGE, alpha=0.55, label="all 32 candidates", zorder=2)
        frontier_idx = [i for i, m in enumerate(mask) if m]
        fx = xs[frontier_idx]; fy = ys[frontier_idx]
        order = np.argsort(fx)
        ax.plot(fx[order], fy[order], color=COLOR_ACCENT, linewidth=2.0, zorder=3, marker="o",
                markersize=7, label="Pareto frontier")
        for Bc in labelset:
            i = next(k for k, (B, s, L) in enumerate(rows) if B == Bc)
            ax.annotate("$\\varnothing$" if Bc == () else "{" + ",".join(map(str, Bc)) + "}",
                        (xs[i], ys[i]), textcoords="offset points", xytext=(6, 6), fontsize=9)
        ax.set_xlabel("$|B|$ (boundary size)")
        ax.set_ylabel("$L(B)$ [nats]")
        ax.set_title(title)
        ax.set_xticks(range(0, 6))
        if ax is axes[0]:
            ax.legend(fontsize=8, loc="upper right")

    fig.suptitle("Figure 2 — Boundary complexity vs. leakage, fixed $I=\\{1,2,3\\}$", y=1.02, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "fig2_boundary_vs_leakage"))
    plt.close(fig)

    with open(os.path.join(DATADIR, "fig2_data.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["eps", "B", "size", "L", "on_pareto_frontier"])
        for (B, s, L), m in zip(rows0, mask0):
            w.writerow([0, str(B), s, L, m])
        for (B, s, L), m in zip(rows1, mask1):
            w.writerow([1, str(B), s, L, m])
    print("Figure 2 saved.")
    print("Frontier eps=0:", [rows0[i][0] for i, m in enumerate(mask0) if m])
    print("Frontier eps=1:", [rows1[i][0] for i, m in enumerate(mask1) if m])
