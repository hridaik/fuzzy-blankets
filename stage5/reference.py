"""
Stage 5, Section 5: local endogenous reference distribution p*_{y,z} = N(mu*(y,z), Sigma*(z)).
Sigma*(z) = Omega(z)^-1, c fixed to the 1/3*(1,1,1,0,...,0) phenotype-readout vector
(the same interior-average convention as core5/organization_core in earlier stages).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import core5

N = core5.N
C_VEC = np.zeros(N)
for n in [1, 2, 3]:
    C_VEC[core5.idx[n]] = 1.0 / 3.0


def Sigma_star(z):
    return np.linalg.inv(core5.Omega_of_z(z))


def s_of_z(z, Sigma=None):
    Sigma = Sigma_star(z) if Sigma is None else Sigma
    return float(C_VEC @ Sigma @ C_VEC)


def v_of_z(z, Sigma=None):
    Sigma = Sigma_star(z) if Sigma is None else Sigma
    s = s_of_z(z, Sigma)
    return (Sigma @ C_VEC) / s


def mu_star(y, z, v=None):
    if v is None:
        v = v_of_z(z)
    return v * y


if __name__ == "__main__":
    log = []
    def p(s=""):
        print(s); log.append(s)

    p("=== Stage 5, Section 5: endogenous reference distribution p*_{y,z} ===")
    z_grid = np.linspace(-1, 1, 41)
    max_cv_err = 0.0
    max_qp_err = 0.0
    rng = np.random.default_rng(20260819)
    s_list, v_list = [], []
    for z in z_grid:
        Om = core5.Omega_of_z(z)
        Sig = np.linalg.inv(Om)
        s = s_of_z(z, Sig)
        v = v_of_z(z, Sig)
        s_list.append(s); v_list.append(v)
        cv = C_VEC @ v
        max_cv_err = max(max_cv_err, abs(cv - 1.0))

        # independent numerical verification that mu*(y,z)=v*y solves
        # min_mu 1/2 mu' Omega mu s.t. c'mu=y, via Lagrange stationarity: Omega mu = lam c, c'mu=y
        # => mu = lam Sigma c, y = lam c'Sigma c = lam*s => lam=y/s => mu = (Sigma c / s) y = v*y.
        y_test = rng.uniform(-2, 2)
        mu_claim = v * y_test
        lam = np.linalg.lstsq(np.vstack([Om, C_VEC]), np.concatenate([Om @ mu_claim, [y_test]]), rcond=None)
        # direct KKT residual check instead of lstsq re-derivation:
        # stationarity residual: Omega mu - lam* c should be ~0 for lam*=y/s
        lam_star = y_test / s
        resid_stat = np.max(np.abs(Om @ mu_claim - lam_star * C_VEC))
        resid_constr = abs(C_VEC @ mu_claim - y_test)
        max_qp_err = max(max_qp_err, resid_stat, resid_constr)

        # also brute-force compare against a numerical QP solve via projected-gradient-free
        # closed form cross-check: minimize over mu on constraint by scanning small perturbations
        # orthogonal to c in the Omega metric direction (finite-difference optimality check)
        eps = 1e-6
        f0 = 0.5 * mu_claim @ Om @ mu_claim
        # random direction d with c'd = 0
        d = rng.standard_normal(N)
        d = d - C_VEC * (C_VEC @ d) / (C_VEC @ C_VEC)
        f_plus = 0.5 * (mu_claim + eps * d) @ Om @ (mu_claim + eps * d)
        f_minus = 0.5 * (mu_claim - eps * d) @ Om @ (mu_claim - eps * d)
        # first-order optimality: f_plus - f0 and f_minus - f0 should both be >= -O(eps^2) (numerical noise)
        assert f_plus - f0 > -1e-9 and f_minus - f0 > -1e-9

    p(f"max|c^T v(z) - 1| over grid = {max_cv_err:.2e}")
    p(f"max KKT-stationarity/constraint residual for mu*(y,z) QP = {max_qp_err:.2e}")
    p("Finite-difference optimality check (perturbations orthogonal to c in mu-space) passed at all sampled z.")
    assert max_cv_err < 1e-9
    assert max_qp_err < 1e-8

    p(f"\nSpot values: v(-1) = {v_list[0]}\n            v(0)  = {v_list[len(z_grid)//2]}\n            v(+1) = {v_list[-1]}")
    p(f"s(-1)={s_list[0]:.8f}  s(0)={s_list[len(z_grid)//2]:.8f}  s(+1)={s_list[-1]:.8f}")

    np.savez(os.path.join(os.path.dirname(__file__), "data", "part5_reference.npz"),
             z_grid=z_grid, s=np.array(s_list), v=np.array(v_list), C_VEC=C_VEC)
    with open(os.path.join(os.path.dirname(__file__), "data", "part5_log.txt"), "w") as f:
        f.write("\n".join(log))
    p("\nAll Section 5 checks PASSED.")
