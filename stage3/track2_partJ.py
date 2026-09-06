import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from steering_core import eta_k_lyapunov

TIE_TOL_REL = 1e-3  # explicit relative tie tolerance for "effectively tied" actuators

if __name__ == "__main__":
    print("=== Part 2J: actuator rankings over (q,T) grid ===")
    q_grid = np.linspace(-2, 2, 81)
    T_grid = np.geomspace(1e-3, 10, 81)

    full_set = list(range(1, 9))
    ext_set = [4, 5, 6, 7, 8]

    t0 = time.time()
    eta_all = np.zeros((len(q_grid), len(T_grid), 8))  # index k-1
    n_singular = 0
    for iq, q in enumerate(q_grid):
        for k in range(1, 9):
            for iT, T in enumerate(T_grid):
                eta, _, _ = eta_k_lyapunov(T, q, k)
                if eta <= 0 or not np.isfinite(eta):
                    n_singular += 1
                    eta = np.nan
                eta_all[iq, iT, k - 1] = eta
    print(f"Computed eta_k(T;q) grid: {len(q_grid)} x {len(T_grid)} x 8 nodes in {time.time()-t0:.1f}s "
          f"({n_singular} non-finite entries)")

    E_all = 1.0 / eta_all  # E*_k(T;q) at Y*=1

    def rank_grid(node_list):
        idxs = [k - 1 for k in node_list]
        E_sub = E_all[:, :, idxs]  # (nq, nT, len(node_list))
        best_idx = np.nanargmin(E_sub, axis=2)
        best_E = np.nanmin(E_sub, axis=2)
        E_sorted = np.sort(E_sub, axis=2)
        second_best_E = E_sorted[:, :, 1] if E_sub.shape[2] > 1 else np.full_like(best_E, np.nan)
        ratio = second_best_E / best_E
        # ties: all actuators within TIE_TOL_REL relative energy of the best
        tie_mask = np.abs(E_sub - best_E[:, :, None]) / best_E[:, :, None] < TIE_TOL_REL
        n_tied = tie_mask.sum(axis=2)
        return dict(best_node=np.array(node_list)[best_idx], best_E=best_E,
                    log10_ratio_2nd_over_best=np.log10(ratio), n_tied=n_tied)

    print("\nFull actuator set (1..8):")
    res_full = rank_grid(full_set)
    print("Non-internal/external-access set (4..8) [scientifically primary comparison]:")
    res_ext = rank_grid(ext_set)

    n_tied_cells_ext = np.sum(res_ext["n_tied"] > 1)
    print(f"  Cells with >1 tied actuator (tol={TIE_TOL_REL}) in external-access set: "
          f"{n_tied_cells_ext} / {res_ext['n_tied'].size}")

    np.savez(os.path.join(os.path.dirname(__file__), "data", "part2j_actuator_grid.npz"),
              q_grid=q_grid, T_grid=T_grid, eta_all=eta_all, E_all=E_all,
              best_node_full=res_full["best_node"], best_E_full=res_full["best_E"],
              log10ratio_full=res_full["log10_ratio_2nd_over_best"], n_tied_full=res_full["n_tied"],
              best_node_ext=res_ext["best_node"], best_E_ext=res_ext["best_E"],
              log10ratio_ext=res_ext["log10_ratio_2nd_over_best"], n_tied_ext=res_ext["n_tied"],
              tie_tol_rel=TIE_TOL_REL)
    print(f"\nSaved actuator ranking grid ({eta_all.nbytes/1e6:.1f} MB raw eta array).")

    # -------------------------------------------------------------------
    # finite-T crossover between node 4 and node 6 (numerical companion to Part 2I's analytic q*)
    # -------------------------------------------------------------------
    print("\n=== Finite-T crossover check: node 6 vs node 4 (companion to analytic q*=6/7, -6/11) ===")
    T_small_list = [1e-3, 1e-2, 1e-1, 1.0]
    for T in T_small_list:
        q_scan = np.linspace(-2, 2, 4001)
        E4 = np.array([1.0 / eta_k_lyapunov(T, q, 4)[0] for q in q_scan])
        E6 = np.array([1.0 / eta_k_lyapunov(T, q, 6)[0] for q in q_scan])
        diff = E6 - E4  # negative where node 6 is MORE efficient (lower energy) than node 4
        sign_changes = np.where(np.diff(np.sign(diff)) != 0)[0]
        crossovers = [float(q_scan[i]) for i in sign_changes]
        print(f"  T={T:<6} numerical crossovers (E6=E4): {[f'{c:.4f}' for c in crossovers]}  "
              f"(analytic asymptotic q*: -6/11={-6/11:.4f}, 6/7={6/7:.4f}; need not match exactly at finite T)")
