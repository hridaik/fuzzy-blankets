"""Testbed v3 engine: structure module (v2 G1 point, h removed) + memory module (paracrine ratiometric handedness, reporter).  See ENGINE_SPEC_V3.md.

State per cell: x (2), c (4), mu (S), l (1), d=(dA,dB) (2), e (1).
The structure variables (x, c, mu) never read a memory variable (l, d, e, memory controls); noise is drawn per variable so a memory intervention leaves
structure bit-identical (T4).
"""
from __future__ import annotations
import os, sys
from dataclasses import dataclass
from functools import partial
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'testbed_v2', 'code'))   # v2 code, imported read-only
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
from engine2 import make_template2, Template2          # template (positions, L codes, expected fields)
EPS2 = 1e-12
NSIG_EXTRA = 4          # l, dA, dB, e


@dataclass(frozen=True)
class Params3:
    # structure (v2 G1 operating point)
    pi_c: float = float(np.e); pi_lam: float = float(np.e ** 3); beta_E: float = 4.0; k_mu: float = 0.2; k_a: float = 0.4
    # memory
    r: float = 0.05; g: float = 0.6; k_d: float = 0.4; k_e: float = 0.4; eps: float = 1e-3; kappa_m: float = 1.0
    # noise
    sig_x: float = 0.0; sig_c: float = 0.0; sig_mu: float = 0.0; sig_h: float = 0.0; sig_d: float = 0.0; sig_e: float = 0.0
    freeze_structure: bool = False      # diagnostic: structure drift and noise switched off (positions fixed)
    place_self_attenuation: bool = False   # H4b variant: perception ignores the self term of s^lam and the own-code term (pi_c -> 0 in E); action unchanged


def reporter_sets(tm: Template2):
    br = np.where((tm.CL != tm.CR).any(0))[0]
    Sp = br[tm.Xs[1, br] > 0]; Sm = br[tm.Xs[1, br] < 0]
    assert len(Sp) == 4 and len(Sm) == 4
    return Sp, Sm


