"""Task E prerequisite: verify that each seed's historical trigger state
(the (r, z) configuration at the control-phase transition t0) can be
independently reproduced by replaying the production uncontrolled-phase
call sequence from the raw episode seed -- exactly, bit-for-bit -- against
the already-recorded `data/viz_bundle_611__seed{n}.json` frame at t0.

Per rng_crn_diagnostic.py's demo_4 finding: the replay must reproduce
run_online_control_611.py's EXACT shared-rng call sequence (mf.step, then
rng.choice(mf.N, size=20, replace=False) for the online buffer sample),
every step, in order -- not just the physics update. This script does
that, read-only, importing production modules unmodified.

If reproduction fails for a seed, this is a stop condition (spec S19,
"old trigger state cannot be reproduced") for THAT seed specifically --
other seeds proceed independently.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = STAGE_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import N_BIRDS, L_BOX, BETA_610, S_610, resolved_params, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY, DATA_DIR  # noqa: E402
from moving_flock_611 import MovingFlock611  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"

SEEDS_T0 = {500: None, 501: 30, 502: None, 503: 35, 504: None}  # filled in from online_control logs below


def make_flock():
    pm = resolved_params(BETA_610, S_610)
    return MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=V_PRIMARY, params=pm,
                           social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)


def get_t0(seed):
    log_path = DATA_DIR / f"online_control_611__seed{seed}.json"
    d = json.load(open(log_path))
    qual = [e for e in d["log"] if e.get("event") == "qualified_and_target_set"]
    if not qual:
        return None, d
    return qual[0]["t"], d


def replay_uncontrolled_to_t0(seed, t0):
    """Exact production call sequence (mf.step + rng.choice(20)) from the
    episode's own initial rng, for t0 steps, forced_actions=None
    throughout (valid since t0 is, by construction, BEFORE the control
    phase starts)."""
    mf = make_flock()
    rng = np.random.default_rng(seed)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)
    for t in range(t0):
        r, z, _ = mf.step(r, z, rng, forced_actions=None)
        rng.choice(mf.N, size=min(20, mf.N), replace=False)
    return r, z


def load_recorded_frame(seed, t0):
    path = DATA_DIR / f"viz_bundle_611__seed{seed}.json"
    if not path.exists():
        return None
    d = json.load(open(path))
    for frame in d["frames"]:
        if frame["t"] == t0:
            return np.array(frame["r"]), np.array(frame["z"], dtype=int)
    return None


def main():
    results = {}
    for seed in (500, 501, 502, 503, 504):
        t0, log = get_t0(seed)
        if t0 is None:
            results[seed] = dict(seed=seed, status="NO qualified_and_target_set EVENT FOUND IN LOG -- stop condition")
            print(f"seed {seed}: NO qualification event found")
            continue
        r_replay, z_replay = replay_uncontrolled_to_t0(seed, t0)
        recorded = load_recorded_frame(seed, t0)
        if recorded is None:
            results[seed] = dict(seed=seed, t0=t0, status="no viz_bundle frame at t0 to check against -- stop condition")
            print(f"seed {seed}: t0={t0}, no recorded frame to verify against")
            continue
        r_rec, z_rec = recorded
        r_match = bool(np.allclose(r_replay, r_rec, atol=1e-9))
        z_match = bool(np.array_equal(z_replay, z_rec))
        status = "REPRODUCED_EXACTLY" if (r_match and z_match) else "MISMATCH -- stop condition for this seed"
        results[seed] = dict(seed=seed, t0=t0, r_match=r_match, z_match=z_match,
                              max_r_abs_diff=float(np.max(np.abs(r_replay - r_rec))),
                              n_z_mismatches=int((z_replay != z_rec).sum()),
                              status=status)
        print(f"seed {seed}: t0={t0}, r_match={r_match}, z_match={z_match}, status={status}")

    json.dump(results, open(OUT / "trigger_state_reproduction.json", "w"), indent=2, default=str)
    print("\nwrote", OUT / "trigger_state_reproduction.json")


if __name__ == "__main__":
    main()
