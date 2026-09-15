"""Small smoke test: one scenario, few steps, both trackers, checked for
crashes and basic sanity before the full battery runs. Not a scored
validation run -- see run_synthetic_validation.py for that."""
import time

import numpy as np

from synth_generator import generate
from candidate_proposals import propose_both
from joint_tracker import JointTracker
from baseline_tracker import BaselineTracker


def run_one(scenario, seed, T_cap=None):
    data = generate(scenario, seed)
    T = T_cap or data["T"]
    jt = JointTracker(L=data["L"])
    bt = BaselineTracker(L=data["L"])
    z_hist = []
    for t in range(T):
        r, z = data["frames"][t]
        z_hist.append(z)
        window = z_hist[-3:]
        cands = propose_both(r, z, window, data["L"])
        jt.step(cands, r, z, t)
        bt.step(cands, r, z, t)
    return data, jt, bt


if __name__ == "__main__":
    t0 = time.time()
    for scenario in ["two_clumps", "symmetric_split", "actual_merger", "full_turnover"]:
        data, jt, bt = run_one(scenario, seed=0, T_cap=25)
        print(f"{scenario}: joint labels alive={len(jt.snapshot(24))}, "
              f"events={[e['type'] for e in jt.event_log]}, "
              f"baseline tracks alive={len(bt.snapshot(24))}, "
              f"unaccounted_mass sample={jt.unaccounted_mass_log[-1]}")
    print(f"smoke test wall time: {time.time()-t0:.2f}s")
