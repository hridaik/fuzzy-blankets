"""Exact (non-Monte-Carlo) one-step counterfactual propagation for the ported
active-inference flocking model. EVALUATION-SIDE (imports the lattice) --
this whole subpackage is evaluation-side by design (see ../../PLAN.md),
unlike boundary_inference's Part 1 inference-side/evaluation-side split.

Why exact computation is possible (see ../../PLAN.md's derivation in full):
`flock_sim.active_inference.step` samples `action_i ~ Categorical(ut_i)` then
`z_new_i ~ Categorical(Bu[:, action_i])`, independently across birds given the
current state `z_t` (every RNG draw in `step` is drawn once per bird from an
independent uniform). `Bu` does not depend on `z_t` at all (every column of
the upstream transition tensor is identical -- a documented port
simplification). `ut_i` is a deterministic softmax function of `G[i, :]`,
which depends on `z_t` only through the headings of bird `i`'s lattice
neighbours (`compute_G`: `nbr_heading = z[nbr_ids]`).

Consequences used throughout this module:
  1. The one-step marginal `p(z_{i,t+1} | z_t)` is the exact categorical
     `Bu @ ut_i(z_t)` -- no sampling, no Monte-Carlo variance.
  2. Because next-headings are drawn independently across birds given `z_t`,
     the JOINT distribution over any bird subset factors as the product of
     these per-bird marginals, so `KL(p(X_{I,t+1}|do) || p(X_{I,t+1}))` for a
     product distribution equals the SUM of the per-bird marginal KLs --
     exactly, not approximately.
  3. `do(z_j := z'_j)` changes `p(z_{i,t+1}|z_t)` if and only if `j` is a
     lattice-neighbour of `i` (since that is the only way `j` enters
     `compute_G`'s per-bird sum). A true non-shell exterior bird (`j` not a
     neighbour of any interior bird) therefore has EXACTLY zero effect on the
     interior's one-step distribution, by construction -- see
     `tests/test_exact_zero_effect.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))

from flock_sim.lattice import Lattice  # noqa: E402
from flock_sim.model import ModelParams  # noqa: E402
from flock_sim.active_inference import (  # noqa: E402
    PrecomputedModel, build_model, compute_G, policy_posterior,
)

EPS = 1e-16


def next_heading_dist_all(pm: PrecomputedModel, lattice: Lattice, z: np.ndarray) -> np.ndarray:
    """Exact one-step next-heading marginal for every bird. Returns (nn, nu)."""
    G = compute_G(pm, lattice, z)
    ut = policy_posterior(pm, G)          # (nn, nu): P(action)
    return ut @ pm.Bu.T                    # (nn, nu): P(next heading), see module docstring


def do_next_heading_dist_all(pm: PrecomputedModel, lattice: Lattice, z: np.ndarray,
                              j: int, z_j_prime: int) -> np.ndarray:
    """Same as next_heading_dist_all, but with bird j's CURRENT heading
    counterfactually set to z_j_prime before recomputing G/ut. This is the
    exact infinite-Monte-Carlo-sample limit of forcing z[j] = z_j_prime at
    time t and propagating the real simulator one step (run_simulation with
    interventions={0: {j: z_j_prime}}) -- see
    tests/test_closed_form_matches_rollout.py for the numerical cross-check."""
    z_do = z.copy()
    z_do[j] = z_j_prime
    return next_heading_dist_all(pm, lattice, z_do)


def per_bird_kl(p: np.ndarray, q: np.ndarray, eps: float = EPS) -> np.ndarray:
    """KL(p || q) per row. p, q: (n, nu)."""
    p = np.clip(p, eps, 1.0)
    q = np.clip(q, eps, 1.0)
    return (p * (np.log(p) - np.log(q))).sum(axis=1)


def interior_do_kl(pm: PrecomputedModel, lattice: Lattice, z: np.ndarray, I0: np.ndarray,
                    j: int, z_j_prime: int) -> dict:
    """D_j^do for one (X_t, j, z'_j) triple: exact joint KL over the interior
    next-state distribution, computed as the sum of per-bird marginal KLs
    (exact because next-headings are conditionally independent across birds
    given z_t -- see module docstring point 2). Also returns the per-bird
    breakdown and which interior birds are actually lattice-neighbours of j
    (so a zero total for a non-neighbour j is visibly structural, not a
    numerical coincidence)."""
    I0 = np.asarray(sorted(int(i) for i in I0))
    p_natural = next_heading_dist_all(pm, lattice, z)[I0]
    p_do = do_next_heading_dist_all(pm, lattice, z, j, z_j_prime)[I0]
    kls = per_bird_kl(p_do, p_natural)
    is_neighbor = np.array([j in set(lattice.neighbor_ids[i].tolist()) for i in I0])
    return dict(
        D_do_joint=float(kls.sum()),
        D_do_mean_per_bird=float(kls.mean()) if len(kls) else float("nan"),
        per_bird_kl={int(i): float(k) for i, k in zip(I0, kls)},
        n_neighboring_interior=int(is_neighbor.sum()),
    )


def default_precomputed_model(params: ModelParams | None = None) -> PrecomputedModel:
    return build_model(params or ModelParams())
