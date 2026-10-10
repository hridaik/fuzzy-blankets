"""Driver (evaluation-side: constructs the InterventionOracle and the sampled
observed states, then hands both to the inference-side `causal_discovery.py`
as plain arrays / a black-box callable -- never a Lattice). Task brief
sections 12-14: for each of the 300 panel candidates, tests every exterior
bird j as a causal source via the exact counterfactual propagator, wrapped
so the inference side never inspects which neighbours the simulator used.

Compute note: the exact propagator is O(1) per (X_t, j, z') query (closed
form, no rollout) but still one query per (state, source, alt-heading)
triple. To keep this tractable across 300 candidates x up to 99 sources x 4
headings, `N_STATES_PER_CANDIDATE` observed states are sampled per candidate
(from that snapshot's own pooled window data -- real observed states, never
simulator-privileged) rather than every timestep x replicate combination.
Candidates are embarrassingly parallel (each only needs its own I + sampled
states + a shared oracle), so this driver parallelizes across candidates
with a worker pool, one InterventionOracle built per worker (not per task).
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time

import numpy as np

from common_67 import (
    lattice_100, build_snapshot_replicates, build_window_dataset3, dump_json,
    DATA_DIR, snapshot_key, CONDITIONS, PRIMARY_SEEDS_67,
)
from intervention_api import InterventionOracle
from causal_discovery import estimate_causal_effects, bootstrap_ci_causal, infer_causal_boundary
from exact_intervention import default_precomputed_model

N_STATES_PER_CANDIDATE = 15
CI_N_BOOT = 1000
CI_ALPHA = 0.05

_WORKER_ORACLE = None


def _init_worker():
    global _WORKER_ORACLE
    _WORKER_ORACLE = InterventionOracle(pm=default_precomputed_model(), lattice=lattice_100())


def _process_candidate(args):
    (candidate_id, label, I, X_samples, data_rng_seed) = args
    I_set = set(I)
    exterior = [j for j in range(100) if j not in I_set]
    eff = estimate_causal_effects(I, exterior, X_samples, _WORKER_ORACLE)
    ci = bootstrap_ci_causal(eff["raw_D_samples"], n_boot=CI_N_BOOT, alpha=CI_ALPHA,
                              rng=np.random.default_rng(data_rng_seed + 11))
    B_causal = infer_causal_boundary(ci)
    return dict(candidate_id=candidate_id, label=label, I=I,
                D_j_do=eff["D_j_do"], C_j_to_i=eff["C_j_to_i"], ci=ci,
                B_hat_causal=B_causal, n_states_sampled=len(X_samples))


def load_panel() -> dict:
    return json.loads((DATA_DIR / "candidate_panel.json").read_text())["panels"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_jobs", type=int, default=8)
    args = ap.parse_args()

    lattice = lattice_100()
    panels = load_panel()
    results = {}
    t0_all = time.time()

    pool = mp.Pool(args.n_jobs, initializer=_init_worker) if args.n_jobs > 1 else None
    if pool is None:
        _init_worker()

    try:
        for seed in PRIMARY_SEEDS_67:
            for condition in CONDITIONS:
                key = snapshot_key(seed, condition)
                t0 = time.time()
                data_rng_seed = seed * 1000 + CONDITIONS.index(condition)
                rng = np.random.default_rng(data_rng_seed)
                ref, cond, z_reps, t_snap = build_snapshot_replicates(lattice, seed, condition, rng)
                wds = build_window_dataset3(z_reps, t=t_snap)
                pool_states = np.concatenate([wds.train_prev, wds.val_prev, wds.test_prev], axis=0)
                sample_rng = np.random.default_rng(data_rng_seed + 7)

                tasks = []
                for entry in panels[key]["panel"]:
                    row = entry["row"]
                    idx = sample_rng.choice(len(pool_states),
                                             size=min(N_STATES_PER_CANDIDATE, len(pool_states)), replace=False)
                    X_samples = pool_states[idx]
                    tasks.append((row["candidate_id"], entry["label"], row["node_ids"], X_samples, data_rng_seed))

                if pool is not None:
                    candidate_rows = pool.map(_process_candidate, tasks)
                else:
                    candidate_rows = [_process_candidate(t) for t in tasks]

                elapsed = time.time() - t0
                results[key] = dict(seed=seed, condition=condition, candidates=candidate_rows,
                                     elapsed_seconds=elapsed)
                print(f"[{key}] {len(candidate_rows)} candidates in {elapsed:.1f}s "
                      f"(mean |B_causal|={np.mean([len(r['B_hat_causal']) for r in candidate_rows]):.1f})")
    finally:
        if pool is not None:
            pool.close()
            pool.join()

    total = time.time() - t0_all
    dump_json(dict(results=results, n_states_per_candidate=N_STATES_PER_CANDIDATE,
                    ci_n_boot=CI_N_BOOT, ci_alpha=CI_ALPHA, total_elapsed_seconds=total),
              DATA_DIR / "causal_discovery_panel.json")
    print(f"DONE total={total:.1f}s -> data/causal_discovery_panel.json")


if __name__ == "__main__":
    main()
