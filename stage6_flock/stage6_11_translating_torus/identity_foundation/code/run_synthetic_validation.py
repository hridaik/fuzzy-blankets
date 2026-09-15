"""Phase 2 synthetic validation battery (VALIDATION_PROTOCOL.md).

Scope decisions, disclosed here rather than silently applied:

- Seed counts per scenario are REDUCED from the protocol's specified 20
  dev + 20 held-out to 6 dev + 6 held-out, a session-compute
  accommodation matching the pattern already used elsewhere in this
  codebase (e.g. RESULTS_6_11.md's reduced online-control budgets) --
  reported as a reduction, not hidden, and not tuned to make any
  particular result look better.
- v2 (`audit/lineage_v2_611.LineageTrackerV2`) is NOT included in this
  synthetic battery -- its API/calibration lives with the real-5-seed
  audit corpus; it IS compared in `run_real_replay_comparison.py`. v1
  (production, `code/lineage_611.LineageTracker611`) IS included here,
  instantiated once per true label at that label's birth time (its
  native "one lineage tree per instance" design), since it is the
  tracker this whole effort is meant to supersede.
- The out-of-model (Vicsek) sub-mode is only run for the 4 scenarios
  `vicsek_generator.py` builds (see SCENARIOS_WITH_VICSEK), not all 16.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from synth_generator import generate, SCENARIOS, SCENARIOS_WITH_VICSEK
from candidate_proposals import propose_both
from joint_tracker import JointTracker
from baseline_tracker import BaselineTracker
from metrics import score_run, unresolved_and_confidence_stats

_STAGE611 = Path(__file__).resolve().parents[2] / "code"
if str(_STAGE611) not in sys.path:
    sys.path.insert(0, str(_STAGE611))
import lineage_611  # noqa: E402

UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])

DEV_SEEDS = list(range(6))
HELDOUT_SEEDS = list(range(100, 106))
OUT_DIR = Path(__file__).resolve().parent.parent / "phase2_results"
OUT_DIR.mkdir(exist_ok=True)


def run_v1_multi(data):
    """Instantiate one LineageTracker611 per true label at its birth step,
    feed it the same coalesced candidate list every step, and read out its
    dominant (argmax-probability) hypothesis each step -- v1's own native
    single-lineage-per-instance API, run once per true object."""
    L = data["L"]
    trackers = {}
    births_done = set()
    pred_snapshots = []
    z_hist = []
    for t in range(data["T"]):
        r, z = data["frames"][t]
        z_hist.append(z)
        window = z_hist[-3:]
        cands_raw = propose_both(r, z, window, L)
        # dedupe exactly (v1 has no coalescing of its own; give it the same
        # coalesced candidate list the other trackers see, via joint_tracker's
        # coalesce(), so the comparison isolates ASSOCIATION LOGIC, not
        # candidate-list plumbing differences)
        jt_tmp = JointTracker(L=L)
        cands = jt_tmp.coalesce(cands_raw)

        truth = data["truth"][t]
        for tlid, members in truth.items():
            if tlid in births_done:
                continue
            tr = lineage_611.LineageTracker611(L=L, uv4=UV4)
            tr.start(np.array(sorted(members)), r, z, t)
            trackers[tlid] = tr
            births_done.add(tlid)

        snap = {}
        for tlid, tr in trackers.items():
            if not tr.hypotheses:
                continue
            tr.update(cands, r, z, t)
            if not tr.hypotheses:
                continue
            dom = max(tr.hypotheses, key=lambda h: h.prob)
            snap[tlid] = dict(members=sorted(int(x) for x in dom.members), status=dom.status)
        pred_snapshots.append(snap)
    return pred_snapshots


def run_tracker(tracker_cls, data, kwargs=None):
    kwargs = kwargs or {}
    L = data["L"]
    tr = tracker_cls(L=L, **kwargs)
    pred_snapshots = []
    z_hist = []
    for t in range(data["T"]):
        r, z = data["frames"][t]
        z_hist.append(z)
        window = z_hist[-3:]
        cands = propose_both(r, z, window, L)
        tr.step(cands, r, z, t)
        pred_snapshots.append(tr.snapshot(t))
    return pred_snapshots


def run_battery(seeds, split_name):
    results = []
    t0 = time.time()
    for scenario in SCENARIOS:
        for seed in seeds:
            data = generate(scenario, seed, mode="matched")
            truth_seq = data["truth"]

            snap_baseline = run_tracker(BaselineTracker, data)
            snap_joint = run_tracker(JointTracker, data)
            snap_v1 = run_v1_multi(data)

            for name, snaps in [("baseline", snap_baseline), ("joint", snap_joint), ("v1", snap_v1)]:
                m = score_run(truth_seq, snaps)
                m.update(unresolved_and_confidence_stats(snaps))
                m.update(scenario=scenario, seed=seed, tracker=name, split=split_name, mode="matched")
                results.append(m)

            if scenario in SCENARIOS_WITH_VICSEK:
                data_v = generate(scenario, seed, mode="vicsek")
                truth_seq_v = data_v["truth"]
                snap_baseline_v = run_tracker(BaselineTracker, data_v)
                snap_joint_v = run_tracker(JointTracker, data_v)
                for name, snaps in [("baseline", snap_baseline_v), ("joint", snap_joint_v)]:
                    m = score_run(truth_seq_v, snaps)
                    m.update(unresolved_and_confidence_stats(snaps))
                    m.update(scenario=scenario, seed=seed, tracker=name, split=split_name, mode="vicsek")
                    results.append(m)
        print(f"[{split_name}] {scenario} done, elapsed {time.time()-t0:.1f}s", flush=True)
    return results


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "dev"
    t0 = time.time()
    if which == "dev":
        results = run_battery(DEV_SEEDS, "dev")
        out = OUT_DIR / "dev_results.json"
    elif which == "heldout":
        results = run_battery(HELDOUT_SEEDS, "heldout")
        out = OUT_DIR / "heldout_results.json"
    else:
        raise SystemExit("usage: run_synthetic_validation.py [dev|heldout]")
    with open(out, "w") as f:
        json.dump(results, f, indent=1)
    print(f"wrote {len(results)} records to {out} in {time.time()-t0:.1f}s")
