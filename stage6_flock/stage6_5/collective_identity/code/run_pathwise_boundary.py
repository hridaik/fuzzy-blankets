"""Part 6: pathwise one-step boundary-screening diagnostic, along the SAME
closed-loop episodes produced by Part 5 (adaptive_control.py) for each
representation -- so this directly answers "does the collective remain
surrounded by a compact predictive interface as its description changes
along the very control path Part 5 already ran?" rather than a fresh,
unrelated trajectory.

Scope (PLAN.md): canonical flock (seed 2), one episode per representation
(seed=0, matching the first adaptive-control replicate), t sampled every 4
steps across the full T_u+T_r=40-step episode (11 points) -- a documented
compute-scoped subsample of "every timestep", per Part 6's own instruction
not to attempt an exhaustive exact estimate.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
from common_v2 import find_flock, T_U, T_R  # noqa: E402

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))
from adaptive_control import run_closed_loop_episode  # noqa: E402
from pathwise_boundary import pathwise_leakage, time_above_tolerance  # noqa: E402

FLOCK_SEED = 2
REPRESENTATIONS = ["M", "L", "F"]
T_STEP = 4
N_HONEST, N_CORRUPT = 25, 25
LEAKAGE_TOLERANCE = 0.02  # nats, a small predeclared "essentially screened" tolerance
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main():
    fl = find_flock(FLOCK_SEED)
    n_total = T_U + T_R + 1
    t_values = list(range(0, n_total, T_STEP))
    if t_values[-1] != n_total - 1:
        t_values.append(n_total - 1)

    results = {}
    for rep in REPRESENTATIONS:
        ep = run_closed_loop_episode(fl, rep, seed=0)
        rng = np.random.default_rng(42)
        res = pathwise_leakage(ep["z_hist"], ep["I_track"], ep["B_track"], nn=fl["lattice"].nn,
                                lattice=fl["lattice"], t_values=t_values, n_honest=N_HONEST,
                                n_corrupt=N_CORRUPT, seed_offset=700_000 + 10_000 * ord(rep), rng=rng)
        res["time_above_tolerance"] = time_above_tolerance(res, LEAKAGE_TOLERANCE)
        res["t_values"] = t_values
        results[rep] = res
        print(f"rep={rep}: mean_leakage={res['mean_leakage']:.4f} max_leakage={res['max_leakage']:.4f} "
              f"time_above_tol={res['time_above_tolerance']}/{len(t_values)} "
              f"boundary_sizes={res['boundary_sizes']}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "pathwise_boundary.json", "w") as f:
        json.dump(dict(flock_seed=FLOCK_SEED, t_step=T_STEP, n_honest=N_HONEST, n_corrupt=N_CORRUPT,
                        leakage_tolerance=LEAKAGE_TOLERANCE, results=results), f, indent=1)
    print("\nWrote data/pathwise_boundary.json")


if __name__ == "__main__":
    main()
