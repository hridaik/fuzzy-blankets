"""Task B (spec S6): seed 503, t=46->47 -- candidate split vs confirmed
physical split. Step 2's `seed503_t46_t47_forensics.py` already established,
at the single t=46->47 transition, that the incumbent (37 members) has TWO
substantial material continuations at t=47: candidate 11 (18 members,
R_old=0.486) and candidate 12 (16 members, R_old=0.432) -- both clear the
frozen rule's split_min_share floor, and `ForwardMaterialTrace611` flags
SPLIT and follows candidate 11 (larger absolute retained count).

That single-transition evidence is NOT sufficient to call this a confirmed
PHYSICAL split (spec S6 explicitly forbids declaring one from a single
frame). This script extends the evidence forward: seeds an independent
ForwardMaterialTrace611 on EACH daughter fragment at t=47 (candidate 11 ->
"daughter A", the one Step 2's trace already follows; candidate 12 ->
"daughter B", the one it does not), and tracks both, separately, for the
remainder of the episode, using the identical real recorded trajectory and
the identical frozen rule. Reports, per step:
  - daughter A / B sizes, statuses, split/merge flags;
  - torus-aware centroid-to-centroid distance between A and B;
  - whether A and B's accepted member sets ever overlap again (a concrete,
    checkable "do they rejoin" signal, not inferred from distance alone);
  - each daughter's own heading-alignment fraction at the seed's
    target_heading.

No new physical-split threshold is invented. Per spec S6's explicit
instruction, if the evidence does not support a frozen criterion, this
script (and the accompanying SPLIT_MERGE_SEMANTICS.md) preserves
`unresolved` rather than manufacturing one.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parents[2]
STAGE_DIR = AUDIT_DIR.parent
CODE_DIR = STAGE_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import DATA_DIR, L_BOX  # noqa: E402
from detect_69 import propose  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402
import geometry_611 as geo  # noqa: E402

STEP2_CODE = AUDIT_DIR / "material_identity_step2_20260921" / "code"
sys.path.insert(0, str(STEP2_CODE))
from forward_material_trace_611 import ForwardMaterialTrace611, RULE_FAMILY_BUILDERS, overlap_metrics  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"
FROZEN_JSON = STEP2_CODE.parent / "data" / "identity_rule_calibration.json"
SEED = 503
TARGET_HEADING = 2  # from seed_503_t46_t47_forensics.md / STEP2_FINDINGS.md


def load_frozen_rule():
    calib = json.load(open(FROZEN_JSON))
    frozen = calib["frozen_rule"]
    return RULE_FAMILY_BUILDERS[frozen["letter"]](**frozen["params"]), frozen


def load_frames():
    d = json.load(open(DATA_DIR / f"viz_bundle_611__seed{SEED}.json"))
    return d["frames"]


def build_candidates_and_positions():
    frames = load_frames()
    z_window = []
    out = []          # out[i] = (t, candidates_list, r, z)
    for frame in frames:
        t = frame["t"]
        r = np.array(frame["r"])
        z = np.array(frame["z"], dtype=int)
        z_window.append(z.copy())
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r, z_window, L_BOX) if len(z_window) >= 2 else []
        out.append((t, [frozenset(int(x) for x in c) for c in cands], r, z))
    return out


def torus_centroid(members, r, L):
    pts = r[list(members)]
    theta = pts / L * 2 * np.pi
    c = np.arctan2(np.sin(theta).mean(axis=0), np.cos(theta).mean(axis=0))
    return (c / (2 * np.pi) * L) % L


def frac_at_target(members, z, heading):
    if not members:
        return None
    ids = np.array(list(members), dtype=int)
    return float((z[ids] == heading).mean())


def main():
    rule, frozen = load_frozen_rule()
    timeline = build_candidates_and_positions()
    by_t = {t: (cands, r, z) for t, cands, r, z in timeline}

    t47_cands, r47, z47 = by_t[47]
    t46_cands, r46, z46 = by_t[46]

    # cross-check against Step 2's already-established forensics: candidate
    # indices 11 (18 members) and 12 (16 members) at t=47.
    cand11 = t47_cands[11]
    cand12 = t47_cands[12]
    assert len(cand11) == 18 and len(cand12) == 16, (
        f"candidate-index reproduction MISMATCH vs seed503_t46_t47_forensics.md "
        f"(expected sizes 18/16, got {len(cand11)}/{len(cand12)}) -- STOP, per spec S15, "
        f"do not proceed on an unreproduced base fact")
    print(f"reproduced t=47 candidates 11/12 sizes: {len(cand11)}/{len(cand12)} -- matches Step 2 forensics, OK")

    daughters = {"A_followed": cand11, "B_unfollowed": cand12}
    traces = {}
    for name, seed_members in daughters.items():
        tr = ForwardMaterialTrace611(rule)
        tr.start(47, seed_members)
        traces[name] = tr

    ts_sorted = sorted(t for t in by_t if t >= 47)
    per_step_rows = []
    for t in ts_sorted[1:]:
        cands, r, z = by_t[t]
        for name, tr in traces.items():
            if tr.status != "dead":
                tr.step(t, cands)
        decA = traces["A_followed"].history[-1]
        decB = traces["B_unfollowed"].history[-1]
        memA = decA.accepted_members or frozenset()
        memB = decB.accepted_members or frozenset()
        rejoin_overlap = overlap_metrics(memA, memB) if memA and memB else None
        centroid_dist = None
        if memA and memB:
            cA = torus_centroid(memA, r, L_BOX)
            cB = torus_centroid(memB, r, L_BOX)
            centroid_dist = float(np.sqrt((geo.torus_delta(cA, cB, L_BOX) ** 2).sum()))
        per_step_rows.append(dict(
            t=t,
            A_status=decA.status, A_size=len(memA), A_split=decA.split_flag, A_merge=decA.merge_flag,
            A_frac_at_target=frac_at_target(memA, z, TARGET_HEADING),
            B_status=decB.status, B_size=len(memB), B_split=decB.split_flag, B_merge=decB.merge_flag,
            B_frac_at_target=frac_at_target(memB, z, TARGET_HEADING),
            AB_jaccard=(rejoin_overlap["jaccard"] if rejoin_overlap else None),
            AB_retained=(rejoin_overlap["retained"] if rejoin_overlap else None),
            centroid_distance=centroid_dist,
        ))

    # local scale for interpreting centroid_distance, computed the same way
    # hard_negative_validation.py does (2.5x median nearest-neighbour spacing)
    local_scale_46 = geo.local_scale(r46, L_BOX)

    result = dict(
        seed=SEED, split_transition_t=47, target_heading=TARGET_HEADING,
        local_scale_at_t46=float(local_scale_46),
        daughter_A_seed_size=len(cand11), daughter_B_seed_size=len(cand12),
        per_step=per_step_rows,
    )
    # summary stats
    max_A = max((r for r in per_step_rows), key=lambda r: r["t"])
    ever_rejoin = any((r["AB_retained"] or 0) > 0 for r in per_step_rows)
    min_centroid_dist = min((r["centroid_distance"] for r in per_step_rows if r["centroid_distance"] is not None), default=None)
    max_centroid_dist = max((r["centroid_distance"] for r in per_step_rows if r["centroid_distance"] is not None), default=None)
    n_steps_both_alive = sum(1 for r in per_step_rows if r["A_status"] != "dead" and r["B_status"] != "dead")
    result["summary"] = dict(
        n_steps_traced=len(per_step_rows),
        n_steps_both_daughters_alive=n_steps_both_alive,
        A_final_status=max_A["A_status"], B_final_status=max_A["B_status"],
        A_final_size=max_A["A_size"], B_final_size=max_A["B_size"],
        A_final_frac_at_target=max_A["A_frac_at_target"], B_final_frac_at_target=max_A["B_frac_at_target"],
        ever_any_member_overlap_between_daughters_after_split=ever_rejoin,
        min_centroid_distance_between_daughters=min_centroid_dist,
        max_centroid_distance_between_daughters=max_centroid_dist,
        min_centroid_distance_in_local_scale_units=(min_centroid_dist / local_scale_46) if min_centroid_dist is not None else None,
    )
    json.dump(result, open(OUT / "seed503_split_forensics.json", "w"), indent=2)
    print(json.dumps(result["summary"], indent=2))
    print("wrote", OUT / "seed503_split_forensics.json")


if __name__ == "__main__":
    main()
