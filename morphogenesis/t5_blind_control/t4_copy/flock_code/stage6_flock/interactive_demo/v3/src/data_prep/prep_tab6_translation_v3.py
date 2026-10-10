"""Build interactive_demo/v3/data/tab6_translation.json.

v3-only replacement for v2's prep_tab6_translation.py + prep_tab6_forward_trace.py.
Those built the Translation tab from v1 (`LineageTracker611`) readouts on
seeds 500-504 -- the tracker the whole research programme spent Stage
6.11's audit passes establishing is unreliable (see
`stage6_flock/CURRENT_RESEARCH_STATUS.md`). This script instead re-runs the
FROZEN, already-validated confirmatory intervention protocol (K=1, d=8,
release=24; `simulate_branch` / `trace_target` / `outcome_metrics` /
`ForwardMaterialTrace611`, imported UNMODIFIED from
`stage6_12_control_readiness/code/intervention_612.py` and
`stage6_12B_contact_persistence/code/intervention_612b.py`) for a small,
fixed set of (state, actuator, physics-stream) tuples drawn from the
CONFIRMATORY seed manifests (`stage6_12C_kinematic_contact_confirmation/`,
seeds 63200-63209; `final_translating_flock_closure/`, seeds 64200-64207) --
never seeds 500-504, and never re-implementing the physics or the tracker.

SECOND PASS (this revision): the first v3 pass's 5 exemplars were curated
poorly -- reviewer feedback (see EXEMPLAR_SELECTION.md "Second-pass
curation" section) found the split example was a single buried frame, the
"clean success" case didn't visibly rise during forcing, K=1 felt
unexplained, and there was no scanning/pre-qualification lead-in. This
revision:
  (1) re-scans a much wider (state, actuator, stream) pool from BOTH
      confirmatory sources (see scan performed against
      k1_rollouts_612c.json / closureAB_rollouts.json summary data, then
      ~48 full ForwardMaterialTrace611 replays) and independently verifies
      candidates with matplotlib spot-checks (raw bird-position plots,
      frac-at-target-heading traces) rather than trusting split_flag /
      forward_material_trace.status labels at face value -- see
      EXEMPLAR_SELECTION.md for exactly what was checked and found;
  (2) adds a genuine (not fabricated) SCANNING lead-in phase per exemplar,
      reconstructed by re-running the EXACT deterministic qualification
      rng (`state["seed"]`) forward from t=0 to `state["t0"]` with
      `common_612.make_flock()` + `mf.step` -- bit-exact verified against
      the recorded `r0`/`z0` in the state manifests (max abs diff 0.0);
  (3) replaces the previous 5 exemplars with 5 new ones chosen to each
      make a different point (genuine large success with a forcing-window
      -aligned rise; a visually-confirmed multi-frame split; a
      structural "no boundary/live-parent actuator was even available"
      failure; an ordinary/no-particular-reason failure; a
      kinematic-predictor-reversal caution case) instead of covering
      score-magnitude buckets only.

This IS a legitimate small re-run under an already-frozen, already-validated
protocol purely to produce visualization frame data (full per-step r/z and
per-frame ForwardMaterialTrace611 status were never persisted by the
confirmatory stages, which only kept summary outcome metrics) -- it is not
new science and does not need a fresh confirmatory campaign. See
`EXEMPLAR_SELECTION.md` in this directory for exactly which tuples were
chosen and why.

v1 is dropped entirely from this tab (see EXEMPLAR_SELECTION.md's
rationale) -- ForwardMaterialTrace611 is the sole identity/membership
layer driving the visualization.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

FLOCK_ROOT = Path(__file__).resolve().parents[4]
S612_CODE = FLOCK_ROOT / "stage6_12_control_readiness" / "code"
S612B_CODE = FLOCK_ROOT / "stage6_12B_contact_persistence" / "code"
S612C_CODE = FLOCK_ROOT / "stage6_12C_kinematic_contact_confirmation" / "code"
S612C_DATA = FLOCK_ROOT / "stage6_12C_kinematic_contact_confirmation" / "data"
CLOSURE_DATA = FLOCK_ROOT / "final_translating_flock_closure" / "data"

for _p in (S612_CODE, S612B_CODE, S612C_CODE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import common_612 as C            # noqa: E402  (make_flock, load_frozen_rule, bulk_centroid, frac_at_heading, torus geometry, L_BOX, ForwardMaterialTrace611)
import intervention_612 as I611   # noqa: E402  (simulate_branch, trace_target, outcome_metrics -- FROZEN, reused unmodified)
import intervention_612b as IB    # noqa: E402  (add_conservative, kinematic_contact_scores -- FROZEN, reused unmodified)

OUT = Path(__file__).resolve().parents[2] / "data" / "tab6_translation.json"

D_PRIMARY = 8
R_RELEASE = 24
N_STEPS = D_PRIMARY + R_RELEASE   # 32
N_SCAN = 15   # pre-qualification lead-in frames shown, out of the full t0 available

# ---------------------------------------------------------------------
# Exemplar tuples -- see EXEMPLAR_SELECTION.md "Second-pass curation" for
# the full scan, the independent (non-tracker) verification performed for
# each, and what was ruled out along the way.
# physics_seed formulas are QUOTED from the source stages, not reinvented:
#   closure:  40_000_000 + state_idx*1000 + r     (run_closureAB.py)
#   612C:     14_000_000 + state_idx*1000 + r     (run_confirmatory_612c.py, confirm streams)
# ---------------------------------------------------------------------
EXEMPLARS = [
    dict(
        key="612c02_a357", source="612c", state_idx=2, actuator=357, stream_r=6,
        actuator_class=None,
        actuator_selection="broad-scan realization (not selected by any predictor; found by scanning ~48 candidate rollouts for genuinely large, forcing-window-aligned effects)",
        caption=("The largest genuine effect found in a ~48-candidate broad scan. "
                 "frac-at-target-heading among traced members visibly rises DURING the "
                 "8-step forcing window (0.00→0.26 by t=7) and keeps climbing through "
                 "release to 0.93 -- independently confirmed by re-plotting both the "
                 "traced-member fraction and the all-bird fraction at target heading "
                 "(matplotlib spot-check, not just this metric). This is the per-stream "
                 "'outcome oracle' scale of effect Stage 6.12C's ORACLE_DECOMPOSITION.md "
                 "documents CAN occur (mean ~0.022 vs random's ~0.003) -- shown here as a "
                 "genuine large realization, not as a reproducible or predictable strategy: "
                 "no predictor in the programme (kinematic, organizational-role, or "
                 "search-selected) reliably finds cases like this in advance."),
        chip_label="strong success · ΔJ≈+0.86",
    ),
    dict(
        key="sclosure02_a270", source="closure", state_idx=2, actuator=270, stream_r=1,
        actuator_class="near_exterior_non_parent",
        actuator_selection="organizational-role sampled (near exterior, not a live causal parent at onset)",
        caption=("Visually confirmed split, not just a single advisory flag: the traced "
                 "population bifurcates into two spatially distinct clusters at t=19, "
                 "t=26, and t=31 (matplotlib spot-check of raw bird positions colored by "
                 "membership -- see EXEMPLAR_SELECTION.md figures). ForwardMaterialTrace611 "
                 "follows its own continuation rule (largest retained share) each time, so "
                 "the displayed population is always the SAME rule applied consistently, "
                 "never a hand-picked branch. Note the scoring quirk this exposes: the raw "
                 "association metric ΔJ_assoc is mildly POSITIVE (+0.047), but the "
                 "conservative scoring used everywhere else in this programme sets "
                 "ΔJ_conservative to exactly 0 for ANY split-flagged trial, by construction "
                 "(3 split flags here) -- a deliberately conservative accounting choice, not "
                 "a claim that nothing happened."),
        chip_label="split (visually confirmed) · ΔJ_cons=0",
    ),
    dict(
        key="sclosure00_a313", source="closure", state_idx=0, actuator=313, stream_r=1,
        actuator_class="near_exterior_non_parent",
        actuator_selection="organizational-role sampled -- the only exterior class this state had at qualification",
        caption=("Structural failure mode: this state (sclosure_00) had ZERO boundary-"
                 "member and ZERO live-exterior-parent candidates available at "
                 "qualification (disclosed in "
                 "final_translating_flock_closure/ORGANIZATIONAL_ROLE_RESULTS.md -- 5 of "
                 "the 8 closure states have this constraint). The actuator shown is the "
                 "best-available class (near-exterior non-parent); control still nets a "
                 "small negative outcome and the collective does not visibly turn toward "
                 "the target heading. This is a genuine 'no actuator of the relevant class "
                 "was ever available here' case, not a tuning failure."),
        chip_label="failure · no boundary/parent access",
    ),
    dict(
        key="612c06_a17", source="612c", state_idx=6, actuator=17, stream_r=6,
        actuator_class=None,
        actuator_selection="ordinary candidate, no distinguishing selection criterion",
        caption=("Unremarkable failure: no split/merge flag, an ordinary (not "
                 "kinematic-top, not organizational-role-privileged) candidate, small "
                 "negative ΔJ_conservative close to this state's typical/median realization. "
                 "Included because a lot of the time, nothing distinctive is going on "
                 "mechanistically and control simply doesn't move the collective toward the "
                 "target -- an honest 'ordinary noise' case, not every failure has a "
                 "structural or dramatic explanation."),
        chip_label="failure · ordinary, no particular reason",
    ),
    dict(
        key="612c01_a266", source="612c", state_idx=1, actuator=266, stream_r=0,
        actuator_class=None,
        actuator_selection="kinematic-predicted top candidate (not shown to be reliably better)",
        caption=("The kinematic score's top pick on THIS state, THIS single realization "
                 "(physics stream r=0): ΔJ_conservative=-0.0037. Shown deliberately so this "
                 "demo does not imply the kinematic score is 'usually right, just noisy' -- "
                 "the confirmatory pass (PREDICTOR_VALIDATION.md) found a mild top-vs-"
                 "bottom-quartile REVERSAL, and this state's own 8-confirmatory-stream mean "
                 "for this same candidate is -0.0092, i.e. consistently non-helpful here, "
                 "not just this one draw. (The two numbers -- this single stream's -0.0037 "
                 "and the state's 8-stream mean -0.0092 -- are reported separately here on "
                 "purpose, since conflating a single realization with a multi-stream mean "
                 "was part of what made the first curation pass misleading.)"),
        chip_label="kinematic-top · negative",
    ),
]


def load_state(source: str, state_idx: int) -> dict:
    if source == "closure":
        manifest = json.load(open(CLOSURE_DATA / "state_manifest_closure.json"))
    else:
        manifest = json.load(open(S612C_DATA / "state_manifest_612c.json"))
    return manifest["states"][state_idx]


def physics_seed_for(source: str, state_idx: int, r: int) -> int:
    base = 40_000_000 if source == "closure" else 14_000_000
    return base + state_idx * 1000 + r


def kinematic_score_for(state: dict, mf, actuator: int) -> float | None:
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(int(x) for x in state["interior0"])
    pool = state["pool20"]
    if actuator not in [int(p) for p in pool]:
        return None
    scores = IB.kinematic_contact_scores(r0, z0, pool, seed_members, C.L_BOX, mf.v, D_PRIMARY, R=mf.R)
    return scores.get(int(actuator))


def scanning_frames(mf, rule, state: dict) -> list[dict]:
    """Genuine (not fabricated) pre-qualification lead-in: re-runs the EXACT
    deterministic qualification rng (`state["seed"]`) forward from t=0 using
    the same `mf.step`, and keeps the last N_SCAN steps before `state["t0"]`
    (qualification time). Bit-exact verified at build time (final r,z must
    match the manifest's r0/z0 exactly) before being trusted. No target is
    LOCKED yet during this phase -- material_members/actuators/target_heading
    stay empty/null, honestly, since the real qualification process does not
    have a committed target before t0 either.

    What IS shown now (previously nothing): at every scanning step this
    function also calls `C.detect_propose(r, z_window, C.L_BOX)` and feeds
    the result through a fresh `C.ForwardMaterialTrace611(rule)`, using the
    EXACT SAME window-building convention (rolling z_window capped at
    C.AFFINITY_WINDOW, `len(z_window) >= 2` gate) and the exact same
    start/step call sequence as
    `stage6_12C_kinematic_contact_confirmation/code/world_sampling_612c.py`'s
    `try_world` (and `final_translating_flock_closure/code/
    world_sampling_closure.py`'s copy of the same loop) -- because
    `common_612.detect_propose` IS `detect_69.propose` and
    `common_612.ForwardMaterialTrace611` IS `forward_material_trace_611.
    ForwardMaterialTrace611`, re-exported unmodified through common_612c.py
    and common_closure.py (verified by reading both; not re-derived here).
    This is not a new/reimplemented detector -- it is the literal machinery
    that decided which cluster eventually became this state's qualified
    material target, replayed on the same bit-exact trajectory.

    Two new per-frame fields result:
      - candidate_preview: ALL clusters `detect_propose` proposes this step
        (list of member-id lists) -- i.e. everything genuinely "under
        evaluation" at this step, not just the one the tracker happens to be
        dwelling on. Chosen over showing only the eventual winner because
        that is the more honest answer to "what candidates are being
        evaluated" (see task note / EXEMPLAR_SELECTION.md).
      - candidate_frontrunner: the ForwardMaterialTrace611 instance's
        CURRENTLY-ACCEPTED (dwelling) cluster, i.e. the candidate that is
        presently the front-runner toward eventual qualification -- empty
        until the tracker first acquires a candidate (matches v2's own
        empty/centered t=0 behaviour; nothing is invented before the
        detector actually proposes something).
    `centre` for scanning frames is the bulk centroid of the front-runner
    when one exists, else of the single largest proposed candidate that
    step, else None -- giving the co-moving frame something live to
    recenter on during scanning, mirroring v2's `interior`-tracks-centre
    behaviour, without reintroducing v1's tracker."""
    seed = int(state["seed"]); t0 = int(state["t0"])
    rng = np.random.default_rng(seed)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)
    hist = [(r.copy(), z.copy())]

    z_window: list[np.ndarray] = []
    tr = None
    per_step = []  # per_step[t] = (candidate_lists, frontrunner_list), aligned with hist[t]
    r_cur, z_cur = r, z
    for t in range(t0):
        z_window.append(z_cur.copy())
        if len(z_window) > C.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = C.detect_propose(r_cur, z_window, C.L_BOX) if len(z_window) >= 2 else []
        cands = [frozenset(int(x) for x in c) for c in cands]
        if tr is None and cands:
            tr = C.ForwardMaterialTrace611(rule)
            tr.start(t, cands[0])
        elif tr is not None:
            d = tr.step(t, cands)
            if d.status == "dead":
                tr = None
        per_step.append((
            [sorted(int(x) for x in c) for c in cands],
            sorted(int(x) for x in tr.accepted) if (tr is not None and tr.accepted) else [],
        ))
        r_cur, z_cur, _ = mf.step(r_cur, z_cur, rng)
        hist.append((r_cur.copy(), z_cur.copy()))

    r_final, z_final = hist[-1]
    assert np.allclose(r_final, np.array(state["r0"])), "scanning replay mismatch (r)"
    assert np.array_equal(z_final, np.array(state["z0"], dtype=int)), "scanning replay mismatch (z)"

    n_scan = min(N_SCAN, t0)
    lead_in = hist[-(n_scan + 1):-1] if n_scan > 0 else []  # excludes hist[-1] == frame t=0 of control (added separately)
    lead_info = per_step[-n_scan:] if n_scan > 0 else []
    assert len(lead_in) == len(lead_info)

    frames = []
    for i, ((r_s, z_s), (cand_lists, frontrunner)) in enumerate(zip(lead_in, lead_info)):
        anchor = frontrunner if frontrunner else (cand_lists[0] if cand_lists else [])
        centre = C.bulk_centroid(r_s, anchor, C.L_BOX).tolist() if anchor else None
        frames.append({
            "t": i,
            "r": [[round(float(x), 3), round(float(y), 3)] for x, y in r_s],
            "z": [int(v) for v in z_s],
            "phase": "scanning",
            "material_members": [],
            "actuators": [],
            "target_heading": None,
            "centre": centre,
            "material_retention": None,
            "forward_material_trace": None,
            "candidate_preview": cand_lists,
            "candidate_frontrunner": frontrunner,
        })
    return frames


def run_exemplar(mf, rule, ex: dict) -> dict:
    state = load_state(ex["source"], ex["state_idx"])
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(int(x) for x in state["interior0"])
    h_star = int(state["h_star"])
    z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]
    actuator = int(ex["actuator"])
    physics_seed = physics_seed_for(ex["source"], ex["state_idx"], ex["stream_r"])

    # --- forced (actuated) rollout ---
    r_hist, z_hist = I611.simulate_branch(mf, r0, z0, physics_seed, [actuator], h_star, D_PRIMARY, N_STEPS)
    tr = I611.trace_target(r_hist, z_hist, z_context, seed_members, rule)
    out = I611.outcome_metrics(tr, z_hist, h_star, D_PRIMARY, r_hist=r_hist, S=[actuator], mf=mf)
    out = IB.add_conservative(out)

    # --- CRN-paired no-control baseline, same physics_seed, for delta ---
    r_hist_nc, z_hist_nc = I611.simulate_branch(mf, r0, z0, physics_seed, None, h_star, 0, N_STEPS)
    tr_nc = I611.trace_target(r_hist_nc, z_hist_nc, z_context, seed_members, rule)
    out_nc = I611.outcome_metrics(tr_nc, z_hist_nc, h_star, D_PRIMARY)
    out_nc = IB.add_conservative(out_nc)

    delta_j_conservative = out["J_conservative"] - out_nc["J_conservative"]
    delta_j_assoc = out["J_assoc"] - out_nc["J_assoc"]

    kin_score = kinematic_score_for(state, mf, actuator) if ex["source"] == "612c" else None

    # --- pre-qualification scanning lead-in (genuine replay, see scanning_frames docstring) ---
    scan_frames = scanning_frames(mf, rule, state)
    n_scan = len(scan_frames)

    # --- per-frame records (control + release) ---
    frames = []
    prev_members = None
    for t in range(len(r_hist)):
        members = sorted(int(x) for x in (tr.history[t].accepted_members or []))
        retention = None
        if prev_members is not None:
            i_prev, i_cur = set(prev_members), set(members)
            overlap = len(i_prev & i_cur)
            union = len(i_prev | i_cur)
            retention = {
                "R_old": (overlap / len(i_prev)) if i_prev else None,
                "R_new": (overlap / len(i_cur)) if i_cur else None,
                "jaccard": (overlap / union) if union else None,
                "n_retained": overlap,
                "n_lost": len(i_prev) - overlap,
                "n_gained": len(i_cur) - overlap,
                "prev_size": len(i_prev),
                "cur_size": len(i_cur),
                "retained_ids": sorted(i_prev & i_cur),
                "lost_ids": sorted(i_prev - i_cur),
                "gained_ids": sorted(i_cur - i_prev),
                "overlap_zero": overlap == 0,
            }
        dec = tr.history[t]
        centre = None
        anchor_set = members or list(seed_members)
        if anchor_set:
            centre = C.bulk_centroid(r_hist[t], anchor_set, C.L_BOX).tolist()
        frames.append({
            "t": n_scan + t,
            "r": [[round(float(x), 3), round(float(y), 3)] for x, y in r_hist[t]],
            "z": [int(v) for v in z_hist[t]],
            "phase": "control" if t < D_PRIMARY else "release",
            "material_members": members,
            "actuators": [actuator] if t < D_PRIMARY else [],
            "target_heading": h_star,
            "centre": centre,
            "material_retention": retention,
            "forward_material_trace": {
                "status": dec.status,
                "n_members": len(members),
                "split_flag": bool(dec.split_flag),
                "merge_flag": bool(dec.merge_flag),
                "steps_unresolved": int(dec.steps_unresolved),
                "n_candidates": len(dec.all_candidate_metrics),
                "n_accepting_candidates": int(dec.n_accepting_candidates),
                "frac_trace_at_target": C.frac_at_heading(dec.accepted_members, z_hist[t], h_star),
                "reason": dec.reason,
            },
            "candidate_preview": [],
            "candidate_frontrunner": [],
        })
        prev_members = members

    all_frames = scan_frames + frames

    frac_trace = [{"t": i, "frac": None} for i in range(n_scan)] + \
        [{"t": n_scan + f["t"], "frac": f["forward_material_trace"]["frac_trace_at_target"]} for f in frames]

    events = [
        {"event": "scanning_start", "t": 0},
        {"event": "qualified_and_target_set", "t": n_scan},
        {"event": "release_begin", "t": n_scan + D_PRIMARY},
        {"event": "episode_end", "t": n_scan + len(r_hist) - 1},
    ]

    control_summary = {
        "actuator": actuator,
        "actuator_class": ex["actuator_class"],
        "actuator_selection": ex["actuator_selection"],
        "kinematic_score": kin_score,
        "delta_J_conservative": delta_j_conservative,
        "delta_J_assoc": delta_j_assoc,
        "V": out["V"], "V_conservative": out["V_conservative"],
        "event": out["event"], "event_corrected": out["event_corrected"],
        "physics_seed": physics_seed,
        "state_id": state["state_id"],
        "caption": ex["caption"],
    }

    return dict(
        N=mf.N, L=mf.L, ended_phase="release",
        outcome_label=ex["chip_label"],
        control_summary=control_summary,
        frames=all_frames, events=events,
        frac_interior_at_target_trace=frac_trace,
        final_t=len(all_frames) - 1,
        n_scan=n_scan,
    )


