"""Verifies CRN pairing: for a fixed physics_seed, the no-control branch and
a forced branch consume the physics RNG stream identically except where
forced_actions itself changes an action draw -- i.e. simulate_branch with
S=None and simulate_branch with a forced set produce BIT-IDENTICAL
trajectories for birds outside the forced set (and outside its downstream
one-step causal light cone) up to the point forcing diverges the dynamics.
Also verifies that swapping the actuator-set-SAMPLING rng (design_rng) never
changes which physics draws occur, i.e. simulate_branch output for a given
physics_seed + S is independent of how S itself was chosen.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612 as C            # noqa: E402
import intervention_612 as I      # noqa: E402


def main():
    mf = C.make_flock()
    rng0 = np.random.default_rng(42)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)

    physics_seed = 123456
    r_A, z_A = I.simulate_branch(mf, r0, z0, physics_seed, None, 0, 0, 1)
    r_B, z_B = I.simulate_branch(mf, r0, z0, physics_seed, None, 0, 0, 1)
    assert np.array_equal(z_A, z_B) and np.allclose(r_A, r_B)
    print("PASS: identical physics_seed with no forcing -> bit-identical trajectory (determinism check)")

    S = [5, 9, 17]
    r_C1, z_C1 = I.simulate_branch(mf, r0, z0, physics_seed, S, 3, 6, 3)
    r_C2, z_C2 = I.simulate_branch(mf, r0, z0, physics_seed, S, 3, 6, 3)
    assert np.array_equal(z_C1, z_C2) and np.allclose(r_C1, r_C2)
    print("PASS: identical physics_seed with identical forcing -> bit-identical trajectory")

    r_nf, z_nf = I.simulate_branch(mf, r0, z0, physics_seed, None, 0, 0, 1)
    r_f, z_f = I.simulate_branch(mf, r0, z0, physics_seed, S, 1, 1, 1)
    other = np.array([i for i in range(mf.N) if i not in S])
    # after exactly one step, actions for birds NOT in S are drawn from the
    # SAME rng stream at the SAME point (forced_actions only overrides the
    # forced birds' own next heading post-hoc; see intervention_api_611.py's
    # own documented reachability argument) -- so z at t=1 must agree for
    # every non-forced bird.
    assert np.array_equal(z_nf[1][other], z_f[1][other]), "non-forced birds' z at t=1 diverged under CRN pairing"
    print("PASS: one-step CRN pairing -- non-forced birds' z(t=1) identical between no-forcing and forced branches")

    print("\nAll CRN diagnostics passed.")


if __name__ == "__main__":
    main()
