"""Section 8/24 of the task brief: optional Pareto-nondominance filter across
(C, G, -L, D) (maximize all four). Cheap, off-by-default visualization/
filter only -- never used to drive candidate generation or scientific
conclusions."""
from __future__ import annotations

import numpy as np


def pareto_nondominated(C: np.ndarray, G: np.ndarray, L: np.ndarray, D: np.ndarray) -> np.ndarray:
    """Returns a bool array, True where the candidate is not dominated by any
    other candidate on (C, G, -L, D) (all maximized)."""
    M = np.stack([C, G, -L, D], axis=1)
    n = M.shape[0]
    is_pareto = np.ones(n, dtype=bool)
    for i in range(n):
        ge = np.all(M >= M[i], axis=1)
        gt = np.any(M > M[i], axis=1)
        dominates_i = ge & gt
        dominates_i[i] = False
        if dominates_i.any():
            is_pareto[i] = False
    return is_pareto