def sanity_check(key: str, seed_out: dict, ex: dict):
    """Cross-check delta_J_conservative against the value already recorded
    in the source stage's own saved rollout data, where available -- this
    is an exact-replay check (same physics_seed, same frozen code), not a
    new statistical claim."""
    cs = seed_out["control_summary"]
    if ex["source"] == "closure":
        rows = json.load(open(CLOSURE_DATA / "closureAB_rollouts.json"))
        match = [r for r in rows if r["state_id"] == cs["state_id"] and r["actuator"] == cs["actuator"]
                 and r["stream_idx"] == ex["stream_r"]]
        if match:
            recorded = match[0]["delta_J_conservative"]
            ok = abs(recorded - cs["delta_J_conservative"]) < 1e-6
            print(f"  [{key}] replay check vs closureAB_rollouts.json: recorded={recorded:.4f} "
                  f"replayed={cs['delta_J_conservative']:.4f} {'OK' if ok else 'MISMATCH'}")
    else:
        rows = json.load(open(S612C_DATA / "k1_rollouts_612c.json"))
        match = [r for r in rows if r["state_id"] == cs["state_id"] and r["candidate"] == cs["actuator"]
                 and r.get("stream_role") == "confirm" and r["stream_idx"] == ex["stream_r"]]
        if match:
            recorded = match[0]["delta_conservative"]
            ok = abs(recorded - cs["delta_J_conservative"]) < 1e-6
            print(f"  [{key}] replay check vs k1_rollouts_612c.json: recorded={recorded:.4f} "
                  f"replayed={cs['delta_J_conservative']:.4f} {'OK' if ok else 'MISMATCH'}")


