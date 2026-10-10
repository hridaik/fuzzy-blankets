"""Stage 6.11B item 9 (part 1): recreate the exact pre-control trigger
snapshot for seeds 500-504, from the already-recorded ground truth
(no re-simulation, no RNG needed -- position/heading are recorded exactly).
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
from common_611 import DATA_DIR, dump_json  # noqa: E402

SEEDS = (500, 501, 502, 503, 504)


def extract(seed: int) -> dict:
    viz = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
    log = json.load(open(DATA_DIR / f"online_control_611__seed{seed}.json"))["log"]
    qev = next(e for e in log if e["event"] == "qualified_and_target_set")
    t0 = qev["t"]
    frame = next(f for f in viz["frames"] if f["t"] == t0)
    assert frame["phase"] == "control", f"seed {seed}: frame at t0={t0} is phase={frame['phase']}"
    return dict(seed=seed, t0=t0, r=frame["r"], z=frame["z"], interior_v1=frame["interior"],
                 target_heading=qev["target_heading"], cur_dir=qev["cur_dir"],
                 displacement_at_qualify=qev["displacement"])


def main():
    states = {seed: extract(seed) for seed in SEEDS}
    dump_json(states, AUDIT_DIR / "trigger_states_611.json")
    for seed, s in states.items():
        print(f"seed {seed}: t0={s['t0']} interior_size={len(s['interior_v1'])} "
              f"target_heading={s['target_heading']}")


if __name__ == "__main__":
    main()
