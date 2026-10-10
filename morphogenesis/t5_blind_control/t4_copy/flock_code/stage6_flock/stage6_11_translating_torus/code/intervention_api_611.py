"""Stage 6.11 black-box active-probing interface (task brief item 11).

EVALUATION-SIDE / SIMULATOR. `FiniteProbeMoving611` runs paired common-random-
-number (CRN) one-step rollouts from a fixed-position cache: the SAME rng
seed drives the factual (no intervention) and counterfactual (do(z_j=z'))
arms, so any difference in outcome is attributable to the intervention, not
resampling noise. It exposes only a numeric `.probe(...)` interface -- the
inference-side `probing_611.py` never touches `MovingFlock611`, `cache`, or
any simulator internal.

Uses the paired-discrepancy-RATE statistic (Stage 6.9's finding: marginal KL
saturates and returns all-zero at high policy-saturation, which this
stage's primary regime is not immune to at 53.8% saturation), matching
`intervention_api_69.FiniteProbeMoving`.
"""
from __future__ import annotations

import numpy as np

from moving_flock_611 import MovingFlock611

PROBE_ROLLOUTS = 40      # Stage 6.10 reference budget
PROBE_REPEATS = 3
BUDGET_SENSITIVITY_GRID = ((20, 3), (40, 3), (80, 3))   # (rollouts, repeats) sensitivity check


class FiniteProbeMoving611:
    """One probe object per fixed snapshot (r_t held fixed across rollouts,
    matching MovingFlock611.step_cached's one-step-probe speedup)."""

    def __init__(self, mf: MovingFlock611, r_t: np.ndarray, n_rollouts: int = PROBE_ROLLOUTS,
                 seed: int = 0):
        self.mf = mf
        self.cache = mf.position_cache(r_t)
        self.n_rollouts = int(n_rollouts)
        self.seed = int(seed)
        self._n_probe_calls = 0
        self._n_rollouts_used = 0

    def probe(self, I: np.ndarray, j: int, z_prime: int, z_t: np.ndarray) -> dict:
        """Paired CRN rollouts: baseline vs do(Z_j := z_prime).

        CRITICAL: the intervention is on bird j's CURRENT state z_t[j] (fed
        into THIS step's G_i computation for j's neighbours), NOT on j's
        drawn action/next heading. Forcing the action via `forced_actions`
        only overrides what j itself does next -- G_i(t) for every other
        bird i is already fixed from z_t before any action is drawn, so an
        action-level intervention has a PROVABLY ZERO one-step effect on
        anyone but j itself (this is exactly task brief item 13's reachability
        point, restated as a bug this stage caught rather than assumed: an
        exterior action cannot affect an interior variable at t+1 in this
        update ordering -- but a state intervention at t, which changes what
        j's neighbours currently observe, can). Returns the per-interior-bird
        discrepancy rate and its sum (D_do_joint)."""
        self._n_probe_calls += 1
        self._n_rollouts_used += self.n_rollouts
        N = len(z_t)
        z_do = z_t.copy()
        z_do[int(j)] = int(z_prime)
        disagree = np.zeros(N)
        for k in range(self.n_rollouts):
            seed_k = (self.seed, int(j), int(z_prime), k)
            rng_base = np.random.default_rng(seed_k)
            _, z_nat, _ = self.mf.step_cached(self.cache, z_t, rng_base, forced_actions=None)
            rng_do = np.random.default_rng(seed_k)
            _, z_do_out, _ = self.mf.step_cached(self.cache, z_do, rng_do, forced_actions=None)
            disagree += (z_nat != z_do_out).astype(float)
        disagree /= self.n_rollouts
        per_bird = {int(i): float(disagree[i]) for i in I}
        return dict(D_do_joint=float(sum(per_bird.values())), per_bird=per_bird,
                    per_bird_raw_disagree_series=None)

    def probe_rollout_indicators(self, I: np.ndarray, j: int, z_prime: int, z_t: np.ndarray) -> dict:
        """Same as `.probe` but returns the PER-ROLLOUT binary disagreement
        indicator per interior bird (not just its mean) -- needed for
        pooled-rollout bootstrap CIs in probing_611.py."""
        self._n_probe_calls += 1
        self._n_rollouts_used += self.n_rollouts
        N = len(z_t)
        z_do_state = z_t.copy()
        z_do_state[int(j)] = int(z_prime)
        ind = np.zeros((self.n_rollouts, N))
        for k in range(self.n_rollouts):
            seed_k = (self.seed, int(j), int(z_prime), k)
            rng_base = np.random.default_rng(seed_k)
            _, z_nat, _ = self.mf.step_cached(self.cache, z_t, rng_base, forced_actions=None)
            rng_do = np.random.default_rng(seed_k)
            _, z_do, _ = self.mf.step_cached(self.cache, z_do_state, rng_do, forced_actions=None)
            ind[k] = (z_nat != z_do).astype(float)
        return {int(i): ind[:, i].copy() for i in I}

    def budget(self) -> dict:
        return dict(n_probe_calls=self._n_probe_calls, n_rollouts=self._n_rollouts_used,
                    rollouts_per_call=self.n_rollouts)


