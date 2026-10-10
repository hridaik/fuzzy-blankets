"""Part 1D: minimal sufficient intervention interface. Formulate the
controller as min|A| s.t. a structural coverage requirement, using the
q-fold multicover generalization added in selection_rules_v3.py (motivated
by Part 1C's finding that mean multiplicity, not plain Gamma=frac(m_i>=1),
is the strongest univariate predictor of success -- so q=1 and q=2 are both
tested here as candidate structural criteria, on development flocks only,
BEFORE any held-out evaluation).
"""
from __future__ import annotations

import time

import numpy as np

from common_v3 import V3_DIR, dump_json, load_dev_flocks, dynamical_shell, V3_SEED_OFFSET
from selection_rules_v3 import min_actuators_for_multicover, q_coverage_fraction
from evaluate_v3 import evaluate_arm_v3

GAMMA_GRID = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
Q_VALUES = [1, 2]
N_REP = 20
SEED_BASE = V3_SEED_OFFSET + 500_000


def main():
    t_start = time.time()
    flocks = load_dev_flocks()
    print(f"Loaded {len(flocks)} dev flocks")

    results = {q: {g: [] for g in GAMMA_GRID} for q in Q_VALUES}
    for fl in flocks:
        seed, lattice, I0, z_t0, h_star = fl["seed"], fl["lattice"], fl["I0"], fl["z_t0"], fl["h_star"]
        B_D0 = dynamical_shell(lattice, I0)
        struct_cache: dict = {}
        for q in Q_VALUES:
            for gamma in GAMMA_GRID:
                A = min_actuators_for_multicover(B_D0, I0, lattice, q=q, gamma=gamma)
                achieved = q_coverage_fraction(A, I0, lattice, q)
                m = evaluate_arm_v3(A, I0, B_D0, z_t0, h_star, lattice, n_replicates=N_REP,
                                     seed_offset=SEED_BASE + 1000 * seed, _struct_cache=struct_cache)
                m["seed"] = seed
                m["q"] = q
                m["gamma_target"] = gamma
                m["gamma_achieved"] = achieved
                results[q][gamma].append(m)
        print(f"seed {seed} done ({time.time()-t_start:.1f}s elapsed)")

    summary = dict(q_values=Q_VALUES, gamma_grid=GAMMA_GRID, n_replicates=N_REP, per_q={})
    chosen = {}
    for q in Q_VALUES:
        rows = []
        for gamma in GAMMA_GRID:
            recs = results[q][gamma]
            mean_p = float(np.mean([r["p_success"] for r in recs]))
            mean_k = float(np.mean([r["n_actuators"] for r in recs]))
            mean_f = float(np.mean([r["f_A"] for r in recs]))
            rows.append(dict(gamma=gamma, mean_p_success=mean_p, mean_k=mean_k, mean_f_A=mean_f,
                              per_flock=[dict(seed=r["seed"], k=r["n_actuators"], f_A=r["f_A"],
                                               gamma_achieved=r["gamma_achieved"], p_success=r["p_success"],
                                               coh_traj=r["coh_traj"], Hstar_release_per_rep=r["Hstar_release_per_rep"])
                                         for r in recs]))
            print(f"q={q} gamma_target={gamma}: mean k={mean_k:.1f} mean f_A={mean_f:.3f} "
                  f"mean p_success={mean_p:.3f}")
        summary["per_q"][str(q)] = rows
        # smallest gamma at this q whose dev-mean p_success >= 0.8
        crossing = next((r["gamma"] for r in rows if r["mean_p_success"] >= 0.8), None)
        chosen[str(q)] = dict(
            frozen_gamma=crossing,
            mean_p_success_at_frozen_gamma=(next(r["mean_p_success"] for r in rows if r["gamma"] == crossing)
                                             if crossing is not None else None),
            mean_k_at_frozen_gamma=(next(r["mean_k"] for r in rows if r["gamma"] == crossing)
                                     if crossing is not None else None),
        )

    summary["chosen_thresholds"] = chosen
    dump_json(summary, V3_DIR / "data" / "minimal_interface.json")
    print("\n=== Candidate frozen thresholds (smallest gamma reaching dev-mean p_success>=0.8) ===")
    for q, c in chosen.items():
        print(f"q={q}: gamma={c['frozen_gamma']}  "
              f"mean_p_success={c['mean_p_success_at_frozen_gamma']}  mean_k={c['mean_k_at_frozen_gamma']}")
    print(f"\nDone in {time.time()-t_start:.1f}s. Wrote data/minimal_interface.json")


if __name__ == "__main__":
    main()
