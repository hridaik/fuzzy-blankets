"""Shapes Stage 6.7's scientific outputs into a compact bundle for the
interactive demo: interactive_demo/data/stage6_7_bundle.json. Own exporter,
own bundle file, mirroring stage6_6_collective_landscape/code/
export_demo_data.py's "each pipeline owns one file" convention (see
STAGE6_6_VISUALIZATION_NOTES.md Part 1) -- inlined via its own 5th
placeholder in app/build.py, never merged into another stage's JSON tree.

Only the 300-candidate primary panel is embedded (no subsampling needed --
300 is already small enough to inline directly, unlike Stage 6.6's
5000/snapshot landscape).
"""
from __future__ import annotations

import json
from pathlib import Path

STAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = STAGE_DIR / "data"
DEMO_DATA_DIR = STAGE_DIR.parent / "interactive_demo" / "data"


def load(name):
    return json.loads((DATA_DIR / name).read_text())


def main():
    oracle = load("oracle_validation_panel.json")["rows"]
    blind = {r["candidate_id"]: r for r in load("blind_landscape_panel.json")["rows"]}
    causal = load("causal_discovery_panel.json")["results"]

    by_id = {}
    for r in oracle:
        cid = r["candidate_id"]
        bl = blind.get(cid, {})
        by_id[cid] = dict(
            id=cid, seed=r["seed"], condition=r["condition"], label=r["label"],
            I=r["I"], B_pred=r["B_hat_pred"], B_causal=r["B_hat_causal"] or [], B_D=r["B_D"],
            excess_loss=round(r["excess_loss_test"], 6), predictively_sufficient=r["predictively_sufficient"],
            predictive_jaccard=round(r["predictive_jaccard"], 4),
            causal_jaccard=round(r["causal_jaccard"], 4) if r["causal_jaccard"] is not None else None,
            outcome=r["outcome"], overlap=r["overlap"],
            C=round(r["C_internal"], 5), D=round(r["D_local"], 5),
            G_oracle=round(r["G_internal"], 6), L_oracle=round(r["L_blanket"], 6),
            G_blind=round(bl.get("G_blind", float("nan")), 6) if bl else None,
            L_blind=round(bl.get("L_blind", float("nan")), 6) if bl else None,
        )

    snapshots = {}
    for r in oracle:
        key = f"seed{r['seed']}_{r['condition']}"
        snapshots.setdefault(key, dict(seed=r["seed"], condition=r["condition"], candidates=[]))
        snapshots[key]["candidates"].append(by_id[r["candidate_id"]])

    outcome_counts = load("oracle_validation_panel.json")["outcome_counts"]
    sample_eff = load("sample_efficiency.json")

    bundle = dict(
        snapshots=snapshots, outcome_counts=outcome_counts,
        sample_efficiency=dict(r_grid=sample_eff["r_grid"], rows=sample_eff["rows"]),
        delta_pred=load("oracle_validation_panel.json")["delta_pred"],
    )

    DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DEMO_DATA_DIR / "stage6_7_bundle.json"
    out_path.write_text(json.dumps(bundle, separators=(",", ":")))
    print(f"wrote {out_path} ({out_path.stat().st_size/1024:.0f} KB), {len(snapshots)} snapshots, "
          f"{len(by_id)} candidates")


if __name__ == "__main__":
    main()