class MultiStepAuthorityProbe:
    """Task brief item 13: control-authority estimation over a REACHABLE
    horizon tau >= 2. A single-step forced action at t cannot affect the
    interior task variable at t+1 in this update ordering (z_i(t+1) is drawn
    from G_i computed at t, before any propagated effect of the forced bird's
    new position/heading can reach a neighbour); tau=2 is the minimum
    diagnostic horizon, tau=4 the primary receding-horizon value.

    Exposes only `.authority(...)` -- a numeric duck-typed interface,
    identical in spirit to FiniteProbeMoving611.probe, so the actuator-
    selection logic in control_authority_611.py never touches MovingFlock611
    directly."""

    def __init__(self, mf: MovingFlock611, r_t: np.ndarray, z_t: np.ndarray,
                 tau: int, n_rollouts: int, seed: int = 0):
        self.mf = mf
        self.r_t = r_t
        self.z_t = z_t
        self.tau = int(tau)
        self.n_rollouts = int(n_rollouts)
        self.seed = int(seed)
        self._n_calls = 0
        self._n_rollouts_used = 0

    def _rollout(self, forced: dict | None, seed) -> np.ndarray:
        r, z = self.r_t.copy(), self.z_t.copy()
        rng = np.random.default_rng(seed)
        for step in range(self.tau):
            fa = forced if step == 0 else None
            r, z, _ = self.mf.step(r, z, rng, forced_actions=fa)
        return z

    def authority(self, I, j: int, h_star: int) -> dict:
        """A_j^{h*,tau} = E[H*_{t+tau} | do(u_j=h*)] - E[H*_{t+tau} | baseline],
        H*(z) = fraction of interior members at heading h_star. Paired CRN
        (same seed drives both arms of each rollout k)."""
        self._n_calls += 1
        self._n_rollouts_used += self.n_rollouts
        H_do = np.zeros(self.n_rollouts)
        H_base = np.zeros(self.n_rollouts)
        for k in range(self.n_rollouts):
            seed_k = (self.seed, int(j), int(h_star), k)
            z_do = self._rollout({int(j): int(h_star)}, seed_k)
            z_base = self._rollout(None, seed_k)
            H_do[k] = float((z_do[I] == h_star).mean())
            H_base[k] = float((z_base[I] == h_star).mean())
        return dict(j=int(j), h_star=int(h_star), tau=self.tau,
                    A=float(H_do.mean() - H_base.mean()),
                    H_do_mean=float(H_do.mean()), H_base_mean=float(H_base.mean()),
                    H_do=H_do.tolist(), H_base=H_base.tolist())

    def budget(self) -> dict:
        return dict(n_calls=self._n_calls, n_rollouts=self._n_rollouts_used, tau=self.tau)


def near_exterior(mf: MovingFlock611, r_t: np.ndarray, I: np.ndarray, radius_factor: float = 3.0) -> list[int]:
    """Candidate exterior probe pool: birds within `radius_factor * R` of any
    interior member. ORACLE (uses the true R) -- this is the one place the
    probing driver is allowed to use R, exactly as Stage 6.8/6.9's own
    `near_exterior`/`PROBE_NEAR_RADIUS` do: it only bounds WHICH exterior
    birds are worth spending probe budget on, and is evaluation-side
    infrastructure, never exposed to the predictive/lineage/thingness
    inference code."""
    member_set = set(int(m) for m in I)
    from geometry_611 import torus_delta
    non_members = np.array([i for i in range(len(r_t)) if i not in member_set])
    if len(non_members) == 0:
        return []
    d = torus_delta(r_t[I][:, None, :], r_t[non_members][None, :, :], mf.L)
    D = np.sqrt((d ** 2).sum(-1))
    near = (D <= radius_factor * mf.R).any(axis=0)
    return sorted(int(x) for x in non_members[near])
