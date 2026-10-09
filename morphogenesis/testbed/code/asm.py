"""assembly runner / classifier shared by T2a-T2e"""
import sys, time, dataclasses; sys.path.insert(0,'.')
from common import *
from shape import *
from templates import *

def slot_orbits(tmpl, plan=0, tol=1e-6):
    """orbit id per slot: slots with identical (code, expected-field) fingerprints (mirror twins) are indistinguishable to any
    reflection-invariant cue, so beliefs are aggregated over each such orbit"""
    f = np.vstack([tmpl.Lam[plan], tmpl.Cs[plan]]); n = f.shape[1]
    orb = -np.ones(n, int); k = 0
    for s in range(n):
        if orb[s] >= 0: continue
        m = (np.linalg.norm(f - f[:, [s]], axis=0) < 1e-6) & (orb < 0); orb[m] = k; k += 1
    return orb

TAU_ASM = 0.4   # declared before measuring: 0.4 x template min NN spacing (=1.0 for vanilla8 and the 24-cell bodies)

def run_draws(tmpl, P, n_draws, std=1/8, T=600.0, dt=None, seed0=0, plan=0, MU0s=None, key=None, zeta0=None, x0_radius=0.0):
    eng = make_engine(tmpl, P); n = tmpl.n; eng.dt, eng.rho = auto_dt(eng, tmpl) if dt is None else (dt, np.nan); dt = eng.dt; key = jax.random.PRNGKey(0) if key is None else key
    out = []
    ty = type_vector(tmpl, plan) if tmpl.types is not None else cell_types(tmpl.Cs[plan])
    for k in range(n_draws):
        MU0 = np.random.default_rng(seed0 + k).standard_normal((n, n)) * std if MU0s is None else MU0s[k]
        ZE0 = None if zeta0 is None else zeta0[k]
        st = eng.init_from_mu(MU0, ZE0)
        if x0_radius > 0:   # dispersed start: uniform in a disc
            rr = np.random.default_rng(10_000 + seed0 + k); r = x0_radius * np.sqrt(rr.uniform(size=n)); a = rr.uniform(0, 2 * np.pi, n)
            st = (jnp.asarray(np.stack([r * np.cos(a), r * np.sin(a)], 1)),) + tuple(st[1:])
        fin = eng.run_final(st, 0.0, dt, int(T / dt), key, None, 0)
        out.append(analyse(eng, tmpl, fin, plan, ty))
    return eng, out

def auto_dt(eng, tmpl, cap=0.02, safety=0.8):
    """RK4 step from the Jacobian spectral radius at the sharp template state (dt*rho < safety)"""
    n = tmpl.n
    st = (jnp.array(tmpl.Xs[0].T), jnp.array(tmpl.Cs[0].T), jnp.array(np.eye(n) * 8.0), jnp.zeros((n, eng.K)))
    rho = float(np.abs(np.linalg.eigvals(np.array(eng.jac_flat(st, 1e9)))).max())
    return min(cap, safety / rho), rho

def rigid_motion_rates(eng, tmpl, fin, dt=None, span=2.0, t0=1e4):
    dt = dt or getattr(eng, 'dt', 0.02)
    """advance `span` time units; return (shape_speed = max |d D_ij/dt|, centroid speed, rotation rate deg/time)"""
    k = int(round(span / dt)); fin2 = eng.run_final(fin, t0, dt, k, jax.random.PRNGKey(0), None, 0)
    A = np.array(fin[0]); B = np.array(fin2[0])
    DA = np.linalg.norm(A[:, None] - A[None], axis=-1); DB = np.linalg.norm(B[:, None] - B[None], axis=-1)
    cs = np.linalg.norm(B.mean(0) - A.mean(0)) / span
    a = A - A.mean(0); b = B - B.mean(0); H = a.T @ b; U, S, Vt = np.linalg.svd(H); R = Vt.T @ U.T
    rot = np.degrees(np.arctan2(R[1, 0], R[0, 0])) / span
    return float(np.abs(DB - DA).max() / span), float(cs), float(rot), fin2

