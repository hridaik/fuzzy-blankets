"""Stage 6.11 oracle-best-K=8 control benchmark.

Brackets WHY the sparse adaptive controller failed on seeds 500/504, given
that `run_full_force_benchmark_611.py` showed forcing ~90% of the exterior
population DOES turn both of those collectives (so it is not a fundamental
controllability limit). This uses the SAME actuator budget as the adaptive
run (K_ACT=8) and the SAME re-selection cadence (every 8 steps), but removes
the two things that could make the adaptive run's choice of 8 birds worse
than the best possible 8: (a) the near-exterior radius restriction on the
candidate pool (here every exterior bird is eligible), and (b) rollout noise
in the authority estimate (here estimated with more rollouts per candidate).
If THIS still fails, budget=8 is genuinely too small at this snapshot,
regardless of how well the 8 are chosen. If it succeeds, the adaptive run's
failure was a selection-quality artifact (restricted pool and/or noisy
ranking), not a hard budget limit.
"""
from __future__ import annotations

import numpy as np

from common_611 import DATA_DIR, L_BOX, dump_json
from flock_sim.model import UV4, ROT_CCW
from detect_69 import propose
from lineage_611 import LineageTracker611
from intervention_api_611 import MultiStepAuthorityProbe
import control_authority_611 as CA
from run_online_control_611 import make_flock, bearing_to_cardinal

QUALIFY_MIN_DURATION = 30
QUALIFY_SIZE_RANGE = (0.05, 0.50)
QUALIFY_MIN_DISPLACEMENT_R = 3.0
AFFINITY_WINDOW = 6
T_CONTROL = 24
T_RELEASE = 24
NT_MAX_UNCONTROLLED = 260
R_PRIMARY = 0.9
K_ACT = 8
REINFER_EVERY = 8
TAU_CONTROL = 4
AUTHORITY_ROLLOUTS = 15
MAX_CANDIDATES = 150   # random-subsample the full exterior pool if larger, for tractability (disclosed)
SELECT_ONCE = True     # freeze the chosen 8 for the whole control window instead of every-8-step reselection


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
    age_authority = 0
    B_C_cache = None
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
            full_exterior = np.array([i for i in range(mf.N) if i not in member_set])
            need_select = B_C_cache is None or (not SELECT_ONCE and age_authority >= REINFER_EVERY)
            if need_select:
                pool = full_exterior
                if len(pool) > MAX_CANDIDATES:
                    pool = rng.choice(pool, size=MAX_CANDIDATES, replace=False)
                auth_probe = MultiStepAuthorityProbe(mf, r, z, tau=TAU_CONTROL,
                                                       n_rollouts=AUTHORITY_ROLLOUTS, seed=3000 + t)
                B_C_cache = CA.select_actuators(auth_probe, interior, pool, target_heading, k_act=K_ACT)
                age_authority = 0
            else:
                age_authority += 1
            forced = {j: target_heading for j in B_C_cache["B_C"]}
            control_step += 1
            log.append(dict(t=t, event="control_step", control_step=control_step,
                             B_C=B_C_cache["B_C"], age_authority=age_authority,
                             interior_size=len(interior),
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

        r, z, _ = mf.step(r, z, rng, forced_actions=forced)
        t += 1

    result = dict(seed=seed, log=log, ended_phase=phase, final_t=t)
    if trajectory is not None:
        result["trajectory"] = trajectory
        result["L"] = L_BOX
    return result


def main():
    for seed in (500, 504):
        print(f"[oracle_k8_benchmark] seed={seed} ...", flush=True)
        res = run(seed, record_trajectory=True)
        control = [e for e in res["log"] if e["event"] == "control_step"]
        release = [e for e in res["log"] if e["event"] == "release_step"]
        if control:
            print(f"  control: frac@target {control[0]['frac_interior_at_target']:.3f} -> "
                  f"{control[-1]['frac_interior_at_target']:.3f}", flush=True)
        if release:
            fracs = [e['frac_interior_at_target'] for e in release if e['frac_interior_at_target'] is not None]
            print(f"  release: frac@target mean={np.mean(fracs):.3f} final={fracs[-1]:.3f}", flush=True)
        dump_json(res, DATA_DIR / f"oracle_k8_benchmark_611__seed{seed}.json")
        print(f"  wrote oracle_k8_benchmark_611__seed{seed}.json", flush=True)


if __name__ == "__main__":
    main()
