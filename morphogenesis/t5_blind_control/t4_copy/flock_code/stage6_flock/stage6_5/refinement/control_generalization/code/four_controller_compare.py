"""B3/B4: for each discriminating flock, generate fresh observational
trajectories, re-run the FROZEN (unmodified) inference pipeline to get
B_hat/Ghat, and compare Oracle / Inferred / Fiedler / Random controllers at
a fresh, independent (from the seed-scan screen) replicate count.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))
BOUNDARY_INFERENCE_CODE = ROOT / "stage6_5" / "boundary_inference" / "code"
sys.path.insert(0, str(BOUNDARY_INFERENCE_CODE))

from common_v2 import find_flock, dynamical_shell, evaluate_arm  # noqa: E402
from selection_rules_v3 import min_actuators_for_multicover  # noqa: E402
from trajectory_gen import generate_trajectories, make_splits  # noqa: E402
from api import infer_boundary  # noqa: E402
from nodewise_model import flatten_transitions  # noqa: E402
from graph_inference import infer_incidence_graph  # noqa: E402
from ground_truth_eval import fiedler_boundary_from_trajectories  # noqa: E402
from control_compare import multicover_select  # noqa: E402

N_TRAIN, N_VAL, N_TEST = 100, 30, 30
N_TIME = 15
SHORTLIST_K = 20
DELTA_TOL_FRAC, MIN_GAIN_FRAC = 0.05, 0.005
FROZEN_Q, FROZEN_GAMMA = 2, 0.5
FINAL_N_REP = 50
FINAL_EVAL_SEED_OFFSET = 8_300_000


def true_incidence_graph(B_D, I0, lattice) -> dict:
    """Oracle-arm-only true incidence -- reproduced from
    boundary_inference/code/run_control_comparison.py's own helper of the
    same name (never used to build the Inferred arm)."""
    I0_list = I0.tolist()
    return {i: set(int(j) for j in lattice.neighbor_ids[i].tolist() if j in set(B_D.tolist()))
            for i in I0_list}


def compare_one_flock(seed: int) -> dict:
    fl = find_flock(seed)
    assert fl is not None
    I0, lattice, z_t0, h_star = fl["I0"], fl["lattice"], fl["z_t0"], fl["h_star"]
    nn = lattice.nn
    B_D = dynamical_shell(lattice, I0)

    rng = np.random.default_rng(FINAL_EVAL_SEED_OFFSET + seed)
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
    A_oracle = min_actuators_for_multicover(B_D, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA) if len(B_D) else []
    G_true = true_incidence_graph(B_D, I0, lattice)
    A_fiedler = (multicover_select(list(B_F), I0, {i: G_true.get(i, set()) & set(B_F.tolist())
                                                    for i in I0.tolist()}, q=FROZEN_Q, gamma=FROZEN_GAMMA)
                 if len(B_F) else [])
    budget = max(len(A_inferred), 1)
    exterior = [j for j in range(nn) if j not in set(I0.tolist())]
    A_random = sorted(rng.choice(exterior, size=min(budget, len(exterior)), replace=False).tolist())

    arms = dict(oracle=A_oracle, inferred=A_inferred, fiedler=A_fiedler, random_matched=A_random)
    arm_seed_slot = dict(oracle=0, inferred=1, fiedler=2, random_matched=3)
    row = dict(seed=int(seed), n_I0=len(I0), B_D=sorted(int(b) for b in B_D.tolist()),
               B_hat=sorted(int(b) for b in B_hat), B_F=sorted(int(b) for b in B_F.tolist()),
               excess_loss_B_hat=res.excess_loss_B_hat,
               arms={k: sorted(int(a) for a in v) for k, v in arms.items()})
    recovery_tp = len(set(B_hat) & set(B_D.tolist()))
    row["recall_B_hat"] = recovery_tp / len(B_D) if len(B_D) else float("nan")
    row["precision_B_hat"] = recovery_tp / len(B_hat) if len(B_hat) else float("nan")

    for name, A in arms.items():
        m = evaluate_arm(A, z_t0, I0, h_star, lattice, n_replicates=FINAL_N_REP,
                          seed_offset=FINAL_EVAL_SEED_OFFSET + 10_000 * seed + 100 * arm_seed_slot[name])
        row[name] = m
        print(f"  seed={seed} arm={name:14s} |A|={m['n_actuators']:2d} p_success={m['p_success']:.2f} "
              f"mean_Hstar_end={m['mean_Hstar_end']:.2f}")
    return row


def compare_all(seeds: list[int]) -> list[dict]:
    rows = []
    for seed in seeds:
        print(f"=== flock seed {seed} ===")
        rows.append(compare_one_flock(seed))
    return rows
