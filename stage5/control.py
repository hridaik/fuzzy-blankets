"""
Stage 5, Sections 10-14: control problem core machinery.

State: (y, z, m in R^8, Sigma in R^{8x8}). Controls u_y(t), u_z(t) are piecewise-linear
on 12 predetermined knots over [0,T] (Section 13's recommended starting parameterization;
knot count is swept for convergence in control_sweep.py). Effort E and (for formulation D)
the running D_org integral are tracked as augmented ODE states for accurate quadrature
under adaptive step control (same technique as stage4/riccati_solver.py).

Four formulations (Section 11):
  A: task-only.
  B: task + Lambda_3(T) <= delta (endpoint integrity only).
  C: task + Lambda_3(t) <= delta on a dense checkpoint grid throughout (pathwise integrity).
  D: same pathwise constraint, minimize E + lambda_org * integral(D_org dt).

Optimizer: SLSQP with multiple predetermined starts (Section 13). Results are revalidated
on a checkpoint grid denser than the knot grid; a solution violating the dense-grid check
is reported as infeasible ("best found", never claimed globally optimal).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import core5
import integrity as I
import dynamics as dyn
from reference import v_of_z, C_VEC

N = core5.N
DELTA_PRIMARY = 0.01
T_RELEASE = 4.0
N_KNOTS = 12
N_CHECKPOINTS_OPT = 6     # sparse checkpoint grid used *during* optimization (cost control)
N_CHECKPOINTS_DENSE = 60  # dense revalidation grid (Section 13 requirement)


def pw_linear(knots_t, knots_v):
    def f(t):
        return float(np.interp(t, knots_t, knots_v))
    return f


def simulate(uy_knot_vals, uz_knot_vals, T, rho_z, n_eval=None, compute_Dorg=False,
             rtol=1e-5, atol=1e-7, tau_z=None):
    # NOTE: rtol/atol/tau_z defaults are UNCHANGED from the original Stage-5 baseline
    # (rtol/atol kept at 1e-5/1e-7 for SLSQP wall-clock tractability; tau_z=None uses
    # dynamics.TAU_Z=1.0); the final_patch scripts pass tighter tolerances and/or an
    # explicit tau_z override for post-hoc revalidation / the Part-3 stress test only --
    # these additive parameters never change any previously-computed baseline result.
    """Forward-integrate with augmented running integrals for effort E and (optionally) D_org.
    Returns dict with t, y, z, m, Sigma, E (cumulative array), Dorg_int (cumulative array or None)."""
    knots_t = np.linspace(0, T, N_KNOTS)
    uy_fn = pw_linear(knots_t, uy_knot_vals)
    uz_fn = pw_linear(knots_t, uz_knot_vals) if uz_knot_vals is not None else (lambda t: 0.0)

    y0, z0 = -1.0, -1.0
    m0 = v_of_z(z0) * y0
    Sigma0 = np.linalg.inv(core5.Omega_of_z(z0))
    n_extra = 2 if compute_Dorg else 1
    state0 = np.concatenate([dyn.pack(y0, z0, m0, Sigma0), np.zeros(n_extra)])

    def rhs(t, state):
        y, z, m, Sigma = dyn.unpack(state[:2 + N + N * N])
        z_c = np.clip(z, -dyn.Z_GUARD, dyn.Z_GUARD)
        y_c = np.clip(y, -dyn.Y_GUARD, dyn.Y_GUARD)
        u_y = uy_fn(t); u_z = uz_fn(t)
        dy, dz, dm, dSigma = dyn.moment_rhs(m, Sigma, y_c, z_c, u_y, u_z, tau_z=tau_z)
        dcore = dyn.pack(dy, dz, dm, dSigma)
        dE = u_y**2 + rho_z * u_z**2
        extra = [dE]
        if compute_Dorg:
            val, sign = dyn.D_org(m, Sigma, y_c, z_c)
            extra.append(max(val, 0.0))
        return np.concatenate([dcore, extra])

    sol = solve_ivp(rhs, [0, T], state0, rtol=rtol, atol=atol, method="RK45", dense_output=True)
    if n_eval is None:
        n_eval = N_CHECKPOINTS_DENSE
    t_grid = np.linspace(0, T, n_eval)
    grid = sol.sol(t_grid)
    ys, zs, ms, Sigmas = [], [], [], []
    for i in range(n_eval):
        y, z, m, Sigma = dyn.unpack(grid[:2 + N + N * N, i])
        ys.append(np.clip(y, -dyn.Y_GUARD, dyn.Y_GUARD))
        zs.append(np.clip(z, -dyn.Z_GUARD, dyn.Z_GUARD))
        ms.append(m); Sigmas.append(Sigma)
    E_cum = grid[2 + N + N * N, :]
    Dorg_cum = grid[2 + N + N * N + 1, :] if compute_Dorg else None
    guard_active = bool(np.any(np.abs([r[0] for r in zip(ys)]) >= dyn.Y_GUARD - 1e-6) or
                         np.any(np.abs(zs) >= dyn.Z_GUARD - 1e-6))
    return dict(t=t_grid, y=np.array(ys), z=np.array(zs), m=np.array(ms), Sigma=np.array(Sigmas),
                E=E_cum, Dorg_cum=Dorg_cum, E_total=E_cum[-1],
                Dorg_total=(Dorg_cum[-1] if compute_Dorg else None), guard_active=guard_active,
                uy_fn=uy_fn, uz_fn=uz_fn, knots_t=knots_t)


def lambda3_series(Sigma_array):
    out = np.zeros(len(Sigma_array))
    winners = [None] * len(Sigma_array)
    for i, Sigma in enumerate(Sigma_array):
        val, w = I.Lambda_K(Sigma, 3, from_precision=False)
        out[i] = val; winners[i] = w
    return out, winners


def unpack_x(x, phenotype_only):
    uy = x[:N_KNOTS]
    if phenotype_only:
        return uy, None
    uz = x[N_KNOTS:2 * N_KNOTS]
    return uy, uz


def objective(x, T, rho_z, phenotype_only, formulation, lambda_org, tau_z=None):
    uy, uz = unpack_x(x, phenotype_only)
    res = simulate(uy, uz, T, rho_z, n_eval=N_CHECKPOINTS_OPT, compute_Dorg=(formulation == "D"),
                   tau_z=tau_z)
    val = res["E_total"]
    if formulation == "D":
        val = val + lambda_org * res["Dorg_total"]
    return val


def task_constraints(x, T, rho_z, phenotype_only, tau_z=None):
    uy, uz = unpack_x(x, phenotype_only)
    res = simulate(uy, uz, T, rho_z, n_eval=N_CHECKPOINTS_OPT, compute_Dorg=False, tau_z=tau_z)
    y_T = res["y"][-1]
    cM_T = float(C_VEC @ res["m"][-1])
    return np.array([y_T - 1.0, cM_T - 1.0])


def pathwise_ineq(x, T, rho_z, phenotype_only, delta, endpoint_only, tau_z=None):
    """Returns array g(x) >= 0 required (SLSQP convention): delta - Lambda_3(t_i)."""
    uy, uz = unpack_x(x, phenotype_only)
    res = simulate(uy, uz, T, rho_z, n_eval=N_CHECKPOINTS_OPT, compute_Dorg=False, tau_z=tau_z)
    if endpoint_only:
        L3_T, _ = I.Lambda_K(res["Sigma"][-1], 3, from_precision=False)
        return np.array([delta - L3_T])
    L3, _ = lambda3_series(res["Sigma"])
    return delta - L3


def build_constraints(T, rho_z, phenotype_only, formulation, delta, tau_z=None):
    cons = [dict(type="eq", fun=task_constraints, args=(T, rho_z, phenotype_only, tau_z))]
    if formulation == "B":
        cons.append(dict(type="ineq", fun=pathwise_ineq, args=(T, rho_z, phenotype_only, delta, True, tau_z)))
    elif formulation in ("C", "D"):
        cons.append(dict(type="ineq", fun=pathwise_ineq, args=(T, rho_z, phenotype_only, delta, False, tau_z)))
    return cons


def starting_points(n_knots, phenotype_only, rng):
    """Predetermined multi-start initializations: zero, small ramp toward +y, a
    physics-informed front-loaded pulse (push y,z toward +1 early so the mean m
    has maximal remaining time to relax toward mu*(1,1) under Omega(1), whose
    slowest mode has rate 1 -- see control_sweep diagnostics), and a randomized
    perturbation. Fixed seed so runs are reproducible."""
    dim = n_knots if phenotype_only else 2 * n_knots
    starts = []
    starts.append(np.zeros(dim))
    ramp = np.zeros(dim)
    ramp[:n_knots] = np.linspace(0.0, 1.0, n_knots)
    starts.append(ramp)
    pulse = np.zeros(dim)
    n_pulse = max(1, n_knots // 6)
    pulse[:n_pulse] = 8.0
    if not phenotype_only:
        pulse[n_knots:n_knots + n_pulse] = 8.0
    starts.append(pulse)
    starts.append(rng.normal(0, 0.3, size=dim))
    return starts


def optimize_protocol(T, rho_z, phenotype_only, formulation, delta=DELTA_PRIMARY,
                       lambda_org=0.0, n_knots=N_KNOTS, n_starts=3, seed=0, maxiter=30,
                       tau_z=None):
    # tau_z=None (default) reproduces the exact original Stage-5 baseline (tau_z=1.0
    # via dynamics.TAU_Z); an explicit override is used only by the final_patch Part-3
    # interface-timescale stress test.
    global N_KNOTS
    old_nk = N_KNOTS
    N_KNOTS = n_knots  # module-level knot count used by simulate/unpack_x
    try:
        rng = np.random.default_rng(seed)
        dim = n_knots if phenotype_only else 2 * n_knots
        bounds = [(-6, 6)] * dim
        cons = build_constraints(T, rho_z, phenotype_only, formulation, delta, tau_z=tau_z)
        best = None
        attempts = []
        for x0 in starting_points(n_knots, phenotype_only, rng)[:n_starts]:
            try:
                res = minimize(objective, x0, args=(T, rho_z, phenotype_only, formulation, lambda_org, tau_z),
                                method="SLSQP", bounds=bounds, constraints=cons,
                                options=dict(maxiter=maxiter, ftol=1e-8))
            except Exception as e:
                attempts.append(dict(success=False, error=str(e)))
                continue
            tcons = task_constraints(res.x, T, rho_z, phenotype_only, tau_z=tau_z)
            feas_task = np.max(np.abs(tcons)) < 1e-4
            pcons_ok = True
            if formulation in ("B", "C", "D"):
                endpoint_only = (formulation == "B")
                g = pathwise_ineq(res.x, T, rho_z, phenotype_only, delta, endpoint_only, tau_z=tau_z)
                pcons_ok = np.min(g) > -1e-4
            feasible = feas_task and pcons_ok and res.success
            attempts.append(dict(success=res.success, feasible=feasible, fun=res.fun, x=res.x,
                                  task_resid=tcons, msg=res.message))
            if feasible and (best is None or res.fun < best["fun"]):
                best = dict(fun=res.fun, x=res.x, task_resid=tcons)
        if best is None:
            # fall back to least-infeasible attempt for reporting purposes
            feasible_flag = False
            usable = [a for a in attempts if "x" in a]
            if usable:
                best = min(usable, key=lambda a: a["fun"])
                best = dict(fun=best["fun"], x=best["x"], task_resid=best["task_resid"])
        else:
            feasible_flag = True
        if best is None:
            return dict(feasible=False, attempts=attempts, x=None)
        uy, uz = unpack_x(best["x"], phenotype_only)
        traj = simulate(uy, uz, T, rho_z, n_eval=N_CHECKPOINTS_DENSE, compute_Dorg=True, tau_z=tau_z)
        L3_dense, B3_dense = lambda3_series(traj["Sigma"])
        max_L3 = L3_dense.max()
        dense_feasible = (max_L3 <= delta + 1e-4) if formulation in ("C", "D") else True
        if formulation == "B":
            dense_feasible = L3_dense[-1] <= delta + 1e-4
        return dict(feasible=feasible_flag, dense_feasible=dense_feasible, x=best["x"],
                    E_total=traj["E_total"], Dorg_total=traj["Dorg_total"], traj=traj,
                    L3_dense=L3_dense, B3_dense=B3_dense, max_L3=max_L3,
                    attempts=attempts, uy=uy, uz=uz, T=T, rho_z=rho_z,
                    phenotype_only=phenotype_only, formulation=formulation,
                    delta=delta, lambda_org=lambda_org, n_knots=n_knots, tau_z=tau_z)
    finally:
        N_KNOTS = old_nk


def revalidate_tight(res, n_eval=200, rtol=1e-8, atol=1e-9):
    """final_patch addition: re-simulate an already-optimized solution's knot vector x
    at a TIGHTER integration tolerance and denser checkpoint grid than the SLSQP-time
    default, for final plotted/reported trajectories. Does not touch res['traj'] (the
    original baseline-tolerance trajectory) -- returns a new dict."""
    global N_KNOTS
    old_nk = N_KNOTS
    N_KNOTS = res["n_knots"]
    try:
        uy, uz = res["uy"], res["uz"]
        traj = simulate(uy, uz, res["T"], res["rho_z"], n_eval=n_eval, compute_Dorg=True,
                         rtol=rtol, atol=atol, tau_z=res.get("tau_z"))
        L3_dense, B3_dense = lambda3_series(traj["Sigma"])
        return dict(traj=traj, L3_dense=L3_dense, B3_dense=B3_dense, max_L3=L3_dense.max(),
                     rtol=rtol, atol=atol, n_eval=n_eval)
    finally:
        N_KNOTS = old_nk


def release_phase(res, n_eval=N_CHECKPOINTS_DENSE):
    """Append zero-control release period T_RELEASE after a control solution."""
    traj = res["traj"]
    y_T, z_T, m_T, Sigma_T = traj["y"][-1], traj["z"][-1], traj["m"][-1], traj["Sigma"][-1]
    rel = dyn.integrate(y_T, z_T, m_T, Sigma_T, T_RELEASE, n_eval=n_eval, tau_z=res.get("tau_z"))
    L3_rel, B3_rel = lambda3_series(rel["Sigma"])
    Dorg_rel = np.array([dyn.D_org(rel["m"][i], rel["Sigma"][i], rel["y"][i], rel["z"][i])[0]
                          for i in range(n_eval)])
    # KL to p*_{+1,+1}
    Om_pB = core5.Omega_of_z(1.0)
    v_pB = v_of_z(1.0)
    mu_pB = v_pB * 1.0
    Sigma_pB = np.linalg.inv(Om_pB)
    KL_final = []
    for i in range(n_eval):
        dm = rel["m"][i] - mu_pB
        S = rel["Sigma"][i]
        OmS = Om_pB @ S
        tr_term = np.trace(OmS)
        quad = dm @ Om_pB @ dm
        sign, ld = np.linalg.slogdet(OmS)
        KL_final.append(0.5 * (tr_term + quad - N - ld) if sign > 0 else np.nan)
    KL_final = np.array(KL_final)
    return dict(t=rel["t"], y=rel["y"], z=rel["z"], m=rel["m"], Sigma=rel["Sigma"],
                L3=L3_rel, B3=B3_rel, Dorg=Dorg_rel, KL_to_pB=KL_final,
                relaxes_to_B=bool(abs(rel["y"][-1] - 1.0) < 0.05 and abs(rel["z"][-1] - 1.0) < 0.05),
                final_KL_to_pB=KL_final[-1])