def make_engine3(tm: Template2, P: Params3, N: int = None):
    S = tm.S; n = N or S
    CL = jnp.asarray(tm.CL); Lam = jnp.asarray(tm.LamL); kap = float(tm.kappa)
    Sp, Sm = reporter_sets(tm); mp = np.zeros(S); mp[Sp] = 1.0; mm = np.zeros(S); mm[Sm] = 1.0; mp = jnp.asarray(mp); mm = jnp.asarray(mm)
    idx = jnp.arange(n)

    def unpack(ctl):
        """ctl = (ext (n,4), rg (n,4), mig (n,), uM (n,2), alive (n,), src_pos (m,2), src_amp (m,4), bath (4,), msrc_pos (m2,2), msrc_amp (m2,2), mbath (2,))"""
        dflt = (jnp.zeros((n, 4)), jnp.zeros((n, 4)), jnp.zeros((n,)), jnp.zeros((n, 2)), jnp.ones((n,)), jnp.zeros((1, 2)), jnp.zeros((1, 4)), jnp.zeros((4,)),
                jnp.zeros((1, 2)), jnp.zeros((1, 2)), jnp.zeros((2,)))
        return tuple(ctl) + dflt[len(ctl):]

    # ---------------- structure -------------------------------------------------
    def sens(own, i, X, C, ctl):
        xi, ci = own; ext, rg, _m, _u, alive, sp, sa, bath = unpack(ctl)[:8]
        d = jnp.sqrt(jnp.sum((xi[None, :] - X) ** 2, axis=1) + EPS2); notself = (idx != i).astype(xi.dtype)
        kern = jnp.exp(-kap * d) * notself
        Ce = (C + ext) * alive[:, None]
        dsrc = jnp.sqrt(jnp.sum((xi[None, :] - sp) ** 2, axis=1) + EPS2); fsrc = (jnp.exp(-kap * dsrc)[:, None] * sa).sum(0) + bath
        selfterm = 0.0 if P.place_self_attenuation else 1.0
        lam = ((kern[:, None] * Ce).sum(0) + selfterm * (ci + ext[i]) * alive[i] + fsrc) * (1.0 + rg[i])
        lam_full = ((kern[:, None] * Ce).sum(0) + (ci + ext[i]) * alive[i] + fsrc) * (1.0 + rg[i])
        return ci, lam, lam_full

    def place_E(sc, sl):
        pc = 0.0 if P.place_self_attenuation else P.pi_c
        return 0.5 * (pc * jnp.sum((sc[:, None] - CL) ** 2, 0) + P.pi_lam * jnp.sum((sl[:, None] - Lam) ** 2, 0))

    def action_obj(own, i, X, C, ctl, q):
        sc, sl, slf = sens(own, i, X, C, ctl)
        # action always uses the full (self-sensing) energies
        E = 0.5 * (P.pi_c * jnp.sum((sc[:, None] - CL) ** 2, 0) + P.pi_lam * jnp.sum((slf[:, None] - Lam) ** 2, 0))
        return jnp.sum(q * E)
    gradA = jax.grad(action_obj, argnums=0)

    def struct_drift(X, C, MU, ctl):
        mig = unpack(ctl)[2]; alive = unpack(ctl)[4]
        q = jax.nn.softmax(MU, axis=1)
        gx, gc = jax.vmap(lambda xi, ci, qi, i: gradA((xi, ci), i, X, C, ctl, qi))(X, C, q, idx)
        E = jax.vmap(lambda xi, ci, i: place_E(*sens((xi, ci), i, X, C, ctl)[:2]))(X, C, idx)
        z = MU + P.beta_E * E
        dMU = -P.k_mu * (z - z.mean(1, keepdims=True))
        am = alive[:, None]
        return -P.k_a * (1.0 + mig[:, None]) * gx * am, -P.k_a * gc * am, dMU * am

    # ---------------- memory ----------------------------------------------------
    def paracrine(xi, i, X, D, ctl):
        """returns (A_i, B_i): kernel-weighted memory ligand levels seen by cell i (j != i, alive only; light u, pipettes, bath)"""
        uM, alive, mp_, ma, mb = unpack(ctl)[3], unpack(ctl)[4], unpack(ctl)[8], unpack(ctl)[9], unpack(ctl)[10]
        d = jnp.sqrt(jnp.sum((xi[None, :] - X) ** 2, axis=1) + EPS2); w = jnp.exp(-P.kappa_m * d) * (idx != i) * alive
        L = D + uM
        dsrc = jnp.sqrt(jnp.sum((xi[None, :] - mp_) ** 2, axis=1) + EPS2); fs = (jnp.exp(-P.kappa_m * dsrc)[:, None] * ma).sum(0)
        return (w[:, None] * L).sum(0) + fs + mb

    def memory_drift(X, MU, L, D, E, ctl):
        alive = unpack(ctl)[4]
        AB = jax.vmap(lambda xi, i: paracrine(xi, i, X, D, ctl))(X, idx)           # (n,2)
        f = (AB[:, 0] + P.eps / 2) / (AB[:, 0] + AB[:, 1] + P.eps)
        rho = jax.nn.sigmoid(L); q = jax.nn.softmax(MU, axis=1)
        dL = -2 * P.r * jnp.sinh(L) + P.g * (2 * f - 1)
        dD = P.k_d * (jnp.stack([rho, 1 - rho], 1) - D)
        estar = rho * (q @ mp) + (1 - rho) * (q @ mm)
        dE = P.k_e * (estar - E)
        return dL * alive, dD * alive[:, None], dE * alive, f

    def drift(state, t, ctl):
        X, C, MU, L, D, E = state
        if P.freeze_structure: dX, dC, dMU = jnp.zeros_like(X), jnp.zeros_like(C), jnp.zeros_like(MU)
        else: dX, dC, dMU = struct_drift(X, C, MU, ctl)
        dL, dD, dE, _f = memory_drift(X, MU, L, D, E, ctl)
        return (dX, dC, dMU, dL, dD, dE)

    def rk4(state, t, dt, ctl):
        add = lambda s, k, a: jax.tree_util.tree_map(lambda u, v: u + a * v, s, k)
        k1 = drift(state, t, ctl); k2 = drift(add(state, k1, dt / 2), t + dt / 2, ctl)
        k3 = drift(add(state, k2, dt / 2), t + dt / 2, ctl); k4 = drift(add(state, k3, dt), t + dt, ctl)
        return jax.tree_util.tree_map(lambda s, a, b, c, d: s + dt / 6 * (a + 2 * b + 2 * c + d), state, k1, k2, k3, k4)

    noisy = any(v > 0 for v in (P.sig_x, P.sig_c, P.sig_mu, P.sig_h, P.sig_d, P.sig_e))
    nsig = 2 + 4 + S + NSIG_EXTRA - 1 + 1 + 0     # x2 c4 mu S | l, dA, dB, e  -> 2+4+S+4

    def noise_incr(key, step_idx, dt):
        def one(i): return jax.random.normal(jax.random.fold_in(jax.random.fold_in(key, step_idx), i), (2 + 4 + S + 4,))
        z = jax.vmap(one)(idx) * jnp.sqrt(dt); zm = z[:, 6:6 + S]; zm = zm - zm.mean(1, keepdims=True)
        sc = 0.0 if P.freeze_structure else 1.0
        return (sc * P.sig_x * z[:, :2], sc * P.sig_c * z[:, 2:6], sc * P.sig_mu * zm, P.sig_h * z[:, 6 + S], P.sig_d * z[:, 7 + S:9 + S], P.sig_e * z[:, 9 + S])

    def step(state, t, step_idx, dt, key, ctl):
        new = rk4(state, t, dt, ctl)
        if noisy:
            nz = noise_incr(key, step_idx, dt); al = unpack(ctl)[4]
            new = tuple(a + b * (al[:, None] if b.ndim == 2 else al) for a, b in zip(new, nz))
        return new

    def window(t, ton, toff, ramp):
        up = jnp.clip((t - ton) / ramp, 0.0, 1.0); dn = jnp.clip((toff - t) / ramp, 0.0, 1.0); x = jnp.minimum(up, dn)
        return 0.5 * (1.0 - jnp.cos(jnp.pi * x))

    RAMPED = (0, 1, 2, 3, 6, 7, 9, 10)

    @partial(jax.jit, static_argnames=('n_steps', 'save_every'))
    def run_ctl(state, t0, dt, n_steps, key, amps, ton, toff, ramp, step0=0, save_every=0):
        """amps = peak control tuple (see unpack); ramped entries (ext, rg, mig, uM, src_amp, bath, msrc_amp, mbath) are multiplied by the raised-cosine window."""
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
        X, C, MU, L, D, E = state
        AB = jax.vmap(lambda xi, i: paracrine(xi, i, X, D, ctl))(X, idx); f = (AB[:, 0] + P.eps / 2) / (AB[:, 0] + AB[:, 1] + P.eps)
        q = jax.nn.softmax(MU, axis=1); rho = jax.nn.sigmoid(L)
        E_ik = jax.vmap(lambda xi, ci, i: place_E(*sens((xi, ci), i, X, C, ctl)[:2]))(X, C, idx)
        return dict(q=q, rho=rho, f=f, A=AB[:, 0], B=AB[:, 1], E=E_ik, estar=rho * (q @ mp) + (1 - rho) * (q @ mm))

    def jac_flat(state, t=0.0, ctl=()):
        flat, unflat = flatten_state(state)
        return jax.jacfwd(lambda v: flatten_state(drift(unflat(v), t, ctl))[0])(flat)

    ns = type("Engine3", (), {})()
    ns.tm, ns.P, ns.n, ns.S = tm, P, n, S; ns.run_ctl = run_ctl; ns.window = window; ns.unpack = unpack; ns.dt = 0.0125
    ns.drift = jax.jit(lambda s, t=0.0, ctl=(): drift(s, t, ctl)); ns.diagnostics = jax.jit(lambda s, ctl=(): diagnostics(s, ctl)); ns.jac_flat = jac_flat
    ns.reporter_masks = (np.asarray(mp), np.asarray(mm)); ns.Sp, ns.Sm = Sp, Sm
    return ns


