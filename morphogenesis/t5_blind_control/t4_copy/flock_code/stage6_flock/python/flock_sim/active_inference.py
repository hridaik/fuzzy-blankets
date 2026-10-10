"""Per-timestep active-inference decision step, ported from
active_inference_bird_control.m / active_inference_bird_control_t, specialized to
the no-predator, heading-only (Nf=1) scope documented in METHODS_AUDIT.md.

Key analytic simplification (derived while porting, verified algebraically —
see PORT_VALIDATION.md "Structural simplification" note): because every column of
B(:,:,u) is identical (Eq. 5 has no dependence on the previous heading), the
expected-free-energy G(u) computed by the upstream code provably does NOT depend
on the agent's current belief about its own heading, nor on the "predictive
observation" resample the upstream code performs at the end of
active_inference_bird_control_t (that resample only feeds back into an internal
belief/vFE bookkeeping value that itself never affects G(u) or the physically
sampled state trajectory). Consequently:
  - G(u) reduces to a fixed lookup table indexed only by (neighbor slot, action,
    neighbor's *current* realized heading), precomputed once per ModelParams.
  - The physical simulation only needs two RNG draws per bird per timestep
    (action choice, next-heading sample), matching the audit's RNG inventory
    entries (1) and (2); draw (3) (predictive-observation resample) is provably
    inert for anything measured in this study and is not implemented.
This is a documented, deliberate scope reduction, not an approximation of an
unknown quantity.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .lattice import Lattice
from .model import ModelParams, neighbor_likelihood, transition_matrix, preference_vector


@dataclass
class PrecomputedModel:
    params: ModelParams
    Bu: np.ndarray          # (nu, nu): Bu[:, a] = predicted own-heading dist. after action a
    G_table: np.ndarray     # (8, nu): ambiguity contribution per (slot, action), x2 lookahead steps
    Risk_table: np.ndarray  # (8, nu, nu): risk contribution per (slot, action, neighbor_heading), x2 steps


def build_model(params: ModelParams) -> PrecomputedModel:
    nu = params.nu
    B3 = transition_matrix(params)          # (nu,nu,nu), identical columns per action
    Bu = B3[:, 0, :]                        # (nu, nu): column a = distribution for action a

    G_table = np.zeros((8, nu))
    Risk_table = np.zeros((8, nu, nu))
    for slot in range(8):
        A = neighbor_likelihood(slot, params)      # (nu,nu) column-stochastic
        lnA = np.log(A + 1e-16)
        Hu = np.sum(A * lnA, axis=0)                # (nu,) ambiguity per own-heading column
        for a in range(nu):
            x = Bu[:, a]                            # predicted own-heading dist for action a
            amb = float(Hu @ x)                     # one lookahead step
            G_table[slot, a] = 2.0 * amb            # two identical lookahead steps (x1==x2)
            qo = A @ x                              # predicted distribution over observing this neighbor
            ln_qo = np.log(qo + 1e-16)
            for h in range(nu):
                lnC = np.log(preference_vector(h, params) + 1e-16)
                risk = float(qo @ (lnC - ln_qo))
                Risk_table[slot, a, h] = 2.0 * risk
    return PrecomputedModel(params=params, Bu=Bu, G_table=G_table, Risk_table=Risk_table)


def compute_G(pm: PrecomputedModel, lattice: Lattice, z: np.ndarray) -> np.ndarray:
    """G[i, a] = expected free energy (upstream sign convention: policy posterior is
    softmax(+W*G), i.e. HIGHER G is preferred, matching mdp.ut=spm_softmax(mdp.W(t)*G)
    with no sign flip in the upstream code) for bird i taking action a."""
    nn, nu = lattice.nn, pm.params.nu
    G = np.zeros((nn, nu))
    # Flatten all (bird, neighbor) edges once (static across time; could be cached
    # on the Lattice, done inline here for clarity).
    bird_ids = np.concatenate([np.full(len(ids), i) for i, ids in enumerate(lattice.neighbor_ids)])
    slot_ids = np.concatenate(lattice.neighbor_slot)
    nbr_ids = np.concatenate(lattice.neighbor_ids)

    nbr_heading = z[nbr_ids]                          # (E,)
    contrib = pm.G_table[slot_ids, :] + pm.Risk_table[slot_ids, :, nbr_heading]  # (E, nu)
    np.add.at(G, bird_ids, contrib)
    return G


def policy_posterior(pm: PrecomputedModel, G: np.ndarray) -> np.ndarray:
    """Vectorized replica of the precision self-tuning loop in
    active_inference_bird_control_t (lines ~184-204): N iterations, lambda=0,
    alpha/spm_beta as configured, W initialized at 0 for every bird every timestep."""
    p = pm.params
    nn = G.shape[0]
    W = np.zeros(nn)
    ut = np.full(G.shape, 1.0 / G.shape[1])
    for _ in range(p.n_iter):
        z = W[:, None] * G
        z = z - z.max(axis=1, keepdims=True)
        e = np.exp(z)
        ut = e / e.sum(axis=1, keepdims=True)
        b = p.spm_beta - np.sum(ut * G, axis=1)
        b = np.where(np.abs(b) < 1e-12, 1e-12, b)
        W = p.alpha / b
    return ut


def sample_categorical_rows(probs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """probs: (n, k) row-stochastic. Returns (n,) int samples, one per row, using
    the same cumulative-sum-vs-uniform-draw rule as upstream's
    find(rand < cumsum(P), 1) (first index where the cumulative sum exceeds the
    draw)."""
    u = rng.random(probs.shape[0])
    cdf = np.cumsum(probs, axis=1)
    cdf[:, -1] = 1.0  # guard against floating-point shortfall
    return (u[:, None] > cdf).sum(axis=1).astype(int).clip(max=probs.shape[1] - 1)


def step(
    pm: PrecomputedModel,
    lattice: Lattice,
    z: np.ndarray,
    rng: np.random.Generator,
    forced_actions: dict[int, int] | None = None,
) -> dict:
    """Advance the flock by one timestep.

    Returns a dict with: z_new, natural_action, applied_action, was_overridden,
    G (for diagnostics), ut (policy posterior, for diagnostics).
    """
    G = compute_G(pm, lattice, z)
    ut = policy_posterior(pm, G)
    natural_action = sample_categorical_rows(ut, rng)   # RNG draw #1, consumed for every bird

    applied_action = natural_action.copy()
    was_overridden = np.zeros(lattice.nn, dtype=bool)
    if forced_actions:
        for bird, act in forced_actions.items():
            applied_action[bird] = act
            was_overridden[bird] = True

    Bu = pm.Bu
    action_dists = Bu[:, applied_action].T             # (nn, nu): row i = dist for applied_action[i]
    z_new = sample_categorical_rows(action_dists, rng)  # RNG draw #2, consumed for every bird

    return dict(
        z_new=z_new,
        natural_action=natural_action,
        applied_action=applied_action,
        was_overridden=was_overridden,
        G=G,
        ut=ut,
    )
