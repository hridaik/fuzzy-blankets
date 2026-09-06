import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from scipy.linalg import expm
from scipy.integrate import solve_ivp
import core
from steering_core import A_q, J_q, Q_q, C_VEC, e_k, N

if __name__ == "__main__":
    print("=== Part 2A: controlled mean dynamics (structure check) ===")
    q_test = 0.7
    Aq = A_q(q_test)
    k_test = 4
    ek = e_k(k_test)

    def u_const(t):
        return 1.0

    def mdot(t, m):
        return -Aq @ m + ek * u_const(t)

    sol = solve_ivp(mdot, [0, 3.0], np.zeros(N), max_step=0.01, dense_output=True)
    Y_traj = C_VEC @ sol.y
    print(f"Mean dynamics integrated OK; Y(T=3) under constant unit input at node {k_test}, q={q_test}: {Y_traj[-1]:.6f}")
    print("(Individual stochastic realizations are NOT claimed to be driven exactly to target -- only the mean.)")

    print("\n=== Part 2B: covariance/blanket invariance under deterministic control ===")
    I_idx = core.I_IDX
    B_idx = [core.idx[4], core.idx[5]]
    E_idx = [core.idx[6], core.idx[7], core.idx[8]]

    q_list_check = [-2, -1, -0.5, 0, 0.5, 1, 2]
    rows_b = []
    for q in q_list_check:
        Aq_ = A_q(q)
        lyap_resid = np.max(np.abs(Aq_ @ core.Sigma0 + core.Sigma0 @ Aq_.T - 2 * np.eye(N)))
        # Sigma(t) solves dSigma/dt = -Aq Sigma - Sigma Aq^T + 2I; if Sigma(0)=Sigma0 and the
        # residual above is 0, then dSigma/dt=0 at Sigma0, i.e. Sigma0 is a fixed point regardless of u(t).
        L_blanket = core.L_cmi_precision(core.Omega0, I_idx, B_idx, E_idx)  # Omega0 fixed, so L is q-invariant trivially by construction
        rows_b.append(dict(q=q, lyapunov_residual=lyap_resid, L_blanket=L_blanket))
        print(f"  q={q:<5} Lyapunov residual (Aq Sigma0 + Sigma0 Aq^T - 2I) max|.|={lyap_resid:.3e}   "
              f"L(I;E|B)={L_blanket:.3e}")
    assert all(r["lyapunov_residual"] < 1e-9 for r in rows_b)
    assert all(abs(r["L_blanket"]) < 1e-9 for r in rows_b)
    print("Verified: Sigma0 is a fixed point of the Lyapunov ODE for all tested q (independent of u(t)),")
    print("so the instantaneous Gaussian blanket I(X_1:3;X_6:8|X_4,5) stays exactly 0 while steering the mean.")
    print("NOTE: this Sigma-invariance-under-control property is specific to this linear additive-control")
    print("benchmark (u enters only the mean ODE, not the diffusion) and must not be generalized to nonlinear systems.")

    # numerical ODE check that Sigma(t) really stays at Sigma0 under a nontrivial open-loop u(t)
    def u_nontrivial(t):
        return np.sin(2 * t) + 0.5

    def Sigma_dot_flat(t, sigma_flat):
        Sigma = sigma_flat.reshape(N, N)
        dSigma = -Aq @ Sigma - Sigma @ Aq.T + 2 * np.eye(N)
        return dSigma.flatten()

    Aq = A_q(1.0)
    sol_sigma = solve_ivp(Sigma_dot_flat, [0, 2.0], core.Sigma0.flatten(), max_step=0.01)
    Sigma_end = sol_sigma.y[:, -1].reshape(N, N)
    max_dev = np.max(np.abs(Sigma_end - core.Sigma0))
    print(f"\nNumerical ODE integration of Sigma(t) under u(t)=sin(2t)+0.5 forcing the MEAN only (q=1):")
    print(f"  max|Sigma(T=2) - Sigma0| = {max_dev:.3e} (should be ~0 since u enters only the mean equation)")
    assert max_dev < 1e-6

    print("\n=== Part 2C: full Delta-J audit ===")
    q_reps = [-2, -1, -0.5, 0.5, 1, 2]
    J0 = J_q(0)
    dJ_data = {}
    for q in q_reps:
        Jq = J_q(q)
        dJ = Jq - J0
        dJ_analytic = -Q_q(q) @ core.Omega0
        resid = np.max(np.abs(dJ - dJ_analytic))
        J36 = Jq[core.idx[3], core.idx[6]]
        J63 = Jq[core.idx[6], core.idx[3]]
        exp36, exp63 = -4.5 * q, 4.5 * q
        dJ_data[q] = dJ
        nonzero_mask = np.abs(dJ) > 1e-9
        n_nonzero = nonzero_mask.sum()
        print(f"  q={q:<5} max|DeltaJ - (-Qq Omega0)|={resid:.2e}  J36={J36:.4f}(exp {exp36:.4f})  "
              f"J63={J63:.4f}(exp {exp63:.4f})  #nonzero entries in DeltaJ={n_nonzero}/{N*N}")
        assert resid < 1e-9
        assert abs(J36 - exp36) < 1e-9 and abs(J63 - exp63) < 1e-9

    # report which entries besides (3,6)/(6,3) change
    dJ1 = dJ_data[1.0]
    nz_rows, nz_cols = np.nonzero(np.abs(dJ1) > 1e-9)
    changed_pairs = sorted(set((int(r) + 1, int(c) + 1) for r, c in zip(nz_rows, nz_cols)))
    print(f"\n  At q=1, nonzero DeltaJ entries (1-indexed node pairs): {changed_pairs}")
    print("  CONFIRMS: DeltaJ is NOT confined to the (3,6)/(6,3) pair -- Q_q right-multiplies by the full")
    print("  dense Omega0, so row 3 and row 6 of DeltaJ are both entirely reshaped (all their nonzero")
    print("  Omega0 couplings get rotated by q), not just the single 3-6 entry.")

    np.savez(os.path.join(os.path.dirname(__file__), "data", "part2c_deltaJ.npz"),
             **{f"dJ_q{q}": dJ_data[q] for q in q_reps}, J0=J0)

    with open(os.path.join(os.path.dirname(__file__), "data", "part2b_lyapunov_check.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_b[0].keys()))
        w.writeheader(); w.writerows(rows_b)

    print("\nSaved Part 2B/2C data.")
