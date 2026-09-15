"""VALIDATION_PROTOCOL.md §7: fresh uncontrolled-episode phenomenology,
using the proposed joint model, physical model UNCHANGED, no actuation.

Reuses the "uncontrolled" phase segment already present at the start of
each of the 5 recorded real episodes (`data/viz_bundle_611__seed*.json`)
rather than launching new simulator runs -- the physical model there is
untouched and pre-control, exactly what this phenomenology question asks
about; no target heading, no intervention API call is read here at all.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from candidate_proposals import propose_both
from joint_tracker import JointTracker

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "phase2_results"
OUT_DIR.mkdir(exist_ok=True)


def run_seed(seed):
    with open(DATA_DIR / f"viz_bundle_611__seed{seed}.json") as f:
        d = json.load(f)
    L = d["L"]
    frames = [(np.array(fr["r"]), np.array(fr["z"])) for fr in d["frames"] if fr["phase"] == "uncontrolled"]
    jt = JointTracker(L=L)
    z_hist = []
    lifetimes = {}
    for t, (r, z) in enumerate(frames):
        z_hist.append(z)
        window = z_hist[-3:]
        cands = propose_both(r, z, window, L)
        jt.step(cands, r, z, t)
    for lid, lab in {**jt.labels, **jt.terminated}.items():
        birth_t = lab.history[0]["t"] if lab.history else None
        death_t = lab.history[-1]["t"] if lab.status == "terminated" and lab.history else None
        lifetimes[lid] = dict(birth_t=birth_t, death_t=death_t,
                               lifetime=(death_t - birth_t) if death_t is not None else None,
                               max_size=max((len(h.get("members", [])) for h in lab.history), default=0))
    return dict(seed=seed, n_uncontrolled_frames=len(frames),
                n_labels_total=len(lifetimes), n_still_alive=len(jt.labels),
                n_terminated=len(jt.terminated), lifetimes=lifetimes,
                event_log=jt.event_log)


if __name__ == "__main__":
    results = [run_seed(s) for s in [500, 501, 502, 503, 504]]
    with open(OUT_DIR / "phenomenology_results.json", "w") as f:
        json.dump(results, f, indent=1)
    for r in results:
        print(f"seed {r['seed']}: {r['n_uncontrolled_frames']} uncontrolled frames, "
              f"{r['n_labels_total']} labels seen ({r['n_still_alive']} alive at end, "
              f"{r['n_terminated']} terminated)")
