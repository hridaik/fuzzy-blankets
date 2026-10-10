"""Scoring metrics for Phase 2 validation (VALIDATION_PROTOCOL.md §5).

Deliberately reports an error TRADEOFF (several metrics side by side), per
the mandate's explicit prohibition on optimizing a single jump-count
scalar. A tracker that never detects, kills every track, or freezes a
stale label must score badly on `false_track_rate`/`unresolved_frac` even
if its switch count looks good -- these are reported on the same table,
never hidden in a footnote.
"""
from __future__ import annotations

import numpy as np


def best_match_jaccard(pred_members: set, truth_members: set) -> float:
    if not pred_members and not truth_members:
        return 1.0
    inter = len(pred_members & truth_members)
    union = len(pred_members | truth_members)
    return inter / union if union else 0.0


def score_run(truth_seq: list, pred_snapshots: list) -> dict:
    """truth_seq: list of {true_label_id: set(members)} per step.
    pred_snapshots: list of {pred_label_id: {members: sorted list, status: str}} per step.

    For each step, greedily matches predicted labels to true labels by
    best Jaccard overlap (a simplified stand-in for the full
    assignment-based time-weighted trajectory metric family
    (arXiv:2110.13444) IDENTITY_MODEL.md §1 cites -- the full metric is
    not implemented in this pass; this is disclosed as a scope
    simplification, not claimed to be that metric)."""
    T = len(truth_seq)
    n_true_objects = []
    n_pred_objects = []
    localization_errors = []
    unresolved_frac_per_pred = {}
    switch_events = 0
    prev_best_match = {}  # true_label -> pred_label matched last step
    frag_count = {}       # true_label -> set of distinct pred_labels ever matched to it

    false_track_steps = 0
    missed_true_steps = 0
    total_true_steps = 0
    total_pred_steps = 0

    for t in range(T):
        truth = truth_seq[t]
        pred = pred_snapshots[t]
        pred_sets = {pid: set(info["members"]) for pid, info in pred.items()}
        n_true_objects.append(len(truth))
        n_pred_objects.append(len(pred_sets))
        total_true_steps += len(truth)
        total_pred_steps += len(pred_sets)

        matched_preds = set()
        for tlid, tmembers in truth.items():
            best_pid, best_j = None, 0.0
            for pid, pmembers in pred_sets.items():
                if pid in matched_preds:
                    continue
                j = best_match_jaccard(pmembers, tmembers)
                if j > best_j:
                    best_j, best_pid = j, pid
            if best_pid is None or best_j < 0.3:
                missed_true_steps += 1
                continue
            matched_preds.add(best_pid)
            localization_errors.append(1.0 - best_j)
            frag_count.setdefault(tlid, set()).add(best_pid)
            if tlid in prev_best_match and prev_best_match[tlid] != best_pid:
                switch_events += 1
            prev_best_match[tlid] = best_pid

        for pid in pred_sets:
            if pid not in matched_preds:
                false_track_steps += 1

    n_true_avg = float(np.mean(n_true_objects)) if n_true_objects else 0.0
    n_pred_avg = float(np.mean(n_pred_objects)) if n_pred_objects else 0.0

    return dict(
        mean_true_object_count=n_true_avg,
        mean_pred_object_count=n_pred_avg,
        object_count_bias=n_pred_avg - n_true_avg,
        mean_localization_error=float(np.mean(localization_errors)) if localization_errors else None,
        identity_switch_count=switch_events,
        mean_fragmentation=float(np.mean([len(v) for v in frag_count.values()])) if frag_count else None,
        false_track_rate=false_track_steps / max(total_pred_steps, 1),
        missed_true_rate=missed_true_steps / max(total_true_steps, 1),
        n_steps=T,
    )


def unresolved_and_confidence_stats(pred_snapshots: list) -> dict:
    """Anti-gaming metrics: unresolved time and (for trackers reporting
    one) false-confident assignment rate. A tracker that reports zero
    unresolved time by never abstaining is not automatically good --
    this is reported alongside false_track_rate/missed_true_rate above,
    never as a standalone success metric."""
    total = 0
    unresolved = 0
    for snap in pred_snapshots:
        for pid, info in snap.items():
            total += 1
            if info.get("status") in ("missed", "unresolved"):
                unresolved += 1
    return dict(unresolved_frac=unresolved / max(total, 1), total_label_steps=total)


def duplicate_invariance_check(tracker_cls, candidates_dup_factory, r, z, t, L):
    """Runs the SAME tracker on a candidate list vs. a duplicated version
    of it (per case), returns whether the resulting label set is identical
    -- MATHEMATICAL_CHECKS.md Case 2's hard architectural check, executed
    as code rather than only reasoned about on paper."""
    tr1 = tracker_cls(L=L)
    cands1 = candidates_dup_factory(1)
    tr1.step(cands1, r, z, t)
    snap1 = tr1.snapshot(t)

    tr2 = tracker_cls(L=L)
    cands2 = candidates_dup_factory(3)
    tr2.step(cands2, r, z, t)
    snap2 = tr2.snapshot(t)

    sets1 = sorted([tuple(sorted(v["members"])) for v in snap1.values()])
    sets2 = sorted([tuple(sorted(v["members"])) for v in snap2.values()])
    return dict(invariant=(sets1 == sets2), snap1_n=len(sets1), snap2_n=len(sets2))
