"""Build interactive_demo/v2/data/tab6_translation.json.

Sources, per seed in {500, 501, 502, 503, 504}:
  stage6_11_translating_torus/data/viz_bundle_611__seed{seed}.json
      -- per-frame continuous positions r, discrete headings z, phase,
         interior membership, actuators, target_heading, torus centre
  stage6_11_translating_torus/data/online_control_611__seed{seed}.json
      -- the event log: qualification/target time, per-control-step B_pred /
         B_causal / B_C (task-control interface) and frac_interior_at_target

This is the ORIGINAL Stage 6.11 v1 identity/readout, per the brief's explicit
instruction -- NOT the 6.11B audit and NOT the separate, incomplete
identity_foundation/ tracker (which never passed its own validation gate and
is unrelated to these frozen, already-published v1 results).

Only display-side compaction happens here: positions are rounded to 3
decimals (torus side length 24.0, so this is sub-visual-pixel precision) and
per-frame records are restricted to the fields the viewer actually renders.
No interpolation, no invented frames -- one JSON record per recorded
timestep.

2026-09-21 evidence-recovery audit addition (instrumentation only, no
tracker/controller change): each frame after the first now also carries a
`material_retention` block -- R_old, R_new, Jaccard overlap, and
retained/lost/gained bird-ID counts between this frame's `interior` and the
PREVIOUS frame's `interior`, computed directly from those two already-present
membership lists. This is the same quantity, computed the same way, as
`stage6_11_translating_torus/audit/evidence_recovery_20260921/code/
derive_material_retention.py`'s `*_displayed` columns (frame-to-frame, not
the tracker's internal per-branch bookkeeping -- see that script's docstring
for why the two differ at cross-branch MAP-switch points). No threshold for
"unusually large" discontinuity is hard-coded; the raw numbers are exposed
and the UI marks only the unambiguous overlap==0 case.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "stage6_11_translating_torus/data"
OUT = Path(__file__).resolve().parents[2] / "data" / "tab6_translation.json"

SEEDS = [500, 501, 502, 503, 504]

# Original v1 footnote text, exactly as instructed -- do not editorialize further.
V1_OUTCOMES = {
    500: "no turn", 501: "turn*", 502: "turn*", 503: "turn", 504: "no turn",
}
FOOTNOTE = ("Original v1 readout. Later audit found 501/502 were not corroborated "
            "by ID-independent turn measures; 503 was corroborated.")

seeds_out = {}
for seed in SEEDS:
    viz = json.load(open(DATA / f"viz_bundle_611__seed{seed}.json"))
    ctrl = json.load(open(DATA / f"online_control_611__seed{seed}.json"))

    bc_by_t = {}
    frac_by_t = {}
    events = []
    for e in ctrl["log"]:
        if e["event"] == "control_step":
            bc_by_t[e["t"]] = e["B_C"]
            frac_by_t[e["t"]] = e["frac_interior_at_target"]
        elif e["event"] == "release_step":
            # frac_interior_at_target is also logged through release -- no B_C
            # (no control interface exists once actuation has stopped).
            frac_by_t[e["t"]] = e["frac_interior_at_target"]
        if e["event"] in ("qualified_and_target_set", "release_begin", "episode_end"):
            events.append(e)

    frames = []
    prev_interior = None
    for f in viz["frames"]:
        t = f["t"]
        interior = f["interior"]
        retention = None
        if prev_interior is not None:
            i_prev, i_cur = set(prev_interior), set(interior)
            overlap = len(i_prev & i_cur)
            union = len(i_prev | i_cur)
            retention = {
                "R_old": (overlap / len(i_prev)) if i_prev else None,
                "R_new": (overlap / len(i_cur)) if i_cur else None,
                "jaccard": (overlap / union) if union else None,
                "n_retained": overlap,
                "n_lost": len(i_prev) - overlap,
                "n_gained": len(i_cur) - overlap,
                "prev_size": len(i_prev),
                "cur_size": len(i_cur),
                "retained_ids": sorted(i_prev & i_cur),
                "lost_ids": sorted(i_prev - i_cur),
                "gained_ids": sorted(i_cur - i_prev),
                "overlap_zero": overlap == 0,
            }
        frames.append({
            "t": t,
            "r": [[round(x, 3), round(y, 3)] for x, y in f["r"]],
            "z": f["z"],
            "phase": f["phase"],
            "interior": interior,
            "actuators": f["actuators"],
            "B_C": bc_by_t.get(t, []),
            "target_heading": f["target_heading"],
            "centre": f["centre"],
            "material_retention": retention,
        })
        prev_interior = interior

    frac_trace = [{"t": t, "frac": frac} for t, frac in sorted(frac_by_t.items())]

    seeds_out[str(seed)] = {
        "N": viz["N"], "L": viz["L"], "ended_phase": viz["ended_phase"],
        "v1_outcome": V1_OUTCOMES[seed],
        "frames": frames,
        "events": events,
        "frac_interior_at_target_trace": frac_trace,
        "final_t": ctrl["final_t"],
    }

out = {
    "provenance": {
        "source": "stage6_11_translating_torus/data/viz_bundle_611__seed{500..504}.json + online_control_611__seed{...}.json",
        "identity_version": "Stage 6.11 v1 identity/readout (original, not the 6.11B audit, not identity_foundation/)",
        "geometry": "torus_delta minimum-image wrapping, geometry_611.py",
        "footnote": FOOTNOTE,
        "audit_caveat": (
            "Uses original Stage 6.11 v1 identity/readout for presentation. "
            "Original v1 outcomes: 500/504 no turn; 501/502/503 turn. "
            "Later 6.11B audit found only seed 503's physical turn was independently "
            "corroborated; this view is therefore historical/exploratory, not a "
            "confirmatory control result."
        ),
        "audit_location": "stage6_11_translating_torus/audit/ (FIVE_SEED_CAUSAL_ADJUDICATION.md, RESULTS_6_11B.md) -- cited, not displayed",
        "material_retention_note": (
            "Added 2026-09-21 (evidence-recovery audit, Step 1). Each frame's "
            "material_retention block is R_old/R_new/Jaccard/retained/lost/gained "
            "between this frame's interior and the previous frame's interior, computed "
            "directly from the recorded membership lists -- diagnostic instrumentation "
            "only, no tracker/controller logic changed. No validated 'unusually large "
            "discontinuity' threshold exists in the repository; only the unambiguous "
            "overlap==0 case is marked in the UI."
        ),
    },
    "seed_order": SEEDS,
    "seeds": seeds_out,
    "default_seed": 500,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out))
print("wrote", OUT, OUT.stat().st_size, "bytes")
