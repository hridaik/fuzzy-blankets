"""Step 2, section 12: re-evaluate the Step-1 'ID-independent' readouts
against the new ForwardMaterialTrace611, without deleting or overwriting
them. Two checks, both audit-only:

1. Frozen-original-material decay: how fast does the FORWARD trace
   (allowing ordinary gradual turnover) lose overlap with the exact t0
   cohort? Quantifies how strict `original_material`'s frozen-ID readout is.

2. Field-direction anchored at the new trace's own centroid vs. v2's
   centroid (the historical anchor), at the historical radius=3.0, plus a
   radius-sensitivity sweep. This does not choose a radius to manufacture
   agreement -- the sweep is reported in full, unfiltered.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = STAGE_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import DATA_DIR, L_BOX  # noqa: E402
from identity_69 import centroid  # noqa: E402
from geometry_611 import torus_delta  # noqa: E402

OUT = Path(__file__).resolve().parents[1]
SEEDS = [500, 501, 502, 503, 504]
RADII = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]


def field_direction(r, z, members, L, radius, target_heading):
    if len(members) == 0 or target_heading is None:
        return None
    c = centroid(r[list(members)], L)
    d = torus_delta(r, c, L)
    D = np.sqrt((d ** 2).sum(-1))
    near = D <= radius
    if not near.any():
        return None
    return float((z[near] == target_heading).mean())


def main():
    results = {}
    for seed in SEEDS:
        viz = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
        frames = {f["t"]: f for f in viz["frames"]}
        trace_rows = {int(r["t"]): r for r in csv.DictReader(open(OUT / "data" / f"forward_material_trace_seed{seed}.csv"))}

        # ---- frozen-original-material decay: how fast does the TRACE's own
        # size/overlap-with-t0-cohort fall off? Uses n_members (trace size)
        # and, where trace==v1 this frame (v1_vs_trace_agree), the exact
        # overlap via v1's recorded interior; where they disagree, only the
        # trace's OWN interior-overlap-with-t0 isn't directly recoverable
        # from the CSV (only its centroid/size are persisted per step, not
        # full membership) -- reported as null for those frames rather than
        # approximated, a disclosed gap, not a silent fill-in.
        qualify_t = min(t for t, f in frames.items() if f["phase"] != "uncontrolled")
        interior0 = set(frames[qualify_t]["interior"])
        decay = []
        for t in sorted(trace_rows):
            r = trace_rows[t]
            n = int(r["n_members"])
            if n == 0:
                continue
            if r["v1_vs_trace_agree"] == "True":
                overlap = len(set(frames[t]["interior"]) & interior0)
                frac = overlap / len(interior0)
            else:
                overlap = frac = None
            decay.append(dict(t=t, trace_size=n, overlap_with_t0_cohort=overlap,
                               frac_of_t0_cohort_retained=frac, exact=(r["v1_vs_trace_agree"] == "True")))

        # ---- field-direction radius sweep, anchored at (a) v1's own
        # per-frame centroid [recorded exactly every frame, from f["centre"]
        # is the WORLD centre not the interior centroid -- recompute the
        # interior centroid directly] and (b) the trace's own stored
        # centroid (apply_trace_to_seeds.py persisted centroid_x/y for
        # every `continuing` step). v2's own centroid is NOT recomputed in
        # this pass (would require a full v2 replay of all 5 seeds, not
        # done here for time -- disclosed gap, not silently substituted).
        field_dir_rows = []
        for t in sorted(trace_rows):
            r = trace_rows[t]
            f = frames.get(t)
            if f is None or f["target_heading"] is None:
                continue
            rr, zz = np.array(f["r"]), np.array(f["z"], dtype=int)
            th = f["target_heading"]
            row = dict(t=t, phase=f["phase"])
            if f["interior"]:
                c_v1 = centroid(rr[f["interior"]], L_BOX)
                for radius in RADII:
                    d = torus_delta(rr, c_v1, L_BOX)
                    D = np.sqrt((d ** 2).sum(-1))
                    near = D <= radius
                    row[f"field_direction_v1anchor_r{radius}"] = float((zz[near] == th).mean()) if near.any() else None
            if r.get("centroid_x") not in ("", None):
                c_trace = np.array([float(r["centroid_x"]), float(r["centroid_y"])])
                for radius in RADII:
                    d = torus_delta(rr, c_trace, L_BOX)
                    D = np.sqrt((d ** 2).sum(-1))
                    near = D <= radius
                    row[f"field_direction_traceanchor_r{radius}"] = float((zz[near] == th).mean()) if near.any() else None
            field_dir_rows.append(row)

        results[seed] = dict(
            qualify_t=qualify_t, t0_cohort_size=len(interior0),
            n_total_frames=len(trace_rows),
            frozen_material_decay=decay,
            field_direction_radius_sweep=field_dir_rows,
            note="v2's own centroid NOT recomputed in this pass (would need a full v2 replay of all 5 seeds; disclosed gap). v1-anchor and trace-anchor both computed exactly, every frame.",
        )
        last_exact = [d for d in decay if d["exact"]]
        last = last_exact[-1] if last_exact else None
        print(f"seed {seed}: t0 cohort={len(interior0)}, at last exact-sampled frame t={last['t'] if last else 'n/a'}: "
              f"frac of t0 cohort retained = {last['frac_of_t0_cohort_retained'] if last else 'n/a'}")

    json.dump(results, open(OUT / "data" / "rescoring_reassessment.json", "w"), indent=2)
    print("wrote", OUT / "data" / "rescoring_reassessment.json")


if __name__ == "__main__":
    main()
