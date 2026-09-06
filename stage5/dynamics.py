"""
Stage 5, Sections 6-7: adaptive-interface stochastic dynamics (phenotype y, interface z,
8-node Gaussian moments m,Sigma) and the endogenous-organization diagnostic D_org.

Nondimensional constants tau_x=tau_z=1 (fixed, per spec -- not tuned).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from scipy.integrate import solve_ivp
import core5
import reference as ref

N = core5.N
TAU_X = 1.0
TAU_Z = 1.0
Y_GUARD = 1.5
Z_GUARD = 1.0


def y_rhs(y, u_y):
    return y - y**3 + u_y


def z_rhs(y, z, u_z, tau_z=None):
    # final_patch Part 3 addition: optional tau_z override for the interface-timescale
    # stress test. Defaults to None -> uses module-level TAU_Z (=1.0), IDENTICAL to the
    # original Stage-5 baseline behavior when not explicitly overridden.
    tz = TAU_Z if tau_z is None else tau_z
    return (y - z + u_z) / tz


def moment_rhs(m, Sigma, y, z, u_y, u_z, tau_z=None):
    Om = core5.Omega_of_z(z)
    v = ref.v_of_z(z)
    mu_s = v * y
    dy = y_rhs(y, u_y)
    dz = z_rhs(y, z, u_z, tau_z=tau_z)
    dm = -(Om @ (m - mu_s)) / TAU_X
    dSigma = -(Om @ Sigma + Sigma @ Om - 2 * np.eye(N)) / TAU_X
    return dy, dz, dm, dSigma


def pack(y, z, m, Sigma):
    return np.concatenate([[y, z], m, Sigma.flatten()])


def unpack(state):
    y, z = state[0], state[1]
    m = state[2:2 + N]
    Sigma = state[2 + N:2 + N + N * N].reshape(N, N)
    return y, z, m, Sigma


def make_rhs(u_y_fn, u_z_fn, guard=True, tau_z=None):
    def rhs(t, state):
        y, z, m, Sigma = unpack(state)
        if guard:
            z = np.clip(z, -Z_GUARD, Z_GUARD)
            y = np.clip(y, -Y_GUARD, Y_GUARD)
        u_y = u_y_fn(t, state)
        u_z = u_z_fn(t, state)
        dy, dz, dm, dSigma = moment_rhs(m, Sigma, y, z, u_y, u_z, tau_z=tau_z)
        return pack(dy, dz, dm, dSigma)
    return rhs


def integrate(y0, z0, m0, Sigma0, T, u_y_fn=lambda t, s: 0.0, u_z_fn=lambda t, s: 0.0,
              n_eval=400, rtol=1e-9, atol=1e-11, guard=True, tau_z=None, max_step=None):
    # max_step=None (default) reproduces the exact original Stage-5 baseline (unbounded
    # adaptive step). An explicit max_step is used only by the rate-induced-loss audit,
    # which found that RK45's adaptive step control can occasionally ALIAS OVER a narrow
    # forced transient (skip it entirely) when no step-size ceiling is imposed on a
    # discontinuously-forced u_z(t) -- see rate_induced_audit_core.run_extended.
    state0 = pack(y0, z0, m0, Sigma0)
    rhs = make_rhs(u_y_fn, u_z_fn, guard=guard, tau_z=tau_z)
    t_eval = np.linspace(0, T, n_eval)
    kwargs = dict(rtol=rtol, atol=atol, method="RK45", dense_output=True)
    if max_step is not None:
        kwargs["max_step"] = max_step
    sol = solve_ivp(rhs, [0, T], state0, t_eval=t_eval, **kwargs)
    guard_active = False
    ys, zs, ms, Sigmas = [], [], [], []
    for i in range(len(t_eval)):
        y, z, m, Sigma = unpack(sol.y[:, i])
        if guard and (abs(y) >= Y_GUARD - 1e-6 or abs(z) >= Z_GUARD - 1e-6):
            guard_active = True
        ys.append(y); zs.append(z); ms.append(m); Sigmas.append(Sigma)
    return dict(t=t_eval, y=np.array(ys), z=np.array(zs), m=np.array(ms), Sigma=np.array(Sigmas),
                sol=sol, guard_active=guard_active)


def D_org(m, Sigma, y, z):
    Om = core5.Omega_of_z(z)
    v = ref.v_of_z(z)
    mu_s = v * y
    dm = m - mu_s
    OmSigma = Om @ Sigma
    tr_term = np.trace(OmSigma)
    quad_term = dm @ Om @ dm
    sign, logdet_OmSigma = np.linalg.slogdet(OmSigma)
    val = 0.5 * (tr_term + quad_term - N - logdet_OmSigma)
    return val, sign


if __name__ == "__main__":
    log = []
    def p(s=""):
        print(s); log.append(s)

    p("=== Stage 5, Section 6: equilibrium fixed-point + Gaussian-preservation check ===")
    y0, z0 = -1.0, -1.0
    v0 = ref.v_of_z(z0)
    m0 = v0 * y0
    Sigma0 = np.linalg.inv(core5.Omega_of_z(z0))
    Om0 = core5.Omega_of_z(z0)

    dy0, dz0, dm0, dSigma0 = moment_rhs(m0, Sigma0, y0, z0, 0.0, 0.0)
    p(f"At endpoint-A equilibrium (y=-1,z=-1) with u=0:")
    p(f"  |dy/dt| = {abs(dy0):.3e}  (y - y^3 at y=-1 is exactly 0)")
    p(f"  |dz/dt| = {abs(dz0):.3e}  (y=z=-1)")
    p(f"  max|dm/dt| = {np.max(np.abs(dm0)):.3e}  (m0=mu*(-1,-1) so Omega(m-mu*)=0)")
    p(f"  max|dSigma/dt| = {np.max(np.abs(dSigma0)):.3e}  (Sigma0=Omega^-1 so Omega*Sigma+Sigma*Omega=2I)")
    assert abs(dy0) < 1e-9 and abs(dz0) < 1e-9
    assert np.max(np.abs(dm0)) < 1e-9
    assert np.max(np.abs(dSigma0)) < 1e-9
    p("Fixed point confirmed: with u_y=u_z=0, endpoint-A equilibrium is stationary for (y,z,m,Sigma).")

    p("\nDeterministic-protocol Gaussian preservation: by construction the moment ODEs are the exact "
      "mean/covariance equations of a linear (time-varying, via Omega(z_t)) Ornstein-Uhlenbeck-type SDE "
      "for FIXED deterministic y(t),z(t) protocols, so p_t stays Gaussian for all t (standard OU result: "
      "a Gaussian initial condition evolved under dX = -A(t)(X-b(t))dt + sigma dW remains Gaussian, with "
      "mean/cov obeying exactly these linear ODEs). We additionally verify D_org >= 0 numerically below "
      "as a nonnegativity sanity check on the exact Gaussian KL expression.")

    p("\n=== Section 7: D_org diagnostic ===")
    val0, sign0 = D_org(m0, Sigma0, y0, z0)
    p(f"D_org at initial equilibrium = {val0:.3e} (expect ~0, sign(Omega*Sigma)={sign0})")
    assert abs(val0) < 1e-8

    # nonnegativity stress test: random y,z and random Gaussian (m,Sigma) states
    rng = np.random.default_rng(7)
    min_D = np.inf
    for _ in range(500):
        z = rng.uniform(-1, 1)
        y = rng.uniform(-1.5, 1.5)
        Om = core5.Omega_of_z(z)
        Sig_true = np.linalg.inv(Om)
        # perturb Sigma away from Sigma*(z) while keeping PD, and perturb m away from mu*
        L = np.linalg.cholesky(Sig_true)
        pert = rng.standard_normal((N, N)) * 0.1
        Sigma = Sig_true + 0.05 * (pert @ pert.T)  # PSD perturbation added, stays PD
        m = ref.v_of_z(z) * y + rng.standard_normal(N) * 0.2
        val, sign = D_org(m, Sigma, y, z)
        if sign > 0:
            min_D = min(min_D, val)
    p(f"Min D_org over 500 random perturbed Gaussian states (z in [-1,1]) = {min_D:.3e} (expect >= -tol)")
    assert min_D > -1e-8

    with open(os.path.join(os.path.dirname(__file__), "data", "part6_7_log.txt"), "w") as f:
        f.write("\n".join(log))
    p("\nAll Section 6-7 checks PASSED.")