def analyse(eng, tmpl, fin, plan=0, ty=None, t_eval=1e9):
    n = tmpl.n
    shape_speed, cspeed, rot, _ = rigid_motion_rates(eng, tmpl, fin)
    ty = type_vector(tmpl, plan) if ty is None else ty
    X, C, MU, ZE = [np.array(a) for a in fin]
    p = np.array(jax.nn.softmax(MU, axis=1))
    res = max(float(jnp.abs(a).max()) for a in eng.drift(fin, t_eval, jnp.zeros((n, tmpl.nc))))
    ct = cell_types(C.T)
    dd, info = d_rigid(X.T, ct, tmpl.Xs[plan], ty, return_all=True)
    orb = slot_orbits(tmpl, plan); n_orb = orb.max() + 1
    O = np.zeros((n_orb, n)); O[orb, np.arange(n)] = 1
    po = p @ O.T; orb_cell = po.argmax(1); orb_ok = bool((np.bincount(orb_cell, minlength=n_orb) == np.bincount(orb, minlength=n_orb)).all())
    slot = p.argmax(1)
    return dict(orbit_complete=orb_ok, min_orbit_maxbel=float(po.max(1).min()), shape_speed=shape_speed, centroid_speed=cspeed, rot_rate=rot, d_tmpl=dd, resid=res, min_maxbel=float(p.max(1).min()), mean_maxbel=float(p.max(1).mean()), one_per_slot=bool(len(set(slot)) == n),
                n_slots=int(len(set(slot))), type_ok=int((np.sort(ct) == np.sort(ty)).all()), angle=info['angle_deg'], centroid=X.mean(0).tolist(),
                success=bool(dd < TAU_ASM and shape_speed < 1e-3 and orb_ok and (np.sort(ct) == np.sort(ty)).all()))

def seeded_start(tmpl, k, a=8.0, jit_x=0.5, jit_mu=0.3, plan=0, zeta=None):
    """declared default development start: cells hold committed identities (random cell->slot assignment, logit a) and start at
    their slot positions + Gaussian jitter. returns (X, C, MU, ZE)"""
    n = tmpl.n; rng = np.random.default_rng(777 + k); perm = rng.permutation(n)
    MU = np.zeros((n, n)); MU[np.arange(n), perm] = a; MU += jit_mu * rng.standard_normal((n, n))
    X = tmpl.Xs[plan][:, perm].T + jit_x * rng.standard_normal((n, 2)); C = tmpl.Cs[plan][:, perm].T
    ZE = np.zeros((n, tmpl.K)) if zeta is None else np.tile(np.asarray(zeta, float), (n, 1))
    return jnp.array(X), jnp.array(C), jnp.array(MU), jnp.array(ZE)

def run_seeded(tmpl, P, n_draws, T=400.0, plan=0, **kw):
    eng = make_engine(tmpl, P); eng.dt, eng.rho = auto_dt(eng, tmpl); dt = eng.dt; key = jax.random.PRNGKey(0); out = []
    for k in range(n_draws):
        st = seeded_start(tmpl, k, plan=plan, **kw)
        fin = eng.run_final(st, 0.0, dt, int(T / dt), key, None, 0)
        out.append(analyse(eng, tmpl, fin, plan))
    return eng, out

def tb_params(**kw):
    """declared testbed operating point (T2b): relational (positional OFF), no action priors, log pi_s = 2, log pi_prior = -10, k_mu 1.4, k_a 0.4"""
    ps = float(np.exp(2.0))
    d = dict(k_mu=1.4, k_a=0.4, pi_prior=float(np.exp(-10)), pi_a_x=0.0, pi_a_c=0.0, pos_on=False, pi_x=ps, pi_c=ps, pi_l=ps, pi_ref=ps, pi_act=1.5 * ps / np.e)
    d.update(kw); return Params(**d)
