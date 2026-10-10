"""Part 2D: does control SCHEDULING reduce the transient coherence dip,
without changing the total control budget or the final objective? Compares
Pulse (V1/V2 baseline), Ramp-up, Sequential-sector recruitment, and
Ramp-down/release-taper at matched total actuator-budget, on the 4 flocks
fixed in PROTOCOL_V3.md (seeds 2,3,8,13), using the frozen V3 actuator set
(q=2, gamma=0.5 multicover) as the fixed budget for each flock.
"""
from __future__ import annotations

import time

import numpy as np

from common_v3 import (
    V3_DIR, dump_json, load_dev_flocks, dynamical_shell, run_simulation,
    target_heading_fraction, coherence, analyze_window, T_U, T_R, TW, V3_SEED_OFFSET,
)
from selection_rules_v3 import min_actuators_for_multicover, greedy_multicover_order
from coverage_metrics import structural_report, _sector_ids

FROZEN_Q, FROZEN_GAMMA = 2, 0.5
FLOCK_SEEDS = [2, 3, 8, 13]
N_TRANCHES = 4
N_SECTOR_GROUPS = 8
N_REP = 30
SEED_BASE = V3_SEED_OFFSET + 2_000_000


def make_schedule(kind: str, actuators: list[int], h_star: int, lattice, I0, B_D0,
                   greedy_order: list[int]) -> dict[int, dict[int, int]]:
    """All schedules force the SAME actuator identities (`actuators`) toward
    h_star, differing only in WHEN each one is switched on/off across the
    T_U-step window -- matched total actuator-budget, differing schedule."""
    A = list(actuators)
    n = len(A)

    if kind == "pulse":
        return {t: {int(b): int(h_star) for b in A} for t in range(T_U)}

    if kind == "ramp_up":
        # Partition by greedy-multicover ADDITION ORDER (earliest-added =
        # covers most new core birds first), bring one tranche online each
        # T_U/N_TRANCHES steps, cumulative.
        ordered = [b for b in greedy_order if b in set(A)]
        tranche_size = max(1, -(-len(ordered) // N_TRANCHES))
        step = T_U / N_TRANCHES
        sched: dict[int, dict[int, int]] = {t: {} for t in range(T_U)}
        for idx, b in enumerate(ordered):
            tranche = idx // tranche_size
            on_from = int(tranche * step)
            for t in range(on_from, T_U):
                sched[t][int(b)] = int(h_star)
        return sched

    if kind == "sequential_sectors":
        # Partition by angular sector (breadth-first, not depth-first):
        # activate one sector-group at a time, round-robin.
        sector_ids = _sector_ids(B_D0, I0, lattice, n_sectors=N_SECTOR_GROUPS)
        by_sector: dict[int, list[int]] = {}
        for b in A:
            by_sector.setdefault(sector_ids[b], []).append(b)
        sectors_present = sorted(by_sector.keys())
        n_groups = len(sectors_present)
        step = T_U / max(1, n_groups)
        sched = {t: {} for t in range(T_U)}
        for g_idx, s in enumerate(sectors_present):
            on_from = int(g_idx * step)
            for b in by_sector[s]:
                for t in range(on_from, T_U):
                    sched[t][int(b)] = int(h_star)
        return sched

    if kind == "ramp_down":
        # Full k active for first 3/4, then linearly reduce (reverse of
        # ramp_up) over the final quarter.
        ordered = [b for b in greedy_order if b in set(A)]
        hold_end = int(0.75 * T_U)
        tranche_size = max(1, -(-len(ordered) // N_TRANCHES))
        remaining_steps = T_U - hold_end
        step = remaining_steps / N_TRANCHES if remaining_steps > 0 else 1
        sched = {t: {int(b): int(h_star) for b in A} for t in range(hold_end)}
        for t in range(hold_end, T_U):
            sched[t] = {}
        # remove tranches progressively (last-added actuators dropped first)
        for idx, b in enumerate(reversed(ordered)):
            tranche = idx // tranche_size
            off_from = hold_end + int(tranche * step)
            for t in range(hold_end, off_from):
                sched[t][int(b)] = int(h_star)
        return sched

    raise ValueError(kind)


def evaluate_schedule(kind, actuators, greedy_order, I0, B_D0, z_t0, h_star, lattice,
                       n_replicates, seed_offset):
    Hstar_end = np.zeros(n_replicates)
    Hstar_release = np.zeros(n_replicates)
    coh_traj = np.zeros((n_replicates, T_U + 1))
    lineage_end = np.zeros(n_replicates)
    n_active_traj = np.zeros((n_replicates, T_U))

    for r in range(n_replicates):
        seed = seed_offset + r
        sched = make_schedule(kind, actuators, h_star, lattice, I0, B_D0, greedy_order)
        res = run_simulation(nn=lattice.nn, nt=T_U + T_R, seed=seed, init_z=z_t0,
                              interventions=sched, lattice=lattice)
        Hstar_end[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)
        Hstar_release[r] = target_heading_fraction(res.z_hist[T_U + T_R], I0, h_star)
        for t in range(T_U + 1):
            coh_traj[r, t] = coherence(res.z_hist[t], I0)
        for t in range(T_U):
            n_active_traj[r, t] = len(sched.get(t, {}))
        window = res.z_hist[T_U - TW + 1: T_U + 1]
        sr = analyze_window(window, refclust=I0)
        lineage_end[r] = len(np.intersect1d(I0, sr.core1_nodes)) / len(I0)

    min_coh = coh_traj.min(axis=1)
    success = Hstar_end >= 0.8

    def recovery_time(traj, c_recover=0.8, dwell=3):
        for t in range(len(traj) - dwell + 1):
            if np.all(traj[t:t + dwell] >= c_recover):
                return t
        return None
    rec_times = [recovery_time(coh_traj[r]) for r in range(n_replicates)]
    rec_achieved = [t for t in rec_times if t is not None]

    return dict(
        kind=kind, n_actuators=len(actuators), n_replicates=n_replicates,
        mean_Hstar_end=float(Hstar_end.mean()), p_success=float(success.mean()),
        mean_Hstar_release=float(Hstar_release.mean()), mean_lineage_end=float(lineage_end.mean()),
        mean_min_coherence=float(min_coh.mean()), min_coherence_worst=float(min_coh.min()),
        p_recovery_achieved=len(rec_achieved) / n_replicates,
        mean_recovery_time=float(np.mean(rec_achieved)) if rec_achieved else None,
        mean_control_effort=float(n_active_traj.sum(axis=1).mean()),  # actuator-steps used
        coh_traj_mean_over_reps=coh_traj.mean(axis=0).tolist(),
        n_active_mean_over_reps=n_active_traj.mean(axis=0).tolist(),
    )


def main():
    t_start = time.time()
    all_flocks = {fl["seed"]: fl for fl in load_dev_flocks()}
    results = []
    for seed in FLOCK_SEEDS:
        fl = all_flocks[seed]
        lattice, I0, z_t0, h_star = fl["lattice"], fl["I0"], fl["z_t0"], fl["h_star"]
        B_D0 = dynamical_shell(lattice, I0)
        A = min_actuators_for_multicover(B_D0, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA)
        order = greedy_multicover_order(B_D0, I0, lattice, q=FROZEN_Q)

        flock_out = dict(seed=seed, k=len(A), size_B_D0=len(B_D0), schedules={})
        for kind in ["pulse", "ramp_up", "sequential_sectors", "ramp_down"]:
            m = evaluate_schedule(kind, A, order, I0, B_D0, z_t0, h_star, lattice,
                                   n_replicates=N_REP, seed_offset=SEED_BASE + 1000 * seed)
            flock_out["schedules"][kind] = m
            print(f"seed {seed} {kind:20s} p_success={m['p_success']:.3f} "
                  f"mean_min_coh={m['mean_min_coherence']:.3f} worst_min_coh={m['min_coherence_worst']:.3f} "
                  f"p_recovery={m['p_recovery_achieved']:.3f} mean_rec_t={m['mean_recovery_time']} "
                  f"effort={m['mean_control_effort']:.1f}  ({time.time()-t_start:.1f}s elapsed)")
        results.append(flock_out)

    dump_json(dict(q=FROZEN_Q, gamma=FROZEN_GAMMA, flocks=results), V3_DIR / "data" / "staged_actuation.json")
    print(f"\nDone in {time.time()-t_start:.1f}s. Wrote data/staged_actuation.json")


if __name__ == "__main__":
    main()
