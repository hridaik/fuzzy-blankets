"""Part 1.1-1.7 development-flock sweep. EVALUATION-SIDE DRIVER (imports the
lattice only to generate trajectories and to reveal B^D for the dev-flock
diagnostic column -- the actual selection calls, via api.infer_boundary, see
only z arrays and I0, honoring Part 1's hard requirement).

Purpose: freeze (shortlist_k, delta_tol, min_gain, n_boot, N_train, N_val)
BEFORE any held-out number is computed. Dev seeds are V3's frozen
{2,3,4} (first three of DEV_SEEDS) -- reused, not re-scanned.

Run: python3 run_dev_sweep.py   (from boundary_inference/code/)
"""
from __future__ import annotations

import json
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

from trajectory_gen import generate_trajectories, make_splits  # noqa: E402
from common_v2 import find_flock, dynamical_shell  # noqa: E402
from api import infer_boundary  # noqa: E402

DEV_SEEDS = [2, 3, 4]
N_TRAIN, N_VAL, N_TEST = 100, 30, 30
N_TIME = 15
SHORTLIST_K = 20
# Part 1.5's "delta relative to the full predictor", operationalized as a
# fraction of the total gap (interior_only_loss - full_loss) each flock's
# exterior closes -- see api.py's docstring on why an absolute-nats
# threshold was abandoned after the first sweep (round 1, superseded, see
# PROTOCOL_6_5.md) showed some dev flocks' total gap itself sits near a
# fixed absolute tolerance, making the threshold trivial for them.
DELTA_TOL_FRAC_GRID = [0.05, 0.1, 0.2, 0.4, 0.6]
MIN_GAIN_FRAC_DIVISOR = 10  # min_gain_frac = delta_tol_frac / this
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def run_one(seed: int, delta_tol_frac: float, min_gain_frac: float, rng: np.random.Generator) -> dict:
    fl = find_flock(seed)
    I0 = fl["I0"]
    B_D = dynamical_shell(fl["lattice"], I0)
    z = generate_trajectories(fl["z_t0"], fl["lattice"], n_traj=N_TRAIN + N_VAL + N_TEST, n_time=N_TIME)
    tr, va, te = make_splits(N_TRAIN + N_VAL + N_TEST, N_TRAIN, N_VAL, N_TEST, rng)

    t0 = time.time()
    res = infer_boundary(z[tr], z[va], I0, shortlist_k=SHORTLIST_K, delta_tol=None, min_gain=None,
                          delta_tol_frac=delta_tol_frac, min_gain_frac=min_gain_frac, n_boot=0)
    elapsed = time.time() - t0

    B_hat = set(res.B_hat)
    B_D_set = set(B_D.tolist())
    tp = len(B_hat & B_D_set)
    jaccard = tp / len(B_hat | B_D_set) if (B_hat | B_D_set) else 1.0
    return dict(
        seed=seed, delta_tol_frac=delta_tol_frac, min_gain_frac=min_gain_frac,
        elapsed_sec=round(elapsed, 1),
        B_hat=sorted(B_hat), B_D=sorted(B_D_set), size_hat=len(B_hat), size_true=len(B_D_set),
        jaccard=jaccard, tp=tp, fp=len(B_hat - B_D_set), fn=len(B_D_set - B_hat),
        full_loss=res.full_loss, interior_only_loss=res.interior_only_loss,
        total_gap=res.params["total_gap"], delta_tol_abs=res.params["delta_tol"],
        min_gain_abs=res.params["min_gain"],
        excess_loss_B_hat=res.excess_loss_B_hat, n_greedy_steps=len(res.trace) - 1,
        stop_reason=res.trace[-1].get("stop_reason"),
    )


def main():
    rng = np.random.default_rng(20250906)
    rows = []
    for delta_tol_frac in DELTA_TOL_FRAC_GRID:
        min_gain_frac = delta_tol_frac / MIN_GAIN_FRAC_DIVISOR
        for seed in DEV_SEEDS:
            row = run_one(seed, delta_tol_frac, min_gain_frac, rng)
            rows.append(row)
            print(f"seed={seed} delta_tol_frac={delta_tol_frac} -> total_gap={row['total_gap']:.4f} "
                  f"|B_hat|={row['size_hat']} jaccard={row['jaccard']:.2f} "
                  f"excess={row['excess_loss_B_hat']:.4f} ({row['elapsed_sec']}s, stop={row['stop_reason']})")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "dev_sweep.json", "w") as f:
        json.dump(dict(dev_seeds=DEV_SEEDS, n_train=N_TRAIN, n_val=N_VAL, n_test=N_TEST,
                        n_time=N_TIME, shortlist_k=SHORTLIST_K,
                        delta_tol_frac_grid=DELTA_TOL_FRAC_GRID,
                        min_gain_frac_divisor=MIN_GAIN_FRAC_DIVISOR, rows=rows), f, indent=1)
    print("\nWrote data/dev_sweep.json")


if __name__ == "__main__":
    main()
