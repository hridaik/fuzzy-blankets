"""Aggregate every Stage 6.8 result file into one compact summary, so
RESULTS_6_8.md quotes numbers that came out of the frozen data rather than out
of a transcript. EVALUATION-SIDE, read-only."""
from __future__ import annotations

import numpy as np

from common_68 import load_json, dump_json, DATA_DIR


def _m(v):
    v = [x for x in v if x == x]
    return float(np.mean(v)) if v else float("nan")


def summarize():
    out = {}

    # ---- phase / operating point -----------------------------------------
    scr = load_json(DATA_DIR / "episode_screen.json")
    for op in ("OP1", "OP2"):
        o = scr["ops"][op]
        out[f"episode_screen_{op}"] = dict(
            nn=o["nn"], beta=o["beta"], s=o["s"], n_screened=o["n_screened"],
            n_qualifying=len(o["qualifying"]), fraction=o["fraction"],
            n_dev=len(o["dev_seeds"]), n_heldout=len(o["heldout_seeds"]))

    # ---- oracle interface characterization --------------------------------
    oi = load_json(DATA_DIR / "oracle_interface.json")
    for lab in ("L0_fixed_graph", "L2_fov"):
        rs = [r for r in oi["runs"] if r["label"] == lab]
        out[f"interface_{lab}"] = dict(
            n_seeds=len(rs),
            mean_B_size=_m([r["mean_B_size"] for r in rs]),
            mean_symdiff_per_step=_m([r["mean_symdiff"] for r in rs]),
            mean_B_turnover=_m([r["mean_B_turnover"] for r in rs]),
            mean_node_lifetime=_m([r["mean_node_lifetime"] for r in rs]),
            mean_distinct_interfaces=_m([r["n_distinct_interfaces"] for r in rs]),
            n_timepoints=rs[0]["n_timepoints"] if rs else 0,
            mean_edge_flip_fraction=_m([r["edge_churn"]["mean_edge_flip_fraction"] for r in rs]),
            mean_live_edge_fraction=_m([r["edge_churn"]["mean_live_fraction"] for r in rs]))

    # ---- detection / tracking ---------------------------------------------
    det = load_json(DATA_DIR / "detection.json")
    for meth in ("affinity_louvain", "spectral_coherence"):
        L = [l for ep in det["episodes"].values() for l in ep["lineages"][meth]]
        long10 = [l for l in L if l["duration"] >= 10]
        long20 = [l for l in L if l["duration"] >= 20]
        n_ep = len(det["episodes"])
        out[f"detection_{meth}"] = dict(
            n_episodes=n_ep, n_lineages=len(L),
            lineages_per_episode=len(L) / max(1, n_ep),
            max_duration=max((l["duration"] for l in L), default=0),
            mean_duration=_m([l["duration"] for l in L]),
            n_ge_10_steps=len(long10), n_ge_20_steps=len(long20),
            mean_size=_m([l["mean_size"] for l in L]),
            mean_jaccard=_m([l["mean_jaccard"] for l in L]),
            mean_turnover=_m([l["mean_turnover"] for l in L]),
            mean_coherence=_m([l["mean_coherence"] for l in L]),
            long_mean_turnover=_m([l["mean_turnover"] for l in long10]),
            long_final_material_retention=_m([l["final_material_retention"] for l in long10]),
            mean_candidates_per_step=_m([p["affinity" if meth == "affinity_louvain" else "spectral"]["n_valid"]
                                         for ep in det["episodes"].values() for p in ep["per_t"]]))

    # ---- boundary inference + oracle reveal --------------------------------
    for tag in ("snapshot", "series", "gated"):
        try:
            rev = load_json(DATA_DIR / f"oracle_reveal__{tag}.json")
            inf = load_json(DATA_DIR / f"boundary_inference__{tag}.json")
        except FileNotFoundError:
            continue
        runs = rev["runs"]
        by_method = {}
        for meth in sorted({r["method"] for r in runs}):
            rs = [r for r in runs if r["method"] == meth]
            by_method[meth] = dict(
                n=len(rs),
                mean_I_size=_m([r["I_size"] for r in rs]),
                mean_BD_size=_m([len(r["B_D"]) for r in rs]),
                causal_sampled=dict(
                    mean_size=_m([len(r["B_causal_sampled"]) for r in rs]),
                    precision=_m([r["structural_agreement"]["precision"] for r in rs]),
                    recall=_m([r["structural_agreement"]["recall"] for r in rs]),
                    jaccard=_m([r["structural_agreement"]["jaccard"] for r in rs]),
                    size_error=_m([r["structural_agreement"]["size_error"] for r in rs])),
                causal_exact=dict(
                    mean_size=_m([len(r["B_causal_exact"]) for r in rs]),
                    precision=_m([r["identifiability"]["precision"] for r in rs]),
                    recall=_m([r["identifiability"]["recall"] for r in rs]),
                    jaccard=_m([r["identifiability"]["jaccard"] for r in rs])),
                finite_probe_estimation_error=dict(
                    precision=_m([r["estimation_error"]["precision"] for r in rs]),
                    recall=_m([r["estimation_error"]["recall"] for r in rs]),
                    jaccard=_m([r["estimation_error"]["jaccard"] for r in rs])),
                predictive=dict(
                    mean_size=_m([len(r["B_pred"]) for r in rs]),
                    precision=_m([r["predictive_vs_BD"]["precision"] for r in rs]),
                    recall=_m([r["predictive_vs_BD"]["recall"] for r in rs]),
                    jaccard=_m([r["predictive_vs_BD"]["jaccard"] for r in rs]),
                    jaccard_vs_causal_exact=_m([r["predictive_vs_causal_exact"]["jaccard"] for r in rs])),
                turnover_similarity=dict(
                    causal=_m([r.get("T_B_causal", np.nan) for r in rs]),
                    predictive=_m([r.get("T_B_pred", np.nan) for r in rs]),
                    n=len([r for r in rs if r.get("T_B_causal") is not None])),
                mean_probe_rollouts=_m([r["probe_budget"]["n_rollouts"] for r in rs]),
                mean_probe_calls=_m([r["probe_budget"]["n_probe_calls"] for r in rs]),
                mean_probe_candidates=_m([r["n_probe_candidates"] for r in rs]))
        stops, suff, Lch = {}, [], []
        for r in inf["runs"]:
            stops[r["predictive"]["stop_reason"]] = stops.get(r["predictive"]["stop_reason"], 0) + 1
            c = r.get("certification")
            if c:
                suff.append(c["predictively_sufficient_rel_challenger_class"])
                Lch.append(c["L_challenge_upper"])
        out[f"boundary_{tag}"] = dict(
            n_runs=len(runs), by_method=by_method, stop_reasons=stops,
            certification=dict(n=len(suff),
                               frac_sufficient=float(np.mean(suff)) if suff else float("nan"),
                               mean_L_challenge_upper=_m(Lch)),
            lag=rev.get("temporal_lag", []))

    # ---- gates -------------------------------------------------------------
    try:
        g = load_json(DATA_DIR / "gate_choice.json")
        out["gates"] = dict(any_accepted=any(r["accepted"] for r in g["grid"]),
                            n_grid=len(g["grid"]),
                            baseline_meso=g["baseline_L2"]["mesoscopic_episode_fraction"],
                            fallback=g.get("fallback_for_robustness_probe"),
                            fails_G1=g.get("chosen_is_fallback_failing_G1"))
    except FileNotFoundError:
        pass

    # ---- control -----------------------------------------------------------
    try:
        c = load_json(DATA_DIR / "control.json")
        arms = {}
        for arm in c["arms"]:
            for split in ("dev", "heldout"):
                rs = [r for r in c["runs"] if r["arm"] == arm and r["split"] == split]
                if rs:
                    arms[f"{arm}__{split}"] = dict(
                        n=len(rs),
                        final_target_fraction=_m([r["final_target_fraction"] for r in rs]),
                        sd=float(np.std([r["final_target_fraction"] for r in rs])),
                        mean_actuators=_m([r["mean_actuators"] for r in rs]),
                        mean_final_I=_m([r["final_I_size"] for r in rs]),
                        mean_rollouts=_m([r["probe_budget"]["n_rollouts"] for r in rs]))
        out["control"] = dict(calibration=c["calibration"], arms=arms,
                              K_ACT=c["K_ACT"], T_CONTROL=c["T_CONTROL"])
    except FileNotFoundError:
        pass

    dump_json(out, DATA_DIR / "summary_6_8.json")
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(summarize(), indent=1, default=str)[:9000])
