"""Synthetic larger templates for E6 scaling tests (24, 32 cells).

Construction rule (declared, since these are NOT from any published source):
place cells on the same integer grid logic as T_L2/T_L4 (row, col positions
on a small 2D lattice), assign a cell-type code in {1,2,3,4} by
`((row+col) mod 4) + 1`, i.e. a deterministic checkerboard-like cycle over
the same code alphabet used by the published templates. This keeps the same
downstream decode_template() machinery (p(:,:,i) masks, morphogenesis field)
unchanged, and is used ONLY for E6 runtime/assembly-success scaling checks,
never for any claim about biologically meaningful morphology.
"""
import numpy as np


def synthetic_template(n_cells: int) -> np.ndarray:
    side = int(np.ceil(np.sqrt(n_cells * 2)))  # sparse-ish grid, like published templates
    coords = [(r, c) for r in range(side) for c in range(side)]
    rng = np.random.default_rng(12345 + n_cells)
    rng.shuffle(coords)
    chosen = coords[:n_cells]
    T = np.zeros((side, side))
    for (r, c) in chosen:
        code = ((r + c) % 4) + 1
        T[r, c] = code
    return T
