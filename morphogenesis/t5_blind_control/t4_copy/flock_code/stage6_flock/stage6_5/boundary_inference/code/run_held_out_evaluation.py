"""Part 1.8 / 1.10 / Gate A: held-out evaluation. EVALUATION-SIDE DRIVER.
Uses the FROZEN hyperparameters from PROTOCOL_6_5.md/configs/protocol_6_5.yaml
(passed in as CLI args, defaulting to the frozen values once they exist) --
no threshold here is chosen after seeing these numbers.

Scope (PLAN.md): first three of V3's six frozen held-out seeds
(v3_refinement/data/held_out_flocks.json if present, else recomputed by the
identical scan procedure). Never touched during Part 1.1-1.7 development.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

from trajectory_gen import generate_trajectories, make_splits  # noqa: E402
from common_v2 import dynamical_shell  # noqa: E402
from common_v3 import find_held_out_flocks  # noqa: E402
from api import infer_boundary  # noqa: E402
from ground_truth_eval import compare_boundaries, fiedler_boundary_from_trajectories  # noqa: E402

N_HELD_OUT = 3  # of V3's frozen 6 (see PLAN.md scope note)
N_TRAIN, N_VAL, N_TEST = 100, 30, 30
N_TIME = 15
SHORTLIST_K = 20
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main(delta_tol_frac: float, min_gain_frac: float):
    flocks = find_held_out_flocks()[:N_HELD_OUT]
    print(f"Held-out flocks (first {N_HELD_OUT} of V3's frozen 6): "
          f"{[fl['seed'] for fl in flocks]}")

    all_results = []
    for fl in flocks:
        seed, I0, lattice = fl["seed"], fl["I0"], fl["lattice"]
        B_D = dynamical_shell(lattice, I0)
        candidates = [j for j in range(100) if j not in set(I0.tolist())]

        rng = np.random.default_rng(1_000_000 + seed)
        z = generate_trajectories(fl["z_t0"], lattice, n_traj=N_TRAIN + N_VAL + N_TEST, n_time=N_TIME)
        tr, va, te = make_splits(N_TRAIN + N_VAL + N_TEST, N_TRAIN, N_VAL, N_TEST, rng)

        res = infer_boundary(z[tr], z[va], I0, shortlist_k=SHORTLIST_K, delta_tol=None, min_gain=None,
                              delta_tol_frac=delta_tol_frac, min_gain_frac=min_gain_frac, n_boot=0)

        B_F = fiedler_boundary_from_trajectories(z[te[0]][:5], I0)

        cmp = compare_boundaries(I0, res.B_hat, B_D, B_F, candidates, z[tr], z[te], res.full_loss, rng)
        cmp["seed"] = int(seed)
        cmp["excess_loss_from_infer"] = res.excess_loss_B_hat
        cmp["total_gap"] = res.params["total_gap"]
        all_results.append(cmp)
        print(f"seed={seed}: |B_hat|={len(res.B_hat)} |B_D|={len(B_D)} |B_F|={len(B_F)} "
              f"precision={cmp['recovery_vs_BD']['precision']:.2f} "
              f"recall={cmp['recovery_vs_BD']['recall']:.2f} "
              f"jaccard={cmp['recovery_vs_BD']['jaccard']:.2f} "
              f"dl_hat={cmp['excess_loss']['B_hat']:.4f} dl_BD={cmp['excess_loss']['B_D']:.4f} "
              f"dl_BF={cmp['excess_loss']['B_F']:.4f} dl_rand={cmp['excess_loss']['random_matched_mean']:.4f}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "held_out_evaluation.json", "w") as f:
        json.dump(dict(seeds=[fl["seed"] for fl in flocks], n_train=N_TRAIN, n_val=N_VAL, n_test=N_TEST,
                        n_time=N_TIME, shortlist_k=SHORTLIST_K, delta_tol_frac=delta_tol_frac,
                        min_gain_frac=min_gain_frac, results=all_results), f, indent=1)
    print("\nWrote data/held_out_evaluation.json")


if __name__ == "__main__":
    import sys
    dtf = float(sys.argv[1]) if len(sys.argv) > 1 else 0.2
    mgf = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02
    main(dtf, mgf)
