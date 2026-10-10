"""Stage 6.11B item 6: unit tests proving planning (the imagined `held_rollout`
used to estimate authority) and real execution (the actual controller loop
holding a forced actuator set for d consecutive real steps) apply IDENTICAL
intervention semantics -- same forced_actions dict, same steps, same RNG
draw order -- so the estimand and the executed intervention are provably the
same operation, not merely similarly-described ones.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))
import common_611  # noqa: E402,F401

from common_611 import resolved_params, BETA_610, S_610, N_BIRDS, L_BOX, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY  # noqa: E402
from moving_flock_611 import MovingFlock611  # noqa: E402
from authority_v2_611 import held_rollout  # noqa: E402


def make_flock():
    pm = resolved_params(BETA_610, S_610)
    return MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=V_PRIMARY, params=pm,
                            social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)


def real_execution(mf, r_t, z_t, S, h_star, n_steps, seed):
    """What an actual controller loop does: hold S forced to h_star for
    EVERY real step of a `n_steps`-step block (mirrors
    run_online_control_611.run_episode's `forced = {j: target_heading for j
    in B_C_cache['B_C']}` recomputed and applied every iteration while the
    same actuator set is in force)."""
    r, z = r_t.copy(), z_t.copy()
    rng = np.random.default_rng(seed)
    for _ in range(n_steps):
        forced = {int(j): int(h_star) for j in S}
        r, z, _ = mf.step(r, z, rng, forced_actions=forced)
    return z


def test_held_rollout_matches_real_held_execution_d_equals_tau():
    """d == tau: the imagined rollout holds for the WHOLE horizon, exactly
    matching a real execution block of the same length -- must be bit-for-
    bit identical given the same seed."""
    mf = make_flock()
    rng0 = np.random.default_rng(0)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)
    S = [3, 17, 42]
    h_star = 1
    tau = 4
    z_plan = held_rollout(mf, r0, z0, S, h_star, tau=tau, d=tau, seed=12345)
    z_real = real_execution(mf, r0, z0, S, h_star, n_steps=tau, seed=12345)
    assert np.array_equal(z_plan, z_real), "planning (d=tau) must reproduce real held execution exactly"


def test_held_rollout_matches_real_partial_hold_then_release():
    """d < tau: the imagined rollout holds for d steps then releases,
    exactly matching a real execution that holds for d steps then stops
    forcing (e.g. a refresh boundary) while the world keeps running to tau."""
    mf = make_flock()
    rng0 = np.random.default_rng(1)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)
    S = [5, 9]
    h_star = 2
    tau, d = 6, 3

    def real_partial(seed):
        r, z = r0.copy(), z0.copy()
        rng = np.random.default_rng(seed)
        for step in range(tau):
            forced = {int(j): int(h_star) for j in S} if step < d else None
            r, z, _ = mf.step(r, z, rng, forced_actions=forced)
        return z

    z_plan = held_rollout(mf, r0, z0, S, h_star, tau=tau, d=d, seed=777)
    z_real = real_partial(777)
    assert np.array_equal(z_plan, z_real)


def test_old_semantics_reproduced_as_d_equals_1():
    """d=1 (the OLD MultiStepAuthorityProbe behaviour: forced only at
    step==0) must be bit-identical to the original module's own rollout,
    confirming this generalization is a strict superset, not a silent
    behaviour change at the old default."""
    from intervention_api_611 import MultiStepAuthorityProbe

    mf = make_flock()
    rng0 = np.random.default_rng(2)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)
    j, h_star, tau = 11, 3, 4

    old_probe = MultiStepAuthorityProbe(mf, r0, z0, tau=tau, n_rollouts=1, seed=0)
    z_old = old_probe._rollout({j: h_star}, seed=(0, j, h_star, 0))
    z_new = held_rollout(mf, r0, z0, [j], h_star, tau=tau, d=1, seed=(0, j, h_star, 0))
    assert np.array_equal(z_old, z_new)


def test_baseline_rollout_matches_unforced_real_execution():
    """The baseline arm (no forcing) must exactly match an ordinary,
    un-actuated real trajectory over the same horizon and seed."""
    mf = make_flock()
    rng0 = np.random.default_rng(3)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)
    tau = 5

    def real_unforced(seed):
        r, z = r0.copy(), z0.copy()
        rng = np.random.default_rng(seed)
        for _ in range(tau):
            r, z, _ = mf.step(r, z, rng, forced_actions=None)
        return z

    z_plan = held_rollout(mf, r0, z0, [], 0, tau=tau, d=0, seed=555)
    z_real = real_unforced(555)
    assert np.array_equal(z_plan, z_real)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
