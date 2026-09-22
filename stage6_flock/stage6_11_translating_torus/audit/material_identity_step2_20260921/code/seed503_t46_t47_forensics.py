"""Step-2 dedicated forensics: seed 503, t=46->47.

Corrected observation (per task): the visually-jumpy transition is seed 503
around t=46->47, NOT seed 500. Step-1's lineage_forensics_611 output already
flags this exact transition as zero-overlap
(lineage_forensics_611__seed503__hypotheses.csv: map_hid 11->29 at t=47,
R_retain_step=0.0). This script replays the REAL, UNMODIFIED
lineage_611.LineageTracker611 + detect_69.propose against the recorded
ground-truth trajectory (viz_bundle_611__seed503.json) -- same technique as
lineage_forensics_611.py, same imports, same deterministic replay, only
narrower in scope (one seed, one transition, full bird-ID-level detail
instead of size-only summaries) -- to recover the actual member-ID sets that
audit/lineage_forensics_611__seed503__candidates.csv only reports by size.

No tracker/controller/detector code is modified. This is read-only replay.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parents[2]          # stage6_11_translating_torus/audit
STAGE_DIR = AUDIT_DIR.parent
CODE_DIR = STAGE_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import DATA_DIR, L_BOX  # noqa: E402
from flock_sim.model import UV4  # noqa: E402
from detect_69 import propose  # noqa: E402
from lineage_611 import LineageTracker611, dice, retention_purity  # noqa: E402
from identity_69 import centroid, field as make_field, estimate_translation, similarity  # noqa: E402
from geometry_611 import torus_delta  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "seed_traces"
SEED = 503


def load_frames():
    d = json.load(open(DATA_DIR / f"viz_bundle_611__seed{SEED}.json"))
    return d["frames"]


def frac_at_heading(z, ids, heading):
    ids = np.asarray(list(ids), dtype=int)
    if len(ids) == 0:
        return None
    return float((z[ids] == heading).mean())


def mean_heading_vector(z, ids, L=None):
    """Circular mean of the 4 discrete UV4 headings for a member set -- a
    descriptive summary only, not used by any scoring rule."""
    ids = list(ids)
    if not ids:
        return None
    vecs = UV4[z[np.asarray(ids, dtype=int)]]
    m = vecs.mean(axis=0)
    return dict(vx=float(m[0]), vy=float(m[1]), speed=float(np.hypot(*m)))


def replay_to(target_t: int):
    """Replay the real tracker frame-by-frame up to and including target_t,
    returning: the live hypotheses (member ID arrays) BEFORE the target_t
    update (i.e. state going into target_t, = state after target_t-1's
    update), the raw detector candidates AT target_t, and the tracker AFTER
    target_t's update (so the caller can see which hypothesis won)."""
    frames = load_frames()
    tracker: LineageTracker611 | None = None
    z_window: list[np.ndarray] = []
    pre_state = None
    cands_at_t = None
    for frame in frames:
        t = frame["t"]
        r = np.array(frame["r"])
        z = np.array(frame["z"], dtype=int)
        z_window.append(z.copy())
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r, z_window, L_BOX) if len(z_window) >= 2 else []

        if t == target_t:
            pre_state = [(h.hid, h.prob, sorted(int(x) for x in h.members)) for h in (tracker.hypotheses if tracker else [])]
            cands_at_t = [sorted(int(x) for x in c) for c in cands]

        if tracker is None and cands:
            tracker = LineageTracker611(L=L_BOX, uv4=UV4)
            tracker.start(cands[0], r, z, t)
        elif tracker is not None:
            tracker.update(cands, r, z, t)
            if not tracker.hypotheses and cands:
                tracker = LineageTracker611(L=L_BOX, uv4=UV4)
                tracker.start(cands[0], r, z, t)

        if t == target_t:
            post_state = [(h.hid, h.prob, sorted(int(x) for x in h.members)) for h in (tracker.hypotheses if tracker else [])]
            return dict(t=t, r=r, z=z, frame=frame, pre_hypotheses=pre_state,
                         candidates=cands_at_t, post_hypotheses=post_state)
    raise ValueError(f"t={target_t} not reached")


