"""Stage 6.12 Phase A: random-set generic-susceptibility + between-set
variance map, over the FULL frozen K x d grid, for every sampled state.

DISCLOSED REDUCTION (frozen before any result; see RNG_PROTOCOL.md /
READINESS_MAP.md): task-brief minimum is 32 unique random sets x 8 paired
physics streams per (state,K,d) cell. Measured per-step cost (~0.14s,
dominated by detect_69.propose) makes that infeasible in this session's
compute budget. This script uses N_SETS=3, N_STREAMS=2 per cell instead
(~2.3% of the nominal Monte Carlo budget). The K,d GRID and STATE SAMPLE
are preserved in full -- only per-cell Monte Carlo precision is reduced,
per the task brief's own stated priority order.

RNG separation (frozen, task brief S3/S10): actuator-set SAMPLING uses
`design_rng` = np.random.default_rng(DESIGN_SEED_BASE + state_idx), never
touched by simulation. Each physics replicate r uses
`physics_seed = PHYSICS_SEED_BASE + state_idx*100 + r`, shared bit-for-bit
across the no-control branch and every actuator-set branch for that r
(CRN pairing) -- verified by rng_crn_diagnostic_612.py.
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

N_SETS = 3
N_STREAMS = 2
DESIGN_SEED_BASE = 5_000_000
PHYSICS_SEED_BASE = 6_000_000

MANIFEST_PATH = C.DATA_DIR / "state_manifest_612.json"


def sample_random_sets(pool, K, n_sets, design_rng):
    pool = np.array(sorted(int(x) for x in pool))
    if len(pool) < K:
        return []
    seen = set()
    out = []
    attempts = 0
    while len(out) < n_sets and attempts < n_sets * 50:
        attempts += 1
        chosen = tuple(sorted(int(x) for x in design_rng.choice(pool, size=K, replace=False)))
        if chosen not in seen:
            seen.add(chosen)
            out.append(list(chosen))
    return out


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
    design_rng = np.random.default_rng(DESIGN_SEED_BASE + state_idx)

    # no-control: N_STREAMS full-length (D_MAX+R_RELEASE) rollouts, sliced per d
    no_control_by_stream = []
    for r in range(N_STREAMS):
        physics_seed = PHYSICS_SEED_BASE + state_idx * 100 + r
        oc = I.run_no_control_full(mf, r0, z0, z_context, seed_members, rule, h_star, physics_seed)
        no_control_by_stream.append(oc)

    cells = {}
    for K in I.K_GRID:
        if len(pool) < K:
            for d in I.D_GRID:
                cells[f"K{K}_d{d}"] = dict(K=K, d=d, unavailable=True, reason=f"pool size {len(pool)} < K={K}")
            continue
        sets = sample_random_sets(pool, K, N_SETS, design_rng)
        for d in I.D_GRID:
            rollouts = []
            for si, S in enumerate(sets):
                for r in range(N_STREAMS):
                    physics_seed = PHYSICS_SEED_BASE + state_idx * 100 + r
                    out = I.run_one(mf, r0, z0, z_context, seed_members, rule, h_star, S, d, physics_seed)
                    j0 = no_control_by_stream[r][d]["J"]
                    out["J0"] = j0
                    out["delta"] = out["J"] - j0
                    out["set_idx"] = si
                    out["stream"] = r
                    out["S"] = S
                    rollouts.append(out)
            deltas = [x["delta"] for x in rollouts]
            js = [x["J"] for x in rollouts]
            vs = [x["V"] for x in rollouts]
            set_means = {}
            for si in range(len(sets)):
                vals = [x["J"] for x in rollouts if x["set_idx"] == si]
                set_means[si] = float(np.mean(vals)) if vals else None
            cells[f"K{K}_d{d}"] = dict(
                K=K, d=d, unavailable=False, n_sets=len(sets), n_streams=N_STREAMS,
                sets=sets,
                G_sus_mean=float(np.mean(deltas)), G_sus_median=float(np.median(deltas)),
                G_sus_p10=float(np.percentile(deltas, 10)), G_sus_p90=float(np.percentile(deltas, 90)),
                frac_sets_positive_mean=float(np.mean([v > 0 for v in set_means.values() if v is not None])) if set_means else None,
                identity_valid_fraction=float(np.mean(vs)),
                mean_J=float(np.mean(js)), mean_J0=float(np.mean([no_control_by_stream[r][d]["J"] for r in range(N_STREAMS)])),
                set_means=set_means,
                between_set_var=float(np.var(list(v for v in set_means.values() if v is not None), ddof=1)) if len(set_means) > 1 else 0.0,
                within_set_var=float(np.mean([np.var([x["J"] for x in rollouts if x["set_idx"] == si], ddof=0) for si in range(len(sets))])) if sets else None,
                rollouts=rollouts,
            )
    return dict(state_id=state["state_id"], role=state["role"], no_control=no_control_by_stream, cells=cells)


def main():
    manifest = json.load(open(MANIFEST_PATH))
    states = manifest["states"]
    for i, s in enumerate(states):
        s["_idx"] = i
    results = []
    t_all = time.time()
    for s in states:
        t0 = time.time()
        res = run_state(s)
        dt = time.time() - t0
        print(f"[{s['state_id']} / {s['role']}] done in {dt:.1f}s", flush=True)
        results.append(res)
        json.dump(results, open(C.DATA_DIR / "phaseA_results_612.json", "w"), indent=1)
    print(f"Phase A total wall time: {time.time() - t_all:.1f}s")


if __name__ == "__main__":
    main()
