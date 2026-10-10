"""Part 2: does controlling through the inferred boundary work?
EVALUATION-SIDE DRIVER. For each held-out flock: infer B_hat (blind, using
only the inference-side API), build the inferred incidence graph Ghat
(graph_inference.py, itself lattice-free), select actuators via the FROZEN
V3 multicover rule applied to Ghat, and compare four controllers by actually
running the simulator: Oracle-B^D, Inferred-B_hat, Fiedler-B^F,
random-matched-budget.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

from trajectory_gen import generate_trajectories, make_splits  # noqa: E402
from common_v2 import dynamical_shell, T_U, T_R  # noqa: E402
from common_v3 import find_held_out_flocks  # noqa: E402
from selection_rules_v3 import min_actuators_for_multicover  # noqa: E402
from api import infer_boundary  # noqa: E402
from nodewise_model import flatten_transitions  # noqa: E402
from graph_inference import infer_incidence_graph  # noqa: E402
from ground_truth_eval import fiedler_boundary_from_trajectories  # noqa: E402
from control_compare import multicover_select, evaluate_controller, FROZEN_Q, FROZEN_GAMMA  # noqa: E402

N_HELD_OUT = 3
N_TRAIN, N_VAL, N_TEST = 100, 30, 30
N_TIME = 15
SHORTLIST_K = 20
DELTA_TOL_FRAC, MIN_GAIN_FRAC = 0.05, 0.005
N_REP = 20
CONTROL_SEED_OFFSET = 760_000
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def true_incidence_graph(B_D, I0, lattice) -> dict:
    """The TRUE lattice incidence, for the Oracle controller arm only --
    never used to build the Inferred arm."""
    I0_list = I0.tolist()
    return {i: set(int(j) for j in lattice.neighbor_ids[i].tolist() if j in set(B_D.tolist()))
            for i in I0_list}


def main():
    flocks = find_held_out_flocks()[:N_HELD_OUT]
    all_rows = []
    for fl in flocks:
        seed, I0, lattice, z_t0, h_star = fl["seed"], fl["I0"], fl["lattice"], fl["z_t0"], fl["h_star"]
        nn = lattice.nn
        B_D = dynamical_shell(lattice, I0)

        rng = np.random.default_rng(2_000_000 + seed)
        z = generate_trajectories(z_t0, lattice, n_traj=N_TRAIN + N_VAL + N_TEST, n_time=N_TIME)
        tr, va, te = make_splits(N_TRAIN + N_VAL + N_TEST, N_TRAIN, N_VAL, N_TEST, rng)

        res = infer_boundary(z[tr], z[va], I0, shortlist_k=SHORTLIST_K, delta_tol=None, min_gain=None,
                              delta_tol_frac=DELTA_TOL_FRAC, min_gain_frac=MIN_GAIN_FRAC, n_boot=0)
        B_hat = res.B_hat
        B_F = fiedler_boundary_from_trajectories(z[te[0]][:5], I0)

        train_prev, train_next = flatten_transitions(z[tr])
        val_prev, val_next = flatten_transitions(z[va])
        G_hat_bool, _, _ = infer_incidence_graph(I0, B_hat, train_prev, train_next, val_prev, val_next)
        G_hat = {i: {j for j, edge in row.items() if edge} for i, row in G_hat_bool.items()}

        A_inferred = multicover_select(B_hat, I0, G_hat, q=FROZEN_Q, gamma=FROZEN_GAMMA) if B_hat else []
        A_oracle = (min_actuators_for_multicover(B_D, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA)
                    if len(B_D) else [])
        G_true = true_incidence_graph(B_D, I0, lattice)
        A_fiedler = (multicover_select(list(B_F), I0, {i: G_true.get(i, set()) & set(B_F.tolist())
                                                        for i in I0.tolist()}, q=FROZEN_Q, gamma=FROZEN_GAMMA)
                     if len(B_F) else [])
        budget = max(len(A_inferred), 1)
        A_random = sorted(rng.choice([j for j in range(nn) if j not in set(I0.tolist())],
                                      size=min(budget, nn - len(I0)), replace=False).tolist())

        arms = dict(oracle=A_oracle, inferred=A_inferred, fiedler=A_fiedler, random_matched=A_random)
        arm_seed_slot = dict(oracle=0, inferred=1, fiedler=2, random_matched=3)
        seed_row = dict(seed=int(seed), B_D=sorted(B_D.tolist()), B_hat=sorted(B_hat), B_F=sorted(B_F.tolist()),
                         arms={k: sorted(int(a) for a in v) for k, v in arms.items()})
        for name, A in arms.items():
            m = evaluate_controller(A, z_t0, I0, h_star, nn, lattice, n_replicates=N_REP,
                                     seed_offset=CONTROL_SEED_OFFSET + 10_000 * seed + 100 * arm_seed_slot[name])
            seed_row[name] = m
            print(f"seed={seed} arm={name:14s} |A|={m['n_actuators']:2d} "
                  f"p_success={m['p_success']:.2f} mean_Hstar_end={m['mean_Hstar_end']:.2f}")
        all_rows.append(seed_row)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "control_comparison.json", "w") as f:
        json.dump(dict(seeds=[fl["seed"] for fl in flocks], n_replicates=N_REP, q=FROZEN_Q, gamma=FROZEN_GAMMA,
                        delta_tol_frac=DELTA_TOL_FRAC, min_gain_frac=MIN_GAIN_FRAC, rows=all_rows), f, indent=1)
    print("\nWrote data/control_comparison.json")


if __name__ == "__main__":
    main()
