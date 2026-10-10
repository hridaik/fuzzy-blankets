"""Stage 6.12 S17: PRIMARY (position-only nearest-20, blind_pool_611.nearest_M_pool)
vs SECONDARY (physics-assisted true-R oracle, intervention_api_611.near_exterior)
pool sensitivity, at the frozen primary search budget (K=4, d=8), on a
PREDECLARED subset of the first 3 development states (s612_00..s612_02).
K, d, outcome definition, physics streams, and set/stream counts are matched
between pools; only the candidate pool differs. Reused N_SEARCH_STREAMS=2
scheme, small dedicated random-set sample (N_SETS_POOL=6) per pool -- a
disclosed reduction from a full best-found search, sufficient to answer
"does pool choice materially change the achievable G_sus / spread", not to
re-run the full selectivity pipeline twice.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612 as C            # noqa: E402
import intervention_612 as I      # noqa: E402
from run_phaseA_612 import sample_random_sets  # noqa: E402

K, D = 4, 8
N_SETS_POOL = 6
N_STREAMS = 3
DESIGN_SEED_BASE = 5_900_000
PHYSICS_SEED_BASE = 9_000_000
SUBSET_STATE_IDXS = (0, 1, 2)


def run_pool(mf, r0, z0, z_context, seed_members, rule, h_star, pool, state_idx, pool_name):
    design_rng = np.random.default_rng(DESIGN_SEED_BASE + state_idx + (0 if pool_name == "primary_nearest20" else 500))
    sets = sample_random_sets(pool, K, N_SETS_POOL, design_rng)
    no_control = []
    for r in range(N_STREAMS):
        physics_seed = PHYSICS_SEED_BASE + state_idx * 100 + r
        oc = I.run_no_control_full(mf, r0, z0, z_context, seed_members, rule, h_star, physics_seed)
        no_control.append(oc[D]["J"])
    set_means = []
    for S in sets:
        vals = []
        for r in range(N_STREAMS):
            physics_seed = PHYSICS_SEED_BASE + state_idx * 100 + r
            out = I.run_one(mf, r0, z0, z_context, seed_members, rule, h_star, S, D, physics_seed, with_mechanism=False)
            vals.append(out["J"] - no_control[r])
        set_means.append(float(np.mean(vals)))
    return dict(pool_name=pool_name, pool_size=len(pool), n_sets=len(sets),
                mean_delta=float(np.mean(set_means)) if set_means else None,
                between_set_var=float(np.var(set_means, ddof=1)) if len(set_means) > 1 else 0.0,
                set_means=set_means, mean_J0=float(np.mean(no_control)))


def main():
    rule, _ = C.load_frozen_rule()
    manifest = json.load(open(C.DATA_DIR / "state_manifest_612.json"))
    mf = C.make_flock()
    out = []
    for idx in SUBSET_STATE_IDXS:
        s = manifest["states"][idx]
        r0 = np.array(s["r0"]); z0 = np.array(s["z0"], dtype=int)
        seed_members = frozenset(s["interior0"]); h_star = s["h_star"]
        z_context = [np.array(zc, dtype=int) for zc in s["z_context"]]
        primary_pool = s["pool20"]
        oracle_pool = C.near_exterior(mf, r0, np.array(s["interior0"]), radius_factor=3.0)
        t0 = time.time()
        res_primary = run_pool(mf, r0, z0, z_context, seed_members, rule, h_star, primary_pool, idx, "primary_nearest20")
        res_oracle = run_pool(mf, r0, z0, z_context, seed_members, rule, h_star, oracle_pool, idx, "secondary_physics_assisted")
        dt = time.time() - t0
        print(f"[{s['state_id']}] primary mean_delta={res_primary['mean_delta']:.4f} "
              f"var={res_primary['between_set_var']:.5f} | oracle mean_delta={res_oracle['mean_delta']:.4f} "
              f"var={res_oracle['between_set_var']:.5f} oracle_pool_size={len(oracle_pool)} ({dt:.1f}s)", flush=True)
        out.append(dict(state_id=s["state_id"], primary=res_primary, oracle=res_oracle, oracle_pool_size=len(oracle_pool)))
        json.dump(out, open(C.DATA_DIR / "pool_sensitivity_612.json", "w"), indent=1)


if __name__ == "__main__":
    main()
