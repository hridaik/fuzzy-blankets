"""Part 2 preparatory step: examine baseline transition statistics (C_min,
time-below-threshold, recovery time) from data ALREADY produced by Part 1
(coverage_sweep.json's full-shell conditions, minimal_interface.json's
chosen sparse condition) before choosing any INTEGRITY threshold. No new
simulation is run here -- this script only re-reads coh_traj arrays already
on disk. Numbers printed here are transcribed into PROTOCOL_V3.md by hand,
once, and then frozen.
"""
from __future__ import annotations

import json

import numpy as np

from common_v3 import V3_DIR


def recovery_time(traj: np.ndarray, c_recover: float, dwell: int) -> int | None:
    """First index t such that traj[t:t+dwell] are all >= c_recover (a single
    instantaneous crossing does not count). Returns None if never achieved
    with the required dwell before the trajectory ends."""
    n = len(traj)
    for t in range(n - dwell + 1):
        if np.all(traj[t: t + dwell] >= c_recover):
            return t
    return None


def pool_trajectories(records, key="coh_traj"):
    """Each record's coh_traj is already (n_replicates, T_u+1); flatten across
    both flocks and replicates so every row is one independent trajectory."""
    rows = []
    for r in records:
        rows.extend(r[key])
    return np.array(rows)


def summarize(trajs: np.ndarray, label: str, c_recover_grid, dwell=3):
    c_min = trajs.min(axis=1)
    print(f"\n--- {label} (n={len(trajs)} replicate trajectories) ---")
    print(f"C_min: mean={c_min.mean():.3f} median={np.median(c_min):.3f} "
          f"p10={np.percentile(c_min,10):.3f} min={c_min.min():.3f} max={c_min.max():.3f}")
    for c_ref in [0.5, 0.6, 0.7, 0.8]:
        t_low = (trajs < c_ref).sum(axis=1)
        print(f"  T_low(c_ref={c_ref}): mean={t_low.mean():.2f} median={np.median(t_low):.1f} "
              f"max={t_low.max()}  frac_ever_below={float(np.mean(t_low>0)):.3f}")
    for c_recover in c_recover_grid:
        times = [recovery_time(tr, c_recover, dwell) for tr in trajs]
        achieved = [t for t in times if t is not None]
        frac_achieved = len(achieved) / len(times)
        if achieved:
            print(f"  recovery to {c_recover} (dwell={dwell}): achieved in {frac_achieved:.3f} of reps, "
                  f"mean_t={np.mean(achieved):.2f} median_t={np.median(achieved):.1f} "
                  f"p90_t={np.percentile(achieved,90):.1f} max_t={max(achieved)}")
        else:
            print(f"  recovery to {c_recover} (dwell={dwell}): never achieved in any replicate")
    final_c = trajs[:, -1]
    print(f"final C_{{I0}}(T_u): mean={final_c.mean():.3f} median={np.median(final_c):.3f} "
          f"frac>=0.8={float(np.mean(final_c>=0.8)):.3f}")


def main():
    sweep = json.load(open(V3_DIR / "data" / "coverage_sweep.json"))
    full_shell_records = [c for fl in sweep["flocks"] for c in fl["conditions"]
                           if c["f_A_target"] == 1.0 and c["rule"] == "COVER_greedy"]
    trajs_full = pool_trajectories(full_shell_records)
    summarize(trajs_full, "Full-shell forcing (f_A=1.0, all propagation-based)",
              c_recover_grid=[0.5, 0.6, 0.7, 0.8])

    mi = json.load(open(V3_DIR / "data" / "minimal_interface.json"))
    gamma_rows = mi["per_q"]["2"]
    sparse_row = next(r for r in gamma_rows if r["gamma"] == 0.5)
    sparse_records = sparse_row["per_flock"]
    trajs_sparse = pool_trajectories(sparse_records)
    summarize(trajs_sparse, "Chosen sparse condition (q=2, gamma_target=0.5, mean f_A=0.54)",
              c_recover_grid=[0.5, 0.6, 0.7, 0.8])

    moderate_row = next(r for r in gamma_rows if r["gamma"] == 0.6)
    trajs_moderate = pool_trajectories(moderate_row["per_flock"])
    summarize(trajs_moderate, "q=2, gamma_target=0.6 (mean f_A=0.78, matches V2's 0.75 fraction)",
              c_recover_grid=[0.5, 0.6, 0.7, 0.8])


if __name__ == "__main__":
    main()
