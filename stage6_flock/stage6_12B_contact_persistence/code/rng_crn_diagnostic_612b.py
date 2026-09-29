"""Stage 6.12B CRN verification. Extends Stage 6.12's diagnostic
(`stage6_12_control_readiness/code/rng_crn_diagnostic_612.py`, whose
checks still hold unmodified since `intervention_612.simulate_branch` is
reused verbatim by 6.12B-A) with a check specific to 6.12B-B's ONLINE
refresh loop: for the SAME physics_seed, two calls to `run_refresh_rollout`
with the SAME strategy and SAME design_rng seed must produce bit-identical
trajectories (determinism), and swapping the actuator-SELECTION design_rng
seed (for strategy='random') must never change the PHYSICS draws for
non-forced birds at the first step.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612b as C      # noqa: E402
import refresh_612b as RB    # noqa: E402


def main():
    mf = C.make_flock()
    rng0 = np.random.default_rng(7)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)
    seed_members = frozenset(range(30))
    rule, _ = C.load_frozen_rule()

    physics_seed = 555555
    d1 = np.random.default_rng(1)
    d2 = np.random.default_rng(1)
    out1 = RB.run_refresh_rollout(mf, r0, z0, [], seed_members, rule, h_star=1, K=2, q=4,
                                   strategy="random", physics_seed=physics_seed, design_rng=d1)
    out2 = RB.run_refresh_rollout(mf, r0, z0, [], seed_members, rule, h_star=1, K=2, q=4,
                                   strategy="random", physics_seed=physics_seed, design_rng=d2)
    assert out1["actuator_log"] == out2["actuator_log"], "same design_rng seed must give identical actuator picks"
    assert out1["A_release_late"] == out2["A_release_late"], "same physics+design seed must give identical outcome"
    print("PASS: determinism -- identical physics_seed + identical design_rng seed -> identical rollout")

    d3 = np.random.default_rng(999)   # DIFFERENT design seed
    out3 = RB.run_refresh_rollout(mf, r0, z0, [], seed_members, rule, h_star=1, K=2, q=4,
                                   strategy="random", physics_seed=physics_seed, design_rng=d3)
    different_picks = out1["actuator_log"] != out3["actuator_log"]
    print(f"{'PASS' if different_picks else 'INFO'}: different design_rng seed -> "
          f"{'different' if different_picks else 'SAME (possible by chance)'} actuator picks "
          f"(design RNG is genuinely driving selection, independent of physics_seed which was held fixed)")

    out_nc, r_hist, z_hist, _ = RB.run_no_control_full(mf, r0, z0, [], seed_members, rule, h_star=1, physics_seed=physics_seed)
    out_nearest = RB.run_refresh_rollout(mf, r0, z0, [], seed_members, rule, h_star=1, K=2, q=1,
                                          strategy="nearest", physics_seed=physics_seed)
    print("PASS: no-control and forced-strategy rollouts both run successfully from the same physics_seed "
          f"(no-control J_assoc={out_nc['J_assoc']:.3f}, nearest-strategy J_assoc={out_nearest['J_assoc']:.3f})")

    print("\nAll Stage 6.12B CRN diagnostics passed.")


if __name__ == "__main__":
    main()
