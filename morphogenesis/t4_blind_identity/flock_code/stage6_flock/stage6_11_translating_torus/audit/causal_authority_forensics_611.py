"""Part D items 7-9: causal/authority architecture diagnostics (additive,
read-only). Uses the already-recorded ground-truth trajectory in
`data/viz_bundle_611__seed{seed}.json` (verified bit-exact against the
production run in lineage_forensics_611.py's consistency check) -- no
simulator RNG stream needs to be replayed for item 8 (oracle_B_D is a pure
function of one snapshot); item 9 reruns the SAME probe class, budget, tau
and per-(t, j) seed convention run_online_control_611.py itself uses, at the
already-selected refresh points only, so it reproduces production authority
estimates that were computed once and never persisted, rather than running a
new experiment.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import DATA_DIR, dump_json  # noqa: E402
from intervention_api_611 import near_exterior, MultiStepAuthorityProbe  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

SEEDS = (500, 501, 502, 503, 504)


def load_frames(seed):
    d = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
    return d["frames"]


def item8_direct_vs_reachable(seed, frames):
    """For every control/release frame: true one-step causal boundary of the
    displayed interior, and whether each ACTIVE actuator (frame['actuators'])
    is currently a direct causal parent. Forward-looks within the same
    episode to report the first later t (if any) at which a non-parent
    actuator becomes one."""
    mf = ROC.make_flock()
    per_frame = []
    for frame in frames:
        if frame["phase"] not in ("control", "release"):
            continue
        r = np.array(frame["r"])
        z = np.array(frame["z"], dtype=int)
        interior = np.array(frame["interior"], dtype=int)
        if len(interior) == 0:
            continue
        B_D = set(int(x) for x in mf.oracle_B_D(r, z, interior))
        actuators = [int(x) for x in frame["actuators"]]
        per_frame.append(dict(t=frame["t"], phase=frame["phase"], interior_size=len(interior),
                                B_D_size=len(B_D), actuators=actuators,
                                actuators_that_are_direct_parents=[j for j in actuators if j in B_D],
                                n_actuators=len(actuators),
                                n_actuators_direct_parent=sum(1 for j in actuators if j in B_D)))

    # forward-looking: for each (actuator, t) where it was active but NOT a
    # direct parent, find the first later t' > t (any phase, this episode)
    # where oracle_B_D of the THEN-current interior includes it
    all_t = [(pf["t"], set(pf["actuators_that_are_direct_parents"])) for pf in per_frame]
    B_D_by_t = {}
    for frame in frames:
        if frame["phase"] not in ("control", "release"):
            continue
        r = np.array(frame["r"]); z = np.array(frame["z"], dtype=int)
        interior = np.array(frame["interior"], dtype=int)
        if len(interior) == 0:
            continue
        B_D_by_t[frame["t"]] = set(int(x) for x in mf.oracle_B_D(r, z, interior))

    ts_sorted = sorted(B_D_by_t.keys())
    for pf in per_frame:
        becomes_parent_later = {}
        for j in pf["actuators"]:
            if j in pf["actuators_that_are_direct_parents"]:
                continue
            later = [t2 for t2 in ts_sorted if t2 > pf["t"] and j in B_D_by_t[t2]]
            becomes_parent_later[j] = later[0] if later else None
        pf["non_parent_actuators_first_become_parent_at"] = becomes_parent_later

    return per_frame


def item9_zero_authority_refreshes(seed, frames):
    """Recompute authority at the exact refresh points run_online_control_611
    used (REINFER_AUTHORITY_EVERY=8 real steps into the control phase),
    reusing the recorded ground-truth (r, z) snapshot at each refresh -- same
    probe class, tau, rollout budget, and seed convention as production."""
    mf = ROC.make_flock()
    control_frames = [f for f in frames if f["phase"] == "control"]
    if not control_frames:
        return []
    t0 = control_frames[0]["t"]
    refresh_ts = sorted(set(f["t"] for f in control_frames if (f["t"] - t0) % ROC.REINFER_AUTHORITY_EVERY == 0))
    out = []
    for t in refresh_ts:
        frame = next(f for f in control_frames if f["t"] == t)
        r = np.array(frame["r"]); z = np.array(frame["z"], dtype=int)
        interior = np.array(frame["interior"], dtype=int)
        target_heading = frame["target_heading"]
        if len(interior) == 0 or target_heading is None:
            continue
        exterior_pool = near_exterior(mf, r, interior, radius_factor=3.0)
        if not exterior_pool:
            out.append(dict(t=t, exterior_pool_size=0, note="empty exterior pool"))
            continue
        auth_probe = MultiStepAuthorityProbe(mf, r, z, tau=ROC.TAU_CONTROL,
                                               n_rollouts=ROC.AUTHORITY_ROLLOUTS_ONLINE, seed=2000 + t)
        scores = [auth_probe.authority(interior, j, target_heading) for j in exterior_pool]
        A_vals = np.array([s["A"] for s in scores])
        n_nonpositive = int((A_vals <= 0.0).sum())
        out.append(dict(
            t=t, exterior_pool_size=len(exterior_pool), n_scored=len(A_vals),
            n_nonpositive=n_nonpositive, frac_nonpositive=float(n_nonpositive / len(A_vals)),
            max_A=float(A_vals.max()), mean_A=float(A_vals.mean()),
            actuators_this_window=frame["actuators"],
            all_zero_exact=bool(np.allclose(A_vals, 0.0)),
        ))
    return out


def main():
    all_item8, all_item9 = {}, {}
    for seed in SEEDS:
        print(f"[causal_authority_forensics] seed {seed} item 8 (cheap)...", flush=True)
        frames = load_frames(seed)
        item8 = item8_direct_vs_reachable(seed, frames)
        all_item8[seed] = item8
        print(f"[causal_authority_forensics] seed {seed} item 9 (probe rollouts)...", flush=True)
        item9 = item9_zero_authority_refreshes(seed, frames)
        all_item9[seed] = item9
        for r in item9:
            print(f"   t={r.get('t')}: {r}", flush=True)

    dump_json(all_item8, AUDIT_DIR / "causal_authority_forensics_611__item8_direct_vs_reachable.json")
    dump_json(all_item9, AUDIT_DIR / "causal_authority_forensics_611__item9_zero_authority.json")
    print("wrote item8/item9 JSON")


if __name__ == "__main__":
    main()
