"""Extends v2's evaluate_arm with (a) full per-replicate coherence
trajectories (needed for Part 2's integrity-threshold statistics, which
v2's evaluate_arm only summarizes as a mean) and (b) Part 1A's structural
report, so every simulated arm carries both its structural description and
its simulated outcome in one record. Does not modify or reimport
evaluate_arm's numbers -- recomputes with the identical procedure
(make_pulse, T_U/T_R, common-random-numbers convention) so V3 numbers are
directly comparable to V2's frozen ones."""
from __future__ import annotations

import numpy as np

from common_v3 import run_simulation, make_pulse, target_heading_fraction, coherence, analyze_window, T_U, T_R, TW
from coverage_metrics import structural_report


def evaluate_arm_v3(actuators, I0, B_D0, z_t0, h_star, lattice, n_replicates: int, seed_offset: int,
                     _struct_cache: dict | None = None) -> dict:
    Hstar_end = np.zeros(n_replicates)
    Hstar_release = np.zeros(n_replicates)
    coh_traj = np.zeros((n_replicates, T_U + 1))
    lineage_end = np.zeros(n_replicates)

    for r in range(n_replicates):
        seed = seed_offset + r
        interventions = make_pulse(actuators, h_star, t0=0, t_u=T_U) if len(actuators) else None
        res = run_simulation(nn=lattice.nn, nt=T_U + T_R, seed=seed, init_z=z_t0,
                              interventions=interventions, lattice=lattice)
        Hstar_end[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)
        Hstar_release[r] = target_heading_fraction(res.z_hist[T_U + T_R], I0, h_star)
        for t in range(T_U + 1):
            coh_traj[r, t] = coherence(res.z_hist[t], I0)
        window = res.z_hist[T_U - TW + 1: T_U + 1]
        sr = analyze_window(window, refclust=I0)
        lineage_end[r] = len(np.intersect1d(I0, sr.core1_nodes)) / len(I0)

    min_coh_full = coh_traj.min(axis=1)
    min_coh_recovery = coh_traj[:, -4:].min(axis=1)
    success = Hstar_end >= 0.8
    integrity_full = (min_coh_full >= 0.8) & (lineage_end >= 0.5)
    integrity_recovery = (min_coh_recovery >= 0.8) & (lineage_end >= 0.5)
    persistence = Hstar_release >= 0.5

    out = dict(
        n_replicates=n_replicates,
        mean_Hstar_end=float(Hstar_end.mean()), p_success=float(success.mean()),
        p_success_and_integrity_full=float((success & integrity_full).mean()),
        p_success_and_integrity_recovery=float((success & integrity_recovery).mean()),
        mean_Hstar_release=float(Hstar_release.mean()),
        p_persistence_given_success=float(persistence[success].mean()) if success.any() else None,
        mean_min_coherence=float(min_coh_full.mean()), mean_lineage_end=float(lineage_end.mean()),
        success_per_rep=success.astype(int).tolist(),
        coh_traj=coh_traj.tolist(),
        Hstar_end_per_rep=Hstar_end.tolist(),
        Hstar_release_per_rep=Hstar_release.tolist(),
    )
    out.update(structural_report(actuators, I0, B_D0, lattice, _cache=_struct_cache))
    out["actuators"] = list(int(a) for a in actuators)
    return out
