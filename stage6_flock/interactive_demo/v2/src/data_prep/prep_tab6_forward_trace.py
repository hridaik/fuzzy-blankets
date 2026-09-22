"""Step 2 (material_identity_step2_20260921) visualization wiring.

Merges the frozen ForwardMaterialTrace611 replay
(`stage6_11_translating_torus/audit/material_identity_step2_20260921/data/
forward_material_trace_seed{n}.csv`, produced by `apply_trace_to_seeds.py`)
into `tab6_translation.json`'s per-frame records, alongside the Step-1
material_retention block. This is presentation-layer merging only -- no
tracker/controller code is touched, and the CSV it reads is itself a
read-only replay of the real detector against already-recorded trajectories
(see that script's docstring).

Run AFTER `prep_tab6_translation.py` (adds to its output) and after
`apply_trace_to_seeds.py` has produced the per-seed CSVs.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
STEP2_DATA = ROOT / "stage6_11_translating_torus/audit/material_identity_step2_20260921/data"
TAB6_JSON = Path(__file__).resolve().parents[2] / "data" / "tab6_translation.json"

SEEDS = [500, 501, 502, 503, 504]


def load_trace(seed):
    path = STEP2_DATA / f"forward_material_trace_seed{seed}.csv"
    rows = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows[int(r["t"])] = r
    return rows


def main():
    d = json.load(open(TAB6_JSON))
    for seed in SEEDS:
        trace = load_trace(seed)
        sd = d["seeds"][str(seed)]
        for frame in sd["frames"]:
            t = frame["t"]
            r = trace.get(t)
            if r is None:
                frame["forward_material_trace"] = None
                continue
            frame["forward_material_trace"] = {
                "status": r["status"],
                "n_members": int(r["n_members"]),
                "split_flag": r["split_flag"] == "True",
                "merge_flag": r["merge_flag"] == "True",
                "steps_unresolved": int(r["steps_unresolved"]),
                "n_candidates": int(r["n_candidates"]),
                "n_accepting_candidates": int(r["n_accepting_candidates"]),
                "v1_vs_trace_agree": r["v1_vs_trace_agree"] == "True",
                "v1_material_overlap_with_trace": (int(r["v1_material_overlap_with_trace"])
                                                    if r["v1_material_overlap_with_trace"] not in ("", "None") else None),
                "frac_trace_at_target": (float(r["frac_trace_at_target"])
                                          if r["frac_trace_at_target"] not in ("", "None") else None),
                "reason": r["reason"],
            }
    d["provenance"]["forward_material_trace_note"] = (
        "Added 2026-09-21 (Step 2, material_identity_step2_20260921/). "
        "ForwardMaterialTrace611 -- a deliberately simple, material-overlap-only "
        "audit comparator, frozen from independent uncontrolled-data calibration "
        "(never tuned on these five seeds' outcomes). Statuses: continuing / "
        "unresolved / dead / split-flagged / merge-flagged. Frames where it "
        "disagrees with v1's displayed interior are marked v1_vs_trace_agree=false."
    )
    json.dump(d, open(TAB6_JSON, "w"))
    print("merged forward_material_trace into", TAB6_JSON)


if __name__ == "__main__":
    main()
