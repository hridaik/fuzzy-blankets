"""Build interactive_demo/v2/data/tab4_landscape.json.

Sources:
  stage6_6_collective_landscape/data/collective_landscape_bundle.json
  (re-served here via interactive_demo/data/collective_landscape_bundle.json)
      -- snapshots[cond].candidates: real candidate interior regions (out of
         5000 generated per snapshot; C/G/L/D already computed by
         stage6_6_collective_landscape/code/metrics_66.py), each with its own
         boundary node set B, plus snapshots[cond].representative_z (a real,
         already-stored 100-bird heading snapshot for that condition's
         flock), plus illustrative_trajectories with hand-picked,
         already-labeled examples (e.g. "Scattered-but-connected (diagonal
         snake)").

Derivation (explicitly allowed reuse, not new science): Q (clumpness) was
never computed for the 6.6 candidate set -- it is a Stage 6.10 axis
(morphology.py, Part F) applied there only to episode lineages. We apply the
SAME frozen formula (Q_clump = P_min(area) / P_4(I), Harary-Harborth minimum
polyomino perimeter) to the node_ids already stored for each 6.6 candidate.
No candidate, boundary, or metric is regenerated -- only a structural,
already-validated formula is evaluated post hoc on already-frozen node sets.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[2] / "data" / "tab4_landscape.json"

sys.path.insert(0, str(ROOT / "stage6_10_emergence_adaptive_control/code"))
import morphology  # noqa: E402

bundle = json.load(open(ROOT / "interactive_demo/data/collective_landscape_bundle.json"))
L = bundle["lattice"]["L"]

SEEDS = [2, 3, 4]
CONDITIONS = ["no_control", "disordered", "same_direction"]
SAMPLE_STRIDE = 3  # keep every 3rd candidate across 9 (seed,condition) snapshots

rows = []
rep_z = {}  # (seed,condition) -> representative_z, only stored once per snapshot
for seed in SEEDS:
    for cond in CONDITIONS:
        key = f"seed{seed}_{cond}"
        snap = bundle["snapshots"].get(key)
        if snap is None:
            continue
        rep_z[f"{seed}_{cond}"] = snap["representative_z"]
        cols = snap["candidates"]
        n = len(cols["id"])
        for i in range(0, n, SAMPLE_STRIDE):
            node_ids = cols["I"][i]
            rows.append({
                "id": cols["id"][i],
                "seed": seed,
                "condition": cond,
                "src": cols["src"][i],
                "C": cols["C"][i], "G": cols["G"][i], "L": cols["L"][i], "D": cols["D"][i],
                "Q": round(morphology.q_clump(node_ids, L), 4),
                "n": len(node_ids),
                "node_ids": node_ids,
                "boundary_ids": cols["B"][i],
            })

# Curated archetypes: top 3 per category (a spread of representative examples,
# possibly from different seeds/conditions), picked from the real computed
# rows -- no fabricated data, no hand placement.


def pick_n(pred, key, n=3, reverse=True):
    cands = [r for r in rows if pred(r)]
    cands.sort(key=key, reverse=reverse)
    # prefer diversity across (seed,condition) among the top matches
    chosen, seen = [], set()
    for r in cands:
        sk = (r["seed"], r["condition"])
        if sk in seen and len(chosen) < n:
            continue
        chosen.append(r)
        seen.add(sk)
        if len(chosen) >= n:
            break
    return chosen if chosen else cands[:n]


examples = {
    "compact_clump": pick_n(lambda r: r["C"] > 0.6, lambda r: r["Q"]),
    "coherent_but_hollow": pick_n(lambda r: r["C"] > 0.5 and r["G"] > 0.1, lambda r: -r["D"]),
    "snake_like": pick_n(lambda r: r["C"] > 0.4 and r["n"] >= 10, lambda r: -r["Q"]),
    "weak_noisy": pick_n(lambda r: r["n"] >= 6, lambda r: r["C"], reverse=False),
}

# also surface the hand-labeled illustrative trajectory that literally names
# the snake pattern, for the caption / cross-check
labeled_snake = next(
    (t for t in bundle["illustrative_trajectories"] if "snake" in t["label"].lower()), None
)

out = {
    "provenance": {
        "source": "interactive_demo/data/collective_landscape_bundle.json (from stage6_6_collective_landscape, seeds 2/3/4, conditions: no_control / disordered / same_direction)",
        "metrics_code": "stage6_6_collective_landscape/code/metrics_66.py (C_internal, G_internal, L_blanket, D_local)",
        "q_derivation": "morphology.q_clump(node_ids, L) from stage6_10_emergence_adaptive_control/code/morphology.py, applied post hoc to the frozen 6.6 candidate node sets (see module docstring above).",
        "n_candidates_shown": len(rows),
        "n_candidates_full_per_snapshot": 5000,
        "sample_stride": SAMPLE_STRIDE,
        "labeled_snake_trajectory": labeled_snake["label"] if labeled_snake else None,
        "heading_note": "representative_z is a real, already-stored heading snapshot for that condition's underlying flock -- shared by every candidate drawn from the same (seed,condition), not per-candidate (candidates differ only in which nodes are proposed as the interior/boundary, not in a separate simulated heading state).",
    },
    "lattice": bundle["lattice"],
    "rows": rows,
    "representative_z": rep_z,
    "examples": examples,
    "default_axes": {"x": "D", "y": "G"},
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out))
print("wrote", OUT, OUT.stat().st_size, "bytes")
print("examples picked:", {k: [r["id"] for r in v] for k, v in examples.items()})
