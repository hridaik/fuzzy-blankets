"""Continuous-time active-inference morphogenesis engine (JAX).  See ENGINE_SPEC.md.

State per cell i: position x_i (2), secretion c_i (nc), identity logits mu_i (n), optional plan logits zeta_i (K).
Each flows down the gradient of that cell's OWN free energy F_i (others' states held fixed):
    dmu/dt = -k_mu dF_i/dmu ,  dx/dt = -k_a dF_i/dx ,  dc/dt = -k_a dF_i/dc ,  dzeta/dt = -k_mu dF_i/dzeta
plus optional additive Langevin noise on x, c (mu, zeta) with per-cell counter-based streams (CRN).
"""
from __future__ import annotations
import dataclasses
from dataclasses import dataclass, field
from functools import partial
import numpy as np
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)

EPS2 = 1e-12  # smoothing of |x|^2 inside sqrt for d=0 pairs (cells start coincident)


@dataclass(frozen=True)
class Template:
    """K body plans over n slots. Xs (K,2,n); Cs (K,nc,n) codes; Lam (K,nc,n) expected field at targets (unscaled by tau)."""
    Xs: np.ndarray
    Cs: np.ndarray
    Lam: np.ndarray
    kappa: np.ndarray            # (nc,) per-channel kernel decay
    types: np.ndarray = None     # (K,n) integer cell types (for plotting / distance); optional

    @property
    def K(self): return self.Xs.shape[0]
    @property
    def n(self): return self.Xs.shape[2]
    @property
    def nc(self): return self.Cs.shape[1]


def field_np(X, C, kappa, Y=None):
    """Sum_j C_j exp(-kappa |y_i - x_j|); X (2,n) C (nc,n) -> (nc, ny)."""
    Y = X if Y is None else Y
    d = np.linalg.norm(Y[:, :, None] - X[:, None, :], axis=0)       # (ny,n)
    return np.stack([(np.exp(-k * d) * C[c][None, :]).sum(1) for c, k in enumerate(kappa)])


def make_template(Xs, Cs, kappa, types=None):
    Xs = np.asarray(Xs, float); Cs = np.asarray(Cs, float)
    if Xs.ndim == 2: Xs, Cs = Xs[None], Cs[None]
    kappa = np.broadcast_to(np.asarray(kappa, float), (Cs.shape[1],)).copy()
    Lam = np.stack([field_np(Xs[z], Cs[z], kappa) for z in range(Xs.shape[0])])
    return Template(Xs, Cs, Lam, kappa, types)


@dataclass(frozen=True)
class Params:
    pi_x: float = float(np.exp(3))      # positional channel precision
    pi_c: float = float(np.exp(3))      # secretion channel precision (scalar or per-channel via pi_c_vec)
    pi_l: float = float(np.exp(3))      # field channel precision
    pi_prior: float = float(np.exp(-2) + np.exp(-8))   # M(2).V = exp(-2) plus spm_ADEM's fixed prior Pv = exp(-8) on causes
    # action-side terms of the published scheme (spm_ADEM: G(1).U = exp(2) weights sensory errors in dF/da; Pa = exp(-2) is a prior on a)
    pi_act: float = float(1.5 * np.exp(2))   # sensory-error precision used by the ACTION gradient (perception uses pi_*)
    pi_a_x: float = float(np.exp(-2))   # prior precision on position action (set 0 for translation-invariant relational bodies)
    pi_a_c: float = float(np.exp(-2))   # prior precision on secretion action
    pi_ref: float = float(np.exp(3))    # precision the sensory errors are defined with (pi_act/pi_ref rescales the action gradient)
    pos_mode: str = 'abs'                # 'abs' (published) | 'radial' (distance-to-centroid cue) | 'bodyframe' ((u,|v|) in the collective's own principal-axis frame; rotation, translation and reflection invariant); pos_on=False switches the whole channel OFF
    pos_on: bool = True                 # positional sensory channel switch
    k_mu: float = 1.0
    k_a: float = 1.0
    T_dev: float = 32.0
    # plan layer (K>1)
    pi_zeta: float = 0.0                # prior precision on plan logits
    zeta0: tuple = ()                   # prior mean of plan logits (length K)
    k_zeta: float = 1.0                 # rate multiplier for plan logits relative to k_mu
    pi_c_vec: tuple = ()                # optional per-channel secretion precision overrides (len nc)
    pi_l_vec: tuple = ()                # optional per-channel field precision overrides (len nc)
    # noise (std of dW/sqrt(dt) scaling: dx = f dt + sig dW)
    sig_x: float = 0.0
    sig_c: float = 0.0
    sig_mu: float = 0.0
    sig_z: float = 0.0
    # deferred add-ons (OFF): chiral motility (rotation rate omega about neighbours) and turnover
    omega: float = 0.0
    frame_grad: bool = True             # bodyframe: let cells' action gradients pass through the collective frame (True = exact process; False = frame treated as external)
    nat_grad: bool = False              # D6 (testbed v1 variant): Fisher-preconditioned belief flow: dmu = -k_mu*(centred dF_sens/dp) - k_mu*pi_prior*mu
    warp_eps: float = 0.0               # DH/DT-style distortion of the sensed long-axis position: s1=(1-eps)x1+sgn*eps*x1^2
    warp_sgn: float = 1.0
    turnover_rate: float = 0.0


