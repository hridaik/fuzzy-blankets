"""Sections 11-15 of the task brief: controlled archetypes (fixed I=I0) for
the metric-validation gate, plus the f_E exterior-control-budget sweep
(section 13) and per-t trajectories for the demo's Control-mode live metrics
(section 27). One candidate (I0) evaluated at many timepoints, so this is
cheap even at full time resolution (see run_landscape.py's timing pilot for
why the mask cache makes this affordable).

Usage: python3 run_archetype_validation.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from common_66 import (
    lattice_100, resize_to_k, K_INTERIOR, K_BOUNDARY_BUDGET, PRIMARY_SEEDS,
    R_REPLICATES, T_U, T_R, dump_json,
)
from flock_sim.metrics import target_heading_fraction
from windowed_data import run_condition_replicates, build_window_dataset
from predictive_cache import PredictiveCache
from landscape import evaluate_candidate
from archetypes import build_condition, CONDITIONS
from run_landscape import reference_I0, SEED_OFFSETS

STAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = STAGE_DIR / "data"
LOG_DIR = STAGE_DIR / "logs"

F_E_SWEEP = [0.25, 0.5, 0.75, 1.00]


def evaluate_fixed_candidate_at_t(cache_builder, z_reps, I0, h_star, t: int) -> dict:
    wds = build_window_dataset(z_reps, t=t)
    cache = PredictiveCache(z_reps.shape and cache_builder.lattice, wds.train_prev, wds.train_next,
                             wds.val_prev, wds.val_next)
    row = evaluate_candidate(cache, cache_builder.lattice, wds.representative_z, I0, K=K_BOUNDARY_BUDGET)
    row["H_star"] = float(target_heading_fraction(wds.representative_z, I0, h_star))
    row["effective_window"] = wds.effective_window
    row["cache_n_fits"] = cache.stats()["n_fits"]
    return row


class _Ctx:
    def __init__(self, lattice):
        self.lattice = lattice


def run_condition_trajectory(lattice, I0, h_star, z_t0, condition: str, f_E: float,
                              seed_offset: int, stride: int = 1) -> dict:
    cond = build_condition(lattice, I0, h_star, condition, f_E=f_E, t0=0, t_u=T_U)
    nt = T_U + T_R
    z_reps = run_condition_replicates(z_t0, lattice, cond["interventions"], nt=nt,
                                       n_rep=R_REPLICATES, seed_offset=seed_offset)
    ctx = _Ctx(lattice)
    ts, rows = [], []
    for t in range(1, nt + 1, stride):
        row = evaluate_fixed_candidate_at_t(ctx, z_reps, I0, h_star, t)
        ts.append(t)
        rows.append(row)

    series = dict(
        t=ts,
        C=[r["C_internal"] for r in rows],
        G=[r["G_internal"] for r in rows],
        L=[r["L_blanket"] for r in rows],
        D=[r["D_local"] for r in rows],
        H_E=[r["external_entropy"] for r in rows],
        directional_contrast=[r["directional_contrast"] for r in rows],
        cosine_similarity=[r["cosine_similarity"] for r in rows],
        H_star=[r["H_star"] for r in rows],
        effective_window=[r["effective_window"] for r in rows],
    )
    meta = dict(condition=condition, f_E=f_E, h_star=h_star, h_opp=cond["h_opp"],
                shell=cond["shell"].tolist(), near_exterior=cond["near_exterior"].tolist(),
                controlled_exterior=cond["controlled_exterior"].tolist(),
                n_shell_actuators=len(cond["shell"]),
                n_exterior_actuators=len(cond["controlled_exterior"]),
                T_u=T_U, T_r=T_R, stride=stride)
    return dict(meta=meta, series=series)


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_archetype_validation.log"
    t_start = time.time()
    lattice = lattice_100()
    out = {}
    with open(log_path, "a") as logf:
        logf.write(f"\n=== run_archetype_validation start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        for seed in PRIMARY_SEEDS:
            rng = np.random.default_rng(seed * 7 + 1)
            ref = reference_I0(lattice, seed, rng)
            I0, h_star, z_t0 = ref["I0"], ref["h_star"], ref["z_t0"]
            out[str(seed)] = dict(t0=ref["t0"], h0=ref["h0"], h_star=h_star, I0=I0.tolist(),
                                   size_raw=ref["size_raw"], conditions={})
            for condition in CONDITIONS:
                out[str(seed)]["conditions"][condition] = {}
                f_E_list = [1.0] if condition in ("no_control", "shell_only") else F_E_SWEEP
                for f_E in f_E_list:
                    stride = 1 if f_E == 1.0 else 2
                    t0 = time.time()
                    seed_offset = SEED_OFFSETS[condition] + int(round(f_E * 1000)) + 500_000
                    traj = run_condition_trajectory(lattice, I0, h_star, z_t0, condition, f_E,
                                                     seed_offset=seed_offset, stride=stride)
                    out[str(seed)]["conditions"][condition][f"{f_E:.2f}"] = traj
                    line = (f"seed={seed} condition={condition} f_E={f_E:.2f} "
                            f"elapsed={time.time()-t0:.1f}s")
                    print(line)
                    logf.write(line + "\n")
                    logf.flush()
        total = time.time() - t_start
        logf.write(f"=== done, total {total:.1f}s ===\n")
    dump_json(out, DATA_DIR / "archetype_trajectories.json")
    print(f"DONE total={total:.1f}s -> data/archetype_trajectories.json")


if __name__ == "__main__":
    main()
