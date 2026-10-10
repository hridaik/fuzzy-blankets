"""Task brief section 11: sample-efficiency sweep. For I0 + 5 more
representative panel candidates per seed, repeats the blind boundary
pipeline at R in {5,10,20,50,100} replicates (W=10 fixed).

Compute-scope note (mirrors stage6_5/boundary_inference/code/
run_sample_efficiency.py's own precedent: "bootstrap uncertainty is reported
separately... to bound compute"): the primary 300-candidate panel uses
B_boot=30 bootstrap-stabilized edges (task brief section 5); at R<=20
replicates, bootstrapping the graph-inference procedure itself is barely
meaningful (a 60% training split of 5 replicates is 3 replicates). This
sweep therefore uses the SINGLE (non-bootstrapped) directed graph with raw
Delta>0 as the candidate-pool criterion -- a disclosed, sweep-only scope
reduction, never applied to the primary panel's frozen bootstrap-stability
numbers.
"""
from __future__ import annotations

import json
import time

import numpy as np

from common_67 import (
    lattice_100, build_snapshot_replicates, build_window_dataset3, dump_json,
    DATA_DIR, snapshot_key, PRIMARY_SEEDS_67, DELTA_PRED, K_MAX,
)
from directed_graph_inference import infer_directed_graph
from predictive_boundary import infer_predictive_boundary, test_excess_loss
from oracle_validation import validate_candidate

R_GRID = [5, 10, 20, 50, 100]
SHORTLIST_K = 25
MIN_GAIN = 0.002
CONDITION = "no_control"  # sweep condition: the natural/uncontrolled regime, one fixed choice per seed
N_EXTRA_CANDIDATES = 5


def _raw_positive_stability(G: dict) -> dict:
    """Sweep-only stand-in for graph_bootstrap.stability_flags: every edge
    with Delta > 0 counts as 'stable' (no bootstrap at small R -- see module
    docstring)."""
    return {i: {j: (delta > 0) for j, delta in row.items()} for i, row in G.items()}


def load_panel_candidates(seed: int, n_extra: int) -> list[dict]:
    panels = json.loads((DATA_DIR / "candidate_panel.json").read_text())["panels"]
    panel = panels[snapshot_key(seed, CONDITION)]["panel"]
    I0_entry = next(p for p in panel if p["label"] == "established_I0")
    others = [p for p in panel if p["label"] != "established_I0"][:n_extra]
    return [I0_entry] + others


def main():
    lattice = lattice_100()
    rows = []
    t0_all = time.time()

    for seed in PRIMARY_SEEDS_67:
        candidates = load_panel_candidates(seed, N_EXTRA_CANDIDATES)
        for R in R_GRID:
            t0 = time.time()
            data_rng_seed = seed * 1000 + 900 + R  # distinct from the primary panel's rng range
            rng = np.random.default_rng(data_rng_seed)
            ref, cond, z_reps, t_snap = build_snapshot_replicates(lattice, seed, CONDITION, rng, n_rep=R)
            wds = build_window_dataset3(z_reps, t=t_snap)

            single = infer_directed_graph(wds.train_prev, wds.train_next, wds.val_prev, wds.val_next,
                                           n_bird=100, shortlist_k=SHORTLIST_K, n_jobs=1)
            flags = _raw_positive_stability(single["G"])

            for entry in candidates:
                row = entry["row"]
                I = row["node_ids"]
                pb = infer_predictive_boundary(I, single["G"], flags, wds.train_prev, wds.train_next,
                                                wds.val_prev, wds.val_next, n_bird=100,
                                                delta_tol=DELTA_PRED, min_gain=MIN_GAIN, max_size=K_MAX)
                tel = test_excess_loss(I, pb["B_hat"], wds.train_prev, wds.train_next,
                                        wds.test_prev, wds.test_next, n_bird=100)
                val = validate_candidate(I, pb["B_hat"], None, n_bird=100, lattice=lattice)

                rows.append(dict(
                    seed=seed, R=R, candidate_id=row["candidate_id"], label=entry["label"],
                    B_hat=pb["B_hat"], B_D=val["B_D"],
                    excess_loss_test=tel["excess_loss"],
                    predictively_sufficient=bool(tel["excess_loss"] <= DELTA_PRED),
                    jaccard=val["predictive"]["jaccard"], precision=val["predictive"]["precision"],
                    recall=val["predictive"]["recall"],
                    n_rep_train=wds.n_rep_train, n_rep_val=wds.n_rep_val, n_rep_test=wds.n_rep_test,
                ))
            elapsed = time.time() - t0
            print(f"seed={seed} R={R}: {len(candidates)} candidates in {elapsed:.1f}s")

    total = time.time() - t0_all
    dump_json(dict(rows=rows, r_grid=R_GRID, shortlist_k=SHORTLIST_K, condition=CONDITION,
                    n_extra_candidates=N_EXTRA_CANDIDATES, total_elapsed_seconds=total),
              DATA_DIR / "sample_efficiency.json")
    print(f"DONE total={total:.1f}s -> data/sample_efficiency.json")


if __name__ == "__main__":
    main()
