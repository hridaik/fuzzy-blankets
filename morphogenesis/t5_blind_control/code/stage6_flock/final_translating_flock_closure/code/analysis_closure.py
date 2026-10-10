"""Closure A/B/C statistical analysis. State is the independent
generalization unit throughout -- rollouts within a (state, actuator) are
NOT pooled as independent evidence; every summary aggregates to
one-row-per-state before combining across states (state-paired /
state-clustered).

No after-the-fact per-stream/per-actuator maxima are used as evidence of
selectivity anywhere in this file (winner's-curse lesson from
stable_selectivity_analysis/, explicitly carried forward).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_closure as C  # noqa: E402


def load(name):
    return json.load(open(C.DATA_DIR / name))


def boot_ci(vals, n_boot=4000, seed=7, alpha=0.10):
    vals = np.asarray(vals, dtype=float)
    if len(vals) == 0:
        return dict(mean=None, lo=None, hi=None, n=0)
    rng = np.random.default_rng(seed)
    boots = [rng.choice(vals, size=len(vals), replace=True).mean() for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return dict(mean=float(vals.mean()), lo=float(lo), hi=float(hi), n=int(len(vals)))


def state_paired_class_means(rollouts, class_field="actuator_class", value_field="delta_J_conservative"):
    """One row per (state, class): mean over ALL rollouts of ALL actuators
    sampled in that class in that state (state x class is the aggregation
    unit -- avoids pooling raw rollouts across states as independent)."""
    by_sc = {}
    for r in rollouts:
        key = (r["state_id"], r[class_field])
        by_sc.setdefault(key, []).append(r[value_field])
    rows = []
    for (sid, cls), vals in by_sc.items():
        rows.append(dict(state_id=sid, actuator_class=cls, mean=float(np.mean(vals)), n_rollouts=len(vals)))
    return rows


def class_level_summary(rollouts):
    state_class_rows = state_paired_class_means(rollouts)
    state_class_rows_mj = state_paired_class_means(rollouts, value_field="delta_J_conservative_minus_j")
    by_class = {}
    by_class_mj = {}
    for row in state_class_rows:
        by_class.setdefault(row["actuator_class"], []).append(row["mean"])
    for row in state_class_rows_mj:
        by_class_mj.setdefault(row["actuator_class"], []).append(row["mean"])
    out = {}
    for cls, vals in by_class.items():
        out[cls] = dict(state_paired=boot_ci(vals), n_states_with_class=len(vals))
    out_mj = {cls: boot_ci(vals) for cls, vals in by_class_mj.items()}
    return out, out_mj, state_class_rows, state_class_rows_mj


def paired_comparison(state_class_rows, cls_a, cls_b):
    """Only states where BOTH classes co-occur (spec: 'compare class-level
    effects using state-paired summaries wherever classes co-occur')."""
    by_state = {}
    for row in state_class_rows:
        by_state.setdefault(row["state_id"], {})[row["actuator_class"]] = row["mean"]
    diffs = []
    states_used = []
    for sid, d in by_state.items():
        if cls_a in d and cls_b in d:
            diffs.append(d[cls_a] - d[cls_b])
            states_used.append(sid)
    return dict(cls_a=cls_a, cls_b=cls_b, n_states=len(diffs), states=states_used,
                mean_diff=float(np.mean(diffs)) if diffs else None,
                diff_ci=boot_ci(diffs) if diffs else None, diffs=diffs)


def geometric_vs_directed(rollouts):
    """Closure B Q2: does directed live access relate more strongly to
    delta_J than geometric contact? Spearman correlation per state, then
    combined via state-clustered summary (median of per-state rho +
    bootstrap CI over states) -- never a single pooled correlation across
    all rollouts (would violate state-independence)."""
    by_state = {}
    for r in rollouts:
        by_state.setdefault(r["state_id"], []).append(r)

    def spearman(x, y):
        x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
        if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
            return None
        rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
        return float(np.corrcoef(rx, ry)[0, 1])

    rows = []
    for sid, rs in by_state.items():
        dj = [r["delta_J_conservative"] for r in rs]
        geo = [r["mech_cumulative_contact_edges"] for r in rs]
        live = [r["live_cumulative_actuator_to_target_edges"] for r in rs]
        reach = [r["reach_frac_reached_le3"] for r in rs]
        rows.append(dict(state_id=sid, n=len(rs),
                          rho_geometric=spearman(geo, dj), rho_live_directed=spearman(live, dj),
                          rho_temporal_reach=spearman(reach, dj)))
    valid_geo = [r["rho_geometric"] for r in rows if r["rho_geometric"] is not None]
    valid_live = [r["rho_live_directed"] for r in rows if r["rho_live_directed"] is not None]
    valid_reach = [r["rho_temporal_reach"] for r in rows if r["rho_temporal_reach"] is not None]
    return dict(per_state=rows,
                geometric_ci=boot_ci(valid_geo), live_directed_ci=boot_ci(valid_live),
                temporal_reach_ci=boot_ci(valid_reach))


def class_c_vs_d(rollouts):
    """Closure B Q1: does class C (live exterior parent) outperform class D
    (near exterior non-parent, distance-matched pool)? State-paired."""
    _, _, state_class_rows, _ = class_level_summary(rollouts)
    cmp_ = paired_comparison(state_class_rows, "live_exterior_parent", "near_exterior_non_parent")
    # distance-mismatch diagnostic
    dist_c = [r["static_min_distance"] for r in rollouts if r["actuator_class"] == "live_exterior_parent" and r.get("static_min_distance") is not None]
    dist_d = [r["static_min_distance"] for r in rollouts if r["actuator_class"] == "near_exterior_non_parent" and r.get("static_min_distance") is not None]
    cmp_["distance_diagnostic"] = dict(class_c_mean_dist=float(np.mean(dist_c)) if dist_c else None,
                                        class_d_mean_dist=float(np.mean(dist_d)) if dist_d else None,
                                        class_c_n=len(dist_c), class_d_n=len(dist_d))
    return cmp_


def closureA_analysis(rollouts):
    class_ci, class_ci_mj, state_class_rows, state_class_rows_mj = class_level_summary(rollouts)
    comparisons = dict(
        boundary_vs_core=paired_comparison(state_class_rows, "boundary_member", "core_member"),
        boundary_vs_live_parent=paired_comparison(state_class_rows, "boundary_member", "live_exterior_parent"),
        live_parent_vs_near_nonparent=paired_comparison(state_class_rows, "live_exterior_parent", "near_exterior_non_parent"),
    )
    comparisons_minus_j = dict(
        boundary_vs_core=paired_comparison(state_class_rows_mj, "boundary_member", "core_member"),
    )
    # interior (core+boundary, pooled by relabeling) vs exterior (live_parent+near_nonparent)
    interior_rows, exterior_rows = {}, {}
    for row in state_class_rows_mj:
        bucket = interior_rows if row["actuator_class"] in ("core_member", "boundary_member") else exterior_rows
        bucket.setdefault(row["state_id"], []).append(row["mean"])
    by_state_bucket = []
    for sid in set(list(interior_rows) + list(exterior_rows)):
        if sid in interior_rows and sid in exterior_rows:
            by_state_bucket.append(dict(state_id=sid, interior_mean=float(np.mean(interior_rows[sid])),
                                         exterior_mean=float(np.mean(exterior_rows[sid])),
                                         diff=float(np.mean(interior_rows[sid]) - np.mean(exterior_rows[sid]))))
    interior_vs_exterior = dict(n_states=len(by_state_bucket),
                                 diff_ci=boot_ci([r["diff"] for r in by_state_bucket]) if by_state_bucket else None,
                                 rows=by_state_bucket)
    return dict(class_level_ci=class_ci, class_level_ci_minus_j=class_ci_mj,
                comparisons=comparisons, comparisons_minus_j=comparisons_minus_j,
                interior_vs_exterior_minus_j=interior_vs_exterior)


def closureC_analysis(rows):
    by_state = {}
    for r in rows:
        by_state.setdefault(r["state_id"], []).append(r)
    per_state_summary = []
    for sid, rs in by_state.items():
        by_onset = {}
        for r in rs:
            by_onset.setdefault(r["onset_offset"], []).append(r["delta_J_conservative"])
        onset_means = {int(o): float(np.mean(v)) for o, v in by_onset.items()}
        onset_range = max(onset_means.values()) - min(onset_means.values()) if onset_means else None
        # within-onset actuator spread: mean over onsets of (max-min actuator-mean at that onset)
        by_onset_actuator = {}
        for r in rs:
            by_onset_actuator.setdefault((r["onset_offset"], r["actuator"]), []).append(r["delta_J_conservative"])
        actuator_means_by_onset = {}
        for (o, a), v in by_onset_actuator.items():
            actuator_means_by_onset.setdefault(o, []).append(float(np.mean(v)))
        within_onset_spreads = [max(v) - min(v) for v in actuator_means_by_onset.values() if len(v) >= 2]
        mean_within_onset_spread = float(np.mean(within_onset_spreads)) if within_onset_spreads else None
        per_state_summary.append(dict(state_id=sid, onset_means=onset_means, onset_range=onset_range,
                                       mean_within_onset_actuator_spread=mean_within_onset_spread,
                                       between_onset_ge_within_actuator=(onset_range is not None and
                                                                          mean_within_onset_spread is not None and
                                                                          onset_range > mean_within_onset_spread)))
    onset_ranges = [r["onset_range"] for r in per_state_summary if r["onset_range"] is not None]
    within_spreads = [r["mean_within_onset_actuator_spread"] for r in per_state_summary if r["mean_within_onset_actuator_spread"] is not None]
    return dict(per_state=per_state_summary,
                onset_range_ci=boot_ci(onset_ranges), within_onset_spread_ci=boot_ci(within_spreads),
                n_states_onset_dominates=sum(1 for r in per_state_summary if r["between_onset_ge_within_actuator"]))


def main():
    rollouts = load("closureAB_rollouts.json")
    timing_rows = load("closureC_timing_rollouts.json") if (C.DATA_DIR / "closureC_timing_rollouts.json").exists() else []

    closureA = closureA_analysis(rollouts)
    closureB = dict(class_c_vs_d=class_c_vs_d(rollouts), geometric_vs_directed=geometric_vs_directed(rollouts))
    closureC = closureC_analysis(timing_rows) if timing_rows else {}

    out = dict(closureA=closureA, closureB=closureB, closureC=closureC,
               n_rollouts_AB=len(rollouts), n_rollouts_C=len(timing_rows))
    json.dump(out, open(C.DATA_DIR / "closure_analysis_summary.json", "w"), indent=1, default=str)
    print("wrote", C.DATA_DIR / "closure_analysis_summary.json")
    print(json.dumps({k: (v if not isinstance(v, dict) else "...") for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main()
