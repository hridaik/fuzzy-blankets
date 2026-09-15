"""Real-replay comparison (VALIDATION_PROTOCOL.md §6): all four trackers
(v1, v2, baseline, proposed joint model) run over the SAME recorded raw
observation stream for seeds 500-504, physical replay only -- no
re-simulation, no tracker treated as ground truth.

Common reference-subject rule (disclosed, since none of RESULTS_6_11.md's
five real episodes has a pre-declared "this is the object" label): the
reference subject is the largest Louvain candidate at the first step where
one reaches >= REF_MIN_SIZE members. v1 and v2 (single-lineage-per-instance
trackers) are `start()`-ed on it directly. Baseline and joint (both
multi-object, natural-birth trackers) are run BLIND from t=0 with no
seeding at all; their own label with the highest Jaccard overlap against
the reference candidate at t_start is then followed as "their" reference
subject for the rest of the comparison -- this keeps their birth/coalescing
logic honest (never told where to look) while still allowing a same-subject
comparison across all four.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from candidate_proposals import propose_both
from joint_tracker import JointTracker
from baseline_tracker import BaselineTracker

_STAGE611 = Path(__file__).resolve().parents[2] / "code"
_AUDIT = Path(__file__).resolve().parents[2] / "audit"
for p in (_STAGE611, _AUDIT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import lineage_611  # noqa: E402
import lineage_v2_611  # noqa: E402

UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "phase2_results"
OUT_DIR.mkdir(exist_ok=True)
REF_MIN_SIZE = 20


def load_seed(seed):
    with open(DATA_DIR / f"viz_bundle_611__seed{seed}.json") as f:
        d = json.load(f)
    frames = [(np.array(fr["r"]), np.array(fr["z"]), fr["phase"]) for fr in d["frames"]]
    return d["L"], d["N"], frames


def find_reference_start(frames, L):
    z_hist = []
    for t, (r, z, phase) in enumerate(frames):
        z_hist.append(z)
        window = z_hist[-3:]
        cands = propose_both(r, z, window, L)
        if not cands:
            continue
        biggest = max(cands, key=len)
        if len(biggest) >= REF_MIN_SIZE:
            return t, biggest
    return None, None


def jaccard(a, b):
    a, b = set(a), set(b)
    u = len(a | b)
    return len(a & b) / u if u else 0.0


def run_seed(seed):
    L, N, frames = load_seed(seed)
    t_start, ref_members = find_reference_start(frames, L)
    if t_start is None:
        return dict(seed=seed, error="no candidate ever reached REF_MIN_SIZE")

    tr_v1 = lineage_611.LineageTracker611(L=L, uv4=UV4)
    tr_v2 = lineage_v2_611.LineageTrackerV2(L=L, uv4=UV4)
    tr_v1.start(np.array(sorted(ref_members)), frames[t_start][0], frames[t_start][1], t_start)
    tr_v2.start(np.array(sorted(ref_members)), frames[t_start][0], frames[t_start][1], t_start)

    bt = BaselineTracker(L=L)
    jt = JointTracker(L=L)
    baseline_ref_id = None
    joint_ref_id = None

    per_step = []
    z_hist = []
    for t, (r, z, phase) in enumerate(frames):
        z_hist.append(z)
        window = z_hist[-3:]
        cands = propose_both(r, z, window, L)

        if t >= t_start:
            tr_v1.update(cands, r, z, t)
            tr_v2.update(cands, r, z, t)
        bt.step(cands, r, z, t)
        jt.step(cands, r, z, t)

        # Retry finding the reference match for several steps after
        # t_start, not only exactly at t_start -- the joint tracker's own
        # birth-confirmation delay (BIRTH_CONFIRM_STEPS=2) guarantees its
        # snapshot AT t_start is empty by design, which an earlier version
        # of this script mistook for "never finds it" by only checking
        # once, at t==t_start, and never retrying (caught by this pass's
        # own sanity check on the results, not assumed correct beforehand).
        REF_MATCH_WINDOW = 6
        if baseline_ref_id is None and t_start <= t <= t_start + REF_MATCH_WINDOW:
            b_snap = bt.snapshot(t)
            best_j, best_id = 0.0, None
            for tid, info in b_snap.items():
                j = jaccard(info["members"], ref_members)
                if j > best_j:
                    best_j, best_id = j, tid
            if best_id is not None:
                baseline_ref_id = best_id

        if joint_ref_id is None and t_start <= t <= t_start + REF_MATCH_WINDOW:
            j_snap = jt.snapshot(t)
            best_j, best_id = 0.0, None
            for lid, info in j_snap.items():
                j = jaccard(info["members"], ref_members)
                if j > best_j:
                    best_j, best_id = j, lid
            if best_id is not None:
                joint_ref_id = best_id

        v1_members = []
        if tr_v1.hypotheses:
            v1_members = sorted(int(x) for x in max(tr_v1.hypotheses, key=lambda h: h.prob).members)
        v2_members = []
        dom2 = tr_v2.dominant() if hasattr(tr_v2, "dominant") else None
        if dom2 is not None:
            v2_members = sorted(int(x) for x in dom2.members)
        b_members = []
        if baseline_ref_id is not None:
            snap = bt.snapshot(t)
            if baseline_ref_id in snap:
                b_members = snap[baseline_ref_id]["members"]
            else:
                baseline_ref_id = None  # track died; stop reporting it
        j_members = []
        if joint_ref_id is not None:
            snap = jt.snapshot(t)
            if joint_ref_id in snap:
                j_members = snap[joint_ref_id]["members"]
            else:
                joint_ref_id = None

        per_step.append(dict(
            t=t, phase=phase,
            v1_n=len(v1_members), v2_n=len(v2_members), baseline_n=len(b_members), joint_n=len(j_members),
            jac_v1_v2=jaccard(v1_members, v2_members),
            jac_v1_baseline=jaccard(v1_members, b_members),
            jac_v1_joint=jaccard(v1_members, j_members),
            jac_v2_joint=jaccard(v2_members, j_members),
            jac_baseline_joint=jaccard(b_members, j_members),
        ))

    return dict(seed=seed, L=L, N=N, t_start=t_start, ref_size=len(ref_members),
                per_step=per_step, joint_event_log=jt.event_log,
                baseline_event_log=bt.event_log)


if __name__ == "__main__":
    all_results = []
    for seed in [500, 501, 502, 503, 504]:
        res = run_seed(seed)
        all_results.append(res)
        print(f"seed {seed}: t_start={res.get('t_start')}, ref_size={res.get('ref_size')}, "
              f"n_steps={len(res.get('per_step', []))}")
    with open(OUT_DIR / "real_replay_results.json", "w") as f:
        json.dump(all_results, f, indent=1)
    print(f"wrote real replay results to {OUT_DIR / 'real_replay_results.json'}")
