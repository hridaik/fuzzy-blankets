"""EVALUATION-SIDE DRIVER (reads Stage 6.6's frozen candidate data + the
lattice only to pick a figure/example -- task brief section 8's "documented
diagonal-snake pathology" -- never to bias candidate SELECTION toward a
metric beyond the brief's own explicit picks). Builds the fixed 20-candidate/
snapshot panel (300 total across 15 snapshots) from Stage 6.6's existing,
frozen `data/seed{seed}__{condition}__fE1.00__t20.json` rows:

  1. established I0 (candidate_source == "seed_reference_I0")
  2. highest-C candidate      (argmax C_internal)
  3. highest-G candidate      (argmax G_internal)
  4. highest-D candidate      (argmax D_local)
  5. lowest-L candidate       (argmin L_blanket)
  6. high-C/low-D globally-aligned patch (argmax C_internal - D_local)
  7. the diagonal-snake pathology (argmin avg_internal_degree -- every row is
     already Moore-connected by construction in candidates.py, so this never
     needs to re-derive connectivity, only pick the scattered-but-connected
     extreme; common_66.py's own docstring reserves avg_internal_degree for
     exactly this "figure/example selection" use)
  8. 13 deterministic RNG-drawn candidates from the remaining pool

Rows 2-8 that happen to collide with an earlier pick (same candidate_id) are
deduplicated and the random draw tops up to 20 unique candidates.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from common_67 import lattice_100, avg_internal_degree, STAGE66_DATA_DIR, DATA_DIR, dump_json, CONDITIONS, PRIMARY_SEEDS_67

PANEL_SIZE = 20
PANEL_RNG_SEED = 67_000_000  # distinct from every other stage's offset ranges


def load_stage66_snapshot(seed: int, condition: str) -> dict:
    path = STAGE66_DATA_DIR / f"seed{seed}__{condition}__fE1.00__t20.json"
    if not path.exists():
        raise FileNotFoundError(f"Stage 6.6 snapshot data not found: {path} "
                                 "(run stage6_6_collective_landscape/code/run_all_snapshots.py first)")
    return json.loads(path.read_text())


def _argext(rows, key, mode):
    vals = [r[key] for r in rows]
    idx = int(np.argmax(vals)) if mode == "max" else int(np.argmin(vals))
    return rows[idx]


def build_panel_for_snapshot(seed: int, condition: str, lattice, rng: np.random.Generator) -> dict:
    result = load_stage66_snapshot(seed, condition)
    rows = result["rows"]

    picks = []
    labels = []

    def add(row, label):
        picks.append(row)
        labels.append(label)

    I0_row = next(r for r in rows if r["candidate_source"] == "seed_reference_I0")
    add(I0_row, "established_I0")
    add(_argext(rows, "C_internal", "max"), "highest_C")
    add(_argext(rows, "G_internal", "max"), "highest_G")
    add(_argext(rows, "D_local", "max"), "highest_D")
    add(_argext(rows, "L_blanket", "min"), "lowest_L")

    cd_score = [r["C_internal"] - r["D_local"] for r in rows]
    add(rows[int(np.argmax(cd_score))], "high_C_low_D_patch")

    degrees = [avg_internal_degree(lattice, r["node_ids"]) for r in rows]
    add(rows[int(np.argmin(degrees))], "diagonal_snake_pathology")

    seen = set()
    panel = []
    for row, label in zip(picks, labels):
        if row["candidate_id"] in seen:
            continue
        seen.add(row["candidate_id"])
        panel.append(dict(row=row, label=label))

    remaining = [r for r in rows if r["candidate_id"] not in seen]
    n_random = PANEL_SIZE - len(panel)
    if remaining and n_random > 0:
        idxs = rng.choice(len(remaining), size=min(n_random, len(remaining)), replace=False)
        for k in sorted(idxs.tolist()):
            panel.append(dict(row=remaining[k], label="random_connected"))

    return dict(seed=seed, condition=condition, snapshot_id=result["meta"]["snapshot_id"],
                I0=result["meta"]["I0"], panel=panel)


def build_all_panels() -> dict:
    lattice = lattice_100()
    out = {}
    for seed in PRIMARY_SEEDS_67:
        for condition in CONDITIONS:
            rng = np.random.default_rng(PANEL_RNG_SEED + seed * 100 + CONDITIONS.index(condition))
            snap = build_panel_for_snapshot(seed, condition, lattice, rng)
            key = f"seed{seed}_{condition}"
            out[key] = snap
            print(f"{key}: panel size {len(snap['panel'])}")
    return out


def main():
    panels = build_all_panels()
    n_total = sum(len(v["panel"]) for v in panels.values())
    dump_json(dict(panels=panels, n_snapshots=len(panels), n_total_candidates=n_total),
              DATA_DIR / "candidate_panel.json")
    print(f"wrote data/candidate_panel.json ({len(panels)} snapshots, {n_total} candidates)")


if __name__ == "__main__":
    main()
