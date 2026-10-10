"""Stage 6.12 Phase B (best-found actuator-set search on DEVELOPMENT physics
streams) + Phase C (frozen S_star evaluated on FRESH holdout physics
streams, against a fresh matched random-set sample on the SAME streams).

FROZEN PRIMARY SEARCH BUDGET (task brief S14: "freeze the selection rule and
chosen budgets before running holdout simulations" -- chosen here BEFORE any
Stage 6.12 intervention result existed, not selected post hoc from Phase A):
    K = 4, d = 8   (a mid-grid budget; K=4 is large enough that exhaustive
    enumeration is explicitly not required per S13, and d=8 sits in the
    middle of the duration grid so the result speaks to neither the
    shortest nor the longest tested forcing window).

This is run identically on EVERY state (development and holdout) -- the
budget choice does not depend on any state's Phase A outcome, so running it
on holdout states does not constitute "searching the holdout set for a
favorable budget" (task brief S14's prohibition).

DISCLOSED REDUCTION: search_budget=15 sampled K=4 subsets (of C(20,4)=4845)
evaluated on N_SEARCH_STREAMS=2 development-only physics streams; the
argmax-mean set is frozen as S_star and evaluated, alongside a FRESH sample
of N_HOLDOUT_COMPARATORS=6 random sets, on N_HOLDOUT_STREAMS=5 streams never
used during search (RNG ranges disjoint from Phase A and from the search
step; see RNG_PROTOCOL.md).
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
from run_phaseA_612 import sample_random_sets, DESIGN_SEED_BASE  # noqa: E402

K_STAR, D_STAR = 4, 8
SEARCH_BUDGET = 15
N_SEARCH_STREAMS = 2
N_HOLDOUT_COMPARATORS = 6
N_HOLDOUT_STREAMS = 5

SEARCH_DESIGN_SEED_BASE = 5_500_000     # distinct from Phase A's DESIGN_SEED_BASE
SEARCH_PHYSICS_SEED_BASE = 7_000_000    # distinct from Phase A's PHYSICS_SEED_BASE
HOLDOUT_DESIGN_SEED_BASE = 5_600_000
HOLDOUT_PHYSICS_SEED_BASE = 8_000_000   # distinct range: never used in Phase A or search


def run_state(state):
    rule, _ = C.load_frozen_rule()
    mf = C.make_flock()
    r0 = np.array(state["r0"])
    z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(state["interior0"])
    h_star = state["h_star"]
    pool = state["pool20"]
    z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]
    state_idx = state["_idx"]

    if len(pool) < K_STAR:
        return dict(state_id=state["state_id"], role=state["role"], unavailable=True,
                    reason=f"pool size {len(pool)} < K_STAR={K_STAR}")

    # --- Phase B: search on DEVELOPMENT streams -----------------------
    search_design_rng = np.random.default_rng(SEARCH_DESIGN_SEED_BASE + state_idx)
    search_sets = sample_random_sets(pool, K_STAR, SEARCH_BUDGET, search_design_rng)
    search_evals = []
    for si, S in enumerate(search_sets):
        vals = []
        for r in range(N_SEARCH_STREAMS):
            physics_seed = SEARCH_PHYSICS_SEED_BASE + state_idx * 100 + r
            out = I.run_one(mf, r0, z0, z_context, seed_members, rule, h_star, S, D_STAR,
                             physics_seed, with_mechanism=False)
            vals.append(out["J"])
        search_evals.append(dict(set_idx=si, S=S, mean_J=float(np.mean(vals)), vals=vals))
    best = max(search_evals, key=lambda e: e["mean_J"])
    S_star = best["S"]

    # no-control on the SAME development streams (for reference, not for the holdout comparison)
    dev_no_control = []
    for r in range(N_SEARCH_STREAMS):
        physics_seed = SEARCH_PHYSICS_SEED_BASE + state_idx * 100 + r
        oc = I.run_no_control_full(mf, r0, z0, z_context, seed_members, rule, h_star, physics_seed)
        dev_no_control.append(oc[D_STAR]["J"])

    # --- Phase C: FRESH holdout streams, S_star vs FRESH random comparators --
    holdout_design_rng = np.random.default_rng(HOLDOUT_DESIGN_SEED_BASE + state_idx)
    holdout_random_sets = sample_random_sets(pool, K_STAR, N_HOLDOUT_COMPARATORS, holdout_design_rng)

    def eval_set_holdout(S):
        vals, v_flags = [], []
        for r in range(N_HOLDOUT_STREAMS):
            physics_seed = HOLDOUT_PHYSICS_SEED_BASE + state_idx * 100 + r
            out = I.run_one(mf, r0, z0, z_context, seed_members, rule, h_star, S, D_STAR,
                             physics_seed, with_mechanism=False)
            vals.append(out["J"])
            v_flags.append(out["V"])
        return dict(S=S, mean_J=float(np.mean(vals)), median_J=float(np.median(vals)),
                    vals=vals, identity_valid_fraction=float(np.mean(v_flags)))

    holdout_S_star = eval_set_holdout(S_star)
    holdout_random = [eval_set_holdout(S) for S in holdout_random_sets]
    holdout_no_control = []
    for r in range(N_HOLDOUT_STREAMS):
        physics_seed = HOLDOUT_PHYSICS_SEED_BASE + state_idx * 100 + r
        oc = I.run_no_control_full(mf, r0, z0, z_context, seed_members, rule, h_star, physics_seed)
        holdout_no_control.append(oc[D_STAR]["J"])

    random_medians = [h["mean_J"] for h in holdout_random]
    G_sel = (holdout_S_star["mean_J"] - float(np.median(random_medians))) if random_medians else None

    return dict(
        state_id=state["state_id"], role=state["role"], unavailable=False,
        K=K_STAR, d=D_STAR, search_budget=SEARCH_BUDGET,
        search_evals=search_evals, S_star=S_star, S_star_dev_mean_J=best["mean_J"],
        dev_no_control_mean_J=float(np.mean(dev_no_control)),
        holdout_S_star=holdout_S_star, holdout_random=holdout_random,
        holdout_no_control_mean_J=float(np.mean(holdout_no_control)),
        holdout_random_median_of_means=float(np.median(random_medians)) if random_medians else None,
        G_sel=G_sel,
    )


def main():
    manifest = json.load(open(C.DATA_DIR / "state_manifest_612.json"))
    states = manifest["states"]
    for i, s in enumerate(states):
        s["_idx"] = i
    results = []
    t_all = time.time()
    for s in states:
        t0 = time.time()
        res = run_state(s)
        dt = time.time() - t0
        print(f"[{s['state_id']} / {s['role']}] done in {dt:.1f}s "
              f"G_sel={res.get('G_sel')}", flush=True)
        results.append(res)
        json.dump(results, open(C.DATA_DIR / "phaseBC_results_612.json", "w"), indent=1)
    print(f"Phase B/C total wall time: {time.time() - t_all:.1f}s")


if __name__ == "__main__":
    main()
