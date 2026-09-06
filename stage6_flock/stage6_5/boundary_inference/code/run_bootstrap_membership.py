"""Part 1.7: bootstrap boundary-membership frequency, canonical flock (seed
2) only (PLAN.md scope note). EVALUATION-SIDE DRIVER for data generation and
truth reveal; the bootstrap procedure itself (api.infer_boundary's n_boot
path) only ever sees z arrays + I0.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

from trajectory_gen import generate_trajectories, make_splits  # noqa: E402
from common_v2 import find_flock, dynamical_shell  # noqa: E402
from api import infer_boundary  # noqa: E402

SEED = 2
N_TRAIN, N_VAL, N_TEST = 100, 30, 30
N_TIME = 15
SHORTLIST_K = 20
N_BOOT = 15
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main(delta_tol_frac: float, min_gain_frac: float):
    fl = find_flock(SEED)
    I0 = fl["I0"]
    B_D = dynamical_shell(fl["lattice"], I0)

    rng = np.random.default_rng(2025)
    z = generate_trajectories(fl["z_t0"], fl["lattice"], n_traj=N_TRAIN + N_VAL + N_TEST, n_time=N_TIME)
    tr, va, te = make_splits(N_TRAIN + N_VAL + N_TEST, N_TRAIN, N_VAL, N_TEST, rng)

    res = infer_boundary(z[tr], z[va], I0, shortlist_k=SHORTLIST_K, delta_tol=None, min_gain=None,
                          delta_tol_frac=delta_tol_frac, min_gain_frac=min_gain_frac,
                          n_boot=N_BOOT, rng=np.random.default_rng(7))

    membership = res.membership
    ranked = sorted(membership.items(), key=lambda kv: -kv[1])
    print("Top-15 exterior birds by bootstrap membership frequency m_j:")
    B_D_set = set(B_D.tolist())
    for bird, freq in ranked[:15]:
        print(f"  bird {bird:3d}  m_j={freq:.2f}  {'(in B^D)' if bird in B_D_set else ''}")

    out = dict(seed=SEED, I0=sorted(I0.tolist()), B_D=sorted(B_D_set), n_boot=N_BOOT,
               delta_tol_frac=delta_tol_frac, min_gain_frac=min_gain_frac,
               B_hat_point_estimate=sorted(res.B_hat), membership=membership,
               bootstrap_sets=res.bootstrap_sets)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "bootstrap_membership.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\nWrote data/bootstrap_membership.json")


if __name__ == "__main__":
    import sys
    dtf = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
    mgf = float(sys.argv[2]) if len(sys.argv) > 2 else 0.005
    main(dtf, mgf)
