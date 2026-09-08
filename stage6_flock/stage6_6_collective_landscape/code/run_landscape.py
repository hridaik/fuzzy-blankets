"""Orchestrates one snapshot's full candidate landscape: discover/resize the
seed's reference I0, build the condition's replicate ensemble + windowed
regime dataset, build the predictive cache, generate candidates, evaluate
Phi(I)=(C,G,L,D) for all of them, attach Pareto flags, save JSON+CSV.

Usage: python3 run_landscape.py --seed 2 --condition no_control --n 5000
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from common_66 import (
    lattice_100, find_flock, resize_to_k, K_INTERIOR, K_BOUNDARY_BUDGET,
    R_REPLICATES, T_U, T_R, dump_json,
)
from windowed_data import run_condition_replicates, build_window_dataset
from predictive_cache import PredictiveCache
from candidates import generate_candidate_landbank
from landscape import assemble_landscape, attach_pareto
from archetypes import build_condition, CONDITIONS

STAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = STAGE_DIR / "data"
LOG_DIR = STAGE_DIR / "logs"

SEED_OFFSETS = {  # distinct replicate-RNG ranges per condition, disjoint from V1-V3/6.5's own
    "no_control": 660_000,
    "shell_only": 661_000,
    "same_direction": 662_000,
    "opposite": 663_000,
    "disordered": 664_000,
}


def reference_I0(lattice, seed: int, rng: np.random.Generator) -> dict:
    fl = find_flock(seed, lattice=lattice)
    if fl is None:
        raise RuntimeError(f"seed {seed} does not qualify (find_flock returned None)")
    I0_raw = fl["I0"]
    I0 = resize_to_k(lattice, I0_raw, K_INTERIOR, rng=rng)
    return dict(seed=seed, t0=fl["t0"], h0=fl["h0"], h_star=fl["h_star"],
                I0_raw=I0_raw.tolist(), I0=I0, size_raw=len(I0_raw), z_t0=fl["z_t0"])


def run_snapshot(seed: int, condition: str, n_candidates: int, K: int = K_BOUNDARY_BUDGET,
                  f_E: float = 1.0, rng_seed: int = 0, verbose: bool = True) -> dict:
    t_wall0 = time.time()
    lattice = lattice_100()
    rng = np.random.default_rng(rng_seed)

    ref = reference_I0(lattice, seed, rng)
    cond = build_condition(lattice, ref["I0"], ref["h_star"], condition, f_E=f_E, t0=0, t_u=T_U)

    nt = T_U + T_R
    z_reps = run_condition_replicates(ref["z_t0"], lattice, cond["interventions"], nt=nt,
                                       n_rep=R_REPLICATES, seed_offset=SEED_OFFSETS[condition])
    t_snapshot = T_U  # control-end, task brief section 25

    wds = build_window_dataset(z_reps, t=t_snapshot)
    cache = PredictiveCache(lattice, wds.train_prev, wds.train_next, wds.val_prev, wds.val_next)

    z_window_spectral = z_reps[0, max(0, t_snapshot - 4):t_snapshot + 1]
    cand_rng = np.random.default_rng(rng_seed + 1)
    candidates = generate_candidate_landbank(lattice, wds.representative_z, z_window_spectral,
                                              ref["I0"], K_INTERIOR, n_candidates, cand_rng)

    snapshot_id = f"seed{seed}__{condition}__fE{f_E:.2f}__t{t_snapshot}"
    rows = assemble_landscape(cache, lattice, wds.representative_z, candidates, snapshot_id, K=K)
    rows = attach_pareto(rows)

    elapsed = time.time() - t_wall0
    meta = dict(
        seed=seed, condition=condition, f_E=f_E, t0=ref["t0"], h0=ref["h0"], h_star=ref["h_star"],
        h_opp=cond["h_opp"], I0=ref["I0"].tolist(), I0_raw=ref["I0_raw"], size_raw=ref["size_raw"],
        snapshot_id=snapshot_id, t_snapshot=t_snapshot, K_boundary_budget=K,
        n_candidates_requested=n_candidates, n_candidates_unique=len(rows),
        n_replicates=R_REPLICATES, effective_window=wds.effective_window,
        n_replicates_train=wds.n_replicates_train, n_replicates_val=wds.n_replicates_val,
        controlled_exterior=cond["controlled_exterior"].tolist(),
        shell_size=len(cond["shell"]), near_exterior_size=len(cond["near_exterior"]),
        cache_stats=cache.stats(), elapsed_seconds=elapsed,
        candidate_source_counts={s: sum(1 for r in rows if r["candidate_source"] == s)
                                  for s in sorted(set(r["candidate_source"] for r in rows))},
    )
    if verbose:
        print(f"[{snapshot_id}] n={len(rows)} elapsed={elapsed:.1f}s cache={cache.stats()}")
    return dict(meta=meta, rows=rows, representative_z=wds.representative_z.tolist(),
                lattice_neighbors={str(i): lattice.neighbor_ids[i].tolist() for i in range(lattice.nn)})


def save_snapshot(result: dict, out_dir: Path):
    snapshot_id = result["meta"]["snapshot_id"]
    dump_json(result, out_dir / f"{snapshot_id}.json")
    csv_path = out_dir / f"{snapshot_id}.csv"
    cols = ["candidate_id", "snapshot_id", "candidate_source", "node_ids", "boundary_ids",
            "C_internal", "G_internal", "L_blanket", "D_local", "external_entropy",
            "directional_contrast", "structural_shell_size", "boundary_budget", "boundary_size",
            "is_pareto"]
    with open(csv_path, "w") as f:
        f.write(",".join(cols) + "\n")
        for r in result["rows"]:
            vals = []
            for c in cols:
                v = r[c]
                if isinstance(v, list):
                    v = "|".join(str(x) for x in v)
                vals.append(str(v))
            f.write(",".join(vals) + "\n")
    print(f"saved {csv_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--condition", choices=CONDITIONS, default="no_control")
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--f_E", type=float, default=1.0)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    result = run_snapshot(args.seed, args.condition, args.n, f_E=args.f_E)
    out_dir = Path(args.out) if args.out else DATA_DIR
    save_snapshot(result, out_dir)


if __name__ == "__main__":
    main()
