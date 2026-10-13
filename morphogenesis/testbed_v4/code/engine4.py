"""Testbed v4 engine = v3 engine + (1) state-dependent template, (2) structure reads the cell's own belief rho_i, (3) body-feedback dial alpha,
(4) light damage (ubar), (5) per-dish runtime parameters hp=(g, gamma, alpha).  See ENGINE_SPEC_V4.md.
State per cell: x(2) c(4) mu(S) l d(2) e ubar  -> 7-tuple.  ctl = v3 11-tuple + hp (3,) + rho_fix (n,)  (rho_fix<0: free; >=0: rho clamped, l not integrated).
"""
from __future__ import annotations
import os, sys
from dataclasses import dataclass
from functools import partial
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
from template4 import make_template4, tail_angle
EPS2 = 1e-12


@dataclass(frozen=True)
class Params4:
    pi_c: float = float(np.e); pi_lam: float = float(np.e ** 3); beta_E: float = 4.0; k_mu: float = 0.2; k_a: float = 0.4
    r: float = 0.05; g: float = 0.6; k_d: float = 0.4; k_e: float = 0.4; eps: float = 1e-3; kappa_m: float = 1.0
    alpha: float = 0.0; gamma: float = 0.0; tau_rec: float = 10.0
    sig_x: float = 0.0; sig_c: float = 0.0; sig_mu: float = 0.0; sig_h: float = 0.0; sig_d: float = 0.0; sig_e: float = 0.0


def reporter_sets(tm):
    br = np.where((tm.CL != tm.CR).any(0))[0]
    Sp = br[tm.Xs[1, br] > 0]; Sm = br[tm.Xs[1, br] < 0]; assert len(Sp) == 4 and len(Sm) == 4; return Sp, Sm


