"""Step 2: apply the FROZEN ForwardMaterialTrace611 rule (chosen in
`calibrate_identity_rule.py` from uncontrolled data only, confirmed in
`synthetic_identity_tests.py` against the hand-built known-history suite)
UNCHANGED to the five historical seeds 500-504.

Replay technique: identical to Step 1's `lineage_forensics_611.py` and this
task's `seed503_t46_t47_forensics.py` -- deterministic replay of
`detect_69.propose` against the already-recorded ground-truth (r, z)
trajectory in `data/viz_bundle_611__seed{n}.json`. No simulator RNG is
consumed; no tracker/controller/detector code is modified. Seeding:
ForwardMaterialTrace611.start() is seeded from the EXACT qualification-time
interior recorded in the production run (the same `interior0` used
throughout Step 1's `branch_adjudication_611.py`), not from this tracker's
own candidate detection at t0 -- i.e. it starts from the same "target
selected at qualification" state the task brief specifies, and traces
FORWARD from there, never backward.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = STAGE_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import DATA_DIR, L_BOX  # noqa: E402
from detect_69 import propose  # noqa: E402
from geometry_611 import torus_delta  # noqa: E402
from identity_69 import centroid  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forward_material_trace_611 import ForwardMaterialTrace611, RULE_FAMILY_BUILDERS  # noqa: E402

OUT = Path(__file__).resolve().parents[1]
SEEDS = [500, 501, 502, 503, 504]


def build_frozen_rule():
    calib = json.load(open(OUT / "data" / "identity_rule_calibration.json"))
    frozen = calib["frozen_rule"]
    return RULE_FAMILY_BUILDERS[frozen["letter"]](**frozen["params"]), frozen


def frac_at_heading(z, ids, heading):
    ids = list(ids)
    if not ids or heading is None:
        return None
    return float((z[np.asarray(ids, dtype=int)] == heading).mean())


def run_seed(seed: int, rule):
    d = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
    frames = d["frames"]
    L = L_BOX

    qualify_t = None
    for f in frames:
        if f["phase"] != "uncontrolled":
            qualify_t = f["t"]
            break
    interior0 = None
    for f in frames:
        if f["t"] == qualify_t:
            interior0 = f["interior"]
            break

    tr = ForwardMaterialTrace611(rule, missed_detection_horizon=3)
    tr.start(qualify_t, interior0)

    z_window = []
    rows = []
    prev_r = None
    for f in frames:
        t = f["t"]
        r = np.array(f["r"])
        z = np.array(f["z"], dtype=int)
        z_window.append(z.copy())
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        if t < qualify_t:
            continue
        cands = propose(r, z_window, L) if len(z_window) >= 2 else []
        if t == qualify_t:
            decision = tr.history[0]
        else:
            decision = tr.step(t, cands)

        members = decision.accepted_members
        row = dict(
            seed=seed, t=t, phase=f["phase"], status=decision.status,
            n_members=len(members) if members else 0,
            chosen_candidate_idx=decision.chosen_candidate_idx,
            n_candidates=len(cands), n_accepting_candidates=decision.n_accepting_candidates,
            split_flag=decision.split_flag, merge_flag=decision.merge_flag,
            steps_unresolved=decision.steps_unresolved,
            v1_interior_size=len(f["interior"]),
            v1_material_overlap_with_trace=(len(set(f["interior"]) & set(members)) if members else None),
            v1_vs_trace_agree=(set(f["interior"]) == set(members)) if members else False,
            target_heading=f["target_heading"],
            frac_trace_at_target=frac_at_heading(z, members, f["target_heading"]) if members else None,
            frac_v1_at_target=frac_at_heading(z, f["interior"], f["target_heading"]),
            reason=decision.reason,
        )
        if members:
            c = centroid(r[list(members)], L)
            row["centroid_x"], row["centroid_y"] = float(c[0]), float(c[1])
        rows.append(row)

    return rows


def main():
    rule, frozen = build_frozen_rule()
    print(f"applying frozen rule {rule.name} to seeds {SEEDS} (spec: {frozen})")
    all_rows = []
    for seed in SEEDS:
        rows = run_seed(seed, rule)
        all_rows.extend(rows)
        n_unresolved = sum(1 for r in rows if r["status"] == "unresolved")
        n_dead = sum(1 for r in rows if r["status"] == "dead")
        n_split = sum(1 for r in rows if r["split_flag"])
        n_merge = sum(1 for r in rows if r["merge_flag"])
        n_disagree_v1 = sum(1 for r in rows if not r["v1_vs_trace_agree"])
        print(f"  seed {seed}: {len(rows)} steps traced, unresolved={n_unresolved}, dead={n_dead}, "
              f"split_flags={n_split}, merge_flags={n_merge}, disagree_with_v1={n_disagree_v1}/{len(rows)}")
        import csv
        with open(OUT / "data" / f"forward_material_trace_seed{seed}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print("wrote per-seed CSVs to", OUT / "data")


if __name__ == "__main__":
    main()
