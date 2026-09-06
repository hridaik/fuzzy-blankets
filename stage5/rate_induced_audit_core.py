"""
Rate-induced-loss audit (additive to Stage 5; does NOT modify rate_induced.py,
quasistatic.py, or any previously saved Stage-5 result). Shared simulation and
analysis machinery for the audit requested against Section 9 / Figure 3.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import core5
import integrity as I
import dynamics as dyn
from reference import v_of_z

AUDIT_DIR = os.path.join(os.path.dirname(__file__), "data", "rate_induced_audit")
os.makedirs(AUDIT_DIR, exist_ok=True)

DELTA = 0.01
TAU_X = 1.0  # baseline, unchanged

# --- ramp shapes (predeclared; no shapes added after seeing results) ---
def _linear(r):
    return np.clip(r, 0, 1)


def _linear_deriv(r):
    return np.where((r >= 0) & (r <= 1), 1.0, 0.0)


def _smoothstep(r):
    r = np.clip(r, 0, 1)
    return 3 * r**2 - 2 * r**3


def _smoothstep_deriv(r):
    r = np.clip(r, 0, 1)
    return 6 * r - 6 * r**2


def _smootherstep(r):
    r = np.clip(r, 0, 1)
    return 6 * r**5 - 15 * r**4 + 10 * r**3


def _smootherstep_deriv(r):
    r = np.clip(r, 0, 1)
    return 30 * r**4 - 60 * r**3 + 30 * r**2


SHAPES = {
    "linear": (_linear, _linear_deriv),
    "smoothstep": (_smoothstep, _smoothstep_deriv),
    "smootherstep": (_smootherstep, _smootherstep_deriv),
}


def build_uz_fn(T_ramp, shape="smoothstep"):
    """u_z(t) that forces z(t) to exactly track z_target(t): the ramp shape during
    [0,T_ramp], then HELD at +1 for t>T_ramp (extended-relaxation experiment)."""
    s, sprime = SHAPES[shape]

    def z_target(t):
        r = t / T_ramp if T_ramp > 0 else 1.0
        return -1.0 + 2.0 * s(np.minimum(r, 1.0))

    def zdot_target(t):
        if t >= T_ramp:
            return 0.0
        r = t / T_ramp
        return (2.0 / T_ramp) * sprime(r)

    def u_z_fn(t, state):
        y, z, m, Sigma = dyn.unpack(state)
        return dyn.TAU_Z * zdot_target(t) - (y - z)

    return u_z_fn, z_target


def hold_uz_fn(t, state):
    """u_z that forces dz/dt=0 exactly, holding z at whatever value it currently has --
    time-independent (no T_ramp reference), for use in a SEPARATE segment-2 solve_ivp
    call whose local time resets to 0. (Bug this fixes: reusing the ramp's own u_z_fn,
    whose zdot_target(t) references GLOBAL ramp time via a `t>=T_ramp` cutoff, in a
    segment-2 integration that restarts LOCAL time at 0 spuriously re-triggers ramp-like
    forcing for the first T_ramp of segment 2, driving z far outside [-1,1] before the
    guard clip and cutoff catch up -- caught via an anomalous z=+3.56 in Part 10's
    output and fixed here.)"""
    y, z, m, Sigma = dyn.unpack(state)
    return -(y - z)


def full_candidate_table(Sigma, I_idx=core5.I_IDX):
    """All 31 candidates (sizes 0..4 over pool {4,5,6,7}), computed once."""
    return I.leakage_table(Sigma, from_precision=False, I_idx=I_idx, candidates=I.ALL_CANDIDATES)


def lambda_all_K(table, tie_tol=I.TIE_TOL, Ks=(1, 2, 3, 4)):
    """Given one full_candidate_table() result, return {K: (Lmin, winners)} for all
    requested K without recomputing the underlying CMI values."""
    out = {}
    for K in Ks:
        sub = [(B, L) for B, L in table if len(B) <= K]
        Lmin = min(L for _, L in sub)
        winners = [B for B, L in sub if L <= Lmin + tie_tol]
        out[K] = (Lmin, winners)
    return out


def min_card_family(table, delta=DELTA, tie_tol=I.TIE_TOL):
    """Minimum-cardinality delta-acceptable family (same definition as fig6_revised)."""
    ok = [(B, L) for B, L in table if L <= delta]
    if not ok:
        return None, []
    Kd = min(len(B) for B, L in ok)
    achievers = [B for B, L in ok if len(B) == Kd]
    return Kd, achievers


def run_extended(T_ramp, T_relax=8.0, shape="smoothstep", n_eval=2000,
                  rtol=1e-9, atol=1e-11, y0=-1.0, z0=-1.0, max_step_ramp="auto"):
    """The Part-2 extended-ramp experiment: ramp z over [0,T_ramp], then hold z=+1
    fixed for a further T_relax, integrating the ACTUAL covariance throughout. y is
    free (u_y=0) the whole time, exactly as in the original rate_induced.py/
    quasistatic.slow_ramp_run construction.

    NUMERICAL-INTEGRITY FIX (found during the audit): RK45's adaptive step control can
    ALIAS OVER the narrow forced transient near t=T_ramp (a derivative discontinuity in
    the forcing u_z(t)) when left completely unconstrained, occasionally reporting
    near-zero leakage where a step-capped integration shows a genuine ~1e-5 peak (the
    tell-tale sign is FEWER function evaluations at a "tighter" tolerance). Fixed by
    integrating in TWO segments: [0,T_ramp] with max_step capped at T_ramp/20 (verified
    stable under further refinement to T_ramp/100, agreement to 7 sig figs), then
    [T_ramp, T_ramp+T_relax] with UNCONSTRAINED adaptive stepping (z is simply held
    constant there -- no forcing discontinuity, so the aliasing failure mode does not
    apply, and capping the relax segment too would only waste enormous compute on the
    smooth tail for very small T_ramp with no accuracy benefit).
    Pass max_step_ramp=None to disable the ramp-segment cap (reproduces raw
    unconstrained adaptive stepping in a single solve, as used by the ORIGINAL,
    un-audited rate_induced.py/quasistatic.py -- those call dynamics.integrate directly
    and are UNAFFECTED by this fix, since dynamics.integrate's own max_step default
    remains None)."""
    u_z_fn, z_target = build_uz_fn(T_ramp, shape)
    u_y_fn = lambda t, state: 0.0
    m0 = v_of_z(z0) * y0
    Sigma0 = np.linalg.inv(core5.Omega_of_z(z0))
    T_total = T_ramp + T_relax
    if max_step_ramp == "auto":
        max_step_ramp = max(T_ramp / 20.0, 1e-5)

    n_eval_ramp = max(2, int(round(n_eval * T_ramp / T_total)))
    n_eval_relax = n_eval - n_eval_ramp + 1  # +1 shares the T_ramp junction point
    res1 = dyn.integrate(y0, z0, m0, Sigma0, T_ramp, u_y_fn=u_y_fn, u_z_fn=u_z_fn,
                          n_eval=n_eval_ramp, rtol=rtol, atol=atol, guard=True,
                          max_step=max_step_ramp)
    y1, z1, m1, Sigma1 = res1["y"][-1], res1["z"][-1], res1["m"][-1], res1["Sigma"][-1]
    # segment 2 uses hold_uz_fn (dz/dt=0, time-independent), NOT the ramp's u_z_fn --
    # see hold_uz_fn's docstring for the bug this avoids.
    res2 = dyn.integrate(y1, z1, m1, Sigma1, T_relax, u_y_fn=u_y_fn, u_z_fn=hold_uz_fn,
                          n_eval=n_eval_relax, rtol=rtol, atol=atol, guard=True,
                          max_step=None)

    t = np.concatenate([res1["t"], res2["t"][1:] + T_ramp])
    y = np.concatenate([res1["y"], res2["y"][1:]])
    z = np.concatenate([res1["z"], res2["z"][1:]])
    m = np.concatenate([res1["m"], res2["m"][1:]])
    Sigma = np.concatenate([res1["Sigma"], res2["Sigma"][1:]])
    guard_active = res1["guard_active"] or res2["guard_active"]
    res = dict(t=t, y=y, z=z, m=m, Sigma=Sigma, guard_active=guard_active,
               sol=res2["sol"], sol1=res1["sol"], T_ramp_junction=T_ramp)
    return res, T_total


def analyze_run(res, T_ramp, T_relax, Ks=(1, 2, 3, 4)):
    """Compute L_K(t) for all requested K (single table pass per timepoint), plus
    Kdelta(t) and minimum-cardinality family(t)."""
    n = len(res["t"])
    LK = {K: np.zeros(n) for K in Ks}
    winnersK = {K: [None] * n for K in Ks}
    Kdelta = np.full(n, np.nan)
    families = [None] * n
    for i in range(n):
        table = full_candidate_table(res["Sigma"][i])
        allK = lambda_all_K(table, Ks=Ks)
        for K in Ks:
            LK[K][i] = allK[K][0]
            winnersK[K][i] = allK[K][1]
        Kd, fam = min_card_family(table)
        Kdelta[i] = Kd if Kd is not None else np.nan
        families[i] = fam
    return dict(LK=LK, winnersK=winnersK, Kdelta=Kdelta, families=families)


def peak_summary(t, L, T_ramp, T_relax):
    """During-ramp / post-ramp / full-event peaks, per Part 4."""
    ramp_mask = t <= T_ramp
    post_mask = t > T_ramp
    L_ramp = L[ramp_mask].max() if ramp_mask.any() else np.nan
    t_ramp_arg = t[ramp_mask][np.argmax(L[ramp_mask])] if ramp_mask.any() else np.nan
    L_post = L[post_mask].max() if post_mask.any() else np.nan
    t_post_arg = t[post_mask][np.argmax(L[post_mask])] if post_mask.any() else np.nan
    i_full = np.argmax(L)
    L_full = L[i_full]
    t_full = t[i_full]
    where = "during-ramp" if t_full <= T_ramp else ("post-ramp" if t_full > T_ramp * 1.001 else "ramp-completion")
    return dict(L_max_ramp=float(L_ramp), t_peak_ramp=float(t_ramp_arg),
                L_max_post=float(L_post), t_peak_post=float(t_post_arg),
                L_max_full=float(L_full), t_peak_full=float(t_full),
                t_peak_full_over_Tramp=float(t_full / T_ramp) if T_ramp > 0 else np.nan,
                peak_location=where)


def refine_peak(res, t_grid, L_grid, T_ramp, T_relax, K=3, window_frac=0.02, n_refine=61):
    """Independent local refinement around the coarse-grid full-event peak. `res` is
    the two-segment run_extended() output; the refinement window is evaluated via the
    correct segment's OWN dense (continuous) ODE solution (sol1 for t<=T_ramp, sol for
    t>T_ramp, shifted) -- no re-integration needed -- to confirm the coarse-grid maximum
    is not an artifact of grid spacing."""
    i0 = int(np.argmax(L_grid))
    t0 = t_grid[i0]
    T_total = T_ramp + T_relax
    half_win = max(window_frac * T_total, 2 * (t_grid[1] - t_grid[0]) if len(t_grid) > 1 else 1e-3)
    lo, hi = max(0.0, t0 - half_win), min(T_total, t0 + half_win)
    t_fine = np.linspace(lo, hi, n_refine)
    L_fine = np.zeros(n_refine)
    sol1 = res.get("sol1")
    sol2 = res.get("sol")
    for i, tt in enumerate(t_fine):
        if tt <= T_ramp and sol1 is not None:
            state = sol1.sol(tt)
        else:
            state = sol2.sol(max(tt - T_ramp, 0.0))
        y, z, m, Sigma = dyn.unpack(state)
        table = full_candidate_table(Sigma)
        Lmin, _ = lambda_all_K(table, Ks=(K,))[K]
        L_fine[i] = Lmin
    j = int(np.argmax(L_fine))
    return dict(t_refined=float(t_fine[j]), L_refined=float(L_fine[j]),
                t_coarse=float(t0), L_coarse=float(L_grid[i0]),
                refine_vs_coarse_diff=float(L_fine[j] - L_grid[i0]))


def cov_lag_fro(Sigma_t, z):
    Sigma_star = np.linalg.inv(core5.Omega_of_z(z))
    return float(np.linalg.norm(Sigma_t - Sigma_star, ord="fro"))


def precision_lag_fro(Sigma_t, z):
    K_t = np.linalg.inv(Sigma_t)
    Om = core5.Omega_of_z(z)
    return float(np.linalg.norm(K_t - Om, ord="fro"))
