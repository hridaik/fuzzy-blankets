"""Exports a compact JSON bundle of Stage 6.5 + Stage 6.5-refinement results
for the interactive demo's "Inference & Identity" mode. Reads ONLY already-
saved data/*.json files under stage6_5/ and stage6_5/refinement/ -- computes
nothing, runs no simulation. Sibling to export_scenarios.py, same
conventions (one flat JSON written to this directory, inlined by
app/build.py at build time).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # stage6_flock/
BI_DATA = ROOT / "stage6_5" / "boundary_inference" / "data"
CR_DATA = ROOT / "stage6_5" / "refinement" / "causal_redundancy" / "data"
CG_DATA = ROOT / "stage6_5" / "refinement" / "control_generalization" / "data"
IS_DATA = ROOT / "stage6_5" / "refinement" / "identity_stability" / "data"
OUT_PATH = Path(__file__).resolve().parent / "refinement_bundle.json"


def load(path):
    return json.loads(path.read_text())


def build_boundary_inference():
    boot = load(BI_DATA / "bootstrap_membership.json")
    held_out = load(BI_DATA / "held_out_evaluation.json")
    sample_eff = load(BI_DATA / "sample_efficiency.json")

    membership = {int(k): v for k, v in boot["membership"].items()}
    exterior = sorted(j for j in range(100) if j not in set(boot["I0"]))
    return dict(
        canonical=dict(
            seed=boot["seed"], I0=boot["I0"], B_D=boot["B_D"], B_hat=boot["B_hat_point_estimate"],
            exterior=exterior, membership=[membership.get(j, 0.0) for j in exterior], n_boot=boot["n_boot"],
        ),
        held_out=[dict(
            seed=r["seed"], B_D=r["B_D"], B_hat=r["B_hat"],
            precision=r["recovery_vs_BD"]["precision"], recall=r["recovery_vs_BD"]["recall"],
            excess_loss=r["excess_loss"],
        ) for r in held_out["results"]],
        sample_efficiency=dict(
            seed=sample_eff["seed"],
            rows=[dict(n_traj=row["n_traj"], jaccard=row["jaccard"], size_hat=row["size_hat"],
                       excess_loss=row["excess_loss_B_hat"]) for row in sample_eff["rows"]],
        ),
    )


def build_causal_redundancy():
    d = load(CR_DATA / "causal_redundancy.json")
    out = {}
    for seed, res in d["results"].items():
        pooled = res["pooled_class_distribution"]
        shift = res["delta_shift_by_class"]
        shift_means = {cls: (sum(v["B_hat"] for v in vals.values()) / len(vals)) if vals else 0.0
                       for cls, vals in shift.items()}
        out[seed] = dict(
            n_I0=res["n_I0"], classes=res["classes"],
            pooled_class_distribution=pooled,
            mean_delta_shift_B_hat=shift_means,
            excess_loss_natural=res["natural_exact"]["excess"],
        )
    return out


def build_control_generalization():
    disc = load(CG_DATA / "discriminating_flocks.json")
    fcc = load(CG_DATA / "four_controller_comparison.json")
    agg = load(CG_DATA / "aggregate_summary.json")
    rows = [dict(
        seed=r["seed"], n_B_D=len(r["B_D"]), n_B_hat=len(r["B_hat"]), recall=r["recall_B_hat"],
        oracle=dict(k=r["oracle"]["n_actuators"], p=r["oracle"]["p_success"]),
        inferred=dict(k=r["inferred"]["n_actuators"], p=r["inferred"]["p_success"]),
        fiedler=dict(k=r["fiedler"]["n_actuators"], p=r["fiedler"]["p_success"]),
        random_matched=dict(k=r["random_matched"]["n_actuators"], p=r["random_matched"]["p_success"]),
    ) for r in fcc["rows"]]
    return dict(
        n_scanned=disc["n_seeds_scanned"], n_qualifying=disc["n_qualifying_flocks_scanned"],
        n_discriminating=disc["n_discriminating"], scan_range=[disc["scan_start"], disc["scan_end_inclusive"]],
        rows=rows, summary=agg["summary"],
    )


def build_identity_stability():
    jitter = load(IS_DATA / "jitter_analysis.json")
    rep_cmp = load(IS_DATA / "representation_comparison.json")
    closed_loop = load(IS_DATA / "closed_loop_stabilized.json")
    envelope = load(IS_DATA / "validity_envelope.json")
    calib = load(IS_DATA / "regularized_lineage_calibration.json")

    jitter_summary = {seed: dict(corr=r["pearson_corr_DX_TI"], n_low_DX_high_TI=r["n_low_DX_high_TI"],
                                  n_steps=r["n_steps"]) for seed, r in jitter.items()}
    rep_summary = []
    for flock in rep_cmp["results"]:
        row = dict(seed=flock["seed"])
        for name in ("M", "L", "L_reg", "F", "F_guard"):
            eps = [e[name] for e in flock["episodes"]]
            row[name] = dict(
                p_success=sum(e["success"] for e in eps) / len(eps),
                mean_final_size=sum(e["final_size"] for e in eps) / len(eps),
            )
        rep_summary.append(row)

    return dict(
        jitter=jitter_summary,
        lambda_T_chosen=calib["chosen_lambda_T"], lambda_T_fallback_reason=calib.get("fallback_reason"),
        envelope=dict(L_reg=envelope["L_reg"], F=envelope["F"]),
        representation_comparison=rep_summary,
        closed_loop=[dict(seed=r["seed"], summary=r["summary"], pathwise=r["pathwise"]) for r in closed_loop["results"]],
    )


def main():
    bundle = dict(
        boundary_inference=build_boundary_inference(),
        causal_redundancy=build_causal_redundancy(),
        control_generalization=build_control_generalization(),
        identity_stability=build_identity_stability(),
    )
    OUT_PATH.write_text(json.dumps(bundle, separators=(",", ":")))
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
