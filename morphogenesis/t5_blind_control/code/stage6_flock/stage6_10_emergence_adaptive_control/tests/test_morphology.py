"""Part F validation: Q_clump must order the four reference shapes as stated,
and must not use Moore adjacency."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE))
from morphology import q_clump, perimeter_p4, p_min, morphology, n_components_cardinal

L = 20
def idx(r, c): return c * L + r


def blob(n=5, r0=6, c0=6):        # compact square
    return [idx(r0+i, c0+j) for i in range(n) for j in range(n)]

def strip(rows=2, cols=12, r0=6, c0=4):   # elongated rectangle
    return [idx(r0+i, c0+j) for i in range(rows) for j in range(cols)]

def snake(n=25, r0=4, c0=4):      # diagonal Moore-connected chain
    return [idx(r0+i, c0+i) for i in range(n)]

def fragmented(k=5, m=5):         # k scattered small clusters
    out = []
    for b in range(k):
        r0, c0 = 2 + 4*b, 2 + 3*(b % 3)
        out += [idx(r0+i%2, c0+i//2) for i in range(m)]
    return sorted(set(out))


def test_pmin_formula():
    assert p_min(1) == 4 and p_min(4) == 8 and p_min(9) == 12 and p_min(16) == 16


def test_ordering_blob_strip_snake_fragmented():
    qb, qs = q_clump(blob(), L), q_clump(strip(), L)
    qn, qf = q_clump(snake(), L), q_clump(fragmented(), L)
    assert qb > qs > qn, f"expected blob > strip > snake, got {qb:.3f} {qs:.3f} {qn:.3f}"
    assert qf < qs, f"fragmented ({qf:.3f}) should not beat an elongated strip ({qs:.3f})"
    assert qb > 0.85, f"a compact square should be near 1, got {qb:.3f}"
    assert qn < 0.3, f"a diagonal snake should be low, got {qn:.3f}"


def test_perimeter_uses_cardinal_not_moore_adjacency():
    """A diagonal chain is Moore-CONNECTED but cardinally disconnected: every
    cell contributes all four of its edges. Under Moore adjacency the perimeter
    would be much smaller, so this pins the definition."""
    s = snake(10)
    assert perimeter_p4(s, L) == 4 * len(s)
    assert n_components_cardinal(s, L) == len(s)


def test_lattice_edge_counts_as_exterior():
    """A block in the corner must not be credited with a free boundary."""
    corner = [idx(r, c) for r in range(3) for c in range(3)]
    middle = [idx(r, c) for r in range(8, 11) for c in range(8, 11)]
    assert perimeter_p4(corner, L) == perimeter_p4(middle, L) == 12


def test_single_cell_and_empty():
    assert q_clump([idx(5,5)], L) == 1.0
    assert perimeter_p4([], L) == 0


def test_morphology_reports_components_and_fill():
    m = morphology(fragmented(), L)
    assert m["n_components"] > 1
    assert 0 < m["bbox_fill"] < 1
    m2 = morphology(blob(), L)
    assert m2["n_components"] == 1 and m2["bbox_fill"] == 1.0


# ------------------------------------------------- Part E percentile ranks --
def test_ranks_are_taken_against_comparable_candidates_only():
    """A rank must not be a proxy for size.

    Two clusters of different size, each with its own G scale. If ranks were
    taken over the whole landscape, every large-cluster candidate would
    out-rank every small one regardless of how thing-like it is.
    """
    import thingness as th
    small = [dict(size=20, n_components=1, C=0.5, G=0.01 * i, L=0.0, D=0.2)
             for i in range(1, 6)]
    large = [dict(size=80, n_components=1, C=0.5, G=1.0 + 0.01 * i, L=0.0, D=0.2)
             for i in range(1, 6)]
    cands = small + large
    th.add_percentile_ranks(cands)
    # the weakest large candidate has a far higher raw G than the strongest
    # small one, yet both sit low within their own comparable set
    assert large[0]["G"] > small[-1]["G"]
    assert large[0]["rank_G"] < 0.5 and small[-1]["rank_G"] > 0.5
    # comparable sets did not mix the two sizes
    assert all(c["n_comparable"] == 5 for c in cands)


def test_ranks_respect_component_count():
    import thingness as th
    cands = [dict(size=40, n_components=1, C=0.9, G=0.1, L=0.0, D=0.3),
             dict(size=40, n_components=2, C=0.1, G=0.1, L=0.0, D=0.3)]
    th.add_percentile_ranks(cands)
    # each is alone in its comparable set -> no peers -> nan, not a false 1.0
    assert all(c["n_comparable"] == 1 for c in cands)
    assert cands[0]["rank_C"] != cands[0]["rank_C"]        # nan