def flatten_state(state):
    sh = [a.shape for a in state]; sizes = [int(np.prod(s)) for s in sh]; flat = jnp.concatenate([a.reshape(-1) for a in state])
    def unflat(v):
        out, o = [], 0
        for s, z in zip(sh, sizes): out.append(v[o:o + z].reshape(s)); o += z
        return tuple(out)
    return flat, unflat


def zero_ctl(n, S=24):
    """full-signature zero control (sham and unforced runs use the SAME traced program as forced runs; required for bit-identical twins)"""
    return (jnp.zeros((n, 4)), jnp.zeros((n, 4)), jnp.zeros(n), jnp.zeros((n, 2)), jnp.ones(n), jnp.zeros((1, 2)), jnp.zeros((1, 4)), jnp.zeros(4), jnp.zeros((1, 2)), jnp.zeros((1, 2)), jnp.zeros(2))


def run_plain(eng, state, t0, T, key, step0=0, ctl=None, dt=None):
    dt = dt or eng.dt; ctl = zero_ctl(eng.n) if ctl is None else ctl
    return eng.run_ctl(state, t0, dt, int(round(T / dt)), key, ctl, -1e30, 1e30, 1.0, step0=step0)


def seeded_start3(tm, k, state='a', a=8.0, jit_x=0.3, jit_mu=0.3, lstar=2.29):
    """structure: committed identities at place positions + jitter (as v2); memory: l = +-lstar, d = (rho, 1-rho), reporter at its target"""
    S = tm.S; rng = np.random.default_rng(777 + k); perm = rng.permutation(S)
    MU = np.zeros((S, S)); MU[np.arange(S), perm] = a; MU += jit_mu * rng.standard_normal((S, S))
    X = tm.Xs[:, perm].T + jit_x * rng.standard_normal((S, 2)); C = tm.CL[:, perm].T
    L = np.full(S, lstar if state == 'a' else -lstar); rho = 1 / (1 + np.exp(-L)); D = np.stack([rho, 1 - rho], 1)
    Sp, Sm = reporter_sets(tm); q = np.exp(MU - MU.max(1, keepdims=True)); q /= q.sum(1, keepdims=True)
    E = rho * q[:, Sp].sum(1) + (1 - rho) * q[:, Sm].sum(1)
    return (jnp.array(X), jnp.array(C), jnp.array(MU), jnp.array(L), jnp.array(D), jnp.array(E)), perm
