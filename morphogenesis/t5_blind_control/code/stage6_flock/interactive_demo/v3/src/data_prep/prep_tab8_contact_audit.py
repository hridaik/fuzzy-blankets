"""v3 tab8 data prep: geometric (undirected, FOV-free) contact vs the
simulator's true directed FOV-gated live_edges relation, at one illustrative
closure state (sclosure_06_seed64206, chosen for having non-trivial boundary/
live-parent classes at t0 -- see final_translating_flock_closure/data/
state_manifest_closure.json). Computes both relations directly from the
frozen simulator so the contrast is exact, not illustrative."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
CLOSURE_CODE = ROOT / "final_translating_flock_closure" / "code"
sys.path.insert(0, str(CLOSURE_CODE))
import common_closure as C  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "data" / "tab8_contact_audit.json"
STATE_ID = "sclosure_06_seed64206"


def main():
    manifest = json.load(open(ROOT / "final_translating_flock_closure" / "data" / "state_manifest_closure.json"))
    state = next(s for s in manifest["states"] if s["state_id"] == STATE_ID)
    mf = C.make_flock()
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    target = sorted(int(m) for m in state["interior0"])
    pool20 = sorted(int(p) for p in state["pool20"])

    target_arr = np.array(target)
    pool_arr = np.array(pool20)

    # geometric (undirected, FOV-free) contact: pool candidate <-> ANY target member within R
    delta = C.torus_delta(r0[pool_arr][:, None, :], r0[target_arr][None, :, :], mf.L)
    D = np.sqrt((delta ** 2).sum(-1))
    geometric_contact_pairs = []
    for i, p in enumerate(pool_arr):
        for j, t in enumerate(target_arr):
            if D[i, j] <= mf.R:
                geometric_contact_pairs.append([int(p), int(t)])

    # true directed FOV-gated live edges, restricted to pool<->target
    recv, src, _ = mf.live_edges(r0, z0)
    pool_set, target_set = set(pool20), set(target)
    live_pool_to_target = [[int(s), int(rv)] for s, rv in zip(src.tolist(), recv.tolist())
                            if s in pool_set and rv in target_set]
    live_target_to_pool = [[int(s), int(rv)] for s, rv in zip(src.tolist(), recv.tolist())
                            if s in target_set and rv in pool_set]

    positions = {int(i): [float(r0[i, 0]), float(r0[i, 1])] for i in list(target) + list(pool20)}
    headings = {int(i): int(z0[i]) for i in list(target) + list(pool20)}

    out = dict(
        state_id=STATE_ID, R=mf.R, L=mf.L, target=target, pool20=pool20,
        positions=positions, headings=headings,
        geometric_contact_pairs=geometric_contact_pairs,
        live_pool_to_target=live_pool_to_target, live_target_to_pool=live_target_to_pool,
        n_geometric_contact_pairs=len(geometric_contact_pairs),
        n_live_directed_into_target=len(live_pool_to_target),
        n_live_directed_out_of_target=len(live_target_to_pool),
        note=("Geometric contact (mech_cumulative_contact_edges, used throughout Stage 6.12/6.12B/6.12C) is "
              "undirected and FOV-free: D<=R only. The simulator's actual causal-influence relation "
              "(live_edges, moving_flock.py) additionally requires the RECEIVER's field of view and is "
              "directed/asymmetric. At this state, geometric contact count and live-directed-into-target "
              "count differ (see n_geometric_contact_pairs vs n_live_directed_into_target) -- this is exactly "
              "the gap Closure B was designed to test."),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT, "geometric=", len(geometric_contact_pairs), "live_in=", len(live_pool_to_target))


if __name__ == "__main__":
    main()
