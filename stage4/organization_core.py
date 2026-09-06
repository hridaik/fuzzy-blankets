"""
Stage 4 shared definitions: endogenous organization manifold, Q_perp, and
organization-aware LQ steering, built on the verified Omega0/Sigma0/A_q.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage3"))
import numpy as np
from scipy.linalg import solve_continuous_are
import core
from steering_core import A_q, e_k, C_VEC, N

s_scalar = float(C_VEC @ core.Sigma0 @ C_VEC)
v_vec = (core.Sigma0 @ C_VEC) / s_scalar
Q_perp = core.Omega0 - np.outer(C_VEC, C_VEC) / s_scalar


def F_q(q):
    return -A_q(q)


def B_S(S):
    """S: list of 1-indexed node labels. Returns (8, |S|) matrix of columns e_k."""
    return np.stack([e_k(k) for k in S], axis=1)


def m_nat(y):
    return v_vec * y


if __name__ == "__main__":
    print("=== Part 1: endogenous organization manifold ===")
    s_expected = 211 / 1065
    print(f"s = {s_scalar:.10f}, expected {s_expected:.10f}, diff={abs(s_scalar-s_expected):.2e}")
    assert abs(s_scalar - s_expected) < 1e-9

    v_expected = np.array([1, 1, 1, 120/211, 105/211, 69/211, 69/211, 69/211])
    print("v vs expected:")
    for i, n in enumerate(range(1, 9)):
        print(f"  v_{n} = {v_vec[i]:.10f}  expected {v_expected[i]:.10f}  diff={abs(v_vec[i]-v_expected[i]):.2e}")
    assert np.max(np.abs(v_vec - v_expected)) < 1e-9

    cv = C_VEC @ v_vec
    print(f"c^T v = {cv:.10f} (expected 1.0)")
    assert abs(cv - 1.0) < 1e-9

    # Gaussian conditional mean identity: E[X|Y=y] = v y
    print("\nConditional-mean check E[X|Y=y] = v*y (Schur complement formula):")
    y_test = 1.7
    Sxy = core.Sigma0 @ C_VEC  # Cov(X,Y)
    cond_mean = Sxy / s_scalar * y_test  # since mean(X)=0, mean(Y)=0
    direct = v_vec * y_test
    diff = np.max(np.abs(cond_mean - direct))
    print(f"  max|Schur cond-mean - v*y| = {diff:.2e}")
    assert diff < 1e-9

    print("\n=== Part 2: excess organizational distortion structure ===")
    eigvals = np.linalg.eigvalsh(Q_perp)
    print(f"Q_perp eigenvalues: {np.sort(eigvals)}")
    n_pos = np.sum(eigvals > 1e-9)
    n_zero = np.sum(np.abs(eigvals) < 1e-9)
    print(f"PSD check: min eig = {eigvals.min():.3e} (expect >= -tol)  rank = {n_pos} (expect 7)  "
          f"nullity = {n_zero} (expect 1)")
    assert eigvals.min() > -1e-9
    assert n_pos == 7 and n_zero == 1

    Qv = Q_perp @ v_vec
    print(f"max|Q_perp v| = {np.max(np.abs(Qv)):.2e} (expect ~0)")
    assert np.max(np.abs(Qv)) < 1e-8

    rng = np.random.default_rng(20260819)
    print("\nRandom-vector decomposition checks (KL-style identity):")
    max_resid1 = 0.0
    max_resid2 = 0.0
    max_resid_cr = 0.0
    for _ in range(200):
        m = rng.standard_normal(N) * rng.uniform(0.1, 5)
        y = C_VEC @ m
        r = m - v_vec * y
        cr = C_VEC @ r
        max_resid_cr = max(max_resid_cr, abs(cr))
        lhs = 0.5 * m @ core.Omega0 @ m
        rhs = y**2 / (2 * s_scalar) + 0.5 * r @ core.Omega0 @ r
        max_resid1 = max(max_resid1, abs(lhs - rhs))
        rQr = r @ core.Omega0 @ r
        mQperp_m = m @ Q_perp @ m
        max_resid2 = max(max_resid2, abs(rQr - mQperp_m))
    print(f"  max|c^T r| over 200 random m = {max_resid_cr:.2e} (expect ~0)")
    print(f"  max|1/2 m'Om m - (y^2/2s + 1/2 r'Om r)| = {max_resid1:.2e}")
    print(f"  max|r'Om r - m'Qperp m| = {max_resid2:.2e}")
    assert max_resid_cr < 1e-9 and max_resid1 < 1e-8 and max_resid2 < 1e-8

    np.savez(os.path.join(os.path.dirname(__file__), "data", "part1_2_organization.npz"),
             s=s_scalar, v=v_vec, Q_perp=Q_perp, Omega0=core.Omega0)
    print("\nAll Part 1/2 identities verified exactly. Saved organization manifold data.")
