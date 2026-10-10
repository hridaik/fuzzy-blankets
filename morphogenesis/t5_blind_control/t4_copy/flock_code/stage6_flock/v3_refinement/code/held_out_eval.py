"""Part 1E: the ONLY script in this refinement that touches held-out flocks.
Applies the frozen V3 criterion (q=2 multicover, gamma=0.5, from
PROTOCOL_V3.md) and, for comparison, V2's frozen f_A=0.75-of-shell fraction,
unmodified, to 6 flocks never inspected during Part 1's threshold search.
"""
from __future__ import annotations

import math
import time

import numpy as np

from common_v3 import V3_DIR, dump_json, dynamical_shell, find_held_out_flocks, V3_SEED_OFFSET
from selection_rules_v3 import min_actuators_for_multicover, q_coverage_fraction, rule_DEG_degree
from evaluate_v3 import evaluate_arm_v3

FROZEN_Q = 2
FROZEN_GAMMA = 0.5
V2_FRACTION = 0.75
N_REP = 30
SEED_BASE = V3_SEED_OFFSET + 1_000_000


def main():
    t_start = time.time()
    flocks = find_held_out_flocks()
    print(f"Held-out flocks: seeds {[fl['seed'] for fl in flocks]}")

    rows = []
    for fl in flocks:
        seed, lattice, I0, z_t0, h_star = fl["seed"], fl["lattice"], fl["I0"], fl["z_t0"], fl["h_star"]
        B_D0 = dynamical_shell(lattice, I0)
        if len(B_D0) == 0:
            print(f"seed {seed}: B^D_0 empty -- skipping")
            continue
        struct_cache: dict = {}

        A_v3 = min_actuators_for_multicover(B_D0, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA)
        m_v3 = evaluate_arm_v3(A_v3, I0, B_D0, z_t0, h_star, lattice, n_replicates=N_REP,
                                seed_offset=SEED_BASE + 1000 * seed, _struct_cache=struct_cache)
        m_v3["seed"] = seed
        m_v3["condition"] = f"V3_frozen_q{FROZEN_Q}_gamma{FROZEN_GAMMA}"
        m_v3["gamma_achieved"] = q_coverage_fraction(A_v3, I0, lattice, FROZEN_Q)

        k_v2 = max(1, math.ceil(V2_FRACTION * len(B_D0)))
        A_v2 = rule_DEG_degree(B_D0, I0, lattice, k_v2)
        m_v2 = evaluate_arm_v3(A_v2, I0, B_D0, z_t0, h_star, lattice, n_replicates=N_REP,
                                seed_offset=SEED_BASE + 1000 * seed, _struct_cache=struct_cache)
        m_v2["seed"] = seed
        m_v2["condition"] = "V2_frozen_f_A_0.75_DEG"

        rows.append(dict(seed=seed, size_I0=len(I0), size_B_D0=len(B_D0), t0=fl["t0"],
                          eigengap=fl["eigengap"], v3=m_v3, v2=m_v2))
        print(f"seed {seed}: |I0|={len(I0)} |B^D_0|={len(B_D0)}  "
              f"V3(k={m_v3['n_actuators']},Gamma={m_v3['gamma_achieved']:.2f}) p_success={m_v3['p_success']:.3f}  "
              f"V2(k={k_v2}) p_success={m_v2['p_success']:.3f}  ({time.time()-t_start:.1f}s elapsed)")

    v3_succ = [r["v3"]["p_success"] for r in rows]
    v2_succ = [r["v2"]["p_success"] for r in rows]
    v3_k = [r["v3"]["n_actuators"] for r in rows]
    v2_k = [r["v2"]["n_actuators"] for r in rows]
    v3_pers = [r["v3"]["mean_Hstar_release"] for r in rows]
    v2_pers = [r["v2"]["mean_Hstar_release"] for r in rows]

    summary = dict(
        frozen_q=FROZEN_Q, frozen_gamma=FROZEN_GAMMA, v2_reference_fraction=V2_FRACTION,
        n_held_out_flocks=len(rows),
        v3_mean_p_success=float(np.mean(v3_succ)), v2_mean_p_success=float(np.mean(v2_succ)),
        v3_mean_k=float(np.mean(v3_k)), v2_mean_k=float(np.mean(v2_k)),
        v3_mean_Hstar_release=float(np.mean(v3_pers)), v2_mean_Hstar_release=float(np.mean(v2_pers)),
        rows=rows,
    )
    dump_json(summary, V3_DIR / "data" / "held_out_eval.json")
    print(f"\n=== Held-out generalization ({len(rows)} flocks) ===")
    print(f"V3 (q=2,gamma=0.5): mean p_success={np.mean(v3_succ):.3f}  mean k={np.mean(v3_k):.1f}  "
          f"mean H*_release={np.mean(v3_pers):.3f}")
    print(f"V2 (f_A=0.75, DEG): mean p_success={np.mean(v2_succ):.3f}  mean k={np.mean(v2_k):.1f}  "
          f"mean H*_release={np.mean(v2_pers):.3f}")
    print(f"\nDone in {time.time()-t_start:.1f}s. Wrote data/held_out_eval.json")


if __name__ == "__main__":
    main()
