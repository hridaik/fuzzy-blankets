"""Timing pilot (mirrors stage6_6_collective_landscape's own "timing pilot
before committing to a final count" norm, PLAN.md). Measures actual
wall-clock cost of graph_inference.py + graph_bootstrap.py on ONE snapshot at
small scale, so the primary-run B_boot/shortlist_k can be chosen from a real
measurement rather than a guess. Writes logs/timing_pilot.json.
"""
from __future__ import annotations

import time
import numpy as np

from common_67 import lattice_100, build_window_dataset3, build_snapshot_replicates, dump_json, LOG_DIR
from nodewise_model import flatten_transitions
from directed_graph_inference import infer_directed_graph
from graph_bootstrap import bootstrap_graph


def main():
    lattice = lattice_100()
    rng = np.random.default_rng(0)
    t0 = time.time()
    ref, cond, z_reps, t_snap = build_snapshot_replicates(lattice, seed=2, condition="no_control", rng=rng)
    wds = build_window_dataset3(z_reps, t=t_snap)
    print(f"data built in {time.time()-t0:.1f}s; train n={len(wds.train_prev)} val n={len(wds.val_prev)} "
          f"test n={len(wds.test_prev)}")

    z_train_traj = z_reps[wds.train_ids][:, max(0, t_snap - 9):t_snap + 1]  # (n_rep_train, W, n_bird)

    # --- single-graph timing (no bootstrap), small shortlist ---
    for shortlist_k in (10, 25):
        t0 = time.time()
        result = infer_directed_graph(wds.train_prev, wds.train_next, wds.val_prev, wds.val_next,
                                       n_bird=100, shortlist_k=shortlist_k, n_jobs=1)
        elapsed = time.time() - t0
        print(f"shortlist_k={shortlist_k}: single graph in {elapsed:.1f}s, "
              f"n_fits_total={result['n_fits_total']}, per_fit={elapsed/result['n_fits_total']*1000:.1f}ms")

    # --- bootstrap timing, small n_boot, small shortlist ---
    z_val_traj = z_reps[wds.val_ids][:, max(0, t_snap - 9):t_snap + 1]
    for n_boot, shortlist_k in ((3, 10), (3, 25)):
        t0 = time.time()
        boot = bootstrap_graph(z_train_traj, z_val_traj, n_boot=n_boot, shortlist_k=shortlist_k,
                                n_bird=100, rng=np.random.default_rng(1), n_jobs=1)
        elapsed = time.time() - t0
        per_boot = elapsed / n_boot
        print(f"n_boot={n_boot} shortlist_k={shortlist_k}: {elapsed:.1f}s total, {per_boot:.1f}s/boot "
              f"-> est. {per_boot*30:.0f}s for B_boot=30, x15 snapshots = {per_boot*30*15/60:.1f} min")

    dump_json(dict(note="see stdout for the actual pilot numbers; this file just marks the pilot ran"),
              LOG_DIR / "timing_pilot.json")


if __name__ == "__main__":
    main()
