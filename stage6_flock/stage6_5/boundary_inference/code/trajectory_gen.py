"""EVALUATION-SIDE. Generates observational trajectories by running the real
simulator, and exposes the true structural quantities (B^D, the lattice)
needed to freeze the dev/held-out flock pools and to evaluate \\hat B once it
is frozen. This module is deliberately NOT part of the inference-side import
graph checked by tests/test_no_lattice_leakage.py -- it is the boundary
between "generate/evaluate with full knowledge" and "infer with none", and
every driver script must pass only the plain z[traj,time,bird] arrays (never
this module's Lattice objects) into boundary_inference.code.api.infer_boundary.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))

from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.lattice import Lattice  # noqa: E402
from common_v2 import find_flock, dynamical_shell  # noqa: E402
from common_v3 import load_dev_flocks, find_held_out_flocks, V3_DIR  # noqa: E402

TRAJ_SEED_OFFSET = 650_000  # distinct from v1(100k)/phase6(200k)/v2(300k,400k)/v3(900k+500k)


def generate_trajectories(z_t0: np.ndarray, lattice: Lattice, n_traj: int, n_time: int,
                           seed_offset: int = TRAJ_SEED_OFFSET) -> np.ndarray:
    """Pure baseline continuation (no actuation) from a flock's frozen z_t0:
    n_traj independent stochastic replicates of length n_time, sharing the
    same initial condition but different transition noise. Returns
    z[trajectory, time, bird], time axis length n_time+1 (index 0 = z_t0).
    This is the observational data an outside observer of the flock would
    have: repeated, unforced continuations from (approximately) the same
    starting configuration."""
    nn = lattice.nn
    z = np.zeros((n_traj, n_time + 1, nn), dtype=int)
    for r in range(n_traj):
        res = run_simulation(nn=nn, nt=n_time, seed=seed_offset + r, init_z=z_t0, lattice=lattice)
        z[r] = res.z_hist
    return z


def make_splits(n_traj: int, n_train: int, n_val: int, n_test: int, rng: np.random.Generator):
    """Trajectory-level split: returns (train_idx, val_idx, test_idx),
    disjoint, drawn without replacement from range(n_traj). Never splits by
    timestep -- Part 1.2/1.9's requirement."""
    assert n_train + n_val + n_test <= n_traj, "not enough trajectories for the requested split"
    perm = rng.permutation(n_traj)
    train_idx = perm[:n_train]
    val_idx = perm[n_train:n_train + n_val]
    test_idx = perm[n_train + n_val:n_train + n_val + n_test]
    return train_idx, val_idx, test_idx
