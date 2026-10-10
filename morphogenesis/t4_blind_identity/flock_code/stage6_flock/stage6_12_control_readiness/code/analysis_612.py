"""Stage 6.12 aggregate analysis: readiness classification, between-set
variance decomposition, selectivity summary, identity/disruption summary,
mechanism-vs-outcome exploratory correlation, collateral summary. Reads
Phase A / Phase B-C / pool-sensitivity JSON, writes a single
analysis_summary_612.json plus a few CSV-ish text tables for the docs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612 as C   # noqa: E402
import intervention_612 as I  # noqa: E402


def bootstrap_ci(vals, n_boot=2000, alpha=0.10, seed=1):
    vals = np.asarray([v for v in vals if v is not None], dtype=float)
    if len(vals) == 0:
        return (None, None)
    rng = np.random.default_rng(seed)
    means = [rng.choice(vals, size=len(vals), replace=True).mean() for _ in range(n_boot)]
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def classify_cell(cell):
    if cell.get("unavailable"):
        return "unavailable"
    g = cell["G_sus_mean"]
    var = cell["between_set_var"]
    # heuristic thresholds, predeclared: "positive" = mean delta clears a
    # small floor relative to observed within-set noise; "selective" =
    # between-set variance is a non-trivial fraction of squared mean effect
    # or of within-set variance -- continuous evidence is reported alongside
    # this label, never in place of it (S15).
    generically_susceptible = g is not None and g > 0.03
    within = cell.get("within_set_var") or 0.0
    selective_signal = var > max(0.005, 0.5 * within)
    if not generically_susceptible and not selective_signal:
        return "no_demonstrated_response"
    if generically_susceptible and not selective_signal:
        return "generically_susceptible"
    if selective_signal:
        return "possible_selectivity_signal_dev_only"
    return "ambiguous"


def main():
    phaseA = json.load(open(C.DATA_DIR / "phaseA_results_612.json"))
    phaseBC_path = C.DATA_DIR / "phaseBC_results_612.json"
    phaseBC = json.load(open(phaseBC_path)) if phaseBC_path.exists() else []
    pool_path = C.DATA_DIR / "pool_sensitivity_612.json"
    pool_sens = json.load(open(pool_path)) if pool_path.exists() else []

    readiness_rows = []
    for state_res in phaseA:
        for cell_key, cell in state_res["cells"].items():
            label = classify_cell(cell)
            readiness_rows.append(dict(
                state_id=state_res["state_id"], role=state_res["role"], cell=cell_key,
                K=cell.get("K"), d=cell.get("d"), unavailable=cell.get("unavailable", False),
                G_sus_mean=cell.get("G_sus_mean"), G_sus_median=cell.get("G_sus_median"),
                identity_valid_fraction=cell.get("identity_valid_fraction"),
                between_set_var=cell.get("between_set_var"), within_set_var=cell.get("within_set_var"),
                frac_sets_positive_mean=cell.get("frac_sets_positive_mean"),
                label=label,
            ))

    # generic susceptibility: does typical random forcing move valid flocks at all?
    all_g = [r["G_sus_mean"] for r in readiness_rows if not r["unavailable"] and r["G_sus_mean"] is not None]
    g_lo, g_hi = bootstrap_ci(all_g)

    # by-K,d aggregate (across all states) for the budget-progression question
    by_budget = {}
    for K in I.K_GRID:
        for d in I.D_GRID:
            key = f"K{K}_d{d}"
            vals = [r["G_sus_mean"] for r in readiness_rows if r["cell"] == key and not r["unavailable"]]
            varvals = [r["between_set_var"] for r in readiness_rows if r["cell"] == key and not r["unavailable"]]
            ivf = [r["identity_valid_fraction"] for r in readiness_rows if r["cell"] == key and not r["unavailable"]]
            by_budget[key] = dict(K=K, d=d, n_states=len(vals),
                                    mean_G_sus=float(np.mean(vals)) if vals else None,
                                    mean_between_set_var=float(np.mean(varvals)) if varvals else None,
                                    mean_identity_valid_fraction=float(np.mean(ivf)) if ivf else None)

    label_counts = {}
    for r in readiness_rows:
        label_counts[r["label"]] = label_counts.get(r["label"], 0) + 1

    # Phase B/C: selectivity confirmed on holdout?
    sel_rows = []
    for res in phaseBC:
        if res.get("unavailable"):
            continue
        sel_rows.append(dict(
            state_id=res["state_id"], role=res["role"], G_sel=res["G_sel"],
            S_star_holdout_mean_J=res["holdout_S_star"]["mean_J"],
            holdout_random_median_of_means=res["holdout_random_median_of_means"],
            holdout_no_control_mean_J=res["holdout_no_control_mean_J"],
            S_star_holdout_identity_valid_fraction=res["holdout_S_star"]["identity_valid_fraction"],
        ))
    dev_g_sel = [r["G_sel"] for r in sel_rows if r["role"] == "development" and r["G_sel"] is not None]
    holdout_g_sel = [r["G_sel"] for r in sel_rows if r["role"] == "holdout" and r["G_sel"] is not None]

    summary = dict(
        n_states=len(phaseA), n_cells_per_state=len(I.K_GRID) * len(I.D_GRID),
        overall_G_sus_mean=float(np.mean(all_g)) if all_g else None,
        overall_G_sus_ci90=[g_lo, g_hi],
        readiness_label_counts=label_counts,
        by_budget=by_budget,
        selectivity_dev=dict(n=len(dev_g_sel), mean=float(np.mean(dev_g_sel)) if dev_g_sel else None,
                              median=float(np.median(dev_g_sel)) if dev_g_sel else None,
                              frac_positive=float(np.mean([v > 0 for v in dev_g_sel])) if dev_g_sel else None),
        selectivity_holdout=dict(n=len(holdout_g_sel), mean=float(np.mean(holdout_g_sel)) if holdout_g_sel else None,
                                  median=float(np.median(holdout_g_sel)) if holdout_g_sel else None,
                                  frac_positive=float(np.mean([v > 0 for v in holdout_g_sel])) if holdout_g_sel else None),
        sel_rows=sel_rows,
        pool_sensitivity=pool_sens,
    )
    json.dump(dict(readiness_rows=readiness_rows, summary=summary),
              open(C.DATA_DIR / "analysis_summary_612.json", "w"), indent=1)
    print(json.dumps(summary, indent=1)[:4000])
    print("wrote", C.DATA_DIR / "analysis_summary_612.json")


if __name__ == "__main__":
    main()
