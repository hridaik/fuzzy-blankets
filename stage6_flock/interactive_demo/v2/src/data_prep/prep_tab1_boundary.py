"""Build interactive_demo/v2/data/tab1_boundary.json.

Pure re-export: every number here already exists in a frozen result file.
No simulation, no refitting, no new statistics.

Sources:
  interactive_demo/data/seed2__no_control__cw.json
      -- lattice, headings trajectory, roles.core (= interior I0),
         roles.dynamic_shell (= B^D), roles.fiedler (= B^F), timeline.identify
  stage6_7_blind_boundary/data/predictive_boundary_panel.json
      -- results["seed2_no_control"].candidates[0] ("established_I0"):
         B_hat_pred (= B^pred for this exact flock) and the full 20-candidate
         boundary_size / excess_loss_test scatter for the SAME flock. Each of
         the 20 candidates is itself a DIFFERENT proposed interior I (from a
         real candidate-generation method -- highest_C, highest_G, highest_D,
         lowest_L, diagonal_snake_pathology, etc.) with its own fitted
         predictive boundary B_hat_pred -- both are exported per candidate so
         the demo can show, not just plot, what each point on the scatter is.
  stage6_5/boundary_inference/data/held_out_evaluation.json
      -- the actual generalization test: excess log-loss of B_hat / B_D / B_F /
         random-matched boundaries, evaluated on 3 held-out seeds (17, 18, 20)
  v1_mechanism_audit/data/predictive_screening.json
      -- headline mean log-loss numbers (full exterior vs B^D vs B^F)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[2] / "data" / "tab1_boundary.json"

seed2 = json.load(open(ROOT / "interactive_demo/data/seed2__no_control__cw.json"))
panel = json.load(open(ROOT / "stage6_7_blind_boundary/data/predictive_boundary_panel.json"))
held_out = json.load(open(ROOT / "stage6_5/boundary_inference/data/held_out_evaluation.json"))
screen = json.load(open(ROOT / "v1_mechanism_audit/data/predictive_screening.json"))

snap = panel["results"]["seed2_no_control"]
established = next(c for c in snap["candidates"] if c["label"] == "established_I0")
assert established["I"] == seed2["roles"]["core"], "I0 mismatch between seed2 bundle and 6.7 panel"

candidates = [
    {
        "id": c["candidate_id"].split("__c")[-1],
        "label": c["label"],
        "boundary_size": c["boundary_size"],
        "excess_loss_test": c["excess_loss_test"],
        "C": c["C_internal"], "G": c["G_internal"], "L": c["L_blanket"], "D": c["D_local"],
        "I": c["I"], "B_hat_pred": c["B_hat_pred"],
    }
    for c in snap["candidates"]
]

held_out_seeds = held_out["seeds"]
held_out_rows = [
    {"seed": s, **r["excess_loss"], "size_hat": r["recovery_vs_BD"]["size_hat"],
     "size_true": r["recovery_vs_BD"]["size_true"]}
    for s, r in zip(held_out_seeds, held_out["results"])
]
mean_excess = {
    k: sum(r[k] for r in held_out_rows) / len(held_out_rows)
    for k in ("B_hat", "B_D", "B_F", "random_matched_mean")
}

out = {
    "provenance": {
        "trajectory_source": "interactive_demo/data/seed2__no_control__cw.json (seed 2, no_control, V3 protocol)",
        "predictive_boundary_source": "stage6_7_blind_boundary/data/predictive_boundary_panel.json, results.seed2_no_control, candidate established_I0",
        "generalization_source": "stage6_5/boundary_inference/data/held_out_evaluation.json, held-out seeds 17/18/20",
        "screening_headline_source": "v1_mechanism_audit/data/predictive_screening.json",
        "note": "The lattice/trajectory shown is one illustrative flock (seed 2). Generalization statistics (right-hand bars) are computed on 3 different held-out seeds never used to tune the selection rule -- shown separately, not overlaid on this flock, because that is the actual scientific test.",
    },
    "lattice": seed2["lattice"],
    "neighbors": seed2["neighbors"],
    "timeline": {"start": 0, "identify": seed2["timeline"]["identify"]},
    "headings": seed2["trajectory"],
    "roles": {
        "interior": seed2["roles"]["core"],
        "dynamical_shell": seed2["roles"]["dynamic_shell"],
        "fiedler": seed2["roles"]["fiedler"],
        "predictive": established["B_hat_pred"],
    },
    "screening": {
        "delta_pred": panel["delta_pred"],
        "min_gain": panel["min_gain"],
        "candidates": candidates,
        "reference_sizes": {
            "dynamical_shell": len(seed2["roles"]["dynamic_shell"]),
            "fiedler": len(seed2["roles"]["fiedler"]),
            "predictive": len(established["B_hat_pred"]),
        },
    },
    "generalization": {
        "held_out_seeds": held_out_seeds,
        "per_seed": held_out_rows,
        "mean_excess_loss": mean_excess,
        "shortlist_k": held_out["shortlist_k"],
        "delta_tol_frac": held_out["delta_tol_frac"],
    },
    "headline": {
        "mean_logloss_full": screen["mean_logloss_full"],
        "mean_logloss_BD": screen["mean_logloss_BD"],
        "mean_logloss_BF": screen["mean_logloss_BF"],
        "interpretation": screen["interpretation"],
    },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out))
print("wrote", OUT, OUT.stat().st_size, "bytes")