def main():
    OUT.mkdir(exist_ok=True)
    frames = load_frames()
    by_t = {f["t"]: f for f in frames}
    L = L_BOX
    target_heading = by_t[47]["target_heading"]
    assert by_t[46]["target_heading"] == target_heading == 2, "sanity: control active, target fixed"

    state46 = replay_to(46)
    state47 = replay_to(47)

    z46, z47 = state46["z"], state47["z"]
    r46, r47 = state46["r"], state47["r"]

    # Identify hid=11 (incumbent, displayed at t=46) and hid=29 (new MAP at
    # t=47) from the post-update hypothesis lists, matching by hid.
    post46 = {hid: (prob, members) for hid, prob, members in state46["post_hypotheses"]}
    pre47 = {hid: (prob, members) for hid, prob, members in state47["pre_hypotheses"]}  # == post46, sanity
    post47 = {hid: (prob, members) for hid, prob, members in state47["post_hypotheses"]}

    assert post46 == pre47, "replay determinism check: state entering t=47 must equal state exiting t=46"

    map_hid_46 = max(post46, key=lambda h: post46[h][0])
    map_hid_47 = max(post47, key=lambda h: post47[h][0])
    incumbent_members_46 = post46[map_hid_46][1]     # displayed interior at t=46 (hid 11's members)
    incumbent_prob_46 = post46[map_hid_46][0]
    new_map_members_47 = post47[map_hid_47][1]        # displayed interior at t=47 (hid 29's members)
    new_map_prob_47 = post47[map_hid_47][0]

    # Was the t=47 winner (map_hid_47) ALREADY a live, independently-tracked
    # hypothesis at t=46 (i.e. did it pre-exist the switch, rather than
    # being newly spawned this step)?
    preexisted = map_hid_47 in post46
    preexisting_members_46 = post46[map_hid_47][1] if preexisted else None
    preexisting_prob_46 = post46[map_hid_47][0] if preexisted else None

    incumbent_set = set(incumbent_members_46)
    new_set = set(new_map_members_47)
    overlap = incumbent_set & new_set
    union = incumbent_set | new_set

    def metrics(a: set, b: set):
        inter = len(a & b)
        u = len(a | b)
        return dict(
            retained=inter, lost=len(a - b), gained=len(b - a),
            R_old=(inter / len(a)) if a else None,
            R_new=(inter / len(b)) if b else None,
            jaccard=(inter / u) if u else None,
            dice=(2 * inter / (len(a) + len(b))) if (len(a) + len(b)) else None,
        )

    # For EVERY raw candidate at t=47, compute the full metric set vs the
    # incumbent (t=46 displayed) target -- this directly answers "did the
    # incumbent have another candidate continuation with materially greater
    # overlap" and "how much material does the newly selected candidate
    # share with the incumbent."
    candidate_table = []
    for ci, cand in enumerate(state47["candidates"]):
        cset = set(cand)
        m = metrics(incumbent_set, cset)
        c_incumbent = centroid(r46[list(incumbent_set)], L)
        c_cand = centroid(r47[list(cset)], L)
        disp = torus_delta(np.array(c_cand), np.array(c_incumbent), L)
        candidate_table.append(dict(
            cand_idx=ci, size=len(cset),
            is_new_map=(cset == new_set),
            is_preexisting_hid29_members=(preexisted and cset == set(preexisting_members_46)),
            **m,
            centroid_displacement_from_incumbent=float(np.hypot(*disp)),
            frac_at_target_heading_after=frac_at_heading(z47, cset, target_heading),
        ))
    candidate_table.sort(key=lambda d: -(d["R_old"] or 0))

    incumbent_metrics_vs_new = metrics(incumbent_set, new_set)
    incumbent_heading_before = frac_at_heading(z46, incumbent_set, target_heading)
    incumbent_heading_after_had_it_survived = None  # incumbent as a set doesn't exist at t=47 as a tracked object
    new_group_heading_before_selection = frac_at_heading(z46, preexisting_members_46, target_heading) if preexisted else None
    new_group_heading_after = frac_at_heading(z47, new_set, target_heading)

    report = dict(
        seed=SEED, transition="t=46 -> t=47", target_heading=int(target_heading),
        incumbent_hid=map_hid_46, incumbent_prob_at_46=incumbent_prob_46,
        incumbent_members_46=sorted(incumbent_members_46), incumbent_size_46=len(incumbent_members_46),
        new_map_hid=map_hid_47, new_map_prob_at_47=new_map_prob_47,
        new_map_members_47=sorted(new_map_members_47), new_map_size_47=len(new_map_members_47),
        new_map_preexisted_as_live_hypothesis_at_t46=preexisted,
        new_map_preexisting_hid=map_hid_47 if preexisted else None,
        new_map_preexisting_prob_at_46=preexisting_prob_46,
        new_map_preexisting_members_46=sorted(preexisting_members_46) if preexisted else None,
        incumbent_vs_new_map_metrics=incumbent_metrics_vs_new,
        incumbent_heading_frac_before_transition_t46=incumbent_heading_before,
        new_group_heading_frac_BEFORE_selection_t46=new_group_heading_before_selection,
        new_group_heading_frac_after_selection_t47=new_group_heading_after,
        all_t47_hypotheses=[dict(hid=h, prob=p, size=len(m), members=sorted(m)) for h, (p, m) in post47.items()],
        all_t46_hypotheses=[dict(hid=h, prob=p, size=len(m), members=sorted(m)) for h, (p, m) in post46.items()],
        candidate_table_t47_vs_incumbent=candidate_table,
        best_alternative_incumbent_continuation=candidate_table[0] if candidate_table else None,
    )
    json.dump(report, open(OUT / "seed503_t46_t47_forensics.json", "w"), indent=2)
    print(f"incumbent (hid {map_hid_46}, size {len(incumbent_members_46)}) vs "
          f"new MAP (hid {map_hid_47}, size {len(new_map_members_47)}): "
          f"overlap={incumbent_metrics_vs_new['retained']}, R_old={incumbent_metrics_vs_new['R_old']:.3f}, "
          f"R_new={incumbent_metrics_vs_new['R_new']:.3f}, jaccard={incumbent_metrics_vs_new['jaccard']:.3f}")
    print(f"new MAP pre-existed as live hypothesis at t=46: {preexisted} "
          f"(hid={map_hid_47}, prob_at_46={preexisting_prob_46})")
    print(f"new group heading frac BEFORE selection (t=46): {new_group_heading_before_selection}")
    print(f"new group heading frac AFTER selection (t=47): {new_group_heading_after}")
    print(f"incumbent heading frac before transition (t=46): {incumbent_heading_before}")
    print("best alternative incumbent continuation (any candidate, by R_old):",
          json.dumps(candidate_table[0], indent=2) if candidate_table else None)
    print("wrote", OUT / "seed503_t46_t47_forensics.json")


if __name__ == "__main__":
    main()
