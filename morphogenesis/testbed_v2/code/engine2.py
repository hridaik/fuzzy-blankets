"""Testbed v2 engine: categorical place identity + collective handedness memory.  See ENGINE_SPEC_V2.md.

State per cell: x (2), c (4) secretion, d (2) memory secretion, mu (S) place logits, l () handedness log-odds.
Ligand vector (6) = [c(4), d(2)], kernel decay kap = [kappa]*4 + [kappa_m]*2.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from functools import partial
import numpy as np
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
EPS2 = 1e-12
NL = 6   # 4 morphological + 2 memory ligands


@dataclass(frozen=True)
class Template2:
    Xs: np.ndarray        # (2,S) place positions
    CL: np.ndarray        # (4,S) L codes
    CR: np.ndarray        # (4,S) R codes = CL[:, m]
    mirror: np.ndarray    # (S,) mirror map
    types: np.ndarray     # (2,S) cell types per form (row 0 = L, row 1 = R) for plotting / classification
    kappa: float
    kappa_m: float
    w: np.ndarray         # (S,) kernel weights w_k
    LamL: np.ndarray      # (4,S)
    LamR: np.ndarray
    @property
    def S(self): return self.Xs.shape[1]


def make_template2(kappa=1.0, kappa_m=1.0):
    from templates import make_body, type_vector
    t = make_body('chiral', kappa)
    Xs, CL, ty = t.Xs[0], t.Cs[0], t.types[0]
    S = Xs.shape[1]
    mirror = np.array([int(np.argmin(np.linalg.norm(Xs - np.array([[Xs[0, k]], [-Xs[1, k]]]), axis=0))) for k in range(S)])
    assert sorted(mirror.tolist()) == list(range(S)), 'mirror map not a bijection'
    assert (mirror[mirror] == np.arange(S)).all(), 'mirror map not an involution'
    assert np.abs(Xs[:, mirror] - Xs * np.array([[1], [-1]])).max() < 1e-9, 'positions not mirror symmetric'
    CR = CL[:, mirror]
    D = np.linalg.norm(Xs[:, :, None] - Xs[:, None, :], axis=0)
    w = np.exp(-kappa_m * D).sum(1)
    K = np.exp(-kappa * D)
    LamL = CL @ K.T          # sum_j C_j exp(-kappa|Xk - Xj|)  -> (4,S)
    LamR = CR @ K.T
    tyR = ty[mirror]
    return Template2(Xs, CL, CR, mirror, np.stack([ty, tyR]), kappa, kappa_m, w, LamL, LamR)


@dataclass(frozen=True)
class Params2:
    pi_c: float = float(np.exp(2)); pi_lam: float = float(np.exp(2))
    pi_d: float = 0.0; pi_psi: float = 0.0
    beta_E: float = 1.0
    k_mu: float = 0.2; k_a: float = 0.4; k_h: float = 1.0; r: float = 0.05
    sig_x: float = 0.0; sig_c: float = 0.0; sig_d: float = 0.0; sig_mu: float = 0.0; sig_h: float = 0.0
    fix_rho: float = -1.0       # >=0: handedness frozen at this rho (G0/G1); l not integrated
    tau: float = 1.0            # developmental factor hook (adult); unused
    psi_scale: float = 1.0      # global coupling multiplier on pi_psi (hysteresis continuation)


def make_engine2(tm: Template2, P: Params2, N: int = None):
    S = tm.S; n = N or S
    XsJ = jnp.asarray(tm.Xs); CLJ = jnp.asarray(tm.CL); CRJ = jnp.asarray(tm.CR)
    LamL = jnp.asarray(tm.LamL); LamR = jnp.asarray(tm.LamR); wk = jnp.asarray(tm.w)
    kap = jnp.asarray([tm.kappa] * 4 + [tm.kappa_m] * 2)
    DL = jnp.asarray([1.0, 0.0]); DR = jnp.asarray([0.0, 1.0])
    PsiL = wk[None, :] * DL[:, None]; PsiR = wk[None, :] * DR[:, None]    # (2,S)
    idx = jnp.arange(n)
    pi_psi = P.pi_psi * P.psi_scale
    nsig = 2 + 4 + 2 + S + 1

    def unpack(ctl):
        """ctl tuple: (ext (n,6), rg (n,6), mig (n,), fb (n,S), alive (n,), src_pos (m,2), src_amp (m,6), bath (6,))"""
        dflt = (jnp.zeros((n, NL)), jnp.zeros((n, NL)), jnp.zeros((n,)), jnp.zeros((n, S)), jnp.ones((n,)), jnp.zeros((1, 2)), jnp.zeros((1, NL)), jnp.zeros((NL,)))
        if isinstance(ctl, tuple): return tuple(ctl) + dflt[len(ctl):]
        return (ctl,) + dflt[1:]

    def sens(own, i, X, Lg, ctl):
        """own = (xi (2), ci (4), di (2)); X (n,2); Lg (n,6) ligand levels of all cells (own row ignored)."""
        xi, ci, di = own
        ext, rg, _m, _fb, alive, src_pos, src_amp, bath = unpack(ctl)
        d = jnp.sqrt(jnp.sum((xi[None, :] - X) ** 2, axis=1) + EPS2)
        notself = (idx != i).astype(xi.dtype)
        kern = jnp.exp(-kap[None, :] * d[:, None]) * notself[:, None]
        Lge = (Lg + ext) * alive[:, None]
        own6 = jnp.concatenate([ci, di])
        dsrc = jnp.sqrt(jnp.sum((xi[None, :] - src_pos) ** 2, axis=1) + EPS2)
        fsrc = (jnp.exp(-kap[None, :] * dsrc[:, None]) * src_amp).sum(0) + bath
        s = ((kern * Lge).sum(0) + (own6 + ext[i]) * alive[i] + fsrc) * (1.0 + rg[i])
        return ci, di, s[:4], s[4:]

    def energies(own, i, X, Lg, ctl):
        sc, sd, sl, sp = sens(own, i, X, Lg, ctl)
        def E(Cst, Lam, Dst, Psi):
            return 0.5 * (P.pi_c * jnp.sum((sc[:, None] - Cst) ** 2, 0) + P.pi_lam * jnp.sum((sl[:, None] - Lam) ** 2, 0)
                          + P.pi_d * jnp.sum((sd - Dst) ** 2) + pi_psi * jnp.sum((sp[:, None] - Psi) ** 2, 0))
        return E(CLJ, LamL, DL, PsiL), E(CRJ, LamR, DR, PsiR)

    def A_obj(own, i, X, Lg, ctl, q, rho):
        EL, ER = energies(own, i, X, Lg, ctl)
        return jnp.sum(q * (rho * EL + (1 - rho) * ER))

    gradA = jax.grad(A_obj, argnums=0)

    def rho_of(l):
        return jnp.full_like(l, P.fix_rho) if P.fix_rho >= 0 else jax.nn.sigmoid(l)

    def drift(state, t, ctl):
        X, C, D, MU, L = state
        Lg = jnp.concatenate([C, D], axis=1)
        _e, _rg, mig, fb, alive, _sp, _sa, _bt = unpack(ctl)
        q = jax.nn.softmax(MU, axis=1); rho = rho_of(L)
        gx, gc, gd = jax.vmap(lambda xi, ci, di, qi, ri, i: gradA((xi, ci, di), i, X, Lg, ctl, qi, ri))(X, C, D, q, rho, idx)
        EL, ER = jax.vmap(lambda xi, ci, di, i: energies((xi, ci, di), i, X, Lg, ctl))(X, C, D, idx)
        Ebar = rho[:, None] * EL + (1 - rho[:, None]) * ER
        z = MU + P.beta_E * Ebar
        dMU = -P.k_mu * (z - z.mean(1, keepdims=True)) + fb
        Delta = jnp.sum(q * (ER - EL), axis=1)
        dL = -2 * P.r * jnp.sinh(L) + P.k_h * P.beta_E * Delta
        if P.fix_rho >= 0: dL = jnp.zeros_like(dL)
        dX = -P.k_a * (1.0 + mig[:, None]) * gx; dC = -P.k_a * gc; dD = -P.k_a * gd
        am = alive[:, None]
        return (dX * am, dC * am, dD * am, dMU * am, dL * alive)

    def rk4(state, t, dt, ctl):
        add = lambda s, k, a: jax.tree_util.tree_map(lambda u, v: u + a * v, s, k)
        k1 = drift(state, t, ctl); k2 = drift(add(state, k1, dt / 2), t + dt / 2, ctl)
        k3 = drift(add(state, k2, dt / 2), t + dt / 2, ctl); k4 = drift(add(state, k3, dt), t + dt, ctl)
        return jax.tree_util.tree_map(lambda s, a, b, c, d: s + dt / 6 * (a + 2 * b + 2 * c + d), state, k1, k2, k3, k4)

    noisy = any(v > 0 for v in (P.sig_x, P.sig_c, P.sig_d, P.sig_mu, P.sig_h))

    def noise_incr(key, step_idx, dt):
        def one(i):
            return jax.random.normal(jax.random.fold_in(jax.random.fold_in(key, step_idx), i), (nsig,))
        z = jax.vmap(one)(idx) * jnp.sqrt(dt)
        zm = z[:, 8:8 + S]; zm = zm - zm.mean(1, keepdims=True)      # centred: only the (identifiable) centred logits are driven
        return (P.sig_x * z[:, :2], P.sig_c * z[:, 2:6], P.sig_d * z[:, 6:8], P.sig_mu * zm, P.sig_h * z[:, 8 + S])

    def step(state, t, step_idx, dt, key, ctl):
        new = rk4(state, t, dt, ctl)
        if noisy:
            nz = noise_incr(key, step_idx, dt); al = unpack(ctl)[4]
            new = tuple(a + b * (al[:, None] if b.ndim == 2 else al) for a, b in zip(new, nz))
        return new

    def window(t, ton, toff, ramp):
        up = jnp.clip((t - ton) / ramp, 0.0, 1.0); dn = jnp.clip((toff - t) / ramp, 0.0, 1.0); x = jnp.minimum(up, dn)
        return 0.5 * (1.0 - jnp.cos(jnp.pi * x))

    @partial(jax.jit, static_argnames=('n_steps', 'save_every'))
    def run_ctl(state, t0, dt, n_steps, key, amps, ton, toff, ramp, step0=0, save_every=0):
        """amps = (ext (n,6), rg (n,6), mig (n,), fb (n,S), alive (n,) [not ramped], src_pos, src_amp, bath) PEAK values; ramped by w(t) except alive/src_pos."""
        amps = tuple(amps) + tuple(unpack(())[len(amps):]) if len(amps) < 8 else tuple(amps)
        def one(s, k):
            t = t0 + k * dt; w = window(t, ton, toff, ramp)
            ctl = tuple(w * a for a in amps[:4]) + (amps[4], amps[5]) + tuple(w * a for a in amps[6:])
            return step(s, t, step0 + k, dt, key, ctl)
        body = lambda s, k: (one(s, k), None)
        if save_every:
            def blk(s, kk):
                s2, _ = jax.lax.scan(body, s, kk); return s2, s2
            ks = jnp.arange(n_steps).reshape(-1, save_every)
            return jax.lax.scan(blk, state, ks)
        fin, _ = jax.lax.scan(body, state, jnp.arange(n_steps)); return fin

    def jac_flat(state, t=0.0):
        flat, unflat = flatten_state(state)
        f = lambda v: flatten_state(drift(unflat(v), t, ()))[0]
        return jax.jacfwd(f)(flat)

    def diagnostics(state, ctl=()):
        """per-cell hidden quantities: q, rho, Delta, EL, ER (n,S)"""
        X, C, D, MU, L = state
        Lg = jnp.concatenate([C, D], axis=1); q = jax.nn.softmax(MU, axis=1)
        EL, ER = jax.vmap(lambda xi, ci, di, i: energies((xi, ci, di), i, X, Lg, ctl))(X, C, D, idx)
        return dict(q=q, rho=rho_of(L), Delta=jnp.sum(q * (ER - EL), 1), EL=EL, ER=ER)

    ns = type("Engine2", (), {})()
    ns.tm, ns.P, ns.n, ns.S, ns.nc = tm, P, n, S, NL
    ns.drift = jax.jit(lambda s, t=0.0, ctl=(): drift(s, t, ctl)); ns.run_ctl = run_ctl; ns.step = step; ns.window = window
    ns.jac_flat = jac_flat; ns.diagnostics = jax.jit(lambda s, ctl=(): diagnostics(s, ctl)); ns.unpack = unpack
    ns.dt = 0.02
    return ns


def flatten_state(state):
    sh = [a.shape for a in state]; sizes = [int(np.prod(s)) for s in sh]
    flat = jnp.concatenate([a.reshape(-1) for a in state])
    def unflat(v):
        out, o = [], 0
        for s, z in zip(sh, sizes): out.append(v[o:o + z].reshape(s)); o += z
        return tuple(out)
    return flat, unflat


def run_plain(eng, state, t0, T, key, step0=0, ctl=None, dt=None):
    """no forcing; convenience (T multiple of dt)"""
    dt = dt or eng.dt; n = eng.n
    amps = (jnp.zeros((n, NL)), jnp.zeros((n, NL)), jnp.zeros(n), jnp.zeros((n, eng.S)), jnp.ones(n)) if ctl is None else ctl
    return eng.run_ctl(state, t0, dt, int(round(T / dt)), key, amps, -1e30, 1e30, 1.0, step0=step0)


def seeded_start2(tm, k, form='L', a=8.0, jit_x=0.3, jit_mu=0.3, l0=None, rho_d=None):
    """cells hold committed place identities (random cell->place assignment) at place positions + jitter; codes consistent with `form`.
    Memory secretion consistent with the form (d = D*(h)), l = +-l0 (default +-3)."""
    S = tm.S; rng = np.random.default_rng(777 + k); perm = rng.permutation(S)
    MU = np.zeros((S, S)); MU[np.arange(S), perm] = a; MU += jit_mu * rng.standard_normal((S, S))
    X = tm.Xs[:, perm].T + jit_x * rng.standard_normal((S, 2))
    Cc = (tm.CL if form == 'L' else tm.CR)[:, perm].T
    Dd = np.tile([1.0, 0.0] if form == 'L' else [0.0, 1.0], (S, 1))
    l0 = 3.0 if l0 is None else l0
    L = np.full(S, l0 if form == 'L' else -l0)
    return (jnp.array(X), jnp.array(Cc), jnp.array(Dd), jnp.array(MU), jnp.array(L)), perm


def auto_dt2(eng, state=None, cap=0.02, safety=0.8):
    if state is None:
        tm = eng.tm; S = tm.S
        state, _ = seeded_start2(tm, 0, 'L', jit_x=0.0, jit_mu=0.0)
    rho = float(np.abs(np.linalg.eigvals(np.array(eng.jac_flat(state)))).max())
    return min(cap, safety / rho), rho
