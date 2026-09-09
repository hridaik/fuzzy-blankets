"""Black-box intervention API for Stage 6.8 (task brief sections 16-17).

EVALUATION-SIDE. Must import the simulator, because it has to actually run
interventions. It exposes ONLY numeric effect estimates through a duck-typed
interface and never returns `visible`, `is_neighbor`, an edge list, a slot id
or any other topology-derived field. `probing.py` (inference-side) receives an
instance purely as a callable and never imports `fov_dynamics` or `common_68`.

Two estimators, kept strictly separate (task brief section 17: "do not
collapse these into one number"):

`FiniteProbe.probe(...)`  -- PRIMARY. Finite active probing: sample real
    observed states, force Z_j := z', run PAIRED one-step rollouts under
    common random numbers (the same `numpy.random.Generator` seed drives the
    factual and counterfactual rollout, so the paired difference removes the
    shared sampling noise), and estimate the induced change in the interior's
    next-state distribution from the empirical rollout frequencies. Has
    genuine estimation error, which is the point.

`ExactPropagator.exact(...)` -- VALIDATION ONLY, run after the finite-probe
    estimator is frozen. Closed-form one-step counterfactual, the same
    derivation Stage 6.5/6.7 used (`stage6_5/refinement/causal_redundancy/
    code/exact_intervention.py`), generalized to the masked FOV edge set. It
    is the infinite-rollout limit of `probe`, so the difference between the
    two isolates estimation error due to finite probing from identifiability.
"""
from __future__ import annotations

import numpy as np

EPS = 1e-12
NU = 4


def _kl(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    p = np.clip(p, EPS, 1.0)
    q = np.clip(q, EPS, 1.0)
    return (p * (np.log(p) - np.log(q))).sum(axis=-1)


class ExactPropagator:
    """Closed-form one-step interventional effect under the true interaction
    graph. At L3 the live graph is FOV visibility AND the latent gate state, so
    the propagator must be handed the true current gate or it would compute the
    effect in a system that does not exist. The gate never leaves this object;
    inference-side code only ever sees the returned numbers."""

    def __init__(self, sim, channel_state=None):
        self._sim = sim
        self._channel = channel_state

    def _dist(self, z):
        m = self._sim.visible_mask(z)
        if self._channel is not None:
            m = m & self._channel
        return self._sim.next_state_dist(z, m)

    def exact(self, I, j: int, z_prime: int, z_t: np.ndarray) -> dict:
        I = np.asarray(sorted(int(i) for i in I))
        p_nat = self._dist(np.asarray(z_t))[I]
        z_do = np.asarray(z_t).copy()
        z_do[int(j)] = int(z_prime)
        p_do = self._dist(z_do)[I]
        kls = _kl(p_do, p_nat)
        return dict(D_do_joint=float(kls.sum()),
                    per_bird_kl={int(i): float(k) for i, k in zip(I, kls)})


class FiniteProbe:
    """Finite active probing with paired common-random-number rollouts."""

    def __init__(self, sim, n_rollouts: int = 200, seed: int = 0, channel_state=None):
        """`channel_state` is the true latent per-edge availability at the
        moment of probing (L3 only; None at L0/L2, where every visible edge is
        live). A real experimenter probing a gated system experiences the gates
        whether or not they can see them, so the rollouts must run under them.
        The state is held privately and is never returned or exposed -- the
        inference-side caller only ever receives numeric effect estimates."""
        self._sim = sim
        self.n_rollouts = int(n_rollouts)
        self._rng = np.random.default_rng(seed)
        self._channel = channel_state
        self.n_calls = 0
        self.n_rollouts_used = 0

    def _empirical(self, z_t: np.ndarray, I: np.ndarray, rng_seed: int) -> np.ndarray:
        """(|I|, NU) empirical next-heading frequencies over n_rollouts one-step
        rollouts from `z_t`, driven by a generator seeded with `rng_seed`."""
        rng = np.random.default_rng(rng_seed)
        counts = np.zeros((len(I), NU))
        for _ in range(self.n_rollouts):
            out = self._sim.step(np.asarray(z_t), rng, gate=self._channel)
            counts[np.arange(len(I)), out["z_new"][I]] += 1
        return counts / self.n_rollouts

    def probe(self, I, j: int, z_prime: int, z_t: np.ndarray, alpha: float = 0.5) -> dict:
        """Paired factual/counterfactual rollouts under common random numbers.
        `alpha` is a Dirichlet/Laplace smoothing constant applied to both arms
        identically, so the KL is finite at modest rollout counts and the
        smoothing cannot by itself manufacture an effect."""
        I = np.asarray(sorted(int(i) for i in I))
        crn = int(self._rng.integers(0, 2 ** 31 - 1))
        z_do = np.asarray(z_t).copy()
        z_do[int(j)] = int(z_prime)
        f_nat = self._empirical(np.asarray(z_t), I, crn)
        f_do = self._empirical(z_do, I, crn)
        n = self.n_rollouts
        p_nat = (f_nat * n + alpha) / (n + alpha * NU)
        p_do = (f_do * n + alpha) / (n + alpha * NU)
        kls = _kl(p_do, p_nat)
        self.n_calls += 1
        self.n_rollouts_used += 2 * self.n_rollouts
        return dict(D_do_joint=float(kls.sum()),
                    per_bird_kl={int(i): float(k) for i, k in zip(I, kls)})

    def budget(self) -> dict:
        return dict(n_probe_calls=self.n_calls, n_rollouts=self.n_rollouts_used,
                    rollouts_per_call=2 * self.n_rollouts)