def tau_clock(t, T_dev):
    return 1.0 - jnp.exp(-2.0 * t / T_dev)


def _prec_vectors(P: Params, nc):
    pc = jnp.full((nc,), P.pi_c) if not P.pi_c_vec else jnp.asarray(P.pi_c_vec)
    pl = jnp.full((nc,), P.pi_l) if not P.pi_l_vec else jnp.asarray(P.pi_l_vec)
    return pc, pl


def make_engine(tmpl: Template, P: Params, N: int = None):
    """Returns namespace of jitted functions bound to template and parameters."""
    S, nc, K = tmpl.n, tmpl.nc, tmpl.K       # S = number of slots; n = number of cell positions (alive or dead), default S
    n = N or S
    Xs = jnp.asarray(tmpl.Xs); Cs = jnp.asarray(tmpl.Cs); Lam = jnp.asarray(tmpl.Lam)
    kap = jnp.asarray(tmpl.kappa)
    pc, pl = _prec_vectors(P, nc)
    z0 = jnp.asarray(P.zeta0) if len(P.zeta0) else jnp.zeros((K,))
    rstar = jnp.linalg.norm(Xs - Xs.mean(2, keepdims=True), axis=1)       # (K,n) template distance-to-centroid

    def frame_of(Xn):
        c = Xn - Xn.mean(0, keepdims=True)
        S = c.T @ c / Xn.shape[0]
        th = 0.5 * jnp.arctan2(2 * S[0, 1], S[0, 0] - S[1, 1])
        u = jnp.cos(th) * c[:, 0] + jnp.sin(th) * c[:, 1]
        flip = jnp.where(jnp.mean(u ** 3) >= 0, 1.0, -1.0)
        return Xn.mean(0), th, flip

    def own_coords(xi, frame):
        xb, th, flip = frame
        c = xi - xb
        u = jnp.cos(th) * c[0] + jnp.sin(th) * c[1]
        v = -jnp.sin(th) * c[0] + jnp.cos(th) * c[1]
        return jnp.stack([u * flip, jnp.sqrt(v ** 2 + EPS2)])

    def body_coords(Xn):
        """Xn (m,2) cloud -> (m,2) coordinates (u, |v|) in its own frame (centroid, principal axis, sign by skew)."""
        c = Xn - Xn.mean(0, keepdims=True)
        S = c.T @ c / Xn.shape[0]
        th = 0.5 * jnp.arctan2(2 * S[0, 1], S[0, 0] - S[1, 1])
        u = jnp.cos(th) * c[:, 0] + jnp.sin(th) * c[:, 1]
        v = -jnp.sin(th) * c[:, 0] + jnp.cos(th) * c[:, 1]
        flip = jax.lax.stop_gradient(jnp.where(jnp.mean(u ** 3) >= 0, 1.0, -1.0))
        return jnp.stack([u * flip, jnp.sqrt(v ** 2 + EPS2)], axis=1)
    bstar = jnp.stack([body_coords(Xs[z].T).T for z in range(K)])        # (K,2,n)
    idx = jnp.arange(n)

    def unpack(ctl):
        """ctl: array (n,nc) = exogenous secretion only (legacy), or tuple (ext (n,nc), rg (n,nc) receptor gain, mig (n,) migration gain, fb (n,n) fate-bias drive on logits)"""
        dflt = (None, jnp.zeros((n, nc)), jnp.zeros((n,)), jnp.zeros((n, S)), jnp.ones((n,)), jnp.zeros((1, 2)), jnp.zeros((1, nc)), jnp.zeros((nc,)))
        if isinstance(ctl, tuple):
            return tuple(ctl) + dflt[len(ctl):]
        return (ctl,) + dflt[1:]

    def predictions(mu, zeta):
        return predictions_p(jax.nn.softmax(mu), zeta)

    def predictions_p(p, zeta):
        w = jax.nn.softmax(zeta) if K > 1 else jnp.ones((1,))
        gx = jnp.einsum('z,zdn,n->d', w, Xs, p)
        gc = jnp.einsum('z,zcn,n->c', w, Cs, p)
        gl = jnp.einsum('z,zcn,n->c', w, Lam, p)
        return gx, gc, gl, p, w

    def F_cell(own, i, X, C, ext, tau):
        """own = (x_i, c_i, mu_i, zeta_i); X (n,2) C (n,nc) all cells (own slot ignored); ext (n,nc) exogenous secretion."""
        xi, ci, mui, zi = own
        return F_core((xi, ci, jax.nn.softmax(mui), zi), i, X, C, ext, tau)

    def F_core(own, i, X, C, ext, tau):
        xi, ci, p_in, zi = own
        ext, rg, _mig, _fb, alive, src_pos, src_amp, bath = unpack(ext)
        d2 = jnp.sum((xi[None, :] - X) ** 2, axis=1)
        d = jnp.sqrt(d2 + EPS2)
        notself = (idx != i).astype(xi.dtype)
        Ce = (C + ext) * alive[:, None]
        kern = jnp.exp(-kap[None, :] * d[:, None]) * notself[:, None]       # (n,nc)
        dsrc = jnp.sqrt(jnp.sum((xi[None, :] - src_pos) ** 2, axis=1) + EPS2)                 # pipette sources (point emitters) and bath (global level)
        field_src = (jnp.exp(-kap[None, :] * dsrc[:, None]) * src_amp).sum(0) + bath
        lam = ((kern * Ce).sum(0) + (ci + ext[i]) * alive[i] + field_src) * (1.0 + rg[i])             # self-term: kernel(0)=1; rg = receptor gain (D7 actuator)
        gx, gc, gl, p, w = predictions_p(p_in, zi)
        if P.pos_on and P.pos_mode == 'radial':
            xbar = ((notself[:, None] * X).sum(0) + xi) / n
            sr = jnp.sqrt(jnp.sum((xi - xbar) ** 2) + EPS2)
            gr = jnp.einsum('z,zn,n->', w, rstar, p)
            Fx = 0.5 * P.pi_x * (sr - gr) ** 2
        elif P.pos_on and P.pos_mode == 'bodyframe':
            Xall = jnp.where((idx == i)[:, None], xi[None, :], X)
            if P.frame_grad:
                sx = body_coords(Xall)[i]
            else:
                sx = own_coords(xi, jax.lax.stop_gradient(frame_of(Xall)))
            gb = jnp.einsum('z,zdn,n->d', w, bstar, p)
            Fx = 0.5 * P.pi_x * jnp.sum((sx - gb) ** 2)
        elif P.pos_on:
            sx = xi if P.warp_eps == 0.0 else jnp.stack([(1 - P.warp_eps) * xi[0] + P.warp_sgn * P.warp_eps * xi[0] ** 2, xi[1]])
            Fx = 0.5 * P.pi_x * jnp.sum((sx - gx) ** 2)
        else:
            Fx = 0.0
        Fc = 0.5 * jnp.sum(pc * (ci - gc) ** 2)
        Fl = 0.5 * jnp.sum(pl * (tau * lam - tau * gl) ** 2)
        return Fx + Fc + Fl

    gradF = jax.grad(F_cell, argnums=0)
    gradP = jax.grad(F_core, argnums=0)

    def drift(state, t, ext):
        X, C, MU, ZE = state
        tau = tau_clock(t, P.T_dev)
        gx_, gc_, gmu_, gz_ = jax.vmap(lambda xi, ci, mi, zi, i: gradF((xi, ci, mi, zi), i, X, C, ext, tau))(X, C, MU, ZE, idx)
        if P.nat_grad:
            gp_ = jax.vmap(lambda xi, ci, mi, zi, i: gradP((xi, ci, jax.nn.softmax(mi), zi), i, X, C, ext, tau)[2])(X, C, MU, ZE, idx)
            gmu_ = gp_ - gp_.mean(axis=1, keepdims=True)
        _e, _rg, mig, fb, alive_, _sp, _sa, _bt = unpack(ext)
        r = P.pi_act / P.pi_ref
        dX = -P.k_a * (1.0 + mig[:, None]) * (r * gx_ + P.pi_a_x * X); dC = -P.k_a * (r * gc_ + P.pi_a_c * C)
        dMU = -P.k_mu * (gmu_ + P.pi_prior * MU) + fb
        dZE = -P.k_mu * P.k_zeta * (gz_ + (P.pi_zeta * (ZE - z0) if K > 1 else 0.0))
        am = alive_[:, None]; dX, dC, dMU, dZE = dX * am, dC * am, dMU * am, dZE * am     # dead cells are frozen
        if P.omega != 0.0:  # deferred add-on (flag only): rotation about the centroid
            r = X - X.mean(0, keepdims=True)
            dX = dX + P.omega * jnp.stack([-r[:, 1], r[:, 0]], axis=1)
        return (dX, dC, dMU, dZE)

    def F_total_parts(state, t, ext=None):
        X, C, MU, ZE = state
        ext = jnp.zeros((n, nc)) if ext is None else ext
        tau = tau_clock(t, P.T_dev)
        Fs = jax.vmap(lambda xi, ci, mi, zi, i: F_cell((xi, ci, mi, zi), i, X, C, ext, tau))(X, C, MU, ZE, idx)
        return Fs + 0.5 * P.pi_prior * jnp.sum(MU ** 2, axis=1) + (0.5 * P.pi_zeta * jnp.sum((ZE - z0) ** 2, axis=1) if K > 1 else 0.0)

    def rk4(state, t, dt, ext):
        add = lambda s, k, a: jax.tree_util.tree_map(lambda u, v: u + a * v, s, k)
        k1 = drift(state, t, ext)
        k2 = drift(add(state, k1, dt / 2), t + dt / 2, ext)
        k3 = drift(add(state, k2, dt / 2), t + dt / 2, ext)
        k4 = drift(add(state, k3, dt), t + dt, ext)
        return jax.tree_util.tree_map(lambda s, a, b, c, d: s + dt / 6 * (a + 2 * b + 2 * c + d), state, k1, k2, k3, k4)

    def noise_incr(key, step, dt):
        """Independent per-cell, per-step Gaussian increments indexed by (key, absolute step, cell): CRN-safe."""
        def one(i):
            k = jax.random.fold_in(jax.random.fold_in(key, step), i)
            return jax.random.normal(k, (2 + nc + S + K,))
        z = jax.vmap(one)(idx) * jnp.sqrt(dt)
        return (P.sig_x * z[:, :2], P.sig_c * z[:, 2:2 + nc], P.sig_mu * z[:, 2 + nc:2 + nc + S], P.sig_z * z[:, 2 + nc + S:])

    noisy = (P.sig_x > 0) or (P.sig_c > 0) or (P.sig_mu > 0) or (P.sig_z > 0)

    def step(state, t, step_idx, dt, key, ext):
        new = rk4(state, t, dt, ext)
        if noisy:
            nx, nc_, nm, nz = noise_incr(key, step_idx, dt)
            al = unpack(ext)[4][:, None]; nx, nc_, nm, nz = nx * al, nc_ * al, nm * al, nz * al
            new = (new[0] + nx, new[1] + nc_, new[2] + nm, new[3] + nz)
        return new

    @partial(jax.jit, static_argnames=('n_steps', 'save_every'))
    def run(state, t0, dt, n_steps, key, ext_fn_args=None, step0=0, save_every=1):
        """Integrate n_steps of size dt from absolute time t0 (absolute step counter step0 for CRN). Returns final state and saved states
        every save_every steps (including the state after step save_every). ext_fn_args=(ext_amp (n,nc), t_on, t_off): box-window exogenous secretion."""
        def body(carry, k):
            s = carry
            t = t0 + k * dt
            if ext_fn_args is None:
                ext = jnp.zeros((n, nc))
            else:
                amp, ton, toff = ext_fn_args
                ext = amp * ((t >= ton) & (t < toff)).astype(amp.dtype)
            s2 = step(s, t, step0 + k, dt, key, ext)
            return s2, s2
        final, traj = jax.lax.scan(body, state, jnp.arange(n_steps))
        traj = jax.tree_util.tree_map(lambda a: a[save_every - 1::save_every], traj)
        return final, traj

    @partial(jax.jit, static_argnames=('n_steps',))
    def run_final(state, t0, dt, n_steps, key, ext_fn_args=None, step0=0):
        def body(s, k):
            t = t0 + k * dt
            if ext_fn_args is None:
                ext = jnp.zeros((n, nc))
            else:
                amp, ton, toff = ext_fn_args
                ext = amp * ((t >= ton) & (t < toff)).astype(amp.dtype)
            return step(s, t, step0 + k, dt, key, ext), None
        final, _ = jax.lax.scan(body, state, jnp.arange(n_steps))
        return final

    def init_from_mu(MU, ZE=None):
        MU = jnp.asarray(MU)
        ZE = jnp.zeros((n, K)) if ZE is None else jnp.asarray(ZE)
        p = jax.nn.softmax(MU, axis=1)
        w = jax.nn.softmax(ZE, axis=1) if K > 1 else jnp.ones((n, 1))
        X = jnp.einsum('iz,zdn,in->id', w, Xs, p)
        C = jnp.einsum('iz,zcn,in->ic', w, Cs, p)
        return (X, C, MU, ZE)

    def free_energy(state, t=1e9, ext=None):
        return F_total_parts(state, t, ext)

    def jac_flat(state, t=1e9):
        """Full Jacobian of the drift w.r.t. the flattened state (deterministic)."""
        flat, unflat = flatten_state(state)
        f = lambda v: flatten_state(drift(unflat(v), t, jnp.zeros((n, nc))))[0]
        return jax.jacfwd(f)(flat)

    def window(t, ton, toff, ramp):
        up = jnp.clip((t - ton) / ramp, 0.0, 1.0); dn = jnp.clip((toff - t) / ramp, 0.0, 1.0); x = jnp.minimum(up, dn)
        return 0.5 * (1.0 - jnp.cos(jnp.pi * x))

    @partial(jax.jit, static_argnames=('n_steps', 'remat', 'save_every'))
    def run_ctl(state, t0, dt, n_steps, key, amps, ton, toff, ramp, step0=0, remat=False, save_every=0):
        """Forcing with smooth raised-cosine on/off ramps. amps = (ext (n,nc), rg (n,nc), mig (n,), fb (n,n)) are PEAK values; the applied control at time t is w(t)*amps.
        Differentiable w.r.t. state and amps (set remat=True for reverse mode). save_every>0 also returns the saved states."""
        amps = tuple(amps) + ((jnp.ones((n,)),) if len(amps) < 5 else ())
        def one(s, k):
            t = t0 + k * dt; w = window(t, ton, toff, ramp)
            ctl = tuple(w * a for a in amps[:4]) + (amps[4],) + tuple(w * a for a in amps[5:])
            return step(s, t, step0 + k, dt, key, ctl)
        body = jax.checkpoint(lambda s, k: (one(s, k), None)) if remat else (lambda s, k: (one(s, k), None))
        if save_every:
            def blk(s, kk):
                s2, _ = jax.lax.scan(body, s, kk); return s2, s2
            ks = jnp.arange(n_steps).reshape(-1, save_every)
            fin, tr = jax.lax.scan(blk, state, ks); return fin, tr
        fin, _ = jax.lax.scan(body, state, jnp.arange(n_steps)); return fin

    ns = type("Engine", (), {})()
    ns.tmpl, ns.P, ns.n, ns.S, ns.nc, ns.K = tmpl, P, n, S, nc, K
    ns.run_ctl = run_ctl; ns.step = step; ns.window = window; ns.drift = jax.jit(drift); ns.run = run; ns.run_final = run_final; ns.init_from_mu = init_from_mu
    ns.free_energy = jax.jit(free_energy); ns.predictions = predictions; ns.jac_flat = jac_flat
    ns.F_cell = F_cell
    return ns


def flatten_state(state):
    sh = [a.shape for a in state]
    sizes = [int(np.prod(s)) for s in sh]
    flat = jnp.concatenate([a.reshape(-1) for a in state])
    def unflat(v):
        out, o = [], 0
        for s, z in zip(sh, sizes):
            out.append(v[o:o + z].reshape(s)); o += z
        return tuple(out)
    return flat, unflat
