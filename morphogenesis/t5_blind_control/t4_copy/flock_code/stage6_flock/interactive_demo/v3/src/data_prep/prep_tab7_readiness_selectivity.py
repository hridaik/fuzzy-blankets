"""v3 tab7 data prep: Stage 6.12 control-readiness map + Stage 6.12C
winner's-curse / stable-selectivity audit. Pure re-export of already-frozen
upstream JSON -- no new statistics computed here (v2's stated philosophy,
carried forward)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
S612 = ROOT / "stage6_12_control_readiness" / "data" / "analysis_summary_612.json"
SSA = ROOT / "stage6_12C_kinematic_contact_confirmation" / "stable_selectivity_analysis" / "data" / "stable_selectivity_results.json"
K1C = ROOT / "stage6_12C_kinematic_contact_confirmation" / "data" / "k1_candidates_612c.json"
OUT = Path(__file__).resolve().parents[2] / "data" / "tab7_readiness_selectivity.json"


def main():
    s612 = json.load(open(S612))
    ssa = json.load(open(SSA))
    k1c = json.load(open(K1C))

    summary = s612["summary"]
    readiness = dict(
        n_states=summary["n_states"], overall_G_sus_mean=summary["overall_G_sus_mean"],
        overall_G_sus_ci90=summary["overall_G_sus_ci90"],
        readiness_label_counts=summary["readiness_label_counts"],
        by_budget=summary["by_budget"],
        selectivity_dev=summary["selectivity_dev"], selectivity_holdout=summary["selectivity_holdout"],
    )

    three = ssa["three_oracles"]["full_12stream"]["per_state"]
    perm = ssa["permutation_null"]["full_12stream"]["per_state"]
    oracle_states = []
    for sid in sorted(three.keys()):
        o = three[sid]
        p = perm[sid]
        oracle_states.append(dict(
            state_id=sid, random_median=o["random_median"],
            A_clairvoyant=o["A_per_stream_clairvoyant_oracle"], B_state_stable=o["B_state_stable_mean_oracle"],
            C_cross_validated=o["C_cross_validated_stable_oracle"],
            excess_B=p["excess_B"], null_B_ci90=p["null_B"]["ci90"],
        ))
    var = ssa["variance_decomposition"]["confirm_only"]["per_state"]
    var_states = [dict(state_id=sid, var_actuator_frac=v["var_actuator_frac"],
                        var_stream_frac=v["var_stream_frac"], var_residual_frac=v["var_residual_frac"])
                  for sid, v in sorted(var.items())]

    # heatmap: one representative state's 20 candidates x 8 confirm streams
    target_state = "s612c_02_seed63202"  # highest apparent oracle in three_oracles, good illustrative case
    rows = [r for r in k1c if r["state_id"] == target_state]
    rows.sort(key=lambda r: -sum(r["confirm_delta_conservative_all"]) / len(r["confirm_delta_conservative_all"]))
    heatmap = dict(state_id=target_state, candidates=[r["candidate"] for r in rows],
                   matrix=[r["confirm_delta_conservative_all"] for r in rows],
                   per_candidate_mean=[float(sum(r["confirm_delta_conservative_all"]) / len(r["confirm_delta_conservative_all"])) for r in rows])

    out = dict(readiness=readiness, oracle_states=oracle_states, variance_states=var_states, heatmap=heatmap,
               provenance=dict(
                   readiness_source=str(S612.relative_to(ROOT)), selectivity_source=str(SSA.relative_to(ROOT)),
                   heatmap_source=str(K1C.relative_to(ROOT)),
                   note="Pooled null hides state heterogeneity: overall_G_sus_ci90 spans zero while per-state "
                        "cells vary widely (see stage6_12_control_readiness/README.md). B (state-stable-mean) "
                        "oracle excess vs its own permutation null is at/below zero in every state shown -- "
                        "not evidence of reproducible actuator selectivity."))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
