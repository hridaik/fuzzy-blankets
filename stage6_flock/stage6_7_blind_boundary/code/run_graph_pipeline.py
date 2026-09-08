"""Driver (evaluation-side: builds data via the lattice/simulator, then hands
plain arrays to the inference-side pipeline). For each of the 15 primary
snapshots (3 seeds x 5 conditions):

  1. build the W=10/R=100 replicate window dataset, 60/20/20 trajectory-level
     split (task brief section 2);
  2. infer_directed_graph (single fit) at shortlist_k=25 (task brief section 4);
  3. bootstrap_graph at B_boot=30 (task brief section 5) -- the dominant cost,
     ~4.7 min/snapshot single-process per the timing pilot (logs/timing_pilot.json),
     parallelized here across the 30 bootstrap resamples with N_JOBS worker
     processes;
  4. save data/graph__{snapshot}.json (G, full_losses, shortlists, edge_stats).

Run: python3 run_graph_pipeline.py [--n_jobs N] [--seeds 2,3,4] [--conditions ...]
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from common_67 import (
    lattice_100, build_snapshot_replicates, build_window_dataset3, dump_json,
    DATA_DIR, LOG_DIR, PRIMARY_SEEDS_67, CONDITIONS, SHORTLIST_K_DEFAULT, B_BOOT_SPEC,
    snapshot_key,
)
from directed_graph_inference import infer_directed_graph
from graph_bootstrap import bootstrap_graph


def run_one_snapshot(seed: int, condition: str, lattice, shortlist_k: int, n_boot: int,
                      n_jobs: int, data_rng_seed: int) -> dict:
    t_wall0 = time.time()
    rng = np.random.default_rng(data_rng_seed)
    ref, cond, z_reps, t_snap = build_snapshot_replicates(lattice, seed, condition, rng)
    wds = build_window_dataset3(z_reps, t=t_snap)

    t0 = time.time()
    single = infer_directed_graph(wds.train_prev, wds.train_next, wds.val_prev, wds.val_next,
                                   n_bird=100, shortlist_k=shortlist_k, n_jobs=1)
    t_single = time.time() - t0

    start = max(0, t_snap - 9)
    z_train_traj = z_reps[wds.train_ids][:, start:t_snap + 1]
    z_val_traj = z_reps[wds.val_ids][:, start:t_snap + 1]

    t0 = time.time()
    boot_rng = np.random.default_rng(data_rng_seed + 1)
    boot = bootstrap_graph(z_train_traj, z_val_traj, n_boot=n_boot, shortlist_k=shortlist_k,
                            n_bird=100, rng=boot_rng, n_jobs=n_jobs)
    t_boot = time.time() - t0

    elapsed = time.time() - t_wall0
    key = snapshot_key(seed, condition)
    print(f"[{key}] single={t_single:.1f}s boot={t_boot:.1f}s total={elapsed:.1f}s "
          f"n_fits_single={single['n_fits_total']}")

    return dict(
        seed=seed, condition=condition, snapshot_id=key, t_snapshot=t_snap,
        I0=ref["I0"].tolist(),
        n_rep_train=wds.n_rep_train, n_rep_val=wds.n_rep_val, n_rep_test=wds.n_rep_test,
        train_ids=wds.train_ids, val_ids=wds.val_ids, test_ids=wds.test_ids,
        G=single["G"], full_losses=single["full_losses"], shortlists=single["shortlists"],
        n_fits_single=single["n_fits_total"],
        edge_stats=boot["edge_stats"], n_boot=n_boot, shortlist_k=shortlist_k,
        elapsed_seconds=elapsed, t_single=t_single, t_boot=t_boot,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_jobs", type=int, default=8)
    ap.add_argument("--n_boot", type=int, default=B_BOOT_SPEC)
    ap.add_argument("--shortlist_k", type=int, default=SHORTLIST_K_DEFAULT)
    ap.add_argument("--seeds", type=str, default="2,3,4")
    ap.add_argument("--conditions", type=str, default=",".join(CONDITIONS))
    args = ap.parse_args()

    seeds = [int(s) for s in args.seeds.split(",")]
    conditions = args.conditions.split(",")

    lattice = lattice_100()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_graph_pipeline.log"
    t_start = time.time()
    manifest = []
    with open(log_path, "a") as logf:
        logf.write(f"\n=== run_graph_pipeline start {time.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"n_jobs={args.n_jobs} n_boot={args.n_boot} shortlist_k={args.shortlist_k} ===\n")
        logf.flush()
        idx = 0
        for seed in seeds:
            for condition in conditions:
                idx += 1
                data_rng_seed = seed * 1000 + CONDITIONS.index(condition)
                try:
                    result = run_one_snapshot(seed, condition, lattice, args.shortlist_k, args.n_boot,
                                               args.n_jobs, data_rng_seed)
                    dump_json(result, DATA_DIR / f"graph__{result['snapshot_id']}.json")
                    line = (f"[{idx}/{len(seeds)*len(conditions)}] {result['snapshot_id']} "
                            f"elapsed={result['elapsed_seconds']:.1f}s")
                    manifest.append(dict(seed=seed, condition=condition, status="ok",
                                          elapsed_seconds=result["elapsed_seconds"]))
                except Exception as e:  # noqa: BLE001
                    line = f"[{idx}] seed={seed} condition={condition} FAILED: {e!r}"
                    manifest.append(dict(seed=seed, condition=condition, status="failed", error=repr(e)))
                print(line)
                logf.write(line + "\n")
                logf.flush()
        total = time.time() - t_start
        logf.write(f"=== run_graph_pipeline done, total {total:.1f}s ===\n")
    dump_json(dict(manifest=manifest, total_elapsed_seconds=total, n_jobs=args.n_jobs,
                    n_boot=args.n_boot, shortlist_k=args.shortlist_k),
              DATA_DIR / "graph_pipeline_manifest.json")
    print(f"DONE total={total:.1f}s")


if __name__ == "__main__":
    main()
