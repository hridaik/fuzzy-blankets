"""Stage 6.11 interactive-demo data export (task brief item 20).

EVALUATION-SIDE. Reruns one online-control episode with full per-step
trajectory recording, then writes a compact JSON bundle for the interactive
HTML visualization (world frame + co-moving frame, blind quantities only by
default -- oracle overlays, if added, must default off per PLAN.md Section U).
"""
from __future__ import annotations

import numpy as np

from common_611 import DATA_DIR, L_BOX, dump_json
from run_online_control_611 import load_pretrained_model, run_episode


def comoving_centroid(r_members: np.ndarray, L: float) -> np.ndarray:
    if len(r_members) == 0:
        return np.array([L / 2, L / 2])
    ref = r_members[0]
    rel = (r_members - ref + L / 2) % L - L / 2
    return (ref + rel.mean(axis=0)) % L


def main(seed: int = 501):
    model, base_rows, dist_cuts = load_pretrained_model(M_obs=12)
    print(f"[export_viz_611] rerunning seed={seed} with trajectory recording...")
    result = run_episode(seed=seed, model=model, base_rows=base_rows, dist_cuts=dist_cuts,
                          M_obs=12, record_trajectory=True)
    traj = result["trajectory"]
    print(f"[export_viz_611] {len(traj)} steps recorded, ended_phase={result['ended_phase']}")

    # co-moving frame: recentre each frame on the current interior's centroid
    # (torus-safe reference-point centroid), estimated from observables only
    frames = []
    unwrapped_centroid = None
    prev_centroid = None
    for step in traj:
        r = np.array(step["r"])
        z = np.array(step["z"])
        interior = np.array(step["interior"], dtype=int)
        if len(interior) > 0:
            c = comoving_centroid(r[interior], L_BOX)
        else:
            c = np.array([L_BOX / 2, L_BOX / 2])
        frames.append(dict(
            t=step["t"], r=step["r"], z=step["z"], phase=step["phase"],
            interior=step["interior"], actuators=step["actuators"],
            target_heading=step["target_heading"], centre=c.tolist(),
        ))

    bundle = dict(N=len(traj[0]["z"]) if traj else 0, L=L_BOX, seed=seed,
                  ended_phase=result["ended_phase"], frames=frames)
    out_path = DATA_DIR / f"viz_bundle_611__seed{seed}.json"
    dump_json(bundle, out_path)
    print(f"[export_viz_611] wrote {out_path} ({len(frames)} frames)")
    return out_path


if __name__ == "__main__":
    import sys
    main(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 501)
