"""Two structurally different candidate-proposal mechanisms, per
IDENTITY_MODEL.md §1C.2 / §5's requirement that a single detector's own
systematic error (e.g. Louvain's node-order-dependent local optimum,
CLAIMS_LEDGER.md item D1) not silently become the only source of "what is
a candidate" for every downstream number.

1. `louvain_propose` -- reuses Stage 6.9's `detect_69.propose` unchanged.
2. `field_propose` -- a position/heading density-grid connected-components
   detector, independent of Louvain's graph-partition machinery entirely.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_STAGE69 = Path(__file__).resolve().parents[3] / "stage6_9_translating_collective" / "code"
_STAGE68 = Path(__file__).resolve().parents[3] / "stage6_8_dynamic_interactions" / "code"
for p in (_STAGE69, _STAGE68):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import detect_69  # noqa: E402

MIN_SIZE_FRAC = 0.03
MAX_SIZE_FRAC = 0.55
GRID_CELL = 1.5


def torus_wrap(x, L):
    return np.mod(x, L)


def louvain_propose(r, z_window, L):
    return detect_69.propose(r, z_window, L)


def field_propose(r, L, cell=GRID_CELL):
    """Coarse density-grid connected components: bins birds into a torus
    grid, thresholds cells above the mean count, 4-connects thresholded
    cells (torus-wrapped), returns each component's member bird ids."""
    N = r.shape[0]
    n_cells = max(int(round(L / cell)), 3)
    idx = np.floor(torus_wrap(r, L) / L * n_cells).astype(int) % n_cells
    grid_members = {}
    counts = np.zeros((n_cells, n_cells))
    for i in range(N):
        key = (idx[i, 0], idx[i, 1])
        grid_members.setdefault(key, []).append(i)
        counts[key] += 1
    thresh = max(counts.mean() * 1.3, 1.0)
    active = counts >= thresh
    seen = np.zeros((n_cells, n_cells), dtype=bool)
    out = []
    for a in range(n_cells):
        for b in range(n_cells):
            if not active[a, b] or seen[a, b]:
                continue
            stack = [(a, b)]
            seen[a, b] = True
            comp_cells = []
            while stack:
                x, y = stack.pop()
                comp_cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = (x + dx) % n_cells, (y + dy) % n_cells
                    if active[nx, ny] and not seen[nx, ny]:
                        seen[nx, ny] = True
                        stack.append((nx, ny))
            members = []
            for cell_xy in comp_cells:
                members.extend(grid_members.get(cell_xy, []))
            if MIN_SIZE_FRAC * N <= len(members) <= MAX_SIZE_FRAC * N:
                out.append(np.array(sorted(members)))
    out.sort(key=len, reverse=True)
    return out


def propose_both(r, z, z_window, L):
    """Returns the combined raw candidate list from both mechanisms
    (deduplication/coalescing happens downstream, in the tracker, per
    §5/§9(5) -- this function does NOT dedupe, so duplicate-invariance
    checks can exercise the tracker's own coalescing logic honestly)."""
    return louvain_propose(r, z_window, L) + field_propose(r, L)
