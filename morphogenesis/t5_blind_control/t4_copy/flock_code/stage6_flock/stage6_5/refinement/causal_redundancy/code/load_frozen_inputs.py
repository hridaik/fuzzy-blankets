"""EVALUATION-SIDE. Loads the already-frozen Stage 6.5 Part 1 outputs (B_hat,
B^D per held-out flock) without refitting the inference pipeline (A1's "do
not refit"), and regenerates the exact flocks/trajectories they were computed
from -- everything here is a deterministic function of a seed, so this is
reproduction, not re-derivation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))
BOUNDARY_INFERENCE_CODE = ROOT / "stage6_5" / "boundary_inference" / "code"
sys.path.insert(0, str(BOUNDARY_INFERENCE_CODE))

from common_v2 import find_flock, dynamical_shell  # noqa: E402
from trajectory_gen import generate_trajectories, make_splits, TRAJ_SEED_OFFSET  # noqa: E402

HELD_OUT_EVAL_PATH = ROOT / "stage6_5" / "boundary_inference" / "data" / "held_out_evaluation.json"
N_TRAIN, N_VAL, N_TEST = 100, 30, 30
N_TIME = 15

# Disjoint from Part 1's trajectory seed range (TRAJ_SEED_OFFSET=650_000,
# consumes 650_000..650_159 per flock) and from held-out-evaluation's split
# rng (np.random.default_rng(1_000_000 + seed)) -- this offset generates
# genuinely fresh natural continuations never used to train or validate the
# frozen inference pipeline or its predictive models.
PERTURBATION_TRAJ_SEED_OFFSET = 6_650_000
N_PERTURBATION_TRAJ = 30
CHECKPOINT_T = 7  # of n_time=15 -- mid-window, matches TRAJ_SEED_OFFSET-era trajectory length


def load_held_out_frozen(seeds: list[int]) -> dict[int, dict]:
    """Returns {seed: {B_hat, B_D, recovery_vs_BD, excess_loss}} read verbatim
    from the frozen Part 1 results file -- never recomputed."""
    data = json.load(open(HELD_OUT_EVAL_PATH))
    by_seed = {r["seed"]: r for r in data["results"]}
    out = {}
    for s in seeds:
        assert s in by_seed, f"seed {s} not found in {HELD_OUT_EVAL_PATH}"
        r = by_seed[s]
        out[s] = dict(B_hat=list(r["B_hat"]), B_D=list(r["B_D"]),
                      recovery_vs_BD=r["recovery_vs_BD"], excess_loss=r["excess_loss"])
    return out


def load_flock_with_frozen_boundary(seed: int) -> dict:
    """Reproduces the flock (lattice, I0, z_t0, h_star) exactly as Part 1 saw
    it, plus its frozen B_hat/B_D, plus the SAME train/val trajectory split
    Part 1 used (fully deterministic given seed) so a re-fit predictive model
    is byte-identical to Part 1's."""
    fl = find_flock(seed)
    assert fl is not None
    frozen = load_held_out_frozen([seed])[seed]
    B_D_true = dynamical_shell(fl["lattice"], fl["I0"])
    assert sorted(int(b) for b in B_D_true.tolist()) == sorted(frozen["B_D"]), (
        "reconstructed B^D does not match the frozen Part 1 record -- flock reconstruction drifted"
    )

    z = generate_trajectories(fl["z_t0"], fl["lattice"], n_traj=N_TRAIN + N_VAL + N_TEST, n_time=N_TIME,
                               seed_offset=TRAJ_SEED_OFFSET)
    rng = np.random.default_rng(1_000_000 + seed)
    tr, va, te = make_splits(N_TRAIN + N_VAL + N_TEST, N_TRAIN, N_VAL, N_TEST, rng)

    return dict(
        seed=seed, lattice=fl["lattice"], I0=fl["I0"], z_t0=fl["z_t0"], h0=fl["h0"], h_star=fl["h_star"],
        B_hat=frozen["B_hat"], B_D=frozen["B_D"], recovery_vs_BD=frozen["recovery_vs_BD"],
        excess_loss_natural_part1=frozen["excess_loss"],
        z_train=z[tr], z_val=z[va], z_test=z[te],
    )


def generate_perturbation_checkpoints(fl: dict, n_traj: int = N_PERTURBATION_TRAJ,
                                       checkpoint_t: int = CHECKPOINT_T) -> np.ndarray:
    """Fresh held-out X_t states: n_traj independent natural continuations
    from z_t0, using a seed offset disjoint from every Part-1 trajectory
    generation, read off at a fixed mid-window checkpoint. Returns (n_traj, n_bird)."""
    z = generate_trajectories(fl["z_t0"], fl["lattice"], n_traj=n_traj, n_time=N_TIME,
                               seed_offset=PERTURBATION_TRAJ_SEED_OFFSET)
    return z[:, checkpoint_t, :]


def exterior_classes(fl: dict, n_bird: int = 100, e_sample_size: int = 10,
                      e_sample_seed: int = 64_000) -> dict:
    """Partitions the true exterior into the three A3 classes for one flock:
    B_hat (included true-shell states), B^D \\ B_hat (omitted true-shell
    states), and a fixed random sample of E^D (true non-shell exterior,
    negative control)."""
    I0 = set(int(i) for i in fl["I0"].tolist())
    B_hat = set(int(b) for b in fl["B_hat"])
    B_D = set(int(b) for b in fl["B_D"])
    assert B_hat <= B_D, "frozen B_hat is not a subset of frozen B^D -- Part 1 invariant violated"
    E_D = [j for j in range(n_bird) if j not in I0 and j not in B_D]

    rng = np.random.default_rng(e_sample_seed + fl["seed"])
    e_sample = sorted(int(j) for j in rng.choice(E_D, size=min(e_sample_size, len(E_D)), replace=False))

    return dict(
        included_shell=sorted(B_hat),
        omitted_shell=sorted(B_D - B_hat),
        non_shell_sample=e_sample,
        n_non_shell_total=len(E_D),
    )
