"""
Part 7: the TRUE T_ramp -> 0 limit -- instantaneous structural jump.
At t=0, z jumps -1 -> +1 instantaneously while Sigma(0)=Sigma_A* is held fixed (no
time for the covariance to react); then ONLY the B-structure covariance ODE is
integrated (Lambda_K depends on Sigma alone, not on the mean, so y/m are irrelevant
here and are not simulated). Standalone from the main sweep so it can run quickly.
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.integrate import solve_ivp
import core5
import rate_induced_audit_core as aud

AUDIT_DIR = aud.AUDIT_DIR
N = core5.N


def instantaneous_jump_run(T_window=12.0, n_eval=3000, rtol=1e-11, atol=1e-13):
    Om_B = core5.Omega_of_z(1.0)
    Sigma0 = np.linalg.inv(core5.Omega_of_z(-1.0))  # Sigma_A*, held fixed at the jump instant

    def rhs(t, Sigma_flat):
        Sigma = Sigma_flat.reshape(N, N)
        dSigma = -(Om_B @ Sigma + Sigma @ Om_B - 2 * np.eye(N))
        return dSigma.flatten()

    sol = solve_ivp(rhs, [0, T_window], Sigma0.flatten(), rtol=rtol, atol=atol,
                     method="RK45", dense_output=True)
    t_grid = np.linspace(0, T_window, n_eval)
    Sigmas = np.array([sol.sol(t).reshape(N, N) for t in t_grid])
    return t_grid, Sigmas, sol


if __name__ == "__main__":
    log = []
    def p(s=""):
        print(s); log.append(s)

    p("=== PART 7: instantaneous-jump (T_ramp->0) limit ===")
    p("z: -1 -> +1 instantaneously at t=0; Sigma(0)=Sigma_A*=Omega(-1)^-1 (no reaction time); "
      "then integrate dSigma/dt = -(Omega(+1) Sigma + Sigma Omega(+1) - 2I) alone (Lambda_K depends "
      "only on Sigma, so y/m are irrelevant to this diagnostic and are not simulated).")

    t_grid, Sigmas, sol = instantaneous_jump_run()
    n = len(t_grid)
    LK = {K: np.zeros(n) for K in (1, 2, 3, 4)}
    Kdelta = np.full(n, np.nan)
    families3 = [None] * n
    min_eig = np.inf
    for i in range(n):
        min_eig = min(min_eig, np.linalg.eigvalsh(Sigmas[i]).min())
        table = aud.full_candidate_table(Sigmas[i])
        allK = aud.lambda_all_K(table, Ks=(1, 2, 3, 4))
        for K in (1, 2, 3, 4):
            LK[K][i] = allK[K][0]
        Kd, fam = aud.min_card_family(table)
        Kdelta[i] = Kd if Kd is not None else np.nan
        families3[i] = allK[3][1]

    p(f"SPD check: min eigenvalue of Sigma(t) over the whole window = {min_eig:.3e} (must be > 0)")
    assert min_eig > 0

    for K in (1, 2, 3, 4):
        i_max = int(np.argmax(LK[K]))
        p(f"  K={K}: max_t Lambda_K(t) = {LK[K][i_max]:.6e} at t={t_grid[i_max]:.4f}  "
          f"(t=0 value = {LK[K][0]:.6e}, t={t_grid[-1]:.1f} value = {LK[K][-1]:.3e})")

    p(f"\nLambda_3(t) throughout relaxation from the instantaneous jump -- does it remain small?")
    p(f"  max_t Lambda_3 = {LK[3].max():.6e}  (compare: old Fig-3 peak was ~3.79e-05 at T_ramp~0.2 "
      f"during-ramp-only; small-T_ramp full-event peaks from the main sweep, if similar magnitude, "
      f"indicate this IS effectively the small-T_ramp full-event limit)")
    p(f"  Lambda_3(t=0) = {LK[3][0]:.3e} (expect ~0: Sigma_A* has {{4,5,6}} as an exact separator, "
      f"Section 3)")

    # boundary family through relaxation (sampled)
    p("\nMinimizing K=3 boundary family through relaxation (sampled every ~10% of window):")
    for i in range(0, n, max(1, n // 12)):
        p(f"  t={t_grid[i]:6.3f}  Lambda_3={LK[3][i]:.4e}  K_delta={Kdelta[i]}  "
          f"K=3 family={families3[i]}")

    outcsv = os.path.join(AUDIT_DIR, "instantaneous_jump.csv")
    with open(outcsv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "Lambda1", "Lambda2", "Lambda3", "Lambda4", "Kdelta"])
        for i in range(n):
            w.writerow([t_grid[i], LK[1][i], LK[2][i], LK[3][i], LK[4][i], Kdelta[i]])
    np.savez(os.path.join(AUDIT_DIR, "instantaneous_jump.npz"), t=t_grid, L1=LK[1], L2=LK[2],
             L3=LK[3], L4=LK[4], Kdelta=Kdelta, families3=np.array(families3, dtype=object))
    with open(os.path.join(AUDIT_DIR, "part7_log.txt"), "w") as f:
        f.write("\n".join(log))
    p(f"\nSaved {outcsv} and instantaneous_jump.npz")