def main():
    mf = C.make_flock()
    rule, frozen = C.load_frozen_rule()

    seeds_out = {}
    seed_order = []
    for ex in EXEMPLARS:
        print(f"replaying {ex['key']} ...")
        seed_out = run_exemplar(mf, rule, ex)
        seeds_out[ex["key"]] = seed_out
        seed_order.append(ex["key"])
        sanity_check(ex["key"], seed_out, ex)

    out = {
        "provenance": {
            "source": ("Re-run of the FROZEN confirmatory intervention protocol "
                       "(K=1, d=8, release=24) on tuples drawn from the confirmatory seed "
                       "manifests: stage6_12C_kinematic_contact_confirmation/data/"
                       "state_manifest_612c.json (seeds 63200-63209) and "
                       "final_translating_flock_closure/data/state_manifest_closure.json "
                       "(seeds 64200-64207). Physics/tracker code (simulate_branch, "
                       "trace_target, outcome_metrics, ForwardMaterialTrace611, "
                       "kinematic_contact_scores) imported unmodified from "
                       "stage6_12_control_readiness/code/ and "
                       "stage6_12B_contact_persistence/code/ -- not reimplemented. Scanning "
                       "lead-in frames are a genuine replay of the exact deterministic "
                       "qualification rng (state manifest's own `seed`/`t0`), bit-exact "
                       "verified against the recorded qualification r0/z0, not fabricated."),
            "identity_version": ("ForwardMaterialTrace611 (frozen, Jaccard>=0.30) -- the "
                                 "PRIMARY and ONLY identity/membership layer in this view. "
                                 "v1 (LineageTracker611) is not shown; see "
                                 "src/data_prep/EXEMPLAR_SELECTION.md for why it was dropped "
                                 "rather than kept as a toggle."),
            "geometry": "torus_delta minimum-image wrapping, geometry_611.py (reused unmodified)",
            "protocol": (f"K=1 (single exterior/organizational-role or scan-selected actuator), "
                        f"d={D_PRIMARY} step forcing, release={R_RELEASE} steps, {N_STEPS} total "
                        "control/release steps per rollout, preceded by a genuine "
                        f"(up to {N_SCAN}-step) pre-qualification scanning lead-in. CRN-paired "
                        "against a same-physics-seed no-control baseline for "
                        "delta_J_conservative. This tab deliberately shows the FROZEN K=1 "
                        "singleton-actuator confirmatory protocol only -- a K=2 secondary arm "
                        "exists and was found similarly unreliable (K2_SECONDARY.md, "
                        "90% CI spans zero); genuine multi-actuator / adaptive / online "
                        "control strategies are Tab 5's subject, not this tab's."),
            "exemplar_selection": ("See src/data_prep/EXEMPLAR_SELECTION.md for the full scan "
                                   "(~48 full-replay candidates across both confirmatory "
                                   "sources) and the independent, non-tracker verification "
                                   "(matplotlib spot-checks of raw bird positions and "
                                   "alignment traces) behind each of the 5 exemplars: one "
                                   "genuinely large success with a forcing-window-aligned "
                                   "alignment rise, one visually-confirmed multi-frame split, "
                                   "one structural 'no boundary/live-parent actuator was ever "
                                   "available' failure, one ordinary/no-particular-reason "
                                   "failure, and one kinematic-predictor-reversal caution case."),
            "programme_finding": ("Across Stage 6.9 through the final closure, no static "
                                  "actuator-selection strategy (historical authority, kinematic "
                                  "predicted contact, organizational role, directed causal "
                                  "topology) was found to reliably outperform random/matched "
                                  "selection; the apparent per-stream-maximum 'oracle' advantage "
                                  "is real (large, state-clustering-robust) but not explained by "
                                  "or predictable from any tested feature, including physical "
                                  "contact (ORACLE_DECOMPOSITION.md's Case C). Control "
                                  "opportunity in this system looks predominantly "
                                  "stochastic/trajectory-conditioned. See "
                                  "stage6_flock/TRANSLATING_FLOCK_FINAL_SYNTHESIS.md."),
            "split_merge_semantics": ("split_flag/merge_flag are ForwardMaterialTrace611 "
                                      "ADVISORY heuristics (Jaccard-overlap based), never "
                                      "validated against an independently confirmed physical "
                                      "split/merge ground truth -- never labeled 'confirmed' "
                                      "anywhere in this UI. Conservative scoring "
                                      "(V_conservative/J_conservative) sets the outcome to 0 for "
                                      "ANY split- or merge-flagged trial by construction, "
                                      "regardless of the raw association metric -- see the "
                                      "split exemplar's caption for a concrete illustration. See "
                                      "stage6_12B_contact_persistence/IDENTITY_SEMANTICS_CORRECTION.md."),
            "scanning_phase": ("Pre-qualification lead-in frames (phase='scanning') replay the "
                              "exact deterministic world-sampling rng from t=0 forward to the "
                              "state's own qualification time, using the unmodified "
                              "common_612.make_flock()/mf.step -- the SAME process that "
                              "originally qualified this state. No target heading is LOCKED yet "
                              "and no material_members are tracked during this phase (the real "
                              "qualification process does not have either of those things before "
                              "t0 either). What IS shown: at every scanning step, "
                              "common_612.detect_propose (== detect_69.propose, re-exported "
                              "unmodified) and a fresh common_612.ForwardMaterialTrace611 are run "
                              "exactly as stage6_12C_kinematic_contact_confirmation/code/"
                              "world_sampling_612c.py's (and final_translating_flock_closure's "
                              "matching) try_world loop runs them during real qualification -- "
                              "the literal machinery that decides which cluster eventually "
                              "becomes the material target, not a reimplementation. "
                              "candidate_preview lists EVERY cluster detect_propose proposes that "
                              "step (all candidates genuinely under evaluation); "
                              "candidate_frontrunner is whichever cluster the tracker is "
                              "currently dwelling on toward eventual qualification, shown "
                              "distinctly from candidate_preview and from confirmed "
                              "material_members so provisional evaluation is never visually "
                              "confused with a confirmed target."),
            "frozen_rule": frozen,
        },
        "seed_order": seed_order,
        "seeds": seeds_out,
        "default_seed": seed_order[0],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out))
    print("wrote", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
