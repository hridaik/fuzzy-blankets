"""Stage 6.12B-A: EXHAUSTIVE fixed-actuator-set benchmark.

K=1: all C(20,1)=20 singleton sets from the primary nearest-20 exterior
pool. K=2: all C(20,2)=190 pairs. d in {4,8}. No beam search, no
"best-found" ambiguity for the searched sets themselves -- every set in
the grid is evaluated.

DISCLOSED REDUCTION (frozen before any Stage 6.12B result; priority order
per the task brief S27 -- preserve exhaustive coverage first, then holdout
streams for finalists, then development-stream depth last):
  - N_DEV_STREAMS = 1 per set (nominal: >=8). Exhaustive coverage (210
    sets x 2 durations = 420 set-budget combos) is preserved in full;
    development-stream DEPTH is what is cut, per the stated priority.
  - N_HOLDOUT_STREAMS = 4 per finalist (nominal: >=24), applied only to a
    small finalist set (S_star, median-dev, worst-dev, 5 fresh random
    comparators per K,d cell = 8 finalists x 4 K,d cells = 32 finalist
    sets total per state).
  - EXHAUSTIVE SEARCH ITSELF RUNS ON ONLY 3 OF THE 5 SAMPLED STATES
    (2 development: s612b_00, s612b_01; 1 holdout: s612b_03) -- a further
    state-count reduction beyond STATE_SAMPLING, disclosed here because
    exhaustive search is the dominant compute cost (~39 min/state
    measured). All 5 states remain available for Stage 6.12B-B (much
    cheaper per state) and are listed in `data/state_manifest_612b.json`.

Development/holdout SEPARATION is by PHYSICS STREAM within each state
(matching Stage 6.12's Phase B/C precedent), not by state identity here --
S_star is necessarily state-specific (it names literal bird IDs).
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612b as C            # noqa: E402
import intervention_612b as IB     # noqa: E402

K_GRID = (1, 2)
D_GRID = (4, 8)
N_DEV_STREAMS = 1
N_HOLDOUT_STREAMS = 4
N_RANDOM_COMPARATORS = 5

EXHAUSTIVE_STATE_IDS = ("s612b_00_seed62200", "s612b_01_seed62201", "s612b_03_seed62203")

DEV_PHYSICS_SEED_BASE = 10_000_000
HOLDOUT_PHYSICS_SEED_BASE = 11_000_000
COMPARATOR_DESIGN_SEED_BASE = 12_000_000


def all_sets(pool, K):
    pool = sorted(int(x) for x in pool)
    return [list(c) for c in itertools.combinations(pool, K)]


def run_state(state, state_idx):
    rule, _ = C.load_frozen_rule()
    mf = C.make_flock()
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(state["interior0"]); h_star = state["h_star"]
    pool = state["pool20"]
    z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]

    # no-control on dev + holdout streams (shared across all K,d via slicing)
    dev_streams = list(range(N_DEV_STREAMS))
    holdout_streams = list(range(N_HOLDOUT_STREAMS))
    no_control_dev = {r: IB.run_no_control_full_b(mf, r0, z0, z_context, seed_members, rule, h_star,
                                                   DEV_PHYSICS_SEED_BASE + state_idx * 1000 + r, D_GRID)[0]
                       for r in dev_streams}
    no_control_holdout = {r: IB.run_no_control_full_b(mf, r0, z0, z_context, seed_members, rule, h_star,
                                                        HOLDOUT_PHYSICS_SEED_BASE + state_idx * 1000 + r, D_GRID)[0]
                           for r in holdout_streams}

    results = {}
    for K in K_GRID:
        sets = all_sets(pool, K)
        for d in D_GRID:
            cell_key = f"K{K}_d{d}"
            t0 = time.time()
            search_rows = []
            for si, S in enumerate(sets):
                vals_assoc, vals_cons = [], []
                for r in dev_streams:
                    physics_seed = DEV_PHYSICS_SEED_BASE + state_idx * 1000 + r
                    out = IB.run_one_b(mf, r0, z0, z_context, seed_members, rule, h_star, S, d, physics_seed)
                    j0 = no_control_dev[r][d]
                    vals_assoc.append(out["J_assoc"] - j0["J_assoc"])
                    vals_cons.append(out["J_conservative"] - j0["J_conservative"])
                search_rows.append(dict(set_idx=si, S=S, mean_delta_assoc=float(np.mean(vals_assoc)),
                                         mean_delta_conservative=float(np.mean(vals_cons))))
            dt_search = time.time() - t0

            ranked = sorted(search_rows, key=lambda r: r["mean_delta_assoc"])
            best = ranked[-1]
            worst = ranked[0]
            median = ranked[len(ranked) // 2]
            by_idx = {r["set_idx"]: r for r in search_rows}
            design_rng = np.random.default_rng(COMPARATOR_DESIGN_SEED_BASE + state_idx * 100 + K * 10 + d)
            comparator_idx = design_rng.choice(len(sets), size=min(N_RANDOM_COMPARATORS, len(sets)), replace=False)
            comparators = [dict(**by_idx[int(i)], role="random_comparator") for i in comparator_idx]
            finalists = [dict(**best, role="S_star")] + [dict(**median, role="median_dev")] + \
                        [dict(**worst, role="worst_dev")] + comparators

            t1 = time.time()
            holdout_evals = []
            for f in finalists:
                S = f["S"]
                va, vc, vraw, vcraw = [], [], [], []
                for r in holdout_streams:
                    physics_seed = HOLDOUT_PHYSICS_SEED_BASE + state_idx * 1000 + r
                    out = IB.run_one_b(mf, r0, z0, z_context, seed_members, rule, h_star, S, d, physics_seed)
                    j0 = no_control_holdout[r][d]
                    va.append(out["J_assoc"] - j0["J_assoc"]); vc.append(out["J_conservative"] - j0["J_conservative"])
                    vraw.append(out["J_assoc"]); vcraw.append(out["J_conservative"])
                holdout_evals.append(dict(role=f["role"], S=S, set_idx=f["set_idx"],
                                           dev_mean_delta_assoc=f["mean_delta_assoc"],
                                           holdout_mean_delta_assoc=float(np.mean(va)),
                                           holdout_mean_delta_conservative=float(np.mean(vc)),
                                           holdout_mean_J_assoc=float(np.mean(vraw)),
                                           holdout_mean_J_conservative=float(np.mean(vcraw))))
            dt_holdout = time.time() - t1

            random_holdout = [h for h in holdout_evals if h["role"] == "random_comparator"]
            s_star_h = next(h for h in holdout_evals if h["role"] == "S_star")
            G_sel = (s_star_h["holdout_mean_delta_assoc"] -
                     float(np.median([h["holdout_mean_delta_assoc"] for h in random_holdout]))) if random_holdout else None

            results[cell_key] = dict(
                K=K, d=d, n_sets=len(sets), search_rows=search_rows,
                dev_deltas_assoc=[r["mean_delta_assoc"] for r in search_rows],
                dev_deltas_conservative=[r["mean_delta_conservative"] for r in search_rows],
                best=best, median=median, worst=worst, finalists=finalists,
                holdout_evals=holdout_evals, G_sel=G_sel,
                between_set_var_dev=float(np.var([r["mean_delta_assoc"] for r in search_rows], ddof=1)),
                search_time_s=dt_search, holdout_time_s=dt_holdout,
            )
            print(f"  {state['state_id']} {cell_key}: search {dt_search:.0f}s, holdout {dt_holdout:.0f}s, "
                  f"best_dev_delta={best['mean_delta_assoc']:.4f}, G_sel={G_sel}", flush=True)

    return dict(state_id=state["state_id"], role=state["role"], K_grid=list(K_GRID), d_grid=list(D_GRID),
                n_dev_streams=N_DEV_STREAMS, n_holdout_streams=N_HOLDOUT_STREAMS,
                cells=results)


def main():
    manifest = json.load(open(C.DATA_DIR / "state_manifest_612b.json"))
    states = manifest["states"]
    id_to_idx = {s["state_id"]: i for i, s in enumerate(states)}
    out = []
    t_all = time.time()
    for sid in EXHAUSTIVE_STATE_IDS:
        idx = id_to_idx[sid]
        s = states[idx]
        t0 = time.time()
        res = run_state(s, idx)
        dt = time.time() - t0
        print(f"[{sid}] done in {dt:.1f}s", flush=True)
        out.append(res)
        json.dump(out, open(C.DATA_DIR / "fixed_set_exhaustive_612b.json", "w"), indent=1, default=str)
    print(f"Stage 6.12B-A total wall time: {time.time()-t_all:.1f}s")


if __name__ == "__main__":
    main()
