"""Stage 6.12 CORRECTION PASS (Part I). Uses ONLY existing Phase A/B/C
rollout data -- no new simulation. Produces NEW derivative files with clear
provenance; never overwrites `data/phaseA_results_612.json` or
`data/phaseBC_results_612.json`.

Terminology correction (see IDENTITY_SEMANTICS_CORRECTION note in
STAGE612_CORRECTION_MEMO.md): `intervention_612.outcome_metrics` labels a
rollout `confirmed_split` whenever `ForwardMaterialTrace611.split_flag`
fired at any point AND strict continuation (`V=1`) held throughout. That
flag is a material-overlap heuristic (Jaccard-based `split_min_share`
gate), never checked against an independently validated PHYSICAL split
criterion -- none exists in this repository
(`CURRENT_RESEARCH_STATUS.md`: "No physical-split/merge threshold has been
validated..."). This script renames it, in NEW output only, to
`material_split_flag` (`material_merge_flag` for merges); genuinely
ambiguous/interrupted cases (`V=0`) already used hedged language
(`candidate_split_or_merge_interruption`) and are left as-is.

Two identity-aware utilities are computed for every rollout:
  J_assoc        = the ORIGINAL V * A_release_late (ForwardMaterialTrace's
                    own continuation semantics; split/merge-flagged
                    continuations still count as valid).
  J_conservative  = V_conservative * A_release_late, where
                    V_conservative additionally requires ZERO split flags,
                    ZERO merge flags, and ZERO unresolved steps anywhere
                    in the traced rollout (t0 through end of release).
                    This is a deliberately conservative LOWER-BOUND
                    sensitivity analysis, not a claim of ground truth.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612 as C   # noqa: E402
import intervention_612 as I  # noqa: E402

PHASE_A_IN = C.DATA_DIR / "phaseA_results_612.json"
PHASE_BC_IN = C.DATA_DIR / "phaseBC_results_612.json"
PHASE_A_OUT = C.DATA_DIR / "phaseA_results_612_corrected.json"
PHASE_BC_OUT = C.DATA_DIR / "phaseBC_results_612_corrected.json"
CORRECTION_SUMMARY_OUT = C.DATA_DIR / "correction_612_summary.json"


def correct_event_label(event: str) -> str:
    return event.replace("confirmed_split", "material_split_flag").replace("confirmed_merge", "material_merge_flag")


def add_conservative_fields(entry: dict) -> dict:
    V = entry["V"]
    vc = 1 if (V == 1 and entry["n_split_flags"] == 0 and entry["n_merge_flags"] == 0
               and entry["n_unresolved_steps"] == 0) else 0
    a = entry.get("A_release_late")
    jc = float(vc * a) if a is not None else 0.0
    entry["V_conservative"] = vc
    entry["J_conservative"] = jc
    entry["event_corrected"] = correct_event_label(entry["event"])
    return entry


def correct_phase_a():
    data = json.load(open(PHASE_A_IN))
    for state_res in data:
        for d in state_res["no_control"]:
            for dk, entry in d.items():
                add_conservative_fields(entry)
        for cell_key, cell in state_res["cells"].items():
            if cell.get("unavailable"):
                continue
            for ro in cell["rollouts"]:
                add_conservative_fields(ro)
                j0c = state_res["no_control"][ro["stream"]][str(cell["d"])]["J_conservative"]
                ro["J0_conservative"] = j0c
                ro["delta_conservative"] = ro["J_conservative"] - j0c
                ro["delta_assoc"] = ro["delta"]  # renamed alias, original field kept too
            # recompute cell-level aggregates under both utilities
            deltas_assoc = [r["delta_assoc"] for r in cell["rollouts"]]
            deltas_cons = [r["delta_conservative"] for r in cell["rollouts"]]
            vc_frac = float(np.mean([r["V_conservative"] for r in cell["rollouts"]]))
            set_means_cons = {}
            for si in range(cell["n_sets"]):
                vals = [r["J_conservative"] for r in cell["rollouts"] if r["set_idx"] == si]
                set_means_cons[si] = float(np.mean(vals)) if vals else None
            cell["G_sus_mean_conservative"] = float(np.mean(deltas_cons))
            cell["G_sus_mean_assoc"] = float(np.mean(deltas_assoc))
            cell["identity_valid_fraction_conservative"] = vc_frac
            cell["between_set_var_conservative"] = (
                float(np.var([v for v in set_means_cons.values() if v is not None], ddof=1))
                if sum(v is not None for v in set_means_cons.values()) > 1 else 0.0)
            cell["n_material_split_flag_rollouts"] = sum(1 for r in cell["rollouts"] if "material_split_flag" in r["event_corrected"])
    json.dump(data, open(PHASE_A_OUT, "w"), indent=1, default=str)
    print("wrote", PHASE_A_OUT)
    return data


def correct_phase_bc():
    if not PHASE_BC_IN.exists():
        return None
    data = json.load(open(PHASE_BC_IN))
    # Phase B/C ran with_mechanism=False so rollouts weren't individually
    # stored -- only per-set mean_J. We recompute V_conservative is NOT
    # possible without per-rollout V/split/merge/unresolved counts, which
    # were not persisted for Phase B/C (see run_phaseBC_612.py -- `vals`
    # only kept mean_J, not the full outcome dict). This is a genuine
    # DATA-AVAILABILITY LIMITATION for Part I's "no new simulation" rule,
    # disclosed here rather than silently worked around.
    data_note = ("Phase B/C (search + holdout confirmation) rollouts did not "
                  "persist per-rollout V/split/merge/unresolved fields "
                  "(run_phaseBC_612.py calls run_one(..., with_mechanism=False) "
                  "and only keeps mean_J per set) -- J_conservative CANNOT be "
                  "reconstructed for Phase B/C from existing data alone. "
                  "holdout_S_star['identity_valid_fraction'] IS available (mean V "
                  "across holdout streams) and is reported as-is; it uses the "
                  "ORIGINAL (non-conservative) V. This is flagged, not silently "
                  "patched -- a genuine limitation of Part I's no-new-simulation "
                  "constraint, resolved instead by Stage 6.12B's fresh rollouts.")
    return dict(note=data_note, phaseBC_raw=data)


def audit_high_response(phase_a_corrected, threshold=0.3):
    # NOTE: the rollout's "J" field IS J_assoc under the original naming
    # (outcome_metrics' J = V * A_release_late, V being the ORIGINAL,
    # non-conservative validity flag) -- used directly below, no renaming
    # of the underlying data needed.
    rows = []
    for state_res in phase_a_corrected:
        for cell_key, cell in state_res["cells"].items():
            if cell.get("unavailable"):
                continue
            for ro in cell["rollouts"]:
                if ro["J"] > threshold:
                    rows.append(dict(
                        state_id=state_res["state_id"], role=state_res["role"], cell=cell_key,
                        S=ro["S"], stream=ro["stream"],
                        J_assoc=ro["J"], J_conservative=ro["J_conservative"],
                        V=ro["V"], V_conservative=ro["V_conservative"],
                        event=ro["event"], event_corrected=ro["event_corrected"],
                        n_split_flags=ro["n_split_flags"], n_merge_flags=ro["n_merge_flags"],
                        n_unresolved_steps=ro["n_unresolved_steps"],
                        A_release_late=ro["A_release_late"],
                        J0=ro["J0"], J0_conservative=ro["J0_conservative"],
                        delta_assoc=ro["delta_assoc"], delta_conservative=ro["delta_conservative"],
                    ))
    return rows


def pooled_and_clustered(phase_a_corrected):
    # pooled (naive, all rollouts as independent) -- reported ALONGSIDE the
    # state-clustered version, never as the sole estimate, per S9's
    # instruction to mark an unclustered CI invalid if that's all there was.
    all_assoc, all_cons = [], []
    per_state_assoc, per_state_cons = {}, {}
    per_state_role = {}
    for state_res in phase_a_corrected:
        sid = state_res["state_id"]
        per_state_role[sid] = state_res["role"]
        sa, sc = [], []
        for cell_key, cell in state_res["cells"].items():
            if cell.get("unavailable"):
                continue
            for ro in cell["rollouts"]:
                all_assoc.append(ro["delta_assoc"]); all_cons.append(ro["delta_conservative"])
                sa.append(ro["delta_assoc"]); sc.append(ro["delta_conservative"])
        per_state_assoc[sid] = float(np.mean(sa))
        per_state_cons[sid] = float(np.mean(sc))

    def naive_ci(vals, n_boot=3000, seed=1):
        vals = np.asarray(vals)
        rng = np.random.default_rng(seed)
        means = [rng.choice(vals, size=len(vals), replace=True).mean() for _ in range(n_boot)]
        return float(np.percentile(means, 5)), float(np.percentile(means, 95))

    def state_clustered_ci(state_means: dict, n_boot=3000, seed=2):
        vals = np.array(list(state_means.values()))
        rng = np.random.default_rng(seed)
        means = [rng.choice(vals, size=len(vals), replace=True).mean() for _ in range(n_boot)]
        return float(np.percentile(means, 5)), float(np.percentile(means, 95))

    naive_assoc_ci = naive_ci(all_assoc)
    naive_cons_ci = naive_ci(all_cons)
    clustered_assoc_ci = state_clustered_ci(per_state_assoc)
    clustered_cons_ci = state_clustered_ci(per_state_cons)

    return dict(
        n_rollouts=len(all_assoc), n_states=len(per_state_assoc),
        pooled_mean_assoc=float(np.mean(all_assoc)), pooled_mean_conservative=float(np.mean(all_cons)),
        naive_unclustered_ci90_assoc=list(naive_assoc_ci), naive_unclustered_ci90_conservative=list(naive_cons_ci),
        state_clustered_ci90_assoc=list(clustered_assoc_ci), state_clustered_ci90_conservative=list(clustered_cons_ci),
        per_state_mean_delta_assoc=per_state_assoc, per_state_mean_delta_conservative=per_state_cons,
        per_state_role=per_state_role,
    )


def budget_level(phase_a_corrected):
    by_budget = {}
    for K in I.K_GRID:
        for d in I.D_GRID:
            key = f"K{K}_d{d}"
            assoc_vals, cons_vals = [], []
            for state_res in phase_a_corrected:
                cell = state_res["cells"].get(key)
                if not cell or cell.get("unavailable"):
                    continue
                assoc_vals.append(cell["G_sus_mean_assoc"])
                cons_vals.append(cell["G_sus_mean_conservative"])
            by_budget[key] = dict(K=K, d=d, n_states=len(assoc_vals),
                                   mean_G_sus_assoc=float(np.mean(assoc_vals)) if assoc_vals else None,
                                   mean_G_sus_conservative=float(np.mean(cons_vals)) if cons_vals else None)
    return by_budget


def paired_effect_vs_mechanism(phase_a_corrected):
    """S8: continuous relationship between PRE-forcing-defined DeltaJ and
    POST-treatment mechanism correlates (explicitly labelled as such, never
    causal). Uses Spearman-style rank correlation (dependency-free
    implementation) plus a top/bottom-quartile contrast, per instruction to
    avoid a new arbitrary absolute threshold."""
    rows = []
    for state_res in phase_a_corrected:
        for cell_key, cell in state_res["cells"].items():
            if cell.get("unavailable"):
                continue
            for ro in cell["rollouts"]:
                if ro.get("mech_direct_contacts_t0") is None:
                    continue
                rows.append(ro)

    def spearman(x, y):
        x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
        rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
        if rx.std() == 0 or ry.std() == 0:
            return None
        return float(np.corrcoef(rx, ry)[0, 1])

    mech_keys = ["mech_direct_contacts_t0", "mech_cumulative_contact_edges",
                 "mech_unique_target_coverage", "mech_mean_actuator_target_dist",
                 "mech_actuators_entered_target"]
    corrs = {}
    for mk in mech_keys:
        vals = [r[mk] for r in rows if r[mk] is not None]
        dassoc = [r["delta_assoc"] for r in rows if r[mk] is not None]
        dcons = [r["delta_conservative"] for r in rows if r[mk] is not None]
        corrs[mk] = dict(n=len(vals), spearman_vs_delta_assoc=spearman(vals, dassoc),
                          spearman_vs_delta_conservative=spearman(vals, dcons))

    # top vs bottom quartile of delta_assoc
    d_assoc_all = np.array([r["delta_assoc"] for r in rows])
    q75, q25 = np.percentile(d_assoc_all, [75, 25])
    top = [r for r in rows if r["delta_assoc"] >= q75]
    bot = [r for r in rows if r["delta_assoc"] <= q25]
    quartile_table = {}
    for mk in mech_keys:
        tv = [r[mk] for r in top if r[mk] is not None]
        bv = [r[mk] for r in bot if r[mk] is not None]
        quartile_table[mk] = dict(top_quartile_mean=float(np.mean(tv)) if tv else None,
                                   bottom_quartile_mean=float(np.mean(bv)) if bv else None,
                                   n_top=len(tv), n_bottom=len(bv))

    # restrict to clean (no split/merge flag at all) rollouts and repeat
    clean = [r for r in rows if r["n_split_flags"] == 0 and r["n_merge_flags"] == 0]
    corrs_clean = {}
    for mk in mech_keys:
        vals = [r[mk] for r in clean if r[mk] is not None]
        dassoc = [r["delta_assoc"] for r in clean if r[mk] is not None]
        corrs_clean[mk] = dict(n=len(vals), spearman_vs_delta_assoc=spearman(vals, dassoc))

    return dict(n_rollouts_with_mechanism=len(rows), correlations_all=corrs,
                quartile_contrast=quartile_table, n_top=len(top), n_bottom=len(bot),
                correlations_clean_no_split_merge=corrs_clean, n_clean=len(clean))


def main():
    phase_a = correct_phase_a()
    phase_bc = correct_phase_bc()
    audit34 = audit_high_response(phase_a, threshold=0.3)
    pooled = pooled_and_clustered(phase_a)
    budget = budget_level(phase_a)
    mech = paired_effect_vs_mechanism(phase_a)

    summary = dict(
        pooled_and_clustered=pooled, budget_level=budget,
        high_response_audit_threshold=0.3, high_response_rows=audit34,
        n_high_response=len(audit34),
        paired_effect_vs_mechanism=mech,
        phase_bc_note=(phase_bc["note"] if phase_bc else "phaseBC_results_612.json not found"),
    )
    json.dump(summary, open(CORRECTION_SUMMARY_OUT, "w"), indent=1, default=str)
    if phase_bc:
        json.dump(dict(note=phase_bc["note"]), open(PHASE_BC_OUT, "w"), indent=1)
    print("wrote", CORRECTION_SUMMARY_OUT)
    print(json.dumps({k: v for k, v in pooled.items() if k not in
                       ("per_state_mean_delta_assoc", "per_state_mean_delta_conservative")}, indent=1))


if __name__ == "__main__":
    main()
