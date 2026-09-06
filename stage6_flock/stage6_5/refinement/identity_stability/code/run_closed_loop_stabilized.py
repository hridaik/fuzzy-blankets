"""Part C driver, closed-loop half (C7/C8). Run ONLY after
run_identity_stability.py's evaluation-only outputs (lambda_T, envelopes)
are frozen. Compares Material / Regularized-lineage (guarded) /
Guarded-functional controllers, plus the original unconstrained-functional
definition retained only as the Part-C7 pathology comparator.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
COLLECTIVE_IDENTITY_CODE = ROOT / "stage6_5" / "collective_identity" / "code"
sys.path.insert(0, str(COLLECTIVE_IDENTITY_CODE))
CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from common_v2 import find_flock  # noqa: E402
from pathwise_boundary import pathwise_leakage  # noqa: E402
from guarded_controller import run_guarded_closed_loop_episode, summarize_guarded_episode  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FLOCKS = [2, 3, 4]
N_REP = 30
REPRESENTATIONS = ["M", "L_reg", "F_guard", "F"]  # F = unguarded pathology comparator only
CLOSED_LOOP_EVAL_SEED_OFFSET = 8_900_000
PATHWISE_T_VALUES = list(range(0, 41, 4))  # 11 checkpoints, matches Stage 6.5 Part 6's own convention


def run_flock(seed: int, lambda_T: float, envelopes: dict) -> dict:
    fl = find_flock(seed)
    rep_episodes = {r: [] for r in REPRESENTATIONS}
    representative_episode = {}
    for r in REPRESENTATIONS:
        env = None if r == "M" else (envelopes["L_reg"] if r == "L_reg" else envelopes["F"])
        for rep_i in range(N_REP):
            seed_r = CLOSED_LOOP_EVAL_SEED_OFFSET + 1000 * seed + 100 * REPRESENTATIONS.index(r) + rep_i
            ep = run_guarded_closed_loop_episode(fl, r, seed=seed_r, envelope=env, lambda_T=lambda_T)
            summary = summarize_guarded_episode(ep)
            rep_episodes[r].append(summary)
            if rep_i == 0:
                representative_episode[r] = ep
        p_succ = np.mean([e["nominal_success"] for e in rep_episodes[r]])
        p_valid_succ = np.mean([e["identity_valid_success"] for e in rep_episodes[r]])
        p_collapsed = np.mean([e["identity_collapse_unresolved"] for e in rep_episodes[r]])
        print(f"  seed={seed} rep={r:8s} nominal_p_success={p_succ:.2f} "
              f"identity_valid_p_success={p_valid_succ:.2f} p_collapsed={p_collapsed:.2f} "
              f"mean_final_size={np.mean([e['final_size'] for e in rep_episodes[r]]):.1f} "
              f"mean_n_actuators={np.mean([e['mean_n_actuators'] for e in rep_episodes[r]]):.1f}")

    # C8: pathwise leakage on the representative (replicate 0) episode per representation
    pathwise = {}
    lattice, nn = fl["lattice"], fl["lattice"].nn
    for r in REPRESENTATIONS:
        ep = representative_episode[r]
        pw = pathwise_leakage(ep["z_hist"], ep["I_track"], ep["B_track"], nn, lattice,
                               t_values=PATHWISE_T_VALUES, n_honest=25, n_corrupt=25,
                               seed_offset=8_950_000 + 1000 * seed + REPRESENTATIONS.index(r))
        pathwise[r] = pw
        print(f"  seed={seed} rep={r:8s} pathwise mean_leakage={pw['mean_leakage']:.4f} "
              f"max_leakage={pw['max_leakage']:.4f} boundary_sizes={pw['boundary_sizes']}")

    return dict(
        seed=seed,
        summary={r: dict(
            nominal_p_success=float(np.mean([e["nominal_success"] for e in eps])),
            identity_valid_p_success=float(np.mean([e["identity_valid_success"] for e in eps])),
            p_collapsed=float(np.mean([e["identity_collapse_unresolved"] for e in eps])),
            mean_final_size=float(np.mean([e["final_size"] for e in eps])),
            mean_final_retention=float(np.mean([e["final_retention"] for e in eps])),
            mean_n_actuators=float(np.mean([e["mean_n_actuators"] for e in eps])),
            mean_membership_turnover=float(np.mean([e["membership_turnover_total"] for e in eps])),
            mean_actuator_turnover=float(np.mean([e["actuator_turnover_total"] for e in eps])),
            mean_persistence=float(np.mean([e["persistence"] for e in eps])),
        ) for r, eps in rep_episodes.items()},
        pathwise={r: dict(mean_leakage=pathwise[r]["mean_leakage"], max_leakage=pathwise[r]["max_leakage"],
                           boundary_sizes=pathwise[r]["boundary_sizes"],
                           boundary_turnover=pathwise[r]["boundary_turnover"]) for r in REPRESENTATIONS},
    )


def main():
    calib = json.load(open(DATA_DIR / "regularized_lineage_calibration.json"))
    envelopes = json.load(open(DATA_DIR / "validity_envelope.json"))
    lambda_T = calib["chosen_lambda_T"]
    print(f"Using frozen lambda_T={lambda_T}, envelopes={envelopes}\n")

    results = []
    for seed in FLOCKS:
        print(f"=== flock seed {seed} ===")
        results.append(run_flock(seed, lambda_T, envelopes))

    with open(DATA_DIR / "closed_loop_stabilized.json", "w") as f:
        json.dump(dict(flocks=FLOCKS, n_rep=N_REP, lambda_T=lambda_T, representations=REPRESENTATIONS,
                        results=results), f, indent=1)
    print(f"\nWrote {DATA_DIR / 'closed_loop_stabilized.json'}")


if __name__ == "__main__":
    main()
