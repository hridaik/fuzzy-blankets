"""Task 0: complete episode-level identity-validation reporting.

Extends identity_causal_reconciliation_20260921/code/hard_negative_validation.py's
sequential trace audit (which reported per-trace summary statistics but did
not classify WHAT the competing candidates were at ambiguous-accept steps).
This script re-runs the same 36+36 full-episode traces (dev: seeds
236-247, untouched holdout: seeds 248-259; same 3-seed-targets-per-episode
protocol, same frozen rule, never retuned) and, at every step where more
than one candidate clears the Jaccard>=0.30 gate, classifies EVERY
non-winning accepting candidate into one of:

  nested_fragment : candidate is a (near-)strict subset of the previous
                     accepted target (R_new >= 0.99) -- the detector
                     proposing a sub-clique of the same physical group as
                     its own separate candidate. Genealogically part of
                     the SAME object, not a competing population.
  merge_dilution   : previous target is (near-)fully retained inside a
                      much larger candidate (R_old >= 0.99, size ratio
                      >= 1.8 -- reusing forward_material_trace_611.py's
                      own existing, frozen `merge_min_size_ratio`
                      diagnostic constant, not a newly invented number).
  split_daughter   : candidate retains a "substantial" share of the
                      previous target (>= split_min_share=0.30 of prev's
                      absolute size -- again the frozen, pre-existing
                      constant from forward_material_trace_611.py, not
                      invented here) without being a nested fragment or a
                      merge candidate. This is the SAME criterion the
                      tracker's own split_flag logic already uses.
  unrelated_candidate : clears the Jaccard>=0.30 material-association
                         gate WITHOUT falling into any of the above
                         genealogically-explicable categories -- i.e. a
                         structurally ambiguous case that is the closest
                         operational proxy this pass has for "an unrelated
                         population coincidentally scored high enough to
                         be eligible." This is the category Task 0 calls
                         "erroneous transfer to an unrelated population"
                         RISK (if such a candidate is ever the WINNER, not
                         just present) -- reported separately from mere
                         presence in the candidate pool.

This directly answers Task 0's requirement not to count genealogically
related fragments as ordinary unrelated false positives.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = STAGE_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import DATA_DIR, L_BOX  # noqa: E402
from detect_69 import propose  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

STEP2_CODE = STAGE_DIR / "audit" / "material_identity_step2_20260921" / "code"
sys.path.insert(0, str(STEP2_CODE))
from forward_material_trace_611 import (  # noqa: E402
    ForwardMaterialTrace611, overlap_metrics, RULE_FAMILY_BUILDERS,
)

OUT = Path(__file__).resolve().parents[1] / "data"
FROZEN_JSON = STEP2_CODE.parent / "data" / "identity_rule_calibration.json"

SPLITS = {
    "dev_already_used_for_calibration": DATA_DIR / "observational_corpus_611__val.npz",
    "untouched_validation": DATA_DIR / "observational_corpus_611__test.npz",
}

SPLIT_MIN_SHARE = 0.30       # forward_material_trace_611.py's own frozen constant
MERGE_MIN_SIZE_RATIO = 1.8   # ditto
NESTED_R_NEW_FLOOR = 0.99
MERGE_R_OLD_FLOOR = 0.99


def load_frozen_rule():
    calib = json.load(open(FROZEN_JSON))
    frozen = calib["frozen_rule"]
    rule = RULE_FAMILY_BUILDERS[frozen["letter"]](**frozen["params"])
    return rule, frozen


def run_episode_candidates(r_hist, z_hist, L, stride=1):
    T = r_hist.shape[0]
    z_window = []
    out = []
    for t in range(0, T, stride):
        z_window.append(z_hist[t])
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r_hist[t], z_window, L) if len(z_window) >= 2 else []
        out.append([frozenset(int(x) for x in c) for c in cands])
    return out


def classify_competitor(prev: frozenset, cand: frozenset) -> str:
    m = overlap_metrics(prev, cand)
    if m["R_new"] is not None and m["R_new"] >= NESTED_R_NEW_FLOOR:
        return "nested_fragment"
    if (m["R_old"] is not None and m["R_old"] >= MERGE_R_OLD_FLOOR
            and len(cand) >= MERGE_MIN_SIZE_RATIO * len(prev)):
        return "merge_dilution"
    if m["retained"] >= SPLIT_MIN_SHARE * len(prev):
        return "split_daughter"
    return "unrelated_candidate"


def size_bucket(n):
    if n < 20:
        return "small(<20)"
    if n < 50:
        return "medium(20-49)"
    return "large(>=50)"


def run_traces_for_episode(seed, cands_by_t, rule, n_seed_targets=3, start_t=5):
    seed_cands = sorted(cands_by_t[start_t], key=len, reverse=True)[:n_seed_targets]
    trace_results = []
    for target_idx, seed_target in enumerate(seed_cands):
        if len(seed_target) < 10:
            continue
        tr = ForwardMaterialTrace611(rule)
        tr.start(start_t, seed_target)

        n_unresolved = 0
        n_recovered = 0
        n_candidate_split_events = 0     # winning step had >=2 "split_daughter"-shaped competitors (incl. winner's own share)
        n_candidate_merge_events = 0     # winning step's winner itself is merge-shaped (R_old high, size ratio big) per tracker's own merge_flag
        gap_lengths = []
        cur_gap = 0
        competitor_class_counts = dict(nested_fragment=0, merge_dilution=0, split_daughter=0, unrelated_candidate=0)
        winner_was_unrelated_shaped = 0   # the WINNER itself, relative to ITS OWN prev, would be classified unrelated_candidate if it were a competitor (i.e. winner's material link is not fragment/split/merge shaped -- should basically never happen since winner always jaccard>=0.30 to prev, but check explicitly)
        step_rows = []
        start_members = seed_target
        for t in range(start_t + 1, len(cands_by_t)):
            prev_members = tr.accepted
            d = tr.step(t, cands_by_t[t])
            if d.status == "unresolved":
                n_unresolved += 1
                cur_gap += 1
            else:
                if cur_gap > 0:
                    gap_lengths.append(cur_gap)
                    if d.status == "continuing":
                        n_recovered += 1
                    cur_gap = 0
            if d.status == "continuing" and prev_members is not None:
                if d.split_flag:
                    n_candidate_split_events += 1
                if d.merge_flag:
                    n_candidate_merge_events += 1
                if d.n_accepting_candidates > 1:
                    for m in d.all_candidate_metrics:
                        if m["cand_idx"] == d.chosen_candidate_idx:
                            continue
                        if m["jaccard"] is None or m["jaccard"] < 0.30:
                            continue  # not actually an accepting competitor
                        cand_set = None
                        # reconstruct candidate set from cands_by_t[t] via index
                        cand_set = cands_by_t[t][m["cand_idx"]]
                        cls = classify_competitor(prev_members, cand_set)
                        competitor_class_counts[cls] += 1
                # sanity-check the winner itself
                winner_set = d.accepted_members
                winner_cls = classify_competitor(prev_members, winner_set) if prev_members else None
                if winner_cls == "unrelated_candidate":
                    winner_was_unrelated_shaped += 1
            if d.status == "dead":
                break
        final = tr.history[-1]
        end_members = final.accepted_members if final.accepted_members else frozenset()
        turnover = 1.0 - (len(start_members & end_members) / len(start_members | end_members)
                           if (start_members or end_members) else 0.0)
        trace_results.append(dict(
            seed=int(seed), target_idx=target_idx, start_t=start_t, start_size=len(seed_target),
            size_bucket=size_bucket(len(seed_target)),
            final_status=final.status, final_t=final.t, duration_reached=final.t - start_t,
            n_unresolved_steps=n_unresolved, n_recovered_gaps=n_recovered,
            unresolved_gap_lengths=gap_lengths, max_gap_length=max(gap_lengths) if gap_lengths else 0,
            n_candidate_split_events=n_candidate_split_events,
            n_candidate_merge_events=n_candidate_merge_events,
            competitor_class_counts=competitor_class_counts,
            winner_was_unrelated_shaped_count=winner_was_unrelated_shaped,
            cumulative_turnover=turnover,
        ))
    return trace_results


def summarize_split(split_name, per_episode_traces):
    all_t = [t for ep in per_episode_traces for t in ep["traces"]]
    n = len(all_t)
    n_complete = sum(1 for t in all_t if t["final_status"] == "continuing")
    n_erroneous_transfer = sum(t["winner_was_unrelated_shaped_count"] for t in all_t)
    n_traces_with_erroneous_transfer = sum(1 for t in all_t if t["winner_was_unrelated_shaped_count"] > 0)
    total_unresolved = sum(t["n_unresolved_steps"] for t in all_t)
    total_candidate_split = sum(t["n_candidate_split_events"] for t in all_t)
    total_candidate_merge = sum(t["n_candidate_merge_events"] for t in all_t)
    total_recovered = sum(t["n_recovered_gaps"] for t in all_t)
    all_gaps = [g for t in all_t for g in t["unresolved_gap_lengths"]]
    max_unresolved_duration = max(all_gaps) if all_gaps else 0
    durations = sorted(t["duration_reached"] for t in all_t)

    comp_totals = dict(nested_fragment=0, merge_dilution=0, split_daughter=0, unrelated_candidate=0)
    for t in all_t:
        for k, v in t["competitor_class_counts"].items():
            comp_totals[k] += v

    by_bucket = {}
    for bucket in ("small(<20)", "medium(20-49)", "large(>=50)"):
        sub = [t for t in all_t if t["size_bucket"] == bucket]
        if not sub:
            continue
        by_bucket[bucket] = dict(
            n=len(sub),
            n_continuing_final=sum(1 for t in sub if t["final_status"] == "continuing"),
            n_dead_final=sum(1 for t in sub if t["final_status"] == "dead"),
            mean_duration=float(np.mean([t["duration_reached"] for t in sub])),
            mean_turnover=float(np.mean([t["cumulative_turnover"] for t in sub])),
            n_erroneous_transfer=sum(t["winner_was_unrelated_shaped_count"] for t in sub),
        )

    return dict(
        split=split_name,
        n_traces=n,
        n_complete_continuing=n_complete,
        n_dead=n - n_complete,
        fraction_complete_without_erroneous_transfer=(
            (n - n_traces_with_erroneous_transfer) / n if n else None
        ),
        n_traces_with_any_erroneous_transfer=n_traces_with_erroneous_transfer,
        n_total_erroneous_transfer_steps=n_erroneous_transfer,
        n_total_unresolved_steps=total_unresolved,
        n_total_candidate_split_events=total_candidate_split,
        n_total_candidate_merge_events=total_candidate_merge,
        n_total_recovered_gaps=total_recovered,
        max_unresolved_gap_duration=max_unresolved_duration,
        n_unresolved_gaps_observed=len(all_gaps),
        trace_length_distribution=dict(
            min=durations[0] if durations else None,
            p25=float(np.percentile(durations, 25)) if durations else None,
            median=float(np.percentile(durations, 50)) if durations else None,
            p75=float(np.percentile(durations, 75)) if durations else None,
            max=durations[-1] if durations else None,
        ),
        competitor_classification_totals=comp_totals,
        by_target_size_bucket=by_bucket,
    )


def main():
    rule, frozen = load_frozen_rule()
    print(f"frozen rule under test (NOT retuned): {rule.name}")

    full_results = {}
    for split_name, path in SPLITS.items():
        print(f"\n=== {split_name} ===")
        d = np.load(path, allow_pickle=True)
        seeds, r_hist_all, z_hist_all = d["seeds"], d["r_hist"], d["z_hist"]
        per_episode = []
        for i, seed in enumerate(seeds):
            cands = run_episode_candidates(r_hist_all[i], z_hist_all[i], L_BOX)
            traces = run_traces_for_episode(int(seed), cands, rule)
            per_episode.append(dict(seed=int(seed), traces=traces))
            print(f"  seed {seed}: {len(traces)} traces run")
        summary = summarize_split(split_name, per_episode)
        full_results[split_name] = dict(per_episode=per_episode, summary=summary)
        print(json.dumps(summary, indent=2, default=str))

    json.dump(full_results, open(OUT / "identity_episode_validation.json", "w"), indent=2, default=str)
    print("\nwrote", OUT / "identity_episode_validation.json")


if __name__ == "__main__":
    main()
