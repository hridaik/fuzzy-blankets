"""Part L: apply the frozen V2 policy, unmodified, to the first 10
independently emergent qualifying flocks (seeds 0..N in numeric order), and
compare the four actuator-selection rules head to head. Nothing here is
tuned in response to any result produced by this script.
"""
from __future__ import annotations

import math
import time

import numpy as np

from common_v2 import ROOT, V2_DIR, dump_json, find_flock, dynamical_shell, evaluate_arm, N_REP
from selection_rules import rule_A_degree, rule_B_leverage, rule_C_patch, rule_D_random

N_FLOCKS_TARGET = 10
FRACTION = 0.75
MAX_SEED_SCAN = 60  # scan seeds 0..59 to find 10 qualifying flocks


def main():
    t_start = time.time()
    flocks = []
    seed = 0
    while len(flocks) < N_FLOCKS_TARGET and seed < MAX_SEED_SCAN:
        fl = find_flock(seed)
        if fl is not None:
            flocks.append(fl)
            print(f"seed {seed}: QUALIFIES t0={fl['t0']} |I0|={len(fl['I0'])} h0={fl['h0']} "
                  f"eigengap={fl['eigengap']:.2f}  ({time.time()-t_start:.1f}s elapsed)")
        else:
            print(f"seed {seed}: does not qualify")
        seed += 1
    print(f"\nFound {len(flocks)} qualifying flocks from seeds 0..{seed-1}")

    all_results = []
    for fl in flocks:
        lattice = fl["lattice"]
        I0, z_t0, h_star = fl["I0"], fl["z_t0"], fl["h_star"]
        B_D0 = dynamical_shell(lattice, I0)
        k = max(1, math.ceil(FRACTION * len(B_D0)))
        rng = np.random.default_rng(1000 + fl["seed"])

        actuator_sets = {}
        if len(B_D0) == 0:
            print(f"seed {fl['seed']}: B^D_0 is EMPTY (I0 has no exterior lattice neighbors) -- skipping rules")
            all_results.append(dict(seed=fl["seed"], t0=fl["t0"], size_I0=len(I0), size_B_D0=0,
                                     k=0, note="B^D_0 empty; no control arms evaluable"))
            continue

        actuator_sets["A_degree"] = rule_A_degree(B_D0, I0, lattice, k)
        actuator_sets["B_leverage"] = rule_B_leverage(B_D0, I0, h_star, z_t0, lattice, k,
                                                       seed_offset=400_000 + 1000 * fl["seed"])
        actuator_sets["C_patch"] = rule_C_patch(B_D0, I0, lattice, k)
        actuator_sets["D_random"] = rule_D_random(B_D0, k, rng)
        actuator_sets["reference_full_shell"] = B_D0.tolist()
        actuator_sets["reference_baseline"] = []

        flock_out = dict(seed=fl["seed"], t0=fl["t0"], h0=fl["h0"], size_I0=len(I0),
                          size_B_D0=len(B_D0), k=k, eigengap=fl["eigengap"], rules={})
        for rule_name, actuators in actuator_sets.items():
            m = evaluate_arm(actuators, z_t0, I0, h_star, lattice, n_replicates=N_REP,
                              seed_offset=300_000 + 1000 * fl["seed"])
            m["actuators"] = actuators
            flock_out["rules"][rule_name] = m
            print(f"  seed {fl['seed']} {rule_name:22s} k={len(actuators):2d} "
                  f"mean_Hstar_end={m['mean_Hstar_end']:.3f} p_success={m['p_success']:.3f} "
                  f"p_succ&integrity(full)={m['p_success_and_integrity_full']:.3f} "
                  f"p_succ&integrity(recovery)={m['p_success_and_integrity_recovery']:.3f}"
                  f"  ({time.time()-t_start:.1f}s elapsed)")
        all_results.append(flock_out)

    dump_json(dict(fraction=FRACTION, n_replicates=N_REP, n_flocks=len(flocks), flocks=all_results),
               V2_DIR / "data" / "replication_results.json")

    # summary across flocks
    print("\n=== Summary across flocks ===")
    for rule_name in ["A_degree", "B_leverage", "C_patch", "D_random", "reference_full_shell"]:
        succ = [f["rules"][rule_name]["p_success"] for f in all_results if "rules" in f and rule_name in f["rules"]]
        if succ:
            print(f"{rule_name:22s}: mean P(success) across {len(succ)} flocks = {np.mean(succ):.3f}  "
                  f"(per-flock: {[round(s,2) for s in succ]})")


if __name__ == "__main__":
    main()