def make_engine4(tm, P: Params4, N: int = None):
    S = 24; n = N or S
    CL = jnp.asarray(tm.CL); LamA = jnp.asarray(tm.LamA); LamB = jnp.asarray(tm.LamB); kap = float(tm.kappa)
    Sp, Sm = reporter_sets(tm); mp = np.zeros(S); mp[Sp] = 1.0; mm = np.zeros(S); mm[Sm] = 1.0; mp = jnp.asarray(mp); mm = jnp.asarray(mm)
    idx = jnp.arange(n)
    hp0 = jnp.array([P.g, P.gamma, P.alpha])

    def unpack(ctl):
        dflt = (jnp.zeros((n, 4)), jnp.zeros((n, 4)), jnp.zeros((n,)), jnp.zeros((n, 2)), jnp.ones((n,)), jnp.zeros((1, 2)), jnp.zeros((1, 4)), jnp.zeros((4,)),
                jnp.zeros((1, 2)), jnp.zeros((1, 2)), jnp.zeros((2,)), hp0, -jnp.ones((n,)))
        return tuple(ctl) + dflt[len(ctl):]

    def sens(xi, ci, i, X, C, ctl):
        ext, rg, _m, _u, alive, sp, sa, bath = unpack(ctl)[:8]
        d = jnp.sqrt(jnp.sum((xi[None, :] - X) ** 2, axis=1) + EPS2); notself = (idx != i).astype(xi.dtype); kern = jnp.exp(-kap * d) * notself
        Ce = (C + ext) * alive[:, None]
        dsrc = jnp.sqrt(jnp.sum((xi[None, :] - sp) ** 2, axis=1) + EPS2); fsrc = (jnp.exp(-kap * dsrc)[:, None] * sa).sum(0) + bath
        lam = ((kern[:, None] * Ce).sum(0) + (ci + ext[i]) * alive[i] + fsrc) * (1.0 + rg[i])
        return ci, lam

    def E_pair(sc, sl, pc, pl):
        t1 = pc * jnp.sum((sc[:, None] - CL) ** 2, 0)
        return 0.5 * (t1 + pl * jnp.sum((sl[:, None] - LamA) ** 2, 0)), 0.5 * (t1 + pl * jnp.sum((sl[:, None] - LamB) ** 2, 0))     # E_ik(a), E_ik(b)

    def action_obj(own, i, X, C, ctl, q, rho, pc, pl):
        sc, sl = sens(own[0], own[1], i, X, C, ctl)
        Ea, Eb = E_pair(sc, sl, pc, pl)
        return jnp.sum(q * (rho * Ea + (1 - rho) * Eb)), (Ea, Eb)

    def light_u(ctl):
        c = unpack(ctl); return jnp.maximum(jnp.maximum(jnp.abs(c[3]).max(1), jnp.abs(c[0]).max(1)), jnp.maximum(jnp.abs(c[1]).max(1), jnp.abs(c[2])))

    def rho_struct(L, ctl):
        rf = unpack(ctl)[12]; return jnp.where(rf >= 0, rf, jax.nn.sigmoid(L))

    def struct_and_E(X, C, MU, L, U, ctl):
        c = unpack(ctl); mig, alive, hp = c[2], c[4], c[11]
        q = jax.nn.softmax(MU, axis=1); rho = rho_struct(L, ctl); damp = jnp.exp(-hp[1] * U); pc = P.pi_c * damp; pl = P.pi_lam * damp
        def one(xi, ci, qi, i, ri, pci, pli):
            (_v, (Ea, Eb)), (gx, gc) = jax.value_and_grad(action_obj, argnums=0, has_aux=True)((xi, ci), i, X, C, ctl, qi, ri, pci, pli)
            return gx, gc, Ea, Eb
        gx, gc, Ea, Eb = jax.vmap(one)(X, C, q, idx, rho, pc, pl)
        return q, rho, gx, gc, Ea, Eb

    def struct_drift(X, C, MU, L, U, ctl):
        mig, alive = unpack(ctl)[2], unpack(ctl)[4]
        q, rho, gx, gc, Ea, Eb = struct_and_E(X, C, MU, L, U, ctl)
        Ebar = rho[:, None] * Ea + (1 - rho[:, None]) * Eb; z = MU + P.beta_E * Ebar; dMU = -P.k_mu * (z - z.mean(1, keepdims=True)); am = alive[:, None]
        Delta = jnp.sum(q * (Eb - Ea), axis=1)
        return -P.k_a * (1.0 + mig[:, None]) * gx * am, -P.k_a * gc * am, dMU * am, Delta

    def paracrine(xi, i, X, D, ctl):
        uM, alive, mp_, ma, mb = unpack(ctl)[3], unpack(ctl)[4], unpack(ctl)[8], unpack(ctl)[9], unpack(ctl)[10]
        d = jnp.sqrt(jnp.sum((xi[None, :] - X) ** 2, axis=1) + EPS2); w = jnp.exp(-P.kappa_m * d) * (idx != i) * alive
        L = D + uM
        dsrc = jnp.sqrt(jnp.sum((xi[None, :] - mp_) ** 2, axis=1) + EPS2); fs = (jnp.exp(-P.kappa_m * dsrc)[:, None] * ma).sum(0)
        return (w[:, None] * L).sum(0) + fs + mb

    def drift(state, t, ctl):
        X, C, MU, L, D, E, U = state; c = unpack(ctl); alive, hp, rf = c[4], c[11], c[12]
        dX, dC, dMU, Delta = struct_drift(X, C, MU, L, U, ctl)
        AB = jax.vmap(lambda xi, i: paracrine(xi, i, X, D, ctl))(X, idx); f = (AB[:, 0] + P.eps / 2) / (AB[:, 0] + AB[:, 1] + P.eps)
        rho = jax.nn.sigmoid(L); q = jax.nn.softmax(MU, axis=1)
        dL = (-2 * P.r * jnp.sinh(L) + hp[0] * (2 * f - 1) + hp[2] * P.beta_E * Delta) * (rf < 0)
        dD = P.k_d * (jnp.stack([rho, 1 - rho], 1) - D)
        dE = P.k_e * (rho * (q @ mp) + (1 - rho) * (q @ mm) - E)
        dU = (light_u(ctl) - U) / P.tau_rec
        am = alive
        return (dX, dC, dMU, dL * am, dD * am[:, None], dE * am, dU * am)

    def rk4(state, t, dt, ctl):
        add = lambda s, k, a: jax.tree_util.tree_map(lambda u, v: u + a * v, s, k)
        k1 = drift(state, t, ctl); k2 = drift(add(state, k1, dt / 2), t + dt / 2, ctl)
        k3 = drift(add(state, k2, dt / 2), t + dt / 2, ctl); k4 = drift(add(state, k3, dt), t + dt, ctl)
        return jax.tree_util.tree_map(lambda s, a, b, c, d: s + dt / 6 * (a + 2 * b + 2 * c + d), state, k1, k2, k3, k4)

    noisy = any(v > 0 for v in (P.sig_x, P.sig_c, P.sig_mu, P.sig_h, P.sig_d, P.sig_e))

    def noise_incr(key, step_idx, dt):
        def one(i): return jax.random.normal(jax.random.fold_in(jax.random.fold_in(key, step_idx), i), (2 + 4 + S + 4,))
        z = jax.vmap(one)(idx) * jnp.sqrt(dt); zm = z[:, 6:6 + S]; zm = zm - zm.mean(1, keepdims=True)
        return (P.sig_x * z[:, :2], P.sig_c * z[:, 2:6], P.sig_mu * zm, P.sig_h * z[:, 6 + S], P.sig_d * z[:, 7 + S:9 + S], P.sig_e * z[:, 9 + S])

    def step(state, t, step_idx, dt, key, ctl):
        new = rk4(state, t, dt, ctl)
        if noisy:
            nz = noise_incr(key, step_idx, dt); al = unpack(ctl)[4]; rf = unpack(ctl)[12]
            nz = list(nz); nz[3] = nz[3] * (rf < 0)
            new = tuple(a + b * (al[:, None] if b.ndim == 2 else al) for a, b in zip(new[:6], nz)) + (new[6],)
        return new

    def window(t, ton, toff, ramp):
        up = jnp.clip((t - ton) / ramp, 0.0, 1.0); dn = jnp.clip((toff - t) / ramp, 0.0, 1.0); x = jnp.minimum(up, dn)
        return 0.5 * (1.0 - jnp.cos(jnp.pi * x))
    RAMPED = (0, 1, 2, 3, 6, 7, 9, 10)

    @partial(jax.jit, static_argnames=('n_steps', 'save_every'))
    def run_ctl(state, t0, dt, n_steps, key, amps, ton, toff, ramp, step0=0, save_every=0):
        amps = unpack(tuple(amps))
        def one(s, k):
            t = t0 + k * dt; w = window(t, ton, toff, ramp)
            ctl = tuple(w * a if j in RAMPED else a for j, a in enumerate(amps))
            return step(s, t, step0 + k, dt, key, ctl)
        body = lambda s, k: (one(s, k), None)
        if save_every:
            def blk(s, kk):
                s2, _ = jax.lax.scan(body, s, kk); return s2, s2
            return jax.lax.scan(blk, state, jnp.arange(n_steps).reshape(-1, save_every))
        fin, _ = jax.lax.scan(body, state, jnp.arange(n_steps)); return fin

    def diagnostics(state, ctl=()):
        X, C, MU, L, D, E, U = state
        AB = jax.vmap(lambda xi, i: paracrine(xi, i, X, D, ctl))(X, idx); f = (AB[:, 0] + P.eps / 2) / (AB[:, 0] + AB[:, 1] + P.eps)
        q, rho, gx, gc, Ea, Eb = struct_and_E(X, C, MU, L, U, ctl)
        return dict(q=q, rho=jax.nn.sigmoid(L), f=f, A=AB[:, 0], B=AB[:, 1], Ea=Ea, Eb=Eb, Delta=jnp.sum(q * (Eb - Ea), 1))

    def jac_flat(state, t=0.0, ctl=()):
        flat, unflat = flatten_state(state)
        return jax.jacfwd(lambda v: flatten_state(drift(unflat(v), t, ctl))[0])(flat)

    ns = type("Engine4", (), {})()
    ns.tm, ns.P, ns.n, ns.S = tm, P, n, S; ns.run_ctl = run_ctl; ns.window = window; ns.unpack = unpack; ns.dt = 0.0125; ns.hp0 = hp0
    ns.drift = jax.jit(lambda s, t=0.0, ctl=(): drift(s, t, ctl)); ns.diagnostics = jax.jit(lambda s, ctl=(): diagnostics(s, ctl)); ns.jac_flat = jac_flat
    ns.Sp, ns.Sm = Sp, Sm
    return ns


