"""Task brief section 17: recompute G_blind, L_blind for the 300 primary
candidates using Bhat^pred(I) in place of Stage 6.6's oracle-S(I)-constrained
boundary. C, D are read verbatim from Stage 6.6's existing rows (unchanged).
Requires data/predictive_boundary_panel.json to already exist.
"""
from __future__ import annotations

import json
import time

import numpy as np

from common_67 import lattice_100, build_snapshot_replicates, build_window_dataset3, dump_json
from common_67 import DATA_DIR, snapshot_key, CONDITIONS, PRIMARY_SEEDS_67
from blind_cache import BlindCache
from blind_landscape import blind_G_and_L


def main():
    lattice = lattice_100()
    pred_data = json.loads((DATA_DIR / "predictive_boundary_panel.json").read_text())["results"]
    rows = []
    t0_all = time.time()

    for seed in PRIMARY_SEEDS_67:
        for condition in CONDITIONS:
            key = snapshot_key(seed, condition)
            t0 = time.time()
            data_rng_seed = seed * 1000 + CONDITIONS.index(condition)
            rng = np.random.default_rng(data_rng_seed)
            ref, cond, z_reps, t_snap = build_snapshot_replicates(lattice, seed, condition, rng)
            wds = build_window_dataset3(z_reps, t=t_snap)
            cache = BlindCache(wds.train_prev, wds.train_next, wds.val_prev, wds.val_next)

            for pc in pred_data[key]["candidates"]:
                gl = blind_G_and_L(cache, pc["I"], pc["B_hat_pred"], n_bird=100)
                rows.append(dict(
                    seed=seed, condition=condition, candidate_id=pc["candidate_id"], label=pc["label"],
                    C_internal=pc["C_internal"], D_local=pc["D_local"],
                    G_oracle=pc["G_internal"], L_oracle=pc["L_blanket"],
                    G_blind=gl["G_blind"], L_blind=gl["L_blind"],
                    boundary_size_blind=len(pc["B_hat_pred"]), structural_shell_size=pc["structural_shell_size"],
                ))
            elapsed = time.time() - t0
            print(f"[{key}] {len(pred_data[key]['candidates'])} candidates in {elapsed:.1f}s "
                  f"(cache fits={cache.stats()['n_fits']})")

    total = time.time() - t0_all
    dump_json(dict(rows=rows, total_elapsed_seconds=total), DATA_DIR / "blind_landscape_panel.json")
    print(f"DONE total={total:.1f}s -> data/blind_landscape_panel.json")


if __name__ == "__main__":
    main()
