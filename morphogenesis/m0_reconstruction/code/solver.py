"""Reduced generalized-filtering solver for DEM_morphogenesis.

DISCLOSED DEVIATION (DISCREPANCIES.md sec 9): spm_ADEM.m implements full
generalized filtering via local linearization of the joint (causes, hidden
states, action, hyperparameters) state and matrix-exponential integration
(spm_dx). Because DEM_morphogenesis.m defines no hidden states x and no
hyperparameter components (nh=0), the dynamics that remain are: (1) a
precision-weighted gradient flow on the recognition cause v (identity
beliefs), and (2) a precision-weighted gradient flow on action a (position +
secretion), both driven by the same sensory prediction error. This module
implements that reduced flow with explicit-Euler steps rather than spm_dx's
local-linearization/matrix-exponential update. No MATLAB/Octave reference
run exists to validate this against (README.md), so this is an unvalidated
re-derivation, not a verified port.

Gradient w.r.t. v is analytic (softmax Jacobian). Gradient w.r.t. a is
analytic for the direct (identity-map) sensory channels and computed by
central finite differences for the field-coupled extrinsic-signal channel,
to avoid hand-derivation errors in the field Jacobian under time constraints.
"""
import numpy as np
from generative import Mg, Gg, spm_softmax_cols, sensitivity
from field import field_concentration

PI1 = np.exp(3.0)     # M(1).V, model sensory precision (MODEL_SPEC.md sec 4)
PI2 = np.exp(-2.0)    # M(2).V, prior precision on causes v
G1U = np.exp(2.0)     # G(1).U, action precision/gain (MODEL_SPEC.md sec 4)

N_BINS_DEFAULT = 32   # DEM_morphogenesis.m line 34
ND_INNER = 8           # inner D-step iterations per bin (disclosed simplification)
LR_V = 1.0 / PI1        # step-size heuristics chosen for stability, not sourced
LR_A = 1.0 / (PI1 * G1U)
FD_EPS = 1e-4


def _field_jacobian_vec(a_x, a_s, eps_c, s):
    """Returns (grad_ax, grad_as): d/d(a) of  s * field(a_x,a_s) . eps_c ,
    i.e. the vector-Jacobian product needed for the gradient contribution of
    the extrinsic-signal prediction error, via central finite differences.
    """
    def weighted_field_sum(ax, as_):
        c = s * field_concentration(ax, as_)
        return float(np.sum(c * eps_c))

    grad_ax = np.zeros_like(a_x)
    for idx in np.ndindex(a_x.shape):
        ax_p = a_x.copy(); ax_p[idx] += FD_EPS
        ax_m = a_x.copy(); ax_m[idx] -= FD_EPS
        grad_ax[idx] = (weighted_field_sum(ax_p, a_s) - weighted_field_sum(ax_m, a_s)) / (2 * FD_EPS)

    grad_as = np.zeros_like(a_s)
    for idx in np.ndindex(a_s.shape):
        as_p = a_s.copy(); as_p[idx] += FD_EPS
        as_m = a_s.copy(); as_m[idx] -= FD_EPS
        grad_as[idx] = (weighted_field_sum(a_x, as_p) - weighted_field_sum(a_x, as_m)) / (2 * FD_EPS)

    return grad_ax, grad_as


