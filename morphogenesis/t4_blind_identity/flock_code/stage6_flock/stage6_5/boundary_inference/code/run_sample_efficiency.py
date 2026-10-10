"""Part 1.9: sample-efficiency curve. EVALUATION-SIDE DRIVER (uses the
lattice only to generate trajectories and reveal B^D for the diagnostic
comparison column; infer_boundary itself sees only z arrays + I0).

Scope (see PLAN.md): the canonical flock (seed 2) only -- a within-flock
diagnostic of how much data boundary inference needs, not a cross-flock
generalization claim.
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

SEED = 2
# N_traj=200 was in the originally intended grid (Part 1.9 suggests it) but
# was dropped after timing out (>60s per fit at that point's ~3000 pooled
# training samples with liblinear, vs <5s at N_traj<=100) -- a documented
# compute-scope reduction, not a silent one; see PROTOCOL_6_5.md.
N_TRAJ_GRID = [5, 10, 20, 50, 100]
N_VAL, N_TEST = 30, 30
N_TIME = 15
SHORTLIST_K = 20
DELTA_TOL_FRAC = None  # set from PROTOCOL_6_5.md's frozen value by the caller / __main__ default below
MIN_GAIN_FRAC = None
N_BOOT = 0  # bootstrap uncertainty is reported separately (run_bootstrap_membership.py) to bound compute
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main(delta_tol_frac: float, min_gain_frac: float):
    fl = find_flock(SEED)
    I0 = fl["I0"]
    B_D = set(dynamical_shell(fl["lattice"], I0).tolist())
    n_exterior = 100 - len(I0)

    rng = np.random.default_rng(20250906)
    max_n = max(N_TRAJ_GRID) + N_VAL + N_TEST
    z_all = generate_trajectories(fl["z_t0"], fl["lattice"], n_traj=max_n, n_time=N_TIME)
    # fixed val/test pool for every N_train point (drawn once from the tail of the pool)
    perm = rng.permutation(max_n)
    val_idx = perm[:N_VAL]
    test_idx = perm[N_VAL:N_VAL + N_TEST]
    train_pool = perm[N_VAL + N_TEST:]

    rows = []
    for n_traj in N_TRAJ_GRID:
        train_idx = train_pool[:n_traj]
        t0 = time.time()
        res = infer_boundary(z_all[train_idx], z_all[val_idx], I0, shortlist_k=SHORTLIST_K,
                              delta_tol=None, min_gain=None, delta_tol_frac=delta_tol_frac,
                              min_gain_frac=min_gain_frac, n_boot=N_BOOT)
        elapsed = time.time() - t0
        B_hat = set(res.B_hat)
        jaccard = len(B_hat & B_D) / len(B_hat | B_D) if (B_hat | B_D) else 1.0
        rows.append(dict(
            n_traj=n_traj, elapsed_sec=round(elapsed, 1), size_hat=len(B_hat),
            jaccard=jaccard, tp=len(B_hat & B_D), fp=len(B_hat - B_D), fn=len(B_D - B_hat),
            full_loss=res.full_loss, interior_only_loss=res.interior_only_loss,
            total_gap=res.params["total_gap"], excess_loss_B_hat=res.excess_loss_B_hat,
            B_hat=sorted(B_hat),
        ))
        print(f"n_traj={n_traj}: |B_hat|={len(B_hat)} jaccard={jaccard:.2f} "
              f"excess={res.excess_loss_B_hat:.4f} total_gap={res.params['total_gap']:.4f} "
              f"({elapsed:.1f}s)")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = dict(seed=SEED, I0=sorted(I0.tolist()), B_D=sorted(B_D), n_val=N_VAL, n_test=N_TEST,
               n_time=N_TIME, shortlist_k=SHORTLIST_K, delta_tol_frac=delta_tol_frac,
               min_gain_frac=min_gain_frac, n_traj_grid=N_TRAJ_GRID, rows=rows)
    with open(DATA_DIR / "sample_efficiency.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\nWrote data/sample_efficiency.json")


if __name__ == "__main__":
    import sys
    # frozen values are injected by run_frozen_pipeline.py after PROTOCOL_6_5.md
    # is written; this default lets the script be re-run standalone with the
    # same frozen numbers once they exist.
    dtf = float(sys.argv[1]) if len(sys.argv) > 1 else 0.2
    mgf = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02
    main(dtf, mgf)
