"""Translation feasibility gate (task brief section 33).

UNCONTROLLED dynamics only. No steering experiment may run until this passes.
The five criteria are frozen in
`logs/translation_gate_criteria_predeclared.txt` and are applied unchanged.

Detection and tracking here are the observer-facing modules (`detect_69.py`,
`identity_69.py`); the simulator's true centre trajectory and true interaction
graph are never consulted.
"""
from __future__ import annotations

import numpy as np

from common_69 import (ModelParams, dump_json, DATA_DIR, N_BIRDS, L_BOX, R_RADIUS,
                       V_SPEED, BETA, RHO, OMEGA, GATE_NT, GATE_T_START, GATE_SEEDS,
                       DEV_SEEDS, HELDOUT_SEEDS, UV4)
from moving_flock import MovingFlock
import detect_69 as det

T1_MIN_DURATION = 40
T2_MIN_DISPLACEMENT_RADII = 3.0
T3_MAX_MATERIAL_RETENTION = 0.70
T4_MIN_MEAN_RF = 0.70
T5_MIN_FRAC_VALID = 0.90
GATE_MIN_PASS_RATE = 0.20


def track_episode(mf: MovingFlock, res, t_start=GATE_T_START, t_end=None) -> dict:
    t_end = t_end or (res.z_hist.shape[0] - 1)
    W = det.W_AFFINITY
    tracker = None
    for t in range(t_start, t_end):
        zw = res.z_hist[max(0, t - W + 1):t + 1]
        cands = det.propose(res.r_hist[t], zw, mf.L)
        if not cands:
            if tracker is not None:
                break
            continue
        if tracker is None:
            tracker = det.TranslatingTracker(mf.L)
            tracker.start(cands[0], res.r_hist[t], res.z_hist[t], t)
        elif not tracker.update(cands, res.r_hist[t], res.z_hist[t], t):
            break
    if tracker is None or len(tracker.records) < 2:
        return dict(tracked=False, duration=0)
    recs = tracker.records
    c0, c1 = np.array(recs[0]["centroid"]), np.array(recs[-1]["centroid"])
    disp = float(np.linalg.norm((c1 - c0 + mf.L / 2) % mf.L - mf.L / 2))
    rfs = [r["R_F"] for r in recs if "R_F" in r]
    valid = [(0.03 * mf.N <= r["size"] <= 0.55 * mf.N) and r.get("n_components", 1) <= 2
             for r in recs]
    return dict(
        tracked=True, duration=len(recs), t_start=recs[0]["t"], t_end=recs[-1]["t"],
        size_first=recs[0]["size"], size_last=recs[-1]["size"],
        R_M_final=recs[-1]["R_M"], R_M_min=min(r["R_M"] for r in recs),
        mean_R_F=float(np.mean(rfs)) if rfs else float("nan"),
        min_R_F=float(np.min(rfs)) if rfs else float("nan"),
        mean_D_deform=float(np.mean([r["D_deform"] for r in recs if "D_deform" in r])),
        mean_D_centroid_aligned=float(np.mean([r["D_centroid_aligned_only"] for r in recs
                                               if "D_centroid_aligned_only" in r])),
        mean_D_world_frame=float(np.mean([r["D_world_frame"] for r in recs
                                          if "D_world_frame" in r])),
        displacement=disp, displacement_radii=disp / mf.R,
        mean_bulk_speed=float(np.mean([r["bulk_speed"] for r in recs if "bulk_speed" in r])),
        mean_turnover=float(np.mean([r["turnover"] for r in recs[1:]])) if len(recs) > 1 else 0.0,
        mean_J_prev=float(np.mean([r["J_prev"] for r in recs[1:]])) if len(recs) > 1 else 1.0,
        frac_valid=float(np.mean(valid)),
        mean_aspect_ratio=float(np.mean([r.get("aspect_ratio", 1.0) for r in recs])),
        mean_n_components=float(np.mean([r.get("n_components", 1) for r in recs])),
        n_branch_events=len(tracker.branch_events),
        branch_events=tracker.branch_events,
        records=recs,
    )