def d_step(v, a_x, a_s, P_x, P_s, P_c, t):
    """One gradient-ascent (free-energy-descent) update of (v, a_x, a_s)."""
    g_x_m, g_s_m, g_c_m, p = Mg(v, P_x, P_s, P_c, t)
    g_x_p, g_s_p, g_c_p = Gg(a_x, a_s, t)

    eps_x = g_x_p - g_x_m
    eps_s = g_s_p - g_s_m
    eps_c = g_c_p - g_c_m

    # --- gradient w.r.t. v (analytic softmax Jacobian) ---
    dL_dp = -PI1 * (P_x.T @ eps_x + P_s.T @ eps_s + sensitivity(t) * (P_c.T @ eps_c))
    # per-column softmax-Jacobian-transpose: diag(p)*g - p*(p.g)
    dot = np.sum(p * dL_dp, axis=0, keepdims=True)
    dL_dv = p * dL_dp - p * dot
    dL_dv = dL_dv + PI2 * v
    v_new = v - LR_V * dL_dv

    # --- gradient w.r.t. a (analytic direct terms + FD field coupling) ---
    dL_dax_direct = PI1 * eps_x
    dL_das_direct = PI1 * eps_s
    grad_ax_field, grad_as_field = _field_jacobian_vec(a_x, a_s, eps_c, sensitivity(t))
    dL_dax = dL_dax_direct + PI1 * grad_ax_field
    dL_das = dL_das_direct + PI1 * grad_as_field

    a_x_new = a_x - LR_A * dL_dax
    a_s_new = a_s - LR_A * dL_das

    free_energy = 0.5 * PI1 * (np.sum(eps_x ** 2) + np.sum(eps_s ** 2) + np.sum(eps_c ** 2)) \
        + 0.5 * PI2 * np.sum(v ** 2)

    return v_new, a_x_new, a_s_new, dict(
        eps_x=eps_x, eps_s=eps_s, eps_c=eps_c, p=p,
        g_x_m=g_x_m, g_s_m=g_s_m, g_c_m=g_c_m,
        free_energy=free_energy,
    )


PROCESS_NOISE_STD = 1.0 / np.exp(8.0)  # sqrt(1/G(1).V), G(1).V=exp(16); MODEL_SPEC sec 10.
# DISCLOSED SIMPLIFICATION: spm_ADEM samples generalized (temporally
# correlated, roughness-kernel s=1) noise via spm_DEM_z; here we inject iid
# Gaussian noise of matching marginal variance on the process's action-driven
# outputs each D-step. This is an approximation of the noise *process* (not
# of the precision magnitude, which is taken directly from G(1).V) -- see
# DISCREPANCIES.md sec 9 and OPEN_QUESTIONS.md.


def run(v0, a_x0, a_s0, P_x, P_s, P_c, n_bins=N_BINS_DEFAULT, n_inner=ND_INNER,
        interventions=None, noise_seed=None):
    """Integrate n_bins developmental bins. interventions: optional callable
    (bin_index, v, a_x, a_s) -> (v, a_x, a_s), applied before the bin's D-steps.
    noise_seed: if not None, injects iid process noise each D-step (see
    PROCESS_NOISE_STD docstring above) using a seeded RNG (E2 characterization).
    Returns a dict of per-bin time series (see DATA_SCHEMA.md)."""
    rng = np.random.default_rng(noise_seed) if noise_seed is not None else None
    v, a_x, a_s = v0.copy(), a_x0.copy(), a_s0.copy()
    trace = {k: [] for k in [
        "t", "a_x", "a_s", "v", "p", "g_x_m", "g_s_m", "g_c_m",
        "eps_x", "eps_s", "eps_c", "free_energy",
    ]}
    for b in range(n_bins):
        if interventions is not None:
            v, a_x, a_s = interventions(b, v, a_x, a_s)
        t = (b + 1) / n_bins
        info = None
        for _ in range(n_inner):
            v, a_x, a_s, info = d_step(v, a_x, a_s, P_x, P_s, P_c, t)
        if rng is not None:
            a_x = a_x + rng.normal(scale=PROCESS_NOISE_STD, size=a_x.shape)
            a_s = a_s + rng.normal(scale=PROCESS_NOISE_STD, size=a_s.shape)
        trace["t"].append(t)
        trace["a_x"].append(a_x.copy())
        trace["a_s"].append(a_s.copy())
        trace["v"].append(v.copy())
        trace["p"].append(info["p"].copy())
        trace["g_x_m"].append(info["g_x_m"].copy())
        trace["g_s_m"].append(info["g_s_m"].copy())
        trace["g_c_m"].append(info["g_c_m"].copy())
        trace["eps_x"].append(info["eps_x"].copy())
        trace["eps_s"].append(info["eps_s"].copy())
        trace["eps_c"].append(info["eps_c"].copy())
        trace["free_energy"].append(info["free_energy"])
    return {k: np.array(v) for k, v in trace.items()}
