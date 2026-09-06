"""Integrity / task metrics (Phase 2C) and the true Potts Hamiltonian (Eq. 1),
kept separate from the upstream `compHamiltonian` bookkeeping quantity of the
same name (which is a different diagnostic — see METHODS_AUDIT.md section 11)."""
from __future__ import annotations

import numpy as np

from .lattice import Lattice


def target_heading_fraction(z: np.ndarray, core: np.ndarray, h_star: int) -> float:
    if len(core) == 0:
        return float("nan")
    return float(np.mean(z[core] == h_star))


def coherence(z: np.ndarray, core: np.ndarray) -> float:
    if len(core) == 0:
        return float("nan")
    counts = np.bincount(z[core], minlength=int(z.max()) + 1)
    return float(counts.max() / len(core))


def lineage_retention(core0: np.ndarray, current_interior: np.ndarray) -> float:
    if len(core0) == 0:
        return float("nan")
    return float(len(np.intersect1d(core0, current_interior)) / len(core0))


def potts_energy(z: np.ndarray, lattice: Lattice, J_P: float = 1.0) -> float:
    """Eq. 1: H = J_P * sum_{(i,j) in M} delta(z_i, z_j), summed once per
    unordered neighbor pair (each pair counted once, matching a Hamiltonian over
    the M nearest-neighbor bonds, not double-counted i->j and j->i)."""
    total = 0.0
    for i, nbrs in enumerate(lattice.neighbor_ids):
        for j in nbrs:
            if j > i:
                total += float(z[i] == z[j])
    return J_P * total


def modal_heading(z: np.ndarray, nu: int) -> int:
    counts = np.bincount(z, minlength=nu)
    return int(np.argmax(counts))


_UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])


def polarization(z: np.ndarray) -> float:
    """Port of measurePhi (flocking_AIF_simulation.m): mean unit heading vector
    norm, in [0,1]. 1 = perfect global alignment, ~0 = disordered."""
    vecs = _UV4[z]
    mean_vec = vecs.mean(axis=0)
    return float(np.linalg.norm(mean_vec))