def evaluate(ep: dict) -> dict:
    if not ep.get("tracked"):
        return dict(T1=False, T2=False, T3=False, T4=False, T5=False, passes=False)
    T1 = ep["duration"] >= T1_MIN_DURATION
    T2 = ep["displacement_radii"] >= T2_MIN_DISPLACEMENT_RADII
    T3 = ep["R_M_final"] <= T3_MAX_MATERIAL_RETENTION
    T4 = ep["mean_R_F"] >= T4_MIN_MEAN_RF
    T5 = ep["frac_valid"] >= T5_MIN_FRAC_VALID
    return dict(T1=bool(T1), T2=bool(T2), T3=bool(T3), T4=bool(T4), T5=bool(T5),
                passes=bool(T1 and T2 and T3 and T4 and T5))


def main():
    mf = MovingFlock(N=N_BIRDS, L=L_BOX, R=R_RADIUS, v=V_SPEED,
                     params=ModelParams(beta=BETA, precB=RHO, precC=OMEGA))
    out = dict(protocol="stage6_9 translation feasibility gate",
               model=dict(N=N_BIRDS, L=L_BOX, R=R_RADIUS, v=V_SPEED, beta=BETA,
                          rho=RHO, omega=OMEGA,
                          expected_degree_uniform=mf.expected_degree()),
               criteria=dict(T1_min_duration=T1_MIN_DURATION,
                             T2_min_displacement_radii=T2_MIN_DISPLACEMENT_RADII,
                             T3_max_material_retention=T3_MAX_MATERIAL_RETENTION,
                             T4_min_mean_RF=T4_MIN_MEAN_RF,
                             T5_min_frac_valid=T5_MIN_FRAC_VALID,
                             gate_min_pass_rate=GATE_MIN_PASS_RATE),
               dev_seeds=DEV_SEEDS, heldout_seeds=HELDOUT_SEEDS, episodes=[])
    for seed in GATE_SEEDS:
        res = mf.run(nt=GATE_NT, seed=seed)
        ep = track_episode(mf, res)
        ev = evaluate(ep)
        rec = dict(seed=seed, **{k: v for k, v in ep.items() if k != "records"}, **ev)
        rec["records"] = ep.get("records", [])
        out["episodes"].append(rec)
        if ep.get("tracked"):
            print(f"seed {seed:<3} dur={ep['duration']:<4} size {ep['size_first']:>3}->{ep['size_last']:<3} "
                  f"disp={ep['displacement_radii']:5.1f}R R_M={ep['R_M_final']:.2f} "
                  f"R_F={ep['mean_R_F']:.2f} Ddef={ep['mean_D_deform']:.3f} "
                  f"turn={ep['mean_turnover']:.3f} valid={ep['frac_valid']:.2f} "
                  f"| {''.join(k for k in 'T1 T2 T3 T4 T5'.split() if ev[k])} "
                  f"{'PASS' if ev['passes'] else ''}", flush=True)
        else:
            print(f"seed {seed:<3} no trackable collective", flush=True)
    passes = [e["passes"] for e in out["episodes"]]
    out["pass_rate"] = float(np.mean(passes))
    out["gate_passes"] = bool(out["pass_rate"] >= GATE_MIN_PASS_RATE)
    for k in ("T1", "T2", "T3", "T4", "T5"):
        out[f"rate_{k}"] = float(np.mean([e[k] for e in out["episodes"]]))
    dump_json(out, DATA_DIR / f"translation_gate__R{R_RADIUS}_v{V_SPEED}.json")
    dump_json(out, DATA_DIR / "translation_gate.json")
    print(f"\npass rate {out['pass_rate']:.2f}  gate_passes={out['gate_passes']}")
    print("per-criterion rates:", {k: round(out[f'rate_{k}'], 2) for k in
                                   ('T1', 'T2', 'T3', 'T4', 'T5')})


if __name__ == "__main__":
    main()
