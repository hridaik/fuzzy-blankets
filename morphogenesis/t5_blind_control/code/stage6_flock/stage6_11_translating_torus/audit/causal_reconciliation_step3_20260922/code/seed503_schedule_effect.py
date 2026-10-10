"""Task F2: seed 503 causal/disruption adjudication.

Same schedule-effect harness/CRN methodology as seed501_schedule_effect.py
(see that file and RNG_AND_CRN_AUDIT.md for the full justification --
not repeated here). Adds the DISRUPTION outcome alongside the alignment
outcome: does forcing change the probability/timing of a candidate split
event in the material-continuing target, on top of whatever it does to
heading alignment?

Per spec S11/S12: post-split daughter heading is NOT scored as strict
parent success unless strict parent identity is independently restored
(not established here) -- this script reports the material trace's OWN
followed-branch alignment (exactly what ForwardMaterialTrace611 already
does: continue on one daughter, flagged), and separately reports
split/merge/disruption incidence, WITHOUT re-labelling a post-split
daughter as "the same object succeeding."
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

STEP2_CODE = STAGE_DIR / "audit" / "material_identity_step2_20260921" / "code"
sys.path.insert(0, str(STEP2_CODE))
from forward_material_trace_611 import ForwardMaterialTrace611, RULE_FAMILY_BUILDERS  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"
FROZEN_JSON = STEP2_CODE.parent / "data" / "identity_rule_calibration.json"

SEED = 503
N_REPLICATES = 25
PHYSICS_SEED_BASE = 4_000_000


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
    context_ts = [t for t in range(max(0, t0 - ROC.AFFINITY_WINDOW + 1), t0)]
    z_context = [np.array(frames[t]["z"], dtype=int) for t in context_ts if t in frames]
    return dict(t0=t0, target_heading=target_heading, schedule=schedule,
                t_control_end=t_control_end, t_final=t_final,
                r0=r0, z0=z0, interior0=interior0, z_context=z_context)


def rollout(mf, r0, z0, rng_physics, forced_by_t, t0, n_steps):
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
    z_window = list(z_context)
    out = []
    for t in range(r_hist.shape[0]):
        z_window.append(z_hist[t])
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r_hist[t], z_window, L) if len(z_window) >= 2 else []
        out.append([frozenset(int(x) for x in c) for c in cands])
    return out


def frac_at_heading(members, z, heading):
    if not members:
        return None
    ids = np.array(list(members), dtype=int)
    return float((z[ids] == heading).mean())


def draw_matched_random_schedule(rng_for_draw, historical_schedule, interior0, r0, mf, L):
    out = {}
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
          f"control ends t={trig['t_control_end']}, {len(trig['interior0'])} interior members at t0")
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

        rng_B = np.random.default_rng(physics_seed)
        r_B, z_B = rollout(mf, trig["r0"], trig["z0"], rng_B, forced_historical, t0, n_steps)

        rng_draw = np.random.default_rng(9_500_000 + i)
        random_schedule = draw_matched_random_schedule(rng_draw, trig["schedule"], trig["interior0"], trig["r0"], mf, L_BOX)
        forced_random = {t: {b: target_heading for b in bset} for t, bset in random_schedule.items()}
        rng_C = np.random.default_rng(physics_seed)
        r_C, z_C = rollout(mf, trig["r0"], trig["z0"], rng_C, forced_random, t0, n_steps)

        branch_summaries = {}
        for label, r_hist, z_hist in (("no_forcing", r_A, z_A), ("historical_schedule", r_B, z_B), ("matched_random", r_C, z_C)):
            cands = build_candidates(r_hist, z_hist, trig["z_context"], L_BOX)
            tr = ForwardMaterialTrace611(rule)
            tr.start(0, frozenset(trig["interior0"]))
            for t in range(1, len(cands)):
                tr.step(t, cands[t])
            final = tr.history[-1]
            end_members = final.accepted_members or frozenset()
            end_frac = frac_at_heading(end_members, z_hist[-1], target_heading)
            control_end_idx = trig["t_control_end"] - t0
            control_end_decision = tr.history[control_end_idx] if control_end_idx < len(tr.history) else None
            control_end_frac = (frac_at_heading(control_end_decision.accepted_members, z_hist[control_end_idx], target_heading)
                                 if control_end_decision and control_end_decision.accepted_members else None)
            split_steps = [d.t for d in tr.history if d.split_flag]
            merge_steps = [d.t for d in tr.history if d.merge_flag]
            first_split_t = split_steps[0] if split_steps else None
            branch_summaries[label] = dict(
                final_status=final.status,
                end_of_release_frac_at_target=end_frac,
                end_of_control_frac_at_target=control_end_frac,
                target_size_start=len(trig["interior0"]), target_size_end=len(end_members),
                n_split_events=len(split_steps), first_split_t=first_split_t,
                n_merge_events=len(merge_steps),
                n_unresolved_steps=sum(1 for d in tr.history if d.status == "unresolved"),
                died=(final.status == "dead"),
            )
        replicate_results.append(dict(replicate=i, physics_seed=physics_seed,
                                       random_schedule=random_schedule, branches=branch_summaries))
        def fmt(v):
            return f"{v:.3f}" if v is not None else "None"
        print(f"  replicate {i}: no_forcing end={fmt(branch_summaries['no_forcing']['end_of_release_frac_at_target'])} "
              f"(splits={branch_summaries['no_forcing']['n_split_events']}) "
              f"historical end={fmt(branch_summaries['historical_schedule']['end_of_release_frac_at_target'])} "
              f"(splits={branch_summaries['historical_schedule']['n_split_events']}) "
              f"matched_random end={fmt(branch_summaries['matched_random']['end_of_release_frac_at_target'])} "
              f"(splits={branch_summaries['matched_random']['n_split_events']})")

    def collect(label, key, predicate=lambda v: v is not None):
        return [r["branches"][label][key] for r in replicate_results if predicate(r["branches"][label][key])]

    summary = {}
    for label in ("no_forcing", "historical_schedule", "matched_random"):
        vals = collect(label, "end_of_release_frac_at_target")
        n_split_any = sum(1 for r in replicate_results if r["branches"][label]["n_split_events"] > 0)
        n_died = sum(1 for r in replicate_results if r["branches"][label]["died"])
        first_splits = [r["branches"][label]["first_split_t"] for r in replicate_results if r["branches"][label]["first_split_t"] is not None]
        summary[label] = dict(
            n=len(vals),
            mean_end_of_release=float(np.mean(vals)) if vals else None,
            median_end_of_release=float(np.median(vals)) if vals else None,
            std_end_of_release=float(np.std(vals)) if vals else None,
            n_replicates_with_any_split=n_split_any,
            fraction_replicates_with_split=n_split_any / N_REPLICATES,
            mean_first_split_t=float(np.mean(first_splits)) if first_splits else None,
            n_died=n_died,
            fraction_died=n_died / N_REPLICATES,
        )

    out = dict(seed=SEED, t0=t0, target_heading=target_heading, n_steps=n_steps,
               n_replicates=N_REPLICATES, frozen_rule=frozen["params"],
               historical_schedule=trig["schedule"],
               replicate_results=replicate_results, summary=summary)
    json.dump(out, open(OUT / "seed503_schedule_effect.json", "w"), indent=2, default=str)
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print("\nwrote", OUT / "seed503_schedule_effect.json")


if __name__ == "__main__":
    main()
