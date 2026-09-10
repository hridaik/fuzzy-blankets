"""Stage 6.11 full-observability / maximal-actuation control benchmark.

Answers: "does even the strongest possible boundary actuation turn this
particular collective?" For the two episodes where the adaptive (sparse,
inferred) actuator set failed to turn the interior (seeds 500, 504), this
reruns the SAME episode (same seed -> same emergence, same trigger point,
same target heading, since candidate detection and the qualification rule
are deterministic given the seed) but forces EVERY current exterior bird
(not a chosen K_ACT=8 subset) to the target heading throughout the control
window. This is the loosest possible upper bound on boundary-actuation
authority: full observability (every exterior bird is a legal actuator, no
near-exterior radius restriction) and an unlimited budget (typically
300-380 of 400 birds forced, versus 8 in the adaptive run). No inference
machinery runs here at all -- which birds to force is read directly off the
blind lineage tracker's own current interior, so this is still "control
only birds outside the current interior" (task brief item 15), just with
every eligible bird actuated instead of a chosen few.

If frac_interior_at_target still fails to rise under this benchmark, that is
a genuine non-existence proof for THIS episode: no boundary-actuation
policy, chosen by any method, using any actuator budget, could have done
better within the same horizon -- the interior's own internal consensus is
what is resisting, not a poor choice of which few birds to force.
"""
from __future__ import annotations

import numpy as np

from common_611 import DATA_DIR, L_BOX, dump_json
from flock_sim.model import UV4, ROT_CCW
from detect_69 import propose
from lineage_611 import LineageTracker611
from run_online_control_611 import make_flock, bearing_to_cardinal

QUALIFY_MIN_DURATION = 30
QUALIFY_SIZE_RANGE = (0.05, 0.50)
QUALIFY_MIN_DISPLACEMENT_R = 3.0
AFFINITY_WINDOW = 6
T_CONTROL = 24
T_RELEASE = 24
NT_MAX_UNCONTROLLED = 260
R_PRIMARY = 0.9


def run(seed: int, record_trajectory: bool = False) -> dict:
    mf = make_flock()
    rng = np.random.default_rng(seed)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)

    tracker = None
    z_window = []
    phase = "uncontrolled"
    target_heading = None
    control_step = 0
    release_step = 0
    log = []
    trajectory = [] if record_trajectory else None
    t = 0

    while t < NT_MAX_UNCONTROLLED + T_CONTROL + T_RELEASE:
        z_window.append(z.copy())
        if len(z_window) > AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r, z_window, L_BOX) if len(z_window) >= 2 else []

        if tracker is None and cands:
            tracker = LineageTracker611(L=L_BOX, uv4=UV4)
            tracker.start(cands[0], r, z, t)
        elif tracker is not None:
            tracker.update(cands, r, z, t)
            if not tracker.hypotheses and cands:
                tracker = LineageTracker611(L=L_BOX, uv4=UV4)
                tracker.start(cands[0], r, z, t)

        interior = None
        if tracker is not None and tracker.hypotheses:
            interior = max(tracker.hypotheses, key=lambda h: h.prob).members

        if phase == "uncontrolled":
            if interior is not None and t >= NT_MAX_UNCONTROLLED:
                log.append(dict(t=t, event="stop_condition_no_emergence"))
                break
            if tracker is not None and tracker.hypotheses:
                h = max(tracker.hypotheses, key=lambda h: h.prob)
                recs = h.records
                if len(recs) >= QUALIFY_MIN_DURATION:
                    recent = recs[-QUALIFY_MIN_DURATION:]
                    size_ok = np.mean([QUALIFY_SIZE_RANGE[0] <= r_["size"] / mf.N <= QUALIFY_SIZE_RANGE[1]
                                        for r_ in recent]) >= 0.8
                    disp = float(np.hypot(*np.sum([r_.get("bulk_delta", [0, 0]) for r_ in recent], axis=0)))
                    if size_ok and disp >= QUALIFY_MIN_DISPLACEMENT_R * R_PRIMARY:
                        bulk_delta = np.sum([r_.get("bulk_delta", [0, 0]) for r_ in recent], axis=0)
                        cur_dir = bearing_to_cardinal(bulk_delta)
                        target_heading = int(ROT_CCW[cur_dir])
                        phase = "control"
                        control_step = 0
                        log.append(dict(t=t, event="qualified_and_target_set",
                                         target_heading=target_heading, displacement=disp))

        forced = None
        if phase == "control" and interior is not None:
            member_set = set(int(x) for x in interior)
            actuators = [i for i in range(mf.N) if i not in member_set]
            forced = {j: target_heading for j in actuators}
            control_step += 1
            log.append(dict(t=t, event="control_step", control_step=control_step,
                             n_actuators=len(actuators), interior_size=len(interior),
                             frac_interior_at_target=float((z[interior] == target_heading).mean())))
            if control_step >= T_CONTROL:
                phase = "release"
                release_step = 0
                log.append(dict(t=t, event="release_begin"))
        elif phase == "release":
            release_step += 1
            log.append(dict(t=t, event="release_step", release_step=release_step,
                             interior_size=(len(interior) if interior is not None else 0),
                             frac_interior_at_target=(float((z[interior] == target_heading).mean())
                                                       if interior is not None and target_heading is not None
                                                       else None)))
            if release_step >= T_RELEASE:
                log.append(dict(t=t, event="episode_end"))
                break

        if trajectory is not None:
            trajectory.append(dict(t=t, r=r.tolist(), z=z.tolist(), phase=phase,
                                    interior=(interior.tolist() if interior is not None else []),
                                    actuators=(list(forced.keys()) if forced else []),
                                    target_heading=target_heading))

        r_prev, z_prev = r.copy(), z.copy()
        r, z, _ = mf.step(r, z, rng, forced_actions=forced)
        t += 1

    result = dict(seed=seed, log=log, ended_phase=phase, final_t=t)
    if trajectory is not None:
        result["trajectory"] = trajectory
        result["L"] = L_BOX
    return result


def main():
    for seed in (500, 504):
        print(f"[full_force_benchmark] seed={seed} ...", flush=True)
        res = run(seed, record_trajectory=True)
        control = [e for e in res["log"] if e["event"] == "control_step"]
        release = [e for e in res["log"] if e["event"] == "release_step"]
        if control:
            print(f"  control: n_actuators~{control[0]['n_actuators']}-{control[-1]['n_actuators']}, "
                  f"frac@target {control[0]['frac_interior_at_target']:.3f} -> "
                  f"{control[-1]['frac_interior_at_target']:.3f}", flush=True)
        if release:
            fracs = [e['frac_interior_at_target'] for e in release if e['frac_interior_at_target'] is not None]
            print(f"  release: frac@target mean={np.mean(fracs):.3f} final={fracs[-1]:.3f}", flush=True)
        dump_json(res, DATA_DIR / f"full_force_benchmark_611__seed{seed}.json")
        print(f"  wrote full_force_benchmark_611__seed{seed}.json", flush=True)


if __name__ == "__main__":
    main()
