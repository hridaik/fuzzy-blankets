"""Lattice / neighbor structure, ported from upstream buildW (flocking_AIF_simulation.m).

Upstream uses 1-based, column-major bird indexing on an L x L grid (L = sqrt(nn)),
free (non-periodic) boundary conditions, Moore (8-)neighborhood. See
METHODS_AUDIT.md section 1 for the full derivation. This module reproduces the
neighbor sets exactly (validated in tests/test_lattice.py against hand-worked
1-based MATLAB arithmetic) and exposes them as 0-based numpy arrays.

Neighbor slot order (matches buildW's nh=1..8 and compAexceps's case order):
    slot 0 "top"       : i-1   (one row up,    same column)
    slot 1 "down"      : i+1   (one row down,  same column)
    slot 2 "left"      : i-L   (same row,      one column left)
    slot 3 "right"     : i+L   (same row,      one column right)
    slot 4 "topleft"   : i-L-1
    slot 5 "downright" : i+L+1
    slot 6 "downleft"  : i-L+1
    slot 7 "topright"  : i+L-1
(all still expressed in 1-based MATLAB linear-index arithmetic before conversion)
"""
from __future__ import annotations

import numpy as np


def grid_side(nn: int) -> int:
    L = int(round(nn ** 0.5))
    if L * L != nn:
        raise ValueError(f"nn={nn} is not a perfect square; upstream assumes L=sqrt(nn)")
    return L


def bird_to_rowcol(idx0: np.ndarray, L: int) -> tuple[np.ndarray, np.ndarray]:
    """0-based bird index -> (row, col), 0-based, column-major (Fortran order),
    matching MATLAB's ind2sub([L,L], i) used throughout the upstream plotting code."""
    idx0 = np.asarray(idx0)
    row = idx0 % L
    col = idx0 // L
    return row, col


def rowcol_to_bird(row: np.ndarray, col: np.ndarray, L: int) -> np.ndarray:
    return col * L + row


def neighbor_slots_1based(nn: int, nh: int = 8) -> list[list[int | None]]:
    """Literal translation of buildW: for each bird i (1-based), return the up to
    8 neighbor indices (1-based) in slot order, or None if that slot is absent at
    the boundary (buildW simply leaves the corresponding W(...)=0, i.e. no edge)."""
    L = grid_side(nn)
    out: list[list[int | None]] = []
    for i in range(1, nn + 1):
        slots: list[int | None] = [None] * 8
        if nh > 0 and (i % L) != 1:
            slots[0] = i - 1
        if nh > 1 and (i % L) != 0:
            slots[1] = i + 1
        if nh > 2 and i > L:
            slots[2] = i - L
        if nh > 3 and i <= (nn - L):
            slots[3] = i + L
        if nh > 4 and (i % L) != 1 and i > L:
            slots[4] = i - L - 1
        if nh > 5 and (i % L) != 0 and i <= (nn - L):
            slots[5] = i + L + 1
        if nh > 6 and (i % L) != 0 and i > L:
            slots[6] = i - L + 1
        if nh > 7 and (i % L) != 1 and i <= (nn - L):
            slots[7] = i + L - 1
        out.append(slots)
    return out


class Lattice:
    """0-based neighbor structure for nn birds on an L x L free-boundary grid."""

    def __init__(self, nn: int = 100, nh: int = 8):
        self.nn = nn
        self.nh = nh
        self.L = grid_side(nn)
        slots_1based = neighbor_slots_1based(nn, nh)
        # neighbor_ids[i] = 0-based array of this bird's neighbor indices (variable length)
        # neighbor_slot[i] = which of the 8 canonical slots each neighbor occupies (0-based slot id)
        self.neighbor_ids: list[np.ndarray] = []
        self.neighbor_slot: list[np.ndarray] = []
        for slots in slots_1based:
            ids = [s - 1 for s in slots if s is not None]
            slot_idx = [k for k, s in enumerate(slots) if s is not None]
            self.neighbor_ids.append(np.array(ids, dtype=int))
            self.neighbor_slot.append(np.array(slot_idx, dtype=int))
        self.degree = np.array([len(v) for v in self.neighbor_ids])
