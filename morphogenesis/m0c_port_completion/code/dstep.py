"""Faithful Python port of the spm_ADEM.m D-step for DEM_morphogenesis.

Specialized (not generalized) to this model's fixed structure, established
and dump-validated in PORT_DESIGN_UPDATE.md:
  - nx = 0 (no hidden states, model or process)
  - np = 0, nh = 0 (=> nE forced to 1, single forward pass -- m0b finding)
  - nl = 2 for both M and G (one hierarchical level of causes)
  - n  = 3 (embedding order of responses/process, M(1).E.n+1)
  - d  = 2 (embedding order of causes, M(1).E.d+1)
  - dg.dv == 0 identically (Gg ignores its v argument) -- dump-verified,
    which removes the u.v{i} self-reference risk for this model specifically

Imports m0b's validated primitives (spm_port.py, model.py) unmodified.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                 "m0b_reference_port", "code"))
from spm_port import spm_DEM_R, spm_DEM_embed, spm_dx, DX_STEP  # noqa: E402
from model import Mg, Gg, decode_template, field_concentration, T_L2  # noqa: E402

PI1 = np.exp(3.0)     # M(1).V
PI2 = np.exp(-2.0)    # M(2).V
G1V = np.exp(16.0)    # G(1).V (process sensory precision)
G1U = np.exp(2.0)     # G(1).U (action precision)
N_EMBED = 3            # n = M(1).E.n + 1
D_EMBED = 2             # d = M(1).E.d + 1
S_SMOOTH = 1.0           # M(1).E.s


def jac_fd(f, x0):
    """Forward-difference Jacobian, step=exp(-8), column-major flatten,
    matching m0b's spm_port.spm_diff_jacobian exactly (re-declared here for
    a fixed calling convention: f(x_flat)->y_flat)."""
    f0 = f(x0)
    J = np.zeros((f0.size, x0.size))
    for i in range(x0.size):
        xp = x0.copy()
        xp[i] += DX_STEP
        J[:, i] = (f(xp) - f0) / DX_STEP
    return J


class Config:
    def __init__(self, T=None, n_bins=32):
        if T is None:
            T = T_L2
        self.P_x, self.P_s, self.n, self.m = decode_template(T)
        self.P_c = field_concentration(self.P_x, self.P_s)
        self.n_bins = n_bins
        self.ny = 2 * self.n + 2 * self.m * self.n          # Gg output dim: x(2n)+s(mn)+c(mn)
        self.gr = self.ny + 1                                # + level2 scalar
        self.nv = self.n * self.n                              # causal state dim
        self.na = 2 * self.n + self.m * self.n                  # action dim
        self.ne = self.ny + self.nv                               # error dim/order


def run_dstep(cfg: Config, v0: np.ndarray, a0_flat: np.ndarray,
              Z: np.ndarray, seed_unused=None):
    """Z: (gr, N) exported process noise (z_exported from Octave, level1+level2
    concatenated per column) -- consumed directly, not resampled, per Task 1's
    'export every random draw' requirement (m0b ORACLE_REPORT.md).
    Returns per-bin trace dict.
    """
    N = cfg.n_bins
    n, m = cfg.n, cfg.m
    nv, na, ny, gr, ne = cfg.nv, cfg.na, cfg.ny, cfg.gr, cfg.ne

    iV = spm_DEM_R(N_EMBED, S_SMOOTH)  # roughness kernel (unused directly here;
    # spm_DEM_embed already encodes the same Taylor/embedding logic)

    # generalized cause estimate: qu.v[i], i=0..D_EMBED-1 (order 1,2), each (nv,)
    qu_v = [v0.ravel(order="F").copy(), np.zeros(nv)]
    qu_a = a0_flat.copy()          # order-1 action estimate

    # process generalized response pu.v[i], i=0..N_EMBED-1
    pu_v = [np.zeros(gr) for _ in range(N_EMBED)]

    # action history (grows one column per bin): A[:, 0:b] finalized, col b = current
    A_hist = np.zeros((na, 0))

    trace = {k: [] for k in ["a_x", "a_s", "v", "p", "free_energy",
                              "eps_sensory", "eps_prior", "t"]}

    LR_A = 1.0 / (PI1 * G1U)   # step-size heuristic for the action's own
    # free-energy pull only where a closed-form Newton step is not taken;
    # NOTE: the joint spm_dx step below is what actually moves qu_v/qu_a --
    # this constant is unused in the current (spm_dx-based) implementation
    # and kept only for reference.

    for b in range(N):
        iY = b + 1
        t = iY / N

        # --- action history embedding (A = [finalized bins ; current qu_a]) ---
        A_full = np.concatenate([A_hist, qu_a[:, None]], axis=1)
        pu_a = spm_DEM_embed(A_full, N_EMBED, A_full.shape[1], 1.0, (0,))

        # --- noise embedding (Z fixed for the whole run, exported from Octave) ---
        pu_z = spm_DEM_embed(Z, N_EMBED, iY, 1.0, (0,))

        # --- process Jacobian dg.da (81 x 48), forward-diff of Gg wrt a, at pu_a[0] ---
        def gg_full(a_flat):
            return Gg(a_flat, n, m, t)
        dgda = jac_fd(gg_full, pu_a[0])   # (ny, na)

        # --- predict pu.v at all orders (dg.dv == 0 identically for this model) ---
        g_val = gg_full(pu_a[0])
        pu_v_new = [None] * N_EMBED
        pu_v_new[0] = np.concatenate([g_val + pu_z[0][:ny], pu_z[0][ny:ny + 1]])
        for i in range(1, N_EMBED):
            level1 = dgda @ pu_a[i] + pu_z[i][:ny]
            level2 = pu_z[i][ny:ny + 1]
            pu_v_new[i] = np.concatenate([level1, level2])
        pu_v = pu_v_new

        qu_y = [pu_v[i][:ny] for i in range(N_EMBED)]  # drop level-2 raw noise

        # --- model Jacobian dgdv (ny x nv), forward-diff of Mg wrt v, at qu_v[0] ---
        def mg_full(v_flat):
            return Mg(v_flat, n, cfg.P_x, cfg.P_s, cfg.P_c, t)
        dgdv_model = jac_fd(mg_full, qu_v[0])  # (ny, nv)

        # --- generalized error stack Ev[i], i=0..N_EMBED-1 ---
        mg0 = mg_full(qu_v[0])
        Ev = [None] * N_EMBED
        Ev[0] = np.concatenate([qu_y[0] - mg0, qu_v[0] - 0.0])
        for i in range(1, N_EMBED):
            v_i = qu_v[i] if i < D_EMBED else np.zeros(nv)
            sensory = qu_y[i] - dgdv_model @ v_i
            prior = v_i
            Ev[i] = np.concatenate([sensory, prior])
        E = np.concatenate(Ev)  # (N_EMBED*ne,)

        # --- free energy (J, per spm_ADEM.m line ~630, nE==1 branch) ---
        # J = -0.5*E'*iS*E + logdet(qu.c) + 0.5*logdet(iS); iS block-diag
        # per generalized order with precision PI1 (sensory ne_y) / PI2 (prior nv)
        # implemented directly via weighted sum (iS diagonal in this model):
        w_sensory = PI1
        w_prior = PI2
        e_sq = 0.0
        for i in range(N_EMBED):
            e_sq += w_sensory * np.sum(Ev[i][:ny] ** 2) + w_prior * np.sum(Ev[i][ny:] ** 2)
        # logdet(iS) and logdet(qu.c) terms are additive CONSTANTS (state-independent
        # given fixed precisions) -- tracked as free_energy_shape=-0.5*e_sq (relative
        # trace only; see EQUIVALENCE_REPORT.md for why the constant offset is not
        # reproduced here)
        free_energy = -0.5 * e_sq

        # --- D-step update (Gauss-Newton / local-linearization via spm_dx) ---
        # Reduced joint system: state = [qu_v[0], qu_v[1], qu_a], since
        # dg.dv==0 decouples pu_v entirely from qu (pu_v needs no gradient
        # update -- its own dFdu row is a pure shift/consistency term with
        # no dVdu contribution, per PORT_DESIGN_UPDATE.md).
        # Gradient of -0.5*e_sq wrt qu_v[0]:
        dE0_dv0 = np.concatenate([-dgdv_model, np.eye(nv)], axis=0)  # (ne, nv)
        dE1_dv1 = np.concatenate([-dgdv_model, np.eye(nv)], axis=0)
        Wd = np.concatenate([np.full(ny, w_sensory), np.full(nv, w_prior)])
        grad_v0 = -(dE0_dv0.T * Wd) @ Ev[0] - PI2 * qu_v[0]
        grad_v1 = -(dE1_dv1.T * Wd) @ Ev[1] - PI2 * qu_v[1]
        # action gradient via process Jacobian dg.da (B3 finding)
        dE0_da = np.concatenate([-dgda, np.zeros((nv, na))], axis=0)
        grad_a = -(dE0_da.T * Wd) @ Ev[0] - (1.0 / G1U) * qu_a

        # curvature (Gauss-Newton, diagonal precision-weighted approx):
        H_v0 = (dE0_dv0.T * Wd) @ dE0_dv0 + PI2 * np.eye(nv)
        H_v1 = (dE1_dv1.T * Wd) @ dE1_dv1 + PI2 * np.eye(nv)
        H_a = (dE0_da.T * Wd) @ dE0_da + (1.0 / G1U) * np.eye(na)

        dv0 = spm_dx(-H_v0, grad_v0, 1.0)
        dv1 = spm_dx(-H_v1, grad_v1, 1.0)
        da = spm_dx(-H_a, grad_a, 1.0)

        qu_v = [qu_v[0] + dv0, qu_v[1] + dv1]
        qu_a = qu_a + da

        # record finalized action into history
        A_hist = np.concatenate([A_hist, qu_a[:, None]], axis=1)

        a_x = qu_a[:2 * n].reshape(2, n, order="F")
        a_s = qu_a[2 * n:2 * n + m * n].reshape(m, n, order="F")
        v_mat = qu_v[0].reshape(n, n, order="F")
        p = np.exp(v_mat - v_mat.max(axis=0, keepdims=True))
        p = p / p.sum(axis=0, keepdims=True)

        trace["a_x"].append(a_x.copy())
        trace["a_s"].append(a_s.copy())
        trace["v"].append(v_mat.copy())
        trace["p"].append(p.copy())
        trace["free_energy"].append(free_energy)
        trace["eps_sensory"].append(Ev[0][:ny].copy())
        trace["eps_prior"].append(Ev[0][ny:].copy())
        trace["t"].append(t)

    return {k: np.array(v) for k, v in trace.items()}
