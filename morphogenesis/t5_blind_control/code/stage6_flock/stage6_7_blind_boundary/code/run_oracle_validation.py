"""Driver for oracle_validation.py -- task brief section 9. Runs STRICTLY
AFTER data/predictive_boundary_panel.json and data/causal_discovery_panel.json
already exist (every Bhat^pred/Bhat^causal decision frozen). This is the
first and only point in the pipeline where the true Moore-neighbour graph is
revealed, for every one of the 300 primary candidates. Also applies the
section-10 four-outcome classification (A/B/C/D) per candidate.
"""
from __future__ import annotations

import json

import numpy as np

from common_67 import lattice_100, dump_json, DATA_DIR, snapshot_key, CONDITIONS, PRIMARY_SEEDS_67, DELTA_PRED
from oracle_validation import validate_candidate, classify_outcome


def load(name):
    return json.loads((DATA_DIR / name).read_text())


def main():
    lattice = lattice_100()
    pred_data = load("predictive_boundary_panel.json")["results"]
    causal_data = load("causal_discovery_panel.json")["results"]

    rows = []
    for seed in PRIMARY_SEEDS_67:
        for condition in CONDITIONS:
            key = snapshot_key(seed, condition)
            pred_by_id = {c["candidate_id"]: c for c in pred_data[key]["candidates"]}
            causal_by_id = {c["candidate_id"]: c for c in causal_data[key]["candidates"]}
            for cid, pc in pred_by_id.items():
                cc = causal_by_id.get(cid)
                val = validate_candidate(pc["I"], pc["B_hat_pred"], cc["B_hat_causal"] if cc else None,
                                          n_bird=100, lattice=lattice)
                outcome = classify_outcome(pc["excess_loss_test"], val["predictive"]["jaccard"],
                                            delta_pred=DELTA_PRED)
                rows.append(dict(
                    seed=seed, condition=condition, candidate_id=cid, label=pc["label"], I=pc["I"],
                    B_hat_pred=pc["B_hat_pred"], B_hat_causal=cc["B_hat_causal"] if cc else None,
                    B_D=val["B_D"], excess_loss_test=pc["excess_loss_test"],
                    predictively_sufficient=pc["predictively_sufficient"],
                    predictive_precision=val["predictive"]["precision"], predictive_recall=val["predictive"]["recall"],
                    predictive_jaccard=val["predictive"]["jaccard"],
                    causal_precision=val.get("causal", {}).get("precision"),
                    causal_recall=val.get("causal", {}).get("recall"),
                    causal_jaccard=val.get("causal", {}).get("jaccard"),
                    overlap=val.get("overlap"), outcome=outcome,
                    C_internal=pc["C_internal"], G_internal=pc["G_internal"],
                    L_blanket=pc["L_blanket"], D_local=pc["D_local"],
                    structural_shell_size=pc["structural_shell_size"],
                    boundary_size=pc["boundary_size"], S_pred_size=pc["S_pred_size"],
                ))
            print(f"[{key}] validated {len(pred_by_id)} candidates")

    outcome_counts = {}
    for r in rows:
        outcome_counts[r["outcome"]] = outcome_counts.get(r["outcome"], 0) + 1

    dump_json(dict(rows=rows, n_total=len(rows), outcome_counts=outcome_counts, delta_pred=DELTA_PRED),
              DATA_DIR / "oracle_validation_panel.json")
    print(f"wrote data/oracle_validation_panel.json ({len(rows)} candidates)")
    print("outcome counts:", outcome_counts)
    print("mean predictive jaccard:", np.mean([r["predictive_jaccard"] for r in rows]))
    print("mean causal jaccard:", np.mean([r["causal_jaccard"] for r in rows if r["causal_jaccard"] is not None]))
    print("frac predictively sufficient:", np.mean([r["predictively_sufficient"] for r in rows]))


if __name__ == "__main__":
    main()
