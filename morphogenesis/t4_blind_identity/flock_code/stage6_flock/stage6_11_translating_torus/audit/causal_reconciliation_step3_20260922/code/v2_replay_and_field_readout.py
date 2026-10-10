"""Task D: exact LineageTrackerV2 replay for the five ACTUAL recorded
control seeds (500-504), full per-frame persistence, plus the historical
field-direction readout recomputed at three anchors (v1 centroid, v2
centroid -- the ACTUAL historical Step-1 anchor per
`branch_adjudication_611.field_direction_readout`'s own signature, which
takes `members` and computes `centroid(r[members], L)` internally -- and
ForwardMaterialTrace centroid), swept over the radius grid already used in
prior passes: 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0.

This replays v2 over the REAL recorded trajectory
(data/viz_bundle_611__seed{n}.json -- ground truth (r, z), never
re-simulated), using the exact same detect_69.propose candidate stream v1
already consumes in production, and the exact same `LineageTrackerV2`
class imported unmodified from `audit/lineage_v2_611.py`.

Seeding convention: v2 is started at the FIRST step a candidate exists
(`cands[0]` at that t), mirroring `run_online_control_611.py`'s own v1
seeding convention (`tracker.start(cands[0], r, z, t)`) exactly -- v2 was
never run online in the real experiment, so this pass adopts the same
seeding rule already used for v1, applied consistently, rather than
inventing a different one. Disclosed explicitly, not assumed equivalent
to whatever (if anything) a hypothetical "if v2 had been run online"
seeding would have done differently.

Historical field-direction formula: `branch_adjudication_611.py`'s
`field_direction_readout(r, z, members, L, radius, target_heading)` --
imported and called UNMODIFIED (not reimplemented), so there is no risk
of a subtle reimplementation drift from the actual historical formula.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = STAGE_DIR / "code"
AUDIT_DIR = STAGE_DIR / "audit"
sys.path.insert(0, str(CODE_DIR))
sys.path.insert(0, str(AUDIT_DIR))

from common_611 import DATA_DIR, L_BOX  # noqa: E402
from detect_69 import propose  # noqa: E402
from lineage_611 import LineageTracker611  # noqa: E402
from lineage_v2_611 import LineageTrackerV2  # noqa: E402
from flock_sim.model import UV4  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402
from branch_adjudication_611 import field_direction_readout  # noqa: E402

STEP2_CODE = AUDIT_DIR / "material_identity_step2_20260921" / "code"
sys.path.insert(0, str(STEP2_CODE))
from forward_material_trace_611 import ForwardMaterialTrace611, RULE_FAMILY_BUILDERS  # noqa: E402
from identity_69 import centroid as anchor_centroid  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"
FROZEN_JSON = STEP2_CODE.parent / "data" / "identity_rule_calibration.json"
RADII = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
SEEDS = [500, 501, 502, 503, 504]


def load_frozen_rule():
    calib = json.load(open(FROZEN_JSON))
    frozen = calib["frozen_rule"]
    return RULE_FAMILY_BUILDERS[frozen["letter"]](**frozen["params"]), frozen


def replay_seed(seed, rule):
    viz = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
    frames = viz["frames"]
    ctrl = json.load(open(DATA_DIR / f"online_control_611__seed{seed}.json"))
    qual = [e for e in ctrl["log"] if e["event"] == "qualified_and_target_set"][0]
    t0, target_heading = qual["t"], qual["target_heading"]

    tracker1 = None
    tracker2 = None
    trace = None
    z_window = []
    per_frame = []
    for frame in frames:
        t = frame["t"]
        r = np.array(frame["r"])
        z = np.array(frame["z"], dtype=int)
        z_window.append(z.copy())
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r, z_window, L_BOX) if len(z_window) >= 2 else []

        if tracker1 is None and cands:
            tracker1 = LineageTracker611(L=L_BOX, uv4=UV4)
            tracker1.start(cands[0], r, z, t)
        elif tracker1 is not None:
            tracker1.update(cands, r, z, t)
            if not tracker1.hypotheses and cands:
                tracker1 = LineageTracker611(L=L_BOX, uv4=UV4)
                tracker1.start(cands[0], r, z, t)

        if tracker2 is None and cands:
            tracker2 = LineageTrackerV2(L=L_BOX, uv4=UV4)
            tracker2.start(cands[0], r, z, t)
        elif tracker2 is not None:
            tracker2.update(cands, r, z, t)
            if not tracker2.lineages and cands:
                tracker2 = LineageTrackerV2(L=L_BOX, uv4=UV4)
                tracker2.start(cands[0], r, z, t)

        if trace is None and t == t0:
            interior_t0 = list(frame["interior"])
            trace = ForwardMaterialTrace611(rule)
            trace.start(t, frozenset(interior_t0))
        elif trace is not None and t > t0:
            trace.step(t, cands)

        v1_members = (max(tracker1.hypotheses, key=lambda h: h.prob).members.tolist()
                      if tracker1 is not None and tracker1.hypotheses else [])
        v2_members = (tracker2.dominant().members.tolist()
                      if tracker2 is not None and tracker2.lineages else [])
        v2_dom = tracker2.dominant() if tracker2 is not None and tracker2.lineages else None
        material_members = (sorted(trace.history[-1].accepted_members)
                             if trace is not None and trace.history and trace.history[-1].accepted_members else [])
        material_status = trace.history[-1].status if trace is not None and trace.history else None

        row = dict(
            t=t, phase=frame["phase"],
            v1_members=v1_members, v1_size=len(v1_members),
            v2_members=v2_members, v2_size=len(v2_members),
            v2_prob=(float(v2_dom.prob) if v2_dom else None),
            v2_dwell=(int(v2_dom.dwell) if v2_dom else None),
            material_members=material_members, material_size=len(material_members),
            material_status=material_status,
        )
        per_frame.append(row)

    return dict(seed=seed, t0=t0, target_heading=target_heading, per_frame=per_frame)


def field_readout_sweep(seed_data, seed, L=L_BOX):
    """Recompute field_direction_readout (UNMODIFIED historical formula) at
    v1 / v2 / material-trace anchors, for the full radius grid, at every
    frame where the relevant member set is nonempty."""
    viz = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
    frames_by_t = {f["t"]: f for f in viz["frames"]}
    target_heading = seed_data["target_heading"]
    rows = []
    for pf in seed_data["per_frame"]:
        t = pf["t"]
        f = frames_by_t[t]
        r = np.array(f["r"]); z = np.array(f["z"], dtype=int)
        row = dict(t=t)
        for anchor_name, members in (("v1", pf["v1_members"]), ("v2", pf["v2_members"]), ("material", pf["material_members"])):
            for radius in RADII:
                key = f"{anchor_name}_r{radius}"
                if members:
                    val = field_direction_readout(r, z, np.array(members, dtype=int), L, radius=radius, target_heading=target_heading)
                else:
                    val = None
                row[key] = val
        rows.append(row)
    return rows


def main():
    rule, frozen = load_frozen_rule()
    all_results = {}
    for seed in SEEDS:
        print(f"replaying seed {seed} ...")
        seed_data = replay_seed(seed, rule)
        sweep = field_readout_sweep(seed_data, seed)
        all_results[seed] = dict(seed_data=seed_data, field_readout_sweep=sweep)
        json.dump(dict(seed_data=seed_data, field_readout_sweep=sweep),
                  open(OUT / f"v2_replay_seed{seed}.json", "w"), indent=2, default=str)
        n_frames = len(seed_data["per_frame"])
        n_v1_v2_agree = sum(1 for pf in seed_data["per_frame"] if set(pf["v1_members"]) == set(pf["v2_members"]))
        print(f"  seed {seed}: {n_frames} frames, v1==v2 member-set agreement at {n_v1_v2_agree}/{n_frames} frames")

    print("wrote per-seed v2_replay_seed{n}.json files to", OUT)


if __name__ == "__main__":
    main()
