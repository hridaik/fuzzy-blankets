"""Driver (evaluation-side for data construction, but the actual boundary
inference call is the inference-side `predictive_boundary.py` -- this script
only supplies plain arrays + the already-frozen Ghat/stability flags, never a
Lattice). For each of the 15 snapshots' 20-candidate panel (300 total),
computes Shat^pred(I), runs the greedy conditional selection (task brief
section 6), and the section-7 test-set excess loss.

Requires data/graph__{snapshot}.json (run_graph_pipeline.py) and
data/candidate_panel.json (candidate_panel.py) to already exist.
"""
from __future__ import annotations

import json
import time

import numpy as np

from common_67 import (
    lattice_100, build_snapshot_replicates, build_window_dataset3, dump_json,
    DATA_DIR, snapshot_key, CONDITIONS, PRIMARY_SEEDS_67, DELTA_PRED, K_MAX,
)
from graph_bootstrap import stability_flags
from predictive_boundary import infer_predictive_boundary, test_excess_loss

MIN_GAIN = 0.002   # matches stage6_5/boundary_inference/code/api.py's frozen default
TAU_FREQ, TAU_SIGN = 0.5, 0.7  # frozen edge-stability rule (developed on seeds 2/3, see PROTOCOL_6_7.md)


def load_graph(seed: int, condition: str) -> dict:
    path = DATA_DIR / f"graph__{snapshot_key(seed, condition)}.json"
    raw = json.loads(path.read_text())
    G = {int(i): {int(j): v for j, v in row.items()} for i, row in raw["G"].items()}
    return dict(raw=raw, G=G)


def load_panel() -> dict:
    return json.loads((DATA_DIR / "candidate_panel.json").read_text())["panels"]


def rebuild_wds(seed: int, condition: str, lattice, data_rng_seed: int):
    rng = np.random.default_rng(data_rng_seed)
    ref, cond, z_reps, t_snap = build_snapshot_replicates(lattice, seed, condition, rng)
    wds = build_window_dataset3(z_reps, t=t_snap)
    return ref, z_reps, t_snap, wds


def main():
    lattice = lattice_100()
    panels = load_panel()
    results = {}
    t0_all = time.time()

    for seed in PRIMARY_SEEDS_67:
        for condition in CONDITIONS:
            key = snapshot_key(seed, condition)
            t0 = time.time()
            g = load_graph(seed, condition)
            edge_stats = {int(i): {int(j): v for j, v in row.items()}
                          for i, row in g["raw"]["edge_stats"].items()}
            flags = stability_flags(edge_stats, TAU_FREQ, TAU_SIGN)

            data_rng_seed = seed * 1000 + CONDITIONS.index(condition)
            ref, z_reps, t_snap, wds = rebuild_wds(seed, condition, lattice, data_rng_seed)

            panel = panels[key]["panel"]
            candidate_rows = []
            for entry in panel:
                row = entry["row"]
                I = row["node_ids"]
                pb = infer_predictive_boundary(
                    I, g["G"], flags, wds.train_prev, wds.train_next, wds.val_prev, wds.val_next,
                    n_bird=100, delta_tol=DELTA_PRED, min_gain=MIN_GAIN, max_size=K_MAX,
                )
                tel = test_excess_loss(I, pb["B_hat"], wds.train_prev, wds.train_next,
                                        wds.test_prev, wds.test_next, n_bird=100)
                candidate_rows.append(dict(
                    candidate_id=row["candidate_id"], label=entry["label"], I=I,
                    S_pred_size=len(pb["S_pred"]), S_pred=pb["S_pred"],
                    B_hat_pred=pb["B_hat"], boundary_size=len(pb["B_hat"]),
                    full_loss_val=pb["full_loss"], interior_only_loss_val=pb["interior_only_loss"],
                    excess_loss_test=tel["excess_loss"], full_loss_test=tel["full_loss_test"],
                    B_loss_test=tel["B_loss_test"], I_only_loss_test=tel["I_only_loss_test"],
                    predictively_sufficient=bool(tel["excess_loss"] <= DELTA_PRED),
                    trace=pb["trace"],
                    C_internal=row["C_internal"], G_internal=row["G_internal"],
                    L_blanket=row["L_blanket"], D_local=row["D_local"],
                    structural_shell_size=row["structural_shell_size"],
                ))
            elapsed = time.time() - t0
            results[key] = dict(seed=seed, condition=condition, I0=ref["I0"].tolist(),
                                 candidates=candidate_rows, elapsed_seconds=elapsed)
            print(f"[{key}] {len(candidate_rows)} candidates in {elapsed:.1f}s "
                  f"(mean |B_hat|={np.mean([r['boundary_size'] for r in candidate_rows]):.1f}, "
                  f"mean excess_loss={np.mean([r['excess_loss_test'] for r in candidate_rows]):.4f})")

    total = time.time() - t0_all
    dump_json(dict(results=results, delta_pred=DELTA_PRED, min_gain=MIN_GAIN, k_max=K_MAX,
                    tau_freq=TAU_FREQ, tau_sign=TAU_SIGN, total_elapsed_seconds=total),
              DATA_DIR / "predictive_boundary_panel.json")
    print(f"DONE total={total:.1f}s -> data/predictive_boundary_panel.json")


if __name__ == "__main__":
    main()
