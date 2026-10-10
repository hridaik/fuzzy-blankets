"""Task F1 S10.1: seed 501 historical SCHEDULE effect.

Estimand: what effect does the ACTUAL historical intervention schedule
(exact actuator IDs, forced heading, duration, refresh times, read
verbatim from data/online_control_611__seed501.json) have on the
materially-continuous target, compared to (A) no forcing and (C)
duration/cardinality/cadence/pool-matched random exterior forcing --
holding the CONTROLLER'S OWN DECISION LOGIC OUT OF IT (this is schedule
replay, not policy replay; see seed501_policy_effect.py for the
distinct estimand).

CRN methodology (per rng_crn_diagnostic.py's findings, NOT assumed
valid without that audit): each replicate index i uses a DEDICATED
physics-only rng stream (np.random.default_rng(PHYSICS_SEED_BASE + i)),
shared verbatim across the no-forcing, historical-schedule, and
matched-random-for-that-replicate branches -- so within a replicate,
all three branches see bit-identical physics noise except where
forced_actions actually differs. This is valid because
rng_crn_diagnostic.py's demo_1/demo_3 showed forced_actions alone (with
no auxiliary decision-code sharing the stream) does not change RNG
draw count/order -- and this harness deliberately never routes any
decision-making code through the physics stream (there is no online
re-inference happening here at all; the actuator sets are either fixed
historical values or pre-drawn random sets, not recomputed from live
data mid-rollout).

Trigger state: t0=30, read from data/viz_bundle_611__seed501.json frame
30 (exact bird-ID interior + r + z), independently verified reproducible
from the raw episode seed by reproduce_trigger_states.py (bit-exact
match, both r and z).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = STAGE_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import N_BIRDS, L_BOX, BETA_610, S_610, resolved_params, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY, DATA_DIR  # noqa: E402
from moving_flock_611 import MovingFlock611  # noqa: E402
from detect_69 import propose  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402
from intervention_api_611 import near_exterior  # noqa: E402
from geometry_611 import torus_delta  # noqa: E402

STEP2_CODE = STAGE_DIR / "audit" / "material_identity_step2_20260921" / "code"
sys.path.insert(0, str(STEP2_CODE))
from forward_material_trace_611 import ForwardMaterialTrace611, RULE_FAMILY_BUILDERS  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"
FROZEN_JSON = STEP2_CODE.parent / "data" / "identity_rule_calibration.json"

SEED = 501
N_REPLICATES = 25
PHYSICS_SEED_BASE = 3_000_000


def make_flock():
    pm = resolved_params(BETA_610, S_610)
    return MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=V_PRIMARY, params=pm,
                           social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)


def load_frozen_rule():
    calib = json.load(open(FROZEN_JSON))
    frozen = calib["frozen_rule"]
    return RULE_FAMILY_BUILDERS[frozen["letter"]](**frozen["params"]), frozen


def load_trigger_and_schedule():
    viz = json.load(open(DATA_DIR / f"viz_bundle_611__seed{SEED}.json"))
    frames = {f["t"]: f for f in viz["frames"]}
    ctrl = json.load(open(DATA_DIR / f"online_control_611__seed{SEED}.json"))
    control_events = [e for e in ctrl["log"] if e["event"] == "control_step"]
    qual = [e for e in ctrl["log"] if e["event"] == "qualified_and_target_set"][0]
    t0 = qual["t"]
    target_heading = qual["target_heading"]
    schedule = {e["t"]: e["B_C"] for e in control_events}
    t_control_end = max(schedule.keys())
    t_final = ctrl["final_t"]
    r0 = np.array(frames[t0]["r"])
    z0 = np.array(frames[t0]["z"], dtype=int)
    interior0 = list(frames[t0]["interior"])
    # for the detector's sliding window context, use the ACTUAL recorded
    # z history for AFFINITY_WINDOW-1 steps before t0 (context only, never
    # re-simulated -- t0 itself and everything after IS simulated fresh
    # per-branch).
    context_ts = [t for t in range(max(0, t0 - ROC.AFFINITY_WINDOW + 1), t0)]
    z_context = [np.array(frames[t]["z"], dtype=int) for t in context_ts if t in frames]
    return dict(t0=t0, target_heading=target_heading, schedule=schedule,
                t_control_end=t_control_end, t_final=t_final,
                r0=r0, z0=z0, interior0=interior0, z_context=z_context)


def rollout(mf, r0, z0, rng_physics, forced_by_t: dict, t0: int, n_steps: int):
    """forced_by_t: {t: {bird_id: heading, ...}} or {} entries mean
    unforced that step. Returns r_hist, z_hist (n_steps+1 frames,
    including t0)."""
    r, z = r0.copy(), z0.copy()
    r_hist = [r.copy()]
    z_hist = [z.copy()]
    for i in range(n_steps):
        t = t0 + i
        forced = forced_by_t.get(t)
        r, z, _ = mf.step(r, z, rng_physics, forced_actions=forced)
        r_hist.append(r.copy())
        z_hist.append(z.copy())
    return np.stack(r_hist), np.stack(z_hist)


def build_candidates(r_hist, z_hist, z_context, L):
    """detect_69.propose per step, seeding the sliding window with the
    REAL recorded pre-t0 context, then the branch's own simulated z from
    t0 onward -- identical detector call pattern to production."""
    z_window = list(z_context)
    out = []
    for t in range(r_hist.shape[0]):
        z_window.append(z_hist[t])
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r_hist[t], z_window, L) if len(z_window) >= 2 else []
        out.append([frozenset(int(x) for x in c) for c in cands])
    return out


def trace_material_target(candidates_by_t, seed_members, rule):
    tr = ForwardMaterialTrace611(rule)
    tr.start(0, seed_members)
    for t in range(1, len(candidates_by_t)):
        tr.step(t, candidates_by_t[t])
    return tr


def frac_at_heading(members, z, heading):
    if not members:
        return None
    ids = np.array(list(members), dtype=int)
    return float((z[ids] == heading).mean())


def draw_matched_random_schedule(rng_for_draw, historical_schedule, interior0, r0, mf, L):
    """Matches: actuator COUNT per refresh (len of each historical B_C),
    the SAME refresh times (historical schedule's own t-keys), and draws
    from the SAME eligible-exterior-pool definition the real controller
    used (near_exterior, true-R oracle pool -- reused as-is, not
    redesigned, since the task is to test the HISTORICAL controller's
    choices against matched random ones drawn from the SAME pool it drew
    from, not to fix the pool definition)."""
    out = {}
    # exterior pool computed once at t0's interior (a reasonable, disclosed
    # simplification -- the real controller recomputes `interior` from its
    # own OWN evolving v1 tracker at each refresh, which this audit-only
    # schedule-replay harness does not re-run; see README's disclosed scope).
    pool = near_exterior(mf, r0, np.array(interior0), radius_factor=3.0)
    for t, bset in historical_schedule.items():
        k = len(bset)
        chosen = rng_for_draw.choice(pool, size=min(k, len(pool)), replace=False)
        out[t] = [int(x) for x in chosen]
    return out


def main():
    rule, frozen = load_frozen_rule()
    trig = load_trigger_and_schedule()
    t0, target_heading = trig["t0"], trig["target_heading"]
    n_steps = trig["t_final"] - t0
    print(f"seed {SEED}: t0={t0}, target_heading={target_heading}, n_steps={n_steps}, "
          f"control window ends t={trig['t_control_end']}, {len(trig['interior0'])} interior members at t0")
    print(f"historical schedule refresh times: {sorted(trig['schedule'].keys())[:1]} ... "
          f"actuator sets at each refresh (first occurrence per distinct set):")
    seen = set()
    for t in sorted(trig["schedule"].keys()):
        key = tuple(trig["schedule"][t])
        if key not in seen:
            seen.add(key)
            print(f"  refresh at t={t}: {trig['schedule'][t]}")

    mf = make_flock()
    forced_historical = {t: {b: target_heading for b in bset} for t, bset in trig["schedule"].items()}

    replicate_results = []
    for i in range(N_REPLICATES):
        physics_seed = PHYSICS_SEED_BASE + i
        rng_A = np.random.default_rng(physics_seed)
        r_A, z_A = rollout(mf, trig["r0"], trig["z0"], rng_A, {}, t0, n_steps)

        rng_B = np.random.default_rng(physics_seed)   # SAME physics seed -> CRN-paired with A
        r_B, z_B = rollout(mf, trig["r0"], trig["z0"], rng_B, forced_historical, t0, n_steps)

        rng_draw = np.random.default_rng(9_000_000 + i)   # independent stream for the RANDOM ACTUATOR DRAW itself
        random_schedule = draw_matched_random_schedule(rng_draw, trig["schedule"], trig["interior0"], trig["r0"], mf, L_BOX)
        forced_random = {t: {b: target_heading for b in bset} for t, bset in random_schedule.items()}
        rng_C = np.random.default_rng(physics_seed)   # SAME physics seed again -> CRN-paired with A and B
        r_C, z_C = rollout(mf, trig["r0"], trig["z0"], rng_C, forced_random, t0, n_steps)

        branch_summaries = {}
        for label, r_hist, z_hist in (("no_forcing", r_A, z_A), ("historical_schedule", r_B, z_B), ("matched_random", r_C, z_C)):
            cands = build_candidates(r_hist, z_hist, trig["z_context"], L_BOX)
            tr = trace_material_target(cands, frozenset(trig["interior0"]), rule)
            final = tr.history[-1]
            end_members = final.accepted_members or frozenset()
            end_frac = frac_at_heading(end_members, z_hist[-1], target_heading)
            # end-of-control alignment (t index = t_control_end - t0 within this trajectory)
            control_end_idx = trig["t_control_end"] - t0
            control_end_decision = tr.history[control_end_idx] if control_end_idx < len(tr.history) else None
            control_end_frac = (frac_at_heading(control_end_decision.accepted_members, z_hist[control_end_idx], target_heading)
                                 if control_end_decision and control_end_decision.accepted_members else None)
            n_split = sum(1 for d in tr.history if d.split_flag)
            n_merge = sum(1 for d in tr.history if d.merge_flag)
            n_unresolved = sum(1 for d in tr.history if d.status == "unresolved")
            branch_summaries[label] = dict(
                final_status=final.status,
                end_of_release_frac_at_target=end_frac,
                end_of_control_frac_at_target=control_end_frac,
                start_frac_at_target=frac_at_heading(trig["interior0"], trig["z0"], target_heading),
                target_size_start=len(trig["interior0"]), target_size_end=len(end_members),
                n_split_flags=n_split, n_merge_flags=n_merge, n_unresolved_steps=n_unresolved,
            )
        replicate_results.append(dict(replicate=i, physics_seed=physics_seed,
                                       random_schedule=random_schedule, branches=branch_summaries))
        def fmt(v):
            return f"{v:.3f}" if v is not None else "None(dead)"
        print(f"  replicate {i}: no_forcing end={fmt(branch_summaries['no_forcing']['end_of_release_frac_at_target'])} "
              f"historical end={fmt(branch_summaries['historical_schedule']['end_of_release_frac_at_target'])} "
              f"matched_random end={fmt(branch_summaries['matched_random']['end_of_release_frac_at_target'])}")

    def collect(label, key):
        return [r["branches"][label][key] for r in replicate_results if r["branches"][label][key] is not None]

    summary = {}
    for label in ("no_forcing", "historical_schedule", "matched_random"):
        vals = collect(label, "end_of_release_frac_at_target")
        vals_ctrl = collect(label, "end_of_control_frac_at_target")
        summary[label] = dict(
            n=len(vals),
            mean_end_of_release=float(np.mean(vals)) if vals else None,
            median_end_of_release=float(np.median(vals)) if vals else None,
            std_end_of_release=float(np.std(vals)) if vals else None,
            p10_end_of_release=float(np.percentile(vals, 10)) if vals else None,
            p90_end_of_release=float(np.percentile(vals, 90)) if vals else None,
            mean_end_of_control=float(np.mean(vals_ctrl)) if vals_ctrl else None,
            n_final_status_continuing=sum(1 for r in replicate_results if r["branches"][label]["final_status"] == "continuing"),
            n_final_status_dead=sum(1 for r in replicate_results if r["branches"][label]["final_status"] == "dead"),
        )

    # paired within-replicate differences (valid because CRN-paired: same physics_seed across A/B/C per replicate)
    diffs_hist_minus_none = [r["branches"]["historical_schedule"]["end_of_release_frac_at_target"] - r["branches"]["no_forcing"]["end_of_release_frac_at_target"]
                              for r in replicate_results
                              if r["branches"]["historical_schedule"]["end_of_release_frac_at_target"] is not None
                              and r["branches"]["no_forcing"]["end_of_release_frac_at_target"] is not None]
    diffs_hist_minus_random = [r["branches"]["historical_schedule"]["end_of_release_frac_at_target"] - r["branches"]["matched_random"]["end_of_release_frac_at_target"]
                                for r in replicate_results
                                if r["branches"]["historical_schedule"]["end_of_release_frac_at_target"] is not None
                                and r["branches"]["matched_random"]["end_of_release_frac_at_target"] is not None]
    paired = dict(
        historical_minus_no_forcing=dict(n=len(diffs_hist_minus_none),
                                          mean=float(np.mean(diffs_hist_minus_none)) if diffs_hist_minus_none else None,
                                          std=float(np.std(diffs_hist_minus_none)) if diffs_hist_minus_none else None,
                                          fraction_positive=float(np.mean([d > 0 for d in diffs_hist_minus_none])) if diffs_hist_minus_none else None),
        historical_minus_matched_random=dict(n=len(diffs_hist_minus_random),
                                              mean=float(np.mean(diffs_hist_minus_random)) if diffs_hist_minus_random else None,
                                              std=float(np.std(diffs_hist_minus_random)) if diffs_hist_minus_random else None,
                                              fraction_positive=float(np.mean([d > 0 for d in diffs_hist_minus_random])) if diffs_hist_minus_random else None),
    )

    out = dict(seed=SEED, t0=t0, target_heading=target_heading, n_steps=n_steps,
               n_replicates=N_REPLICATES, frozen_rule=frozen["params"],
               historical_schedule=trig["schedule"],
               replicate_results=replicate_results, summary=summary, paired_differences=paired)
    json.dump(out, open(OUT / "seed501_schedule_effect.json", "w"), indent=2, default=str)
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print("\n=== PAIRED DIFFERENCES (CRN) ===")
    print(json.dumps(paired, indent=2))
    print("\nwrote", OUT / "seed501_schedule_effect.json")


if __name__ == "__main__":
    main()
