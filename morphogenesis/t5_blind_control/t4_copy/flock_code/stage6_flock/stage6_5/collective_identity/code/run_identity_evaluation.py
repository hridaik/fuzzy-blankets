"""Part 4: evaluate the SAME saved (controlled) trajectories under all three
identity definitions (I^M, I^L, I^F). Isolates representation effects from
controller effects -- the controller policy itself is the frozen V3
multicover rule (q=2, gamma=0.5) forcing the TRUE B^D_0, unmodified, exactly
Stage 6's own near-ceiling controller (not re-tuned here, Part 8's
prohibition on further V3 optimization).

Scope (PLAN.md): dev flocks 2, 3, 4; N_REP=8 controlled-episode replicates
per flock (a documented compute-scoped replicate count, in the spirit of
this project's own "development scale" language).
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))

from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.interventions import make_pulse  # noqa: E402
from common_v2 import find_flock, dynamical_shell, T_U, T_R  # noqa: E402
from selection_rules_v3 import min_actuators_for_multicover  # noqa: E402

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))
from definitions import material_track, lineage_track, functional_track  # noqa: E402
from identity_metrics import track_membership_metrics, track_boundary_metrics, per_definition_trajectory_report  # noqa: E402

FLOCKS = [2, 3, 4]
N_REP = 8
FROZEN_Q, FROZEN_GAMMA = 2, 0.5
SEED_OFFSET = 770_000
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def run_one_episode(fl, seed: int) -> np.ndarray:
    lattice, I0, h_star, z_t0 = fl["lattice"], fl["I0"], fl["h_star"], fl["z_t0"]
    B_D = dynamical_shell(lattice, I0)
    A = min_actuators_for_multicover(B_D, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA)
    interventions = make_pulse(A, h_star, t0=0, t_u=T_U)
    res = run_simulation(nn=lattice.nn, nt=T_U + T_R, seed=seed, init_z=z_t0,
                          interventions=interventions, lattice=lattice)
    return res.z_hist, A


def main():
    all_flock_results = []
    for flock_seed in FLOCKS:
        fl = find_flock(flock_seed)
        I0, lattice, h_star = fl["I0"], fl["lattice"], fl["h_star"]
        episodes = []
        for r in range(N_REP):
            seed = SEED_OFFSET + 1000 * flock_seed + r
            z_hist, A = run_one_episode(fl, seed)
            n = z_hist.shape[0]

            track_M = material_track(I0, n)
            track_L = lineage_track(z_hist, I0, t_start=0, t_end=n - 1)
            track_F = functional_track(z_hist, I0, t_start=0, t_end=n - 1, lattice=lattice)

            per_rep = {}
            for rep_name, track in [("M", track_M), ("L", track_L), ("F", track_F)]:
                report = per_definition_trajectory_report(z_hist, I0, track, h_star, T_U, T_R)
                mem = track_membership_metrics(I0, track)
                bnd = track_boundary_metrics(track, lattice)
                per_rep[rep_name] = dict(
                    success=report["success"], persistence=report["persistence"],
                    Hstar_end=report["Hstar_end"], Hstar_release=report["Hstar_release"],
                    recovery_time=report["recovery_time"], min_coherence=report["min_coherence"],
                    final_size=mem["size"][-1], final_R0=mem["R0"][-1], final_Qrecruit=mem["Qrecruit"][-1],
                    total_turnover=int(sum(mem["turnover"])),
                    final_boundary_size=bnd["size"][-1], total_boundary_turnover=int(sum(bnd["turnover"])),
                    decomposition_at_end=report["decomposition_trajectory"][min(T_U, n - 1)],
                    size_series=mem["size"], R0_series=mem["R0"], boundary_size_series=bnd["size"],
                    boundary_turnover_series=bnd["turnover"], Hstar_series=report["Hstar_trajectory"],
                )
            episodes.append(dict(replicate_seed=seed, n_actuators=len(A), per_representation=per_rep))
        all_flock_results.append(dict(flock_seed=flock_seed, I0=sorted(I0.tolist()), episodes=episodes))

        for rep_name in ("M", "L", "F"):
            succ = np.mean([e["per_representation"][rep_name]["success"] for e in episodes])
            pers = np.mean([e["per_representation"][rep_name]["persistence"] for e in episodes])
            print(f"flock={flock_seed} rep={rep_name}: p_success={succ:.2f} p_persistence={pers:.2f}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "identity_evaluation.json", "w") as f:
        json.dump(dict(flocks=FLOCKS, n_rep=N_REP, q=FROZEN_Q, gamma=FROZEN_GAMMA, results=all_flock_results),
                  f, indent=1)
    print("\nWrote data/identity_evaluation.json")


if __name__ == "__main__":
    main()
