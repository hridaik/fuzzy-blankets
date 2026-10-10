"""A^3's negative control, proved exactly rather than only observed
empirically: perturbing a bird that is not a lattice-neighbour of any
interior bird cannot change the interior's one-step distribution, because
`compute_G`'s per-bird sum only touches that bird's own neighbours' headings.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from flock_sim.lattice import Lattice  # noqa: E402
from flock_sim.model import ModelParams  # noqa: E402
from exact_intervention import (  # noqa: E402
    default_precomputed_model, next_heading_dist_all, do_next_heading_dist_all,
    interior_do_kl,
)


def _setup():
    lattice = Lattice(nn=100, nh=8)
    pm = default_precomputed_model(ModelParams())
    rng = np.random.default_rng(0)
    z = rng.integers(0, 4, size=100)
    # a small interior block away from the grid edges (10x10 lattice, L=10)
    I0 = np.array([44, 45, 54, 55])
    return lattice, pm, z, I0


def _true_shell(lattice, I0):
    nbrs = set()
    for i in I0.tolist():
        nbrs.update(lattice.neighbor_ids[i].tolist())
    nbrs -= set(I0.tolist())
    return nbrs


def test_non_neighbor_perturbation_is_exactly_inert():
    lattice, pm, z, I0 = _setup()
    B_D = _true_shell(lattice, I0)
    non_shell = [j for j in range(100) if j not in set(I0.tolist()) and j not in B_D]
    assert len(non_shell) > 0

    natural = next_heading_dist_all(pm, lattice, z)[I0]
    for j in non_shell[:15]:
        for z_prime in range(4):
            if z_prime == z[j]:
                continue
            do_dist = do_next_heading_dist_all(pm, lattice, z, j, z_prime)[I0]
            # exact identity, not "close" -- see module docstring point 3
            np.testing.assert_array_equal(do_dist, natural)
            result = interior_do_kl(pm, lattice, z, I0, j, z_prime)
            assert result["D_do_joint"] == 0.0
            assert result["n_neighboring_interior"] == 0


def test_shell_perturbation_is_generically_not_inert():
    lattice, pm, z, I0 = _setup()
    B_D = sorted(_true_shell(lattice, I0))
    assert len(B_D) > 0
    found_nonzero = False
    for j in B_D:
        for z_prime in range(4):
            if z_prime == z[j]:
                continue
            result = interior_do_kl(pm, lattice, z, I0, j, z_prime)
            assert result["n_neighboring_interior"] >= 1
            if result["D_do_joint"] > 1e-9:
                found_nonzero = True
    assert found_nonzero, "expected at least one true-shell perturbation to have a measurable effect"
