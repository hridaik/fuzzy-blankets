"""Part 1B: coverage sweep. For each of the 10 development flocks (V2's
frozen seeds, reused honestly -- see REFINEMENT_PLAN.md), sweep actuator
fraction f_A in {0.1,...,1.0} x 5 rules (R, DEG, LEV, COVER, PATCH),
20 replicates/condition, common random numbers within each flock (same
convention as V2's replicate.py). Records both Part 1A's structural
quantities and the simulated outcome for every condition. Nothing here is
tuned in response to any result it produces.
"""
from __future__ import annotations

import math
import time

import numpy as np

from common_v3 import (
    V3_DIR, dump_json, load_dev_flocks, dynamical_shell, V3_SEED_OFFSET,
)
from selection_rules_v3 import (
    rule_R_random, rule_DEG_degree, rule_LEV_leverage, rule_COVER_greedy, rule_PATCH_patch,
)
from evaluate_v3 import evaluate_arm_v3

FRACTIONS = [round(0.1 * i, 1) for i in range(1, 11)]  # 0.1..1.0
N_REP = 20
RULES = ["R_random", "DEG_degree", "LEV_leverage", "COVER_greedy", "PATCH_patch"]


def k_of_fraction(f: float, n_shell: int) -> int:
    return int(np.clip(round(f * n_shell), 1, n_shell))


def build_actuators(rule: str, f: float, B_D0, I0, h_star, z_t0, lattice, k: int,
                     lev_ranking: list[int], rng: np.random.Generator) -> list[int]:
    if rule == "R_random":
        return rule_R_random(B_D0, k, rng)
    if rule == "DEG_degree":
        return rule_DEG_degree(B_D0, I0, lattice, k)
    if rule == "LEV_leverage":
        return lev_ranking[:k]
    if rule == "COVER_greedy":
        return rule_COVER_greedy(B_D0, I0, lattice, k)
    if rule == "PATCH_patch":
        return rule_PATCH_patch(B_D0, I0, lattice, k)
    raise ValueError(rule)


def main():
    t_start = time.time()
    flocks = load_dev_flocks()
    print(f"Loaded {len(flocks)} dev flocks: seeds {[f['seed'] for f in flocks]}")

    all_results = []
    for fl in flocks:
        seed, lattice, I0, z_t0, h_star = fl["seed"], fl["lattice"], fl["I0"], fl["z_t0"], fl["h_star"]
        B_D0 = dynamical_shell(lattice, I0)
        if len(B_D0) == 0:
            print(f"seed {seed}: B^D_0 empty -- skipping")
            continue

        # LEV ranking computed once per flock at full shell (Part 1B spec),
        # reusing the exact per-bird sweep procedure from selection_rules.rule_B_leverage.
        lev_full = rule_LEV_leverage(B_D0, I0, h_star, z_t0, lattice, k=len(B_D0),
                                      n_replicates=20, seed_offset=400_000 + 1000 * seed)

        rng = np.random.default_rng(2_000_000 + seed)
        struct_cache: dict = {}
        flock_out = dict(seed=seed, t0=fl["t0"], h0=fl["h0"], size_I0=len(I0), size_B_D0=len(B_D0),
                          eigengap=fl["eigengap"], conditions=[])

        for f in FRACTIONS:
            k = k_of_fraction(f, len(B_D0))
            for rule in RULES:
                actuators = build_actuators(rule, f, B_D0, I0, h_star, z_t0, lattice, k, lev_full, rng)
                seed_offset = V3_SEED_OFFSET + 1000 * seed  # common random numbers within this flock
                m = evaluate_arm_v3(actuators, I0, B_D0, z_t0, h_star, lattice,
                                     n_replicates=N_REP, seed_offset=seed_offset, _struct_cache=struct_cache)
                m["rule"] = rule
                m["f_A_target"] = f
                m["k"] = k
                flock_out["conditions"].append(m)
            row = flock_out["conditions"][-len(RULES):]
            summary = ", ".join(f"{c['rule'].split('_')[0]}:{c['p_success']:.2f}" for c in row)
            print(f"  seed {seed} f_A={f:.1f} k={k}  [{summary}]  ({time.time()-t_start:.1f}s elapsed)")
        all_results.append(flock_out)

    dump_json(dict(fractions=FRACTIONS, rules=RULES, n_replicates=N_REP, n_flocks=len(all_results),
                    flocks=all_results),
              V3_DIR / "data" / "coverage_sweep.json")
    print(f"\nDone in {time.time()-t_start:.1f}s. Wrote data/coverage_sweep.json")


if __name__ == "__main__":
    main()
