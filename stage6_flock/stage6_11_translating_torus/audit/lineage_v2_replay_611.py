"""Replays lineage_v2 (audit comparator) on the same five ground-truth
trajectories used in LINEAGE_FORENSICS_6_11.md (viz_bundle_611__seed{n}.json),
side by side with a fresh v1 replay, to (a) show what v2 does differently at
seed 500 t=20/21 and (b) determine when each seed's lineage would qualify for
control under a per-lineage (not global-MAP) dwell rule.

Qualification rule tested here (item 2): a v2 lineage qualifies once its OWN
dwell >= QUALIFY_MIN_DURATION (not the tree-wide/global-MAP age), its size
fraction condition holds over its own last QUALIFY_MIN_DURATION records, and
net displacement over that same window clears the same bar as the original
-- i.e. the ORIGINAL three conditions, but evaluated against a dwell counter
that resets on a disjoint-lineage switch instead of one that never resets
short of total tracker death.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))
import common_611  # noqa: E402,F401

from common_611 import DATA_DIR, L_BOX, dump_json  # noqa: E402
from flock_sim.model import UV4  # noqa: E402
from detect_69 import propose  # noqa: E402
from lineage_611 import LineageTracker611  # noqa: E402
from lineage_v2_611 import LineageTrackerV2  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

SEEDS = (500, 501, 502, 503, 504)
QUALIFY_MIN_DURATION = ROC.QUALIFY_MIN_DURATION
QUALIFY_SIZE_RANGE = ROC.QUALIFY_SIZE_RANGE
QUALIFY_MIN_DISPLACEMENT_R = ROC.QUALIFY_MIN_DISPLACEMENT_R
from common_611 import R_PRIMARY  # noqa: E402


def load_frames(seed):
    d = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
    return d["frames"]


def check_qualify_v2(lin) -> dict:
    recs = [r for r in lin.records if r.get("size", 0) > 0]
    if lin.dwell < QUALIFY_MIN_DURATION or len(recs) < QUALIFY_MIN_DURATION:
        return dict(qualifies=False, reason="insufficient_dwell", dwell=lin.dwell)
    recent = recs[-QUALIFY_MIN_DURATION:]
    N = 400
    size_ok = float(np.mean([QUALIFY_SIZE_RANGE[0] <= r_["size"] / N <= QUALIFY_SIZE_RANGE[1] for r_ in recent])) >= 0.8
    disp = float(np.hypot(*np.sum([r_.get("bulk_delta", [0, 0]) for r_ in recent], axis=0)))
    ok = size_ok and disp >= QUALIFY_MIN_DISPLACEMENT_R * R_PRIMARY
    return dict(qualifies=bool(ok), dwell=lin.dwell, size_ok=bool(size_ok), displacement=disp,
                 required_displacement=QUALIFY_MIN_DISPLACEMENT_R * R_PRIMARY)


def replay_seed(seed: int):
    frames = load_frames(seed)
    L = L_BOX

    tracker1 = None
    tracker2 = LineageTrackerV2(L=L, uv4=UV4)
    z_window = []
    per_step = []
    v2_qualified_t = None
    v1_qualified_t_from_log = None
    log = json.load(open(DATA_DIR / f"online_control_611__seed{seed}.json"))["log"]
    qev = [e for e in log if e["event"] == "qualified_and_target_set"]
    if qev:
        v1_qualified_t_from_log = qev[0]["t"]

    tracker2_started = False
    for frame in frames:
        t = frame["t"]
        r = np.array(frame["r"]); z = np.array(frame["z"], dtype=int)
        z_window.append(z.copy())
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r, z_window, L) if len(z_window) >= 2 else []

        if tracker1 is None and cands:
            tracker1 = LineageTracker611(L=L, uv4=UV4)
            tracker1.start(cands[0], r, z, t)
        elif tracker1 is not None:
            tracker1.update(cands, r, z, t)
            if not tracker1.hypotheses and cands:
                tracker1 = LineageTracker611(L=L, uv4=UV4)
                tracker1.start(cands[0], r, z, t)

        if not tracker2_started and cands:
            tracker2.start(cands[0], r, z, t)
            tracker2_started = True
        elif tracker2_started:
            tracker2.update(cands, r, z, t)
            if not tracker2.lineages and cands:
                tracker2.start(cands[0], r, z, t)

        map1 = max(tracker1.hypotheses, key=lambda h: h.prob) if (tracker1 and tracker1.hypotheses) else None
        map2 = tracker2.dominant() if tracker2.lineages else None

        row = dict(t=t, phase=frame["phase"],
                    v1_map_hid=map1.hid if map1 else None, v1_map_size=len(map1.members) if map1 else None,
                    v1_map_prob=map1.prob if map1 else None,
                    v2_map_lid=map2.lid if map2 else None, v2_map_size=len(map2.members) if map2 else None,
                    v2_map_prob=map2.prob if map2 else None, v2_map_dwell=map2.dwell if map2 else None,
                    v2_entropy=tracker2.entropy(), v2_margin=tracker2.margin(),
                    v1_members=sorted(int(x) for x in map1.members) if map1 else [],
                    v2_members=sorted(int(x) for x in map2.members) if map2 else [],
                    overlap_v1_v2=(len(set(int(x) for x in map1.members) & set(int(x) for x in map2.members))
                                    if map1 and map2 else None))
        if map2 is not None and v2_qualified_t is None:
            q = check_qualify_v2(map2)
            row["v2_qualify_check"] = q
            if q["qualifies"]:
                v2_qualified_t = t
        per_step.append(row)

    return dict(seed=seed, per_step=per_step, v1_qualified_t=v1_qualified_t_from_log,
                 v2_qualified_t=v2_qualified_t, n_frames=len(frames))


def main():
    summary = {}
    for seed in SEEDS:
        print(f"[lineage_v2_replay] seed {seed} ...", flush=True)
        out = replay_seed(seed)
        dump_json(out, AUDIT_DIR / f"lineage_v2_replay_611__seed{seed}.json")
        # seed-500-specific: dump t=18..24 for direct inspection
        window = [r for r in out["per_step"] if 18 <= r["t"] <= 24]
        summary[seed] = dict(v1_qualified_t=out["v1_qualified_t"], v2_qualified_t=out["v2_qualified_t"],
                               n_frames=out["n_frames"])
        if seed == 500:
            print("  t=18..24 window:")
            for r in window:
                print("   ", {k: r[k] for k in ("t", "v1_map_size", "v1_map_prob", "v2_map_size",
                                                    "v2_map_prob", "v2_map_dwell", "overlap_v1_v2")})
        print(f"  -> {json.dumps(summary[seed])}", flush=True)
    dump_json(summary, AUDIT_DIR / "lineage_v2_replay_611__summary.json")


if __name__ == "__main__":
    main()
