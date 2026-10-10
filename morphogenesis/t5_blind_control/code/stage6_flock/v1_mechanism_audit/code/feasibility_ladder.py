"""Part D: the missing feasibility ladder. Same canonical snapshot, same
target, same T_u=20/T_r=20, same success/integrity/persistence thresholds as
PROTOCOL_V1.md -- nothing here is retuned. Arms D0-D5, common random numbers
(BASE_SEED_OFFSET, identical to phase3_controls.py / phase4_5_response_map.py).

Structural note on D3 vs D4 (see dynamical_shell.py docstring): because I0 is
frozen and the lattice topology is time-invariant in this port, the
"adaptive" dynamical shell B^D_t (recomputed every step from the still-frozen
I0) is IDENTICAL to the static shell B^D_0 at every t. D3 and D4 are
therefore run as the SAME arm here (reported once, not duplicated with fake
distinct random draws) -- this is itself the Outcome-3 finding, stated
plainly rather than manufactured.
"""
from __future__ import annotations

import json
import time
import numpy as np

from common import ROOT, AUDIT_DIR, load_canonical, dump_json, T_U, T_R, BASE_SEED_OFFSET, N_DEV, TW
from flock_sim.simulation import run_simulation
from flock_sim.interventions import make_pulse
from flock_sim.metrics import target_heading_fraction, coherence
from flock_sim.spectral import analyze_window


def run_arm(name, actuators, z_t0, I0, h_star, lattice, n_replicates=N_DEV):
    Hstar_traj = np.zeros((n_replicates, T_U + T_R + 1))
    coh_traj = np.zeros((n_replicates, T_U + T_R + 1))
    lineage_end = np.zeros(n_replicates)
    for r in range(n_replicates):
        seed = BASE_SEED_OFFSET + r
        interventions = make_pulse(actuators, h_star, t0=0, t_u=T_U) if len(actuators) else None
        res = run_simulation(nn=lattice.nn, nt=T_U + T_R, seed=seed, init_z=z_t0,
                              interventions=interventions, lattice=lattice)
        for t in range(T_U + T_R + 1):
            Hstar_traj[r, t] = target_heading_fraction(res.z_hist[t], I0, h_star)
            coh_traj[r, t] = coherence(res.z_hist[t], I0)
        window = res.z_hist[T_U - TW + 1: T_U + 1]
        sr = analyze_window(window, refclust=I0)
        lineage_end[r] = len(np.intersect1d(I0, sr.core1_nodes)) / len(I0)

    Hstar_end = Hstar_traj[:, T_U]
    Hstar_release = Hstar_traj[:, T_U + T_R]
    min_coh = coh_traj[:, :T_U + 1].min(axis=1)
    success = Hstar_end >= 0.8
    integrity = (min_coh >= 0.8) & (lineage_end >= 0.5)
    persistence = Hstar_release >= 0.5

    return dict(
        name=name, actuators=[int(a) for a in actuators],
        n_actuators=len(actuators), n_replicates=n_replicates,
        mean_Hstar_end=float(Hstar_end.mean()), p_success=float(success.mean()),
        p_success_and_integrity=float((success & integrity).mean()),
        mean_Hstar_release=float(Hstar_release.mean()),
        p_persistence_given_success=float(persistence[success].mean()) if success.any() else None,
        mean_min_coherence=float(min_coh.mean()), mean_lineage_end=float(lineage_end.mean()),
        Hstar_traj_mean=Hstar_traj.mean(axis=0).tolist(),
        Hstar_traj_std=Hstar_traj.std(axis=0).tolist(),
        coh_traj_mean=coh_traj.mean(axis=0).tolist(),
    )


def main():
    c = load_canonical()
    lattice, I0, z_t0, h_star = c["lattice"], c["I0"], c["z_t0"], c["h_star"]
    ds = json.load(open(AUDIT_DIR / "data" / "dynamical_shell.json"))
    B_D0 = np.array(ds["B_D0"])
    B_F0 = np.array(ds["B_F0"])
    non_core = np.setdiff1d(np.arange(100), I0)

    arms_spec = [
        ("D0_baseline_empty", np.array([], dtype=int)),
        ("D1_full_interior_I0", I0),
        ("D2_fiedler_boundary_BF0", B_F0),
        ("D3_D4_dynamical_shell_BD0", B_D0),   # static == adaptive here, see docstring
        ("D5_all_non_core", non_core),
    ]

    results = {}
    t_start = time.time()
    for name, actuators in arms_spec:
        r = run_arm(name, actuators, z_t0, I0, h_star, lattice, n_replicates=N_DEV)
        results[name] = r
        print(f"{name}: n_act={r['n_actuators']:3d} mean_Hstar_end={r['mean_Hstar_end']:.3f} "
              f"p_success={r['p_success']:.3f} p_success_and_integrity={r['p_success_and_integrity']:.3f} "
              f"mean_Hstar_release={r['mean_Hstar_release']:.3f}  ({time.time()-t_start:.1f}s elapsed)")

    out = dict(T_u=T_U, T_r=T_R, n_replicates=N_DEV, seed_offset=BASE_SEED_OFFSET,
               I0=I0.tolist(), h_star=int(h_star), B_F0=B_F0.tolist(), B_D0=B_D0.tolist(),
               arms=results,
               note_D3_D4=("D3 (static shell) and D4 (adaptive shell) are reported as a single "
                            "arm 'D3_D4_dynamical_shell_BD0' because B^D_t == B^D_0 for all t in "
                            "this port -- see dynamical_shell.py docstring for the structural proof."))
    dump_json(out, AUDIT_DIR / "data" / "feasibility_ladder.json")


if __name__ == "__main__":
    main()