def flatten_state(state):
    sh = [a.shape for a in state]; sizes = [int(np.prod(s)) for s in sh]; flat = jnp.concatenate([a.reshape(-1) for a in state])
    def unflat(v):
        out, o = [], 0
        for s, z in zip(sh, sizes): out.append(v[o:o + z].reshape(s)); o += z
        return tuple(out)
    return flat, unflat


def zero_ctl(eng):
    n = eng.n
    return (jnp.zeros((n, 4)), jnp.zeros((n, 4)), jnp.zeros(n), jnp.zeros((n, 2)), jnp.ones(n), jnp.zeros((1, 2)), jnp.zeros((1, 4)), jnp.zeros(4), jnp.zeros((1, 2)), jnp.zeros((1, 2)), jnp.zeros(2),
            eng.hp0, -jnp.ones(n))


def run_plain(eng, state, t0, T, key, step0=0, ctl=None, dt=None):
    dt = dt or eng.dt; ctl = zero_ctl(eng) if ctl is None else ctl
    return eng.run_ctl(state, t0, dt, int(round(T / dt)), key, ctl, -1e30, 1e30, 1.0, step0=step0)


def seeded_start4(tm, k, state='a', a=8.0, jit_x=0.3, jit_mu=0.3, lstar=2.29):
    S = 24; rng = np.random.default_rng(777 + k); perm = rng.permutation(S)
    Xs = tm.XsA if state == 'a' else tm.XsB
    MU = np.zeros((S, S)); MU[np.arange(S), perm] = a; MU += jit_mu * rng.standard_normal((S, S))
    X = Xs[:, perm].T + jit_x * rng.standard_normal((S, 2)); C = tm.CL[:, perm].T
    L = np.full(S, lstar if state == 'a' else -lstar); rho = 1 / (1 + np.exp(-L)); D = np.stack([rho, 1 - rho], 1)
    Sp, Sm = reporter_sets(tm); q = np.exp(MU - MU.max(1, keepdims=True)); q /= q.sum(1, keepdims=True)
    E = rho * q[:, Sp].sum(1) + (1 - rho) * q[:, Sm].sum(1)
    return tuple(jnp.array(v) for v in (X, C, MU, L, D, E, np.zeros(S))), perm
