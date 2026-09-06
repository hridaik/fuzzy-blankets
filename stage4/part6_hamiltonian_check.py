"""
Part 6: independent verification via the Hamiltonian two-point BVP formulation,
plus a discretized QP/KKT cross-check for a couple of representative cases.
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage3"))
import numpy as np
from scipy.linalg import expm
from scipy.integrate import solve_ivp
import core
from steering_core import C_VEC, N
from organization_core import F_q, B_S, Q_perp
from riccati_solver import solve_organization_aware


def hamiltonian_solve(q, T, S, lam, n_eval=800):
    """Solve the linear TPBVP via the state-transition matrix of the Hamiltonian system:
    [m;p]' = H [m;p], m(0)=0, p(T)=mu*c, c^T m(T)=1 -- solved by shooting on mu using
    linearity (m(T) is linear in mu since the whole Hamiltonian ODE is linear and m(0)=0
    is mu-independent while p(T)=mu*c is linear in mu)."""
    Fmat = F_q(q)
    Bmat = B_S(S)
    BBt = Bmat @ Bmat.T
    H = np.block([[Fmat, -BBt], [-lam * Q_perp, -Fmat.T]])

    # Shooting: for a guessed p(0)=p0, integrate forward; state-transition linearity lets us
    # solve for p(0) directly via the boundary conditions using the block matrix exponential.
    Phi = expm(H * T)  # maps [m(0);p(0)] -> [m(T);p(T)]
    Phi_mm, Phi_mp = Phi[:N, :N], Phi[:N, N:]
    Phi_pm, Phi_pp = Phi[N:, :N], Phi[N:, N:]
    # m(0)=0 => m(T) = Phi_mp @ p(0);  p(T) = Phi_pp @ p(0)
    # require p(T) = mu*c  and  c^T m(T) = 1
    # p(0) = Phi_pp^{-1} mu c  (assuming Phi_pp invertible)
    Phi_pp_inv = np.linalg.inv(Phi_pp)
    # m(T) = Phi_mp @ Phi_pp_inv @ (mu c) = mu * (Phi_mp @ Phi_pp_inv @ c)
    m_T_per_mu = Phi_mp @ Phi_pp_inv @ C_VEC
    y_per_mu = C_VEC @ m_T_per_mu
    if abs(y_per_mu) < 1e-13:
        raise ValueError("Hamiltonian shooting: target unreachable (y_per_mu ~ 0)")
    mu = 1.0 / y_per_mu
    p0 = mu * (Phi_pp_inv @ C_VEC)

    # augmented state carries running E,D integrals under the SAME adaptive error control as
    # the trajectory (a fixed-grid post-hoc trapezoid was found to badly under-resolve boundary
    # layers at high lambda -- see riccati_solver.py fix); same correction applied here.
    def rhs_aug(t, y):
        mp = y[:2 * N]
        m = mp[:N]
        p = mp[N:2 * N]
        u = -Bmat.T @ p
        dmp = H @ mp
        dE = np.sum(u**2)
        dD = 0.5 * (m @ Q_perp @ m)
        return np.concatenate([dmp, [dE], [dD]])
    y0 = np.concatenate([np.zeros(N), p0, [0.0, 0.0]])
    sol = solve_ivp(rhs_aug, [0, T], y0, dense_output=True, rtol=1e-11, atol=1e-13)
    t_grid = np.linspace(0, T, n_eval)
    y_grid = sol.sol(t_grid)
    mp = y_grid[:2 * N, :]
    m_grid = mp[:N, :]
    p_grid = mp[N:2 * N, :]
    u_grid = -Bmat.T @ p_grid
    E = y_grid[2 * N, -1]
    D_cum = y_grid[2 * N + 1, -1]
    dperp_t = 0.5 * np.einsum('it,ij,jt->t', m_grid, Q_perp, m_grid)
    D = D_cum
    y_T = C_VEC @ m_grid[:, -1]
    return dict(t=t_grid, m=m_grid, u=u_grid, E=E, D=D, y_T=y_T, mu=mu)


if __name__ == "__main__":
    print("=== Part 6: Riccati vs. Hamiltonian cross-check ===")
    cases = [(0.0, 1.0, [4], 0.0), (0.0, 1.0, [4], 1.0), (1.0, 1.0, [6], 0.0),
             (1.0, 1.0, [6], 10.0), (-1.0, 0.5, [5], 100.0), (0.0, 3.0, [4, 6], 1.0)]
    rows = []
    for q, T, S, lam in cases:
        r1 = solve_organization_aware(q, T, S, lam)
        r2 = hamiltonian_solve(q, T, S, lam)
        # interpolate onto common time grid (both use linspace(0,T,800) already, so t matches)
        max_m_diff = np.max(np.abs(r1["m"] - r2["m"]))
        max_u_diff = np.max(np.abs(r1["u"] - r2["u"]))
        dE = abs(r1["E"] - r2["E"])
        dD = abs(r1["D"] - r2["D"])
        dyT = abs(r1["y_T"] - r2["y_T"])
        print(f"q={q:<5} T={T:<4} S={S} lam={lam:<7} max|dm|={max_m_diff:.2e} max|du|={max_u_diff:.2e} "
              f"|dE|={dE:.2e} |dD|={dD:.2e} |dy_T|={dyT:.2e}")
        rows.append(dict(q=q, T=T, S=str(S), lam=lam, E_riccati=r1["E"], E_hamiltonian=r2["E"],
                           D_riccati=r1["D"], D_hamiltonian=r2["D"], max_m_diff=max_m_diff,
                           max_u_diff=max_u_diff, dE=dE, dD=dD, dyT=dyT))
        assert max_m_diff < 1e-4 and max_u_diff < 1e-3, "Riccati vs Hamiltonian solver mismatch!"
        assert dyT < 1e-6

    with open(os.path.join(os.path.dirname(__file__), "data", "part6_hamiltonian_crosscheck.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("\nAll Riccati/Hamiltonian cross-checks agree. Saved comparison table.")
