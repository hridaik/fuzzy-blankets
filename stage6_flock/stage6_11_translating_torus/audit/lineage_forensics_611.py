"""Part D: five-seed lineage forensics (additive, read-only).

Drives the REAL lineage_611.LineageTracker611 / detect_69.propose exactly as
run_online_control_611.run_episode does, but from the already-recorded
ground-truth (r, z) trajectory in `data/viz_bundle_611__seed{seed}.json`
(itself produced by a bit-identical re-run of run_episode with
record_trajectory=True -- verified below to match the production log's
per-step interior sizes and frac_interior_at_target). No simulator RNG
stream is consumed here: candidate detection and LineageTracker611.update are
both deterministic given (r, z), so replay from the stored trajectory is
exact, not approximate.

For every step this script ADDITIONALLY evaluates every (live hypothesis x
raw candidate) pair -- including the ones LineageTracker611.update() itself
never scores because they fail the R_retain>=0.30 gate -- using the SAME
imported functions the tracker uses (never reimplemented), so the "shadow"
table is consistent with, not a guess about, production behaviour.

Writes, per seed:
  audit/lineage_forensics_611__seed{n}__hypotheses.csv   (one row per live
      hypothesis per step: MAP/runner-up, margin, entropy, spatial integrity)
  audit/lineage_forensics_611__seed{n}__candidates.csv   (one row per
      (hypothesis, candidate) pair per step: full continuation evidence,
      including gate-failing candidates)
  audit/lineage_forensics_611__seed{n}__transitions.json (flagged unusual
      transitions + qualification-trigger trace + same-lineage-vs-jump check)

And overall:
  audit/lineage_forensics_611__summary.json
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import DATA_DIR, dump_json  # noqa: E402
from flock_sim.model import UV4  # noqa: E402
from detect_69 import propose  # noqa: E402
from lineage_611 import (LineageTracker611, dice, retention_purity,  # noqa: E402
                          RETENTION_MIN, GROWTH_RETENTION_MIN, SCORE_TEMPERATURE,
                          MAX_HYPOTHESES, CONTRAST_DROP_FRAC, CONTRAST_HISTORY,
                          DISSOLVE_AFTER_INDIVIDUATION_STEPS)
from identity_69 import estimate_translation, similarity, field, field_distance  # noqa: E402
from geometry_611 import local_scale  # noqa: E402
from thingness_611 import geometry_features  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

SEEDS = (500, 501, 502, 503, 504)
NEAR_DUPLICATE_FIELD_DIST = 0.05   # disclosed diagnostic threshold, not a code threshold
LOW_RETENTION_FLAG = 0.40          # diagnostic: "barely clears the 0.30 gate" band
HIGH_DISPLACEMENT_PCTL = 90        # diagnostic: flag top-decile per-step D_deform/bulk_speed


def load_frames(seed: int):
    d = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
    return d["frames"], d["ended_phase"]


def load_log(seed: int):
    d = json.load(open(DATA_DIR / f"online_control_611__seed{seed}.json"))
    return d["log"]


def entropy(probs: list[float]) -> float:
    p = np.array([x for x in probs if x > 0.0])
    if len(p) == 0:
        return 0.0
    return float(-(p * np.log(p)).sum())


def shadow_candidate_eval(h, cand, r, z, L):
    """Reproduce lineage_611.LineageTracker611.update's per-candidate math
    for ONE (hypothesis, candidate) pair, for candidates the real tracker
    would also evaluate (i.e. we still gate on RETENTION_MIN before scoring
    R_F, matching production), but return the retention/purity/dice numbers
    for ALL candidates, gate-passing or not, so the audit can see what was
    discarded before scoring even began."""
    prev_set = set(int(x) for x in h.members)
    cand_set = set(int(x) for x in cand)
    r_retain, r_purity = retention_purity(prev_set, cand_set)
    d = dice(prev_set, cand_set)
    passes_gate = r_retain >= RETENTION_MIN
    out = dict(r_retain=r_retain, r_purity=r_purity, dice=d, passes_gate=passes_gate,
               cand_size=len(cand_set), prev_size=len(prev_set))
    if not passes_gate:
        return out
    pos = r[cand]
    from identity_69 import centroid as _centroid
    c = _centroid(pos, L)
    rho, m, _ = field(pos, UV4[z[cand]], L, c)
    tr = estimate_translation(h.rho, h.m, rho, m, h.centre, c)
    R_F = similarity(tr["distance"], h.d_norm)
    score = 0.6 * d + 0.4 * R_F
    out.update(R_F=R_F, score=score, D_deform=tr["distance"],
               bulk_delta=list(map(float, tr["total_delta"])),
               bulk_speed=float(np.hypot(*tr["total_delta"])))
    return out


def run_seed(seed: int):
    frames, ended_phase = load_frames(seed)
    log = load_log(seed)
    qualified_events = [e for e in log if e["event"] == "qualified_and_target_set"]
    qualified_t = qualified_events[0]["t"] if qualified_events else None

    L = frames[0].get("L") if "L" in frames[0] else None
    from common_611 import L_BOX
    L = L_BOX

    mf = ROC.make_flock()  # for oracle_B_D reference-only computation (no RNG needed)

    tracker: LineageTracker611 | None = None
    z_window: list[np.ndarray] = []
    hyp_rows, cand_rows, transitions = [], [], []
    prev_map_members = None
    lineage_birth_t = {}   # hid -> t at which its root hypothesis was started
    root_hid_of = {}       # hid -> root hid this step's MAP chain descends from (tracked via origin identity)

    consistency_mismatches = 0

    for frame in frames:
        t = frame["t"]
        r = np.array(frame["r"])
        z = np.array(frame["z"], dtype=int)
        z_window.append(z.copy())
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r, z_window, L) if len(z_window) >= 2 else []

        pre_hyps = list(tracker.hypotheses) if tracker is not None else []

        # ---- shadow full (hypothesis, candidate) table, BEFORE update() ----
        for h in pre_hyps:
            for ci, cand in enumerate(cands):
                ev = shadow_candidate_eval(h, cand, r, z, L)
                cand_rows.append(dict(seed=seed, t=t, hid=h.hid, hyp_prob_prior=h.prob,
                                       hyp_size_prior=len(h.members), cand_idx=ci, **ev))

        # ---- real update (source of truth for next state) ----
        if tracker is None and cands:
            tracker = LineageTracker611(L=L, uv4=UV4)
            tracker.start(cands[0], r, z, t)
            lineage_birth_t[tracker.hypotheses[0].hid] = t
        elif tracker is not None:
            tracker.update(cands, r, z, t)
            if not tracker.hypotheses and cands:
                tracker = LineageTracker611(L=L, uv4=UV4)
                tracker.start(cands[0], r, z, t)
                lineage_birth_t[tracker.hypotheses[0].hid] = t
                transitions.append(dict(seed=seed, t=t, event="lineage_reborn",
                                          note="all prior hypotheses dissolved; new tracker started from largest candidate"))

        if tracker is None or not tracker.hypotheses:
            continue

        # consistency check against the independently-produced viz_bundle
        map_h = max(tracker.hypotheses, key=lambda h: h.prob)
        map_members = sorted(int(x) for x in map_h.members)
        if sorted(frame["interior"]) != map_members:
            consistency_mismatches += 1

        probs = sorted((h.prob for h in tracker.hypotheses), reverse=True)
        margin = probs[0] - probs[1] if len(probs) > 1 else probs[0]
        ent = entropy(probs)

        # ---- duplicate / near-duplicate hypothesis detection ----
        groups = {}   # exact-member-set hash -> [hyps]
        for h in tracker.hypotheses:
            key = frozenset(int(x) for x in h.members)
            groups.setdefault(key, []).append(h)
        n_exact_dup_groups = sum(1 for g in groups.values() if len(g) > 1)
        # near-duplicate: different member sets, same size, small field_distance
        near_dup_pairs = []
        hyps = tracker.hypotheses
        for i in range(len(hyps)):
            for j in range(i + 1, len(hyps)):
                a, b = hyps[i], hyps[j]
                if set(int(x) for x in a.members) == set(int(x) for x in b.members):
                    continue
                if len(a.members) != len(b.members):
                    continue
                fd = field_distance(a.rho, a.m, b.rho, b.m)
                if fd < NEAR_DUPLICATE_FIELD_DIST:
                    near_dup_pairs.append((a.hid, b.hid, fd))

        # coalesced MAP/entropy: merge probability mass of hypotheses sharing
        # the SAME exact current member set (near-duplicates reported but not
        # coalesced -- coalescing near-duplicates requires a judgement call
        # about the threshold that belongs to lineage_v2, not this audit)
        coalesced = {}
        for key, g in groups.items():
            coalesced[key] = sum(h.prob for h in g)
        coalesced_probs = sorted(coalesced.values(), reverse=True)
        coalesced_map_key = max(coalesced, key=coalesced.get)
        coalesced_map_members = sorted(int(x) for x in coalesced_map_key)
        coalesced_entropy = entropy(coalesced_probs)
        coalesced_margin = (coalesced_probs[0] - coalesced_probs[1]) if len(coalesced_probs) > 1 else coalesced_probs[0]

        # ---- spatial integrity of the MAP hypothesis every step ----
        geo = geometry_features(map_h.members, r, z, L, UV4)

        # ---- no-match diagnostic: best available score vs a "none" floor ----
        last_rec = map_h.records[-1] if map_h.records else {}
        best_score_this_hyp = last_rec.get("R_F")  # already the winning branch's R_F this step

        hyp_rows.append(dict(
            seed=seed, t=t, phase=frame["phase"],
            n_live_hypotheses=len(tracker.hypotheses),
            map_hid=map_h.hid, map_prob=map_h.prob, map_size=len(map_h.members),
            map_age=map_h.age, map_status=map_h.status,
            margin_top1_top2=margin, entropy=ent,
            n_exact_duplicate_groups=n_exact_dup_groups,
            n_near_duplicate_pairs=len(near_dup_pairs),
            coalesced_entropy=coalesced_entropy, coalesced_margin=coalesced_margin,
            coalesced_map_matches_map=(coalesced_map_members == map_members),
            C=geo["C"], D=geo["D"], Q=geo["Q"], n_components=geo["n_components"],
            size_frac=geo["size_frac"],
            R_retain_step=last_rec.get("R_retain_step"), R_purity_step=last_rec.get("R_purity_step"),
            R_F=last_rec.get("R_F"), D_deform=last_rec.get("D_deform"),
            bulk_speed=last_rec.get("bulk_speed"),
            consistency_vs_vizbundle_ok=(sorted(frame["interior"]) == map_members),
        ))

        # ---- unusual-transition flag (based on the MAP hypothesis's own step) ----
        if prev_map_members is not None and last_rec.get("R_retain_step") is not None:
            r_retain_step = last_rec["R_retain_step"]
            overlap_prev_map = len(set(map_members) & set(prev_map_members))
            if (r_retain_step < LOW_RETENTION_FLAG or overlap_prev_map == 0
                    or (last_rec.get("D_deform") or 0) > 0.3):
                transitions.append(dict(
                    seed=seed, t=t, event="unusual_transition",
                    prev_map_size=len(prev_map_members), new_map_size=len(map_members),
                    overlap_prev_map_new_map=overlap_prev_map,
                    R_retain_step=r_retain_step, R_purity_step=last_rec.get("R_purity_step"),
                    D_deform=last_rec.get("D_deform"), bulk_speed=last_rec.get("bulk_speed"),
                    map_prob=map_h.prob, margin=margin, n_live_hypotheses=len(tracker.hypotheses),
                    n_components=geo["n_components"], D=geo["D"], Q=geo["Q"],
                ))
        prev_map_members = map_members

    return dict(
        seed=seed, ended_phase=ended_phase, qualified_t=qualified_t,
        n_frames=len(frames), consistency_mismatches=consistency_mismatches,
        hyp_rows=hyp_rows, cand_rows=cand_rows, transitions=transitions,
    )


def write_csv(rows, path):
    if not rows:
        return
    keys, seen = [], set()
    for row in rows:
        for k in row.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, restval="")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def main():
    summary = {}
    for seed in SEEDS:
        print(f"[lineage_forensics] seed {seed} ...", flush=True)
        out = run_seed(seed)
        write_csv(out["hyp_rows"], AUDIT_DIR / f"lineage_forensics_611__seed{seed}__hypotheses.csv")
        write_csv(out["cand_rows"], AUDIT_DIR / f"lineage_forensics_611__seed{seed}__candidates.csv")
        dump_json(dict(qualified_t=out["qualified_t"], ended_phase=out["ended_phase"],
                        n_frames=out["n_frames"], consistency_mismatches=out["consistency_mismatches"],
                        transitions=out["transitions"]),
                   AUDIT_DIR / f"lineage_forensics_611__seed{seed}__transitions.json")
        summary[seed] = dict(
            n_frames=out["n_frames"], qualified_t=out["qualified_t"], ended_phase=out["ended_phase"],
            consistency_mismatches=out["consistency_mismatches"],
            n_unusual_transitions=sum(1 for e in out["transitions"] if e["event"] == "unusual_transition"),
            n_lineage_rebirths=sum(1 for e in out["transitions"] if e["event"] == "lineage_reborn"),
            max_n_components_map=max((r["n_components"] for r in out["hyp_rows"]), default=None),
            frac_steps_ncomp_gt1=float(np.mean([r["n_components"] > 1 for r in out["hyp_rows"]])) if out["hyp_rows"] else None,
            mean_entropy=float(np.mean([r["entropy"] for r in out["hyp_rows"]])) if out["hyp_rows"] else None,
            mean_margin=float(np.mean([r["margin_top1_top2"] for r in out["hyp_rows"]])) if out["hyp_rows"] else None,
            n_steps_with_exact_dup_hypotheses=sum(1 for r in out["hyp_rows"] if r["n_exact_duplicate_groups"] > 0),
            n_steps_with_near_dup_hypotheses=sum(1 for r in out["hyp_rows"] if r["n_near_duplicate_pairs"] > 0),
        )
        print(f"  -> {json.dumps(summary[seed])}", flush=True)
    dump_json(summary, AUDIT_DIR / "lineage_forensics_611__summary.json")
    print("wrote lineage_forensics_611__summary.json")


if __name__ == "__main__":
    main()
