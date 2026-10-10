"""One-off pilot timing check (per process brief). Runs a handful of K=1
rollouts at d=8 and d=24 on the pilot state to measure actual per-rollout
cost, compared against the ~4.2s/6.3s estimates. NOT part of confirmatory
inference -- pilot seed range only.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612c as C  # noqa: E402

manifest = json.load(open(C.DATA_DIR / "state_manifest_612c_pilot.json"))
state = manifest["states"][0]
rule, _ = C.load_frozen_rule()
mf = C.make_flock()
r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
seed_members = frozenset(state["interior0"]); h_star = state["h_star"]
pool = state["pool20"]
z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]

print("pool size", len(pool))

t0 = time.time()
for i, j in enumerate(pool[:3]):
    out = C.IB.run_one_b(mf, r0, z0, z_context, seed_members, rule, h_star, [j], 8, 90_000_000 + i)
dt = time.time() - t0
print(f"d=8: {dt/3:.3f}s/rollout")

t0 = time.time()
for i, j in enumerate(pool[:3]):
    out = C.IB.run_one_b(mf, r0, z0, z_context, seed_members, rule, h_star, [j], 24, 91_000_000 + i)
dt = time.time() - t0
print(f"d=24: {dt/3:.3f}s/rollout")

t0 = time.time()
nc, r_hist, z_hist, tr = C.IB.run_no_control_full_b(mf, r0, z0, z_context, seed_members, rule, h_star, 92_000_000, (8, 24))
dt = time.time() - t0
print(f"no-control (8,24) full: {dt:.3f}s")
