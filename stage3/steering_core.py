"""
Track 2 shared definitions: controlled linear dynamics on the verified base model Omega0.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from scipy.linalg import expm, solve_lyapunov
import core

N = core.N
e3v = np.zeros(N); e3v[core.idx[3]] = 1.0
e6v = np.zeros(N); e6v[core.idx[6]] = 1.0


def Q_q(q):
    return q * (np.outer(e3v, e6v) - np.outer(e6v, e3v))


def A_q(q):
    return (np.eye(N) + Q_q(q)) @ core.Omega0


def J_q(q):
    return -A_q(q)


def e_k(k):
    v = np.zeros(N)
    v[core.idx[k]] = 1.0
    return v


C_VEC = np.zeros(N)
for _n in [1, 2, 3]:
    C_VEC[core.idx[_n]] = 1.0 / 3.0


def h_k(t_array, q, k):
    """h_k(t;q) = c^T e^{-A_q t} e_k, evaluated at each t in t_array."""
    Aq = A_q(q)
    ek = e_k(k)
    out = np.empty(len(t_array))
    for i, t in enumerate(t_array):
        out[i] = C_VEC @ expm(-Aq * t) @ ek
    return out


def eta_k_lyapunov(T, q, k):
    """Finite-horizon controllability Gramian scalar output eta_k(T;q) = c^T W_k(T;q) c,
    via the infinite-horizon Lyapunov equation + closed-form finite-horizon correction."""
    Aq = A_q(q)
    ek = e_k(k)
    W_inf = solve_lyapunov(Aq, np.outer(ek, ek))
    EAT = expm(-Aq * T)
    W_T = W_inf - EAT @ W_inf @ EAT.T
    return float(C_VEC @ W_T @ C_VEC), W_T, W_inf


def eta_k_quadrature(T, q, k, n_grid=4000):
    """Independent check: eta_k(T;q) = integral_0^T h_k(t;q)^2 dt via Simpson's rule."""
    from scipy.integrate import simpson
    t_grid = np.linspace(0, T, n_grid)
    h = h_k(t_grid, q, k)
    return simpson(h**2, x=t_grid)


def g_k(q, k):
    """Static gain g_k(q) = c^T A_q^{-1} e_k."""
    Aq = A_q(q)
    ek = e_k(k)
    x = np.linalg.solve(Aq, ek)
    return float(C_VEC @ x)


def s_k(t_array, q, k):
    """Step response s_k(t;q) = c^T A_q^{-1} (I - e^{-A_q t}) e_k."""
    Aq = A_q(q)
    ek = e_k(k)
    Ainv_ek = np.linalg.solve(Aq, ek)
    out = np.empty(len(t_array))
    for i, t in enumerate(t_array):
        out[i] = C_VEC @ (Ainv_ek - expm(-Aq * t) @ Ainv_ek)
    return out
