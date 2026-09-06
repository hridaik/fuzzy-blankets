"""
Parts 3-6: organization-aware LQ steering via backward Riccati + forward state integration.
Exploits linearity in the terminal multiplier mu (m(0)=0 => m(t;mu) = mu*m(t;1)) to avoid
re-integrating the state equation twice.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage3"))
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm
import core
from steering_core import C_VEC, N
from organization_core import F_q, B_S, Q_perp, s_scalar, v_vec


def solve_riccati(Fmat, BBt, lam, T, rtol=1e-9, atol=1e-11):
    def rhs(t, Pflat):
        P = Pflat.reshape(N, N)
        dPdt = -(Fmat.T @ P + P @ Fmat - P @ BBt @ P + lam * Q_perp)
        return dPdt.flatten()
    sol = solve_ivp(rhs, [T, 0.0], np.zeros(N * N), dense_output=True, rtol=rtol, atol=atol,
                     method="RK45")
    return sol  # sol.sol(t) -> Pflat(t); reshape(N,N)


def solve_z(Fmat, BBt, P_sol, T, rtol=1e-9, atol=1e-11):
    def rhs(t, z):
        P = P_sol.sol(t).reshape(N, N)
        return -((Fmat - BBt @ P).T @ z)
    sol = solve_ivp(rhs, [T, 0.0], C_VEC.copy(), dense_output=True, rtol=rtol, atol=atol,
                     method="RK45")
    return sol


def solve_organization_aware(q, T, S, lam, n_eval=800):
    """Returns dict with time grid, m(t), u(t), E, D, Dbar, D_T, D_max, y(T), P_sol, z_sol, mu."""
    Fmat = F_q(q)
    Bmat = B_S(S)
    BBt = Bmat @ Bmat.T

    P_sol = solve_riccati(Fmat, BBt, lam, T)
    z_sol = solve_z(Fmat, BBt, P_sol, T)

    # Augment the mu=1 state ODE with running integrals of u1'u1 and m1'Qperp m1, so that
    # E and D get the SAME adaptive error control as the trajectory itself. A fixed-grid
    # post-hoc trapezoid (even at several thousand points) was found to catastrophically
    # under-resolve a boundary-layer transient at high lambda (D off by ~10x) -- this
    # augmented-state approach is the correct fix, not merely a denser grid.
    def rhs_aug(t, y):
        m1 = y[:N]
        P = P_sol.sol(t).reshape(N, N)
        z = z_sol.sol(t)
        u1 = -Bmat.T @ (P @ m1 + z)
        dm1 = (Fmat - BBt @ P) @ m1 - BBt @ z
        dE1 = np.sum(u1**2)
        dD1 = 0.5 * (m1 @ Q_perp @ m1)
        return np.concatenate([dm1, [dE1], [dD1]])

    y0 = np.zeros(N + 2)
    sol_aug = solve_ivp(rhs_aug, [0.0, T], y0, dense_output=True, rtol=1e-11, atol=1e-13,
                         method="RK45")
    t_grid = np.linspace(0, T, n_eval)
    y_grid = sol_aug.sol(t_grid)
    m1_grid = y_grid[:N, :]
    E1_cum = y_grid[N, :]
    D1_cum = y_grid[N + 1, :]

    y1_T = C_VEC @ m1_grid[:, -1]
    if abs(y1_T) < 1e-13:
        raise ValueError(f"y1(T) too small ({y1_T:.3e}) -- target unreachable / near-singular for q={q},T={T},S={S},lambda={lam}")
    mu = 1.0 / y1_T

    m_grid = mu * m1_grid
    u1_grid = np.zeros((Bmat.shape[1], n_eval))
    for i, t in enumerate(t_grid):
        P = P_sol.sol(t).reshape(N, N)
        z = z_sol.sol(t)
        u1_grid[:, i] = -Bmat.T @ (P @ m1_grid[:, i] + z)
    u_grid = mu * u1_grid

    E = mu**2 * E1_cum[-1]
    D = mu**2 * D1_cum[-1]
    dperp_t = mu**2 * 0.5 * np.einsum('it,ij,jt->t', m1_grid, Q_perp, m1_grid)  # for plotting only
    Dbar = D / T
    D_T = dperp_t[-1]
    # D_max: a uniform grid can miss a narrow boundary-layer peak even though the CUMULATIVE
    # integral (D) is robust (it's part of the adaptively-controlled ODE state above). Also
    # sample at the solver's own adaptive mesh nodes, which are guaranteed dense wherever the
    # dynamics are fast, and take the max over the union.
    m1_adapt = sol_aug.y[:N, :]
    dperp_adapt = mu**2 * 0.5 * np.einsum('it,ij,jt->t', m1_adapt, Q_perp, m1_adapt)
    D_max = max(dperp_t.max(), dperp_adapt.max())
    y_T = C_VEC @ m_grid[:, -1]

    return dict(t=t_grid, m=m_grid, u=u_grid, E=E, D=D, Dbar=Dbar, D_T=D_T, D_max=D_max,
                y_T=y_T, dperp_t=dperp_t, mu=mu, P_sol=P_sol, z_sol=z_sol, q=q, T=T, S=S, lam=lam)


if __name__ == "__main__":
    print("=== Part 5 sanity: single Riccati solve ===")
    res = solve_organization_aware(q=0.0, T=1.0, S=[4], lam=0.0)
    print(f"q=0,T=1,S=[4],lambda=0: E={res['E']:.6f}  D={res['D']:.6f}  y(T)={res['y_T']:.8f} (target 1.0)")
    assert abs(res["y_T"] - 1.0) < 1e-6
    print("OK.")
