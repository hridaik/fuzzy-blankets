"""Stage 6.10 Part F -- clumpness as a SEPARATE morphology axis.

Deliberately independent of the thingness profile (C,G,L,D): a candidate can be
statistically thing-like and shaped like a snake, and that combination is
scientifically interesting rather than a defect. Nothing here deletes or
rejects candidates; `Q_clump` is a coordinate, and the "clear clump stratum"
is a SUBSET selected for visual/control examples, not a filter on the landscape.

Perimeter uses CARDINAL (4-neighbour) grid edges only -- never Moore
adjacency -- and the physical edge of the non-periodic lattice counts as
exterior space, so a blob pressed against the wall is not credited with a
free boundary.

    A        = |I|
    P_4(I)   = #{(i,j) : i in I, j not in I, j shares a cardinal grid edge with i}
    Q_clump  = P_min(A) / P_4(I)

`P_min(A)` is the minimum achievable cardinal perimeter of a polyomino of area
A on a square grid, i.e. the perimeter of the most compact arrangement:

    P_min(A) = 2 * ceil( 2 * sqrt(A) )

(Harary-Harborth). Q_clump is therefore 1 for a maximally compact shape and
falls towards 0 as the region becomes stringy or fragmented.
"""
from __future__ import annotations

import math

import numpy as np


def p_min(area: int) -> int:
    """Minimum cardinal perimeter of a polyomino of the given area."""
    if area <= 0:
        return 0
    return int(2 * math.ceil(2 * math.sqrt(area)))


def rowcol(idx, L):
    idx = np.asarray(idx)
    return idx % L, idx // L          # flock_sim's column-major convention


def perimeter_p4(I, L) -> int:
    """Cardinal-edge perimeter. Off-lattice neighbours count as exterior."""
    I = np.asarray(sorted(int(x) for x in I))
    if len(I) == 0:
        return 0
    inside = set(int(x) for x in I)
    r, c = rowcol(I, L)
    p = 0
    for rr, cc in zip(r, c):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = rr + dr, cc + dc
            if not (0 <= nr < L and 0 <= nc < L):
                p += 1                      # lattice edge == exterior space
            elif (nc * L + nr) not in inside:
                p += 1
    return int(p)


def q_clump(I, L) -> float:
    I = np.asarray(sorted(int(x) for x in I))
    if len(I) == 0:
        return float("nan")
    per = perimeter_p4(I, L)
    return float(p_min(len(I)) / per) if per else float("nan")


def n_components_cardinal(I, L) -> int:
    """Connected components under CARDINAL adjacency."""
    inside = set(int(x) for x in I)
    seen, ncomp = set(), 0
    for s in inside:
        if s in seen:
            continue
        ncomp += 1
        stack = [s]; seen.add(s)
        while stack:
            a = stack.pop()
            ar, ac = a % L, a // L
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = ar + dr, ac + dc
                if 0 <= nr < L and 0 <= nc < L:
                    b = nc * L + nr
                    if b in inside and b not in seen:
                        seen.add(b); stack.append(b)
    return ncomp


def morphology(I, L) -> dict:
    I = np.asarray(sorted(int(x) for x in I))
    r, c = rowcol(I, L)
    ext_r = (r.max() - r.min() + 1) if len(I) else 0
    ext_c = (c.max() - c.min() + 1) if len(I) else 0
    return dict(
        area=int(len(I)),
        perimeter_p4=perimeter_p4(I, L),
        p_min=p_min(len(I)),
        q_clump=q_clump(I, L),
        n_components=n_components_cardinal(I, L),
        bbox_fill=float(len(I) / (ext_r * ext_c)) if ext_r and ext_c else float("nan"),
        aspect_ratio=float(max(ext_r, ext_c) / max(1, min(ext_r, ext_c))),
    )
