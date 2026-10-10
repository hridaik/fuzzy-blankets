import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from flock_sim.lattice import Lattice, neighbor_slots_1based, bird_to_rowcol, rowcol_to_bird


def test_corner_bird_has_3_neighbors():
    # nn=100 grid (10x10). Bird 1 (1-based, top-left by MATLAB column-major
    # convention: row=1,col=1) should have exactly 3 Moore neighbors: down (2),
    # right (11), down-right (12). Hand-derived from buildW's guards.
    slots = neighbor_slots_1based(100, nh=8)[0]  # bird i=1 (0-indexed list -> 1-based bird 1)
    present = [s for s in slots if s is not None]
    assert sorted(present) == [2, 11, 12], present


def test_center_bird_has_8_neighbors():
    lat = Lattice(nn=100, nh=8)
    # bird at row=5,col=5 (0-based) -> 1-based row=6,col=6 -> linear (1-based) = (6-1)*10+6=56
    i0 = rowcol_to_bird(np.array([5]), np.array([5]), 10)[0]
    assert lat.degree[i0] == 8


def test_edge_bird_has_5_neighbors():
    lat = Lattice(nn=100, nh=8)
    # top row, interior column: row=0, col=5 (0-based) -> 1-based (1,6) -> linear=(6-1)*10+1=51
    i0 = rowcol_to_bird(np.array([0]), np.array([5]), 10)[0]
    assert lat.degree[i0] == 5


def test_total_edges_matches_free_boundary_grid_formula():
    # For an LxL grid with free boundary and 8-neighborhood (Moore), total
    # undirected edges = horizontal + vertical + 2*diagonal types
    # = 2*L*(L-1) [4-neighborhood] + 2*(L-1)*(L-1) [two diagonal directions]
    L = 10
    lat = Lattice(nn=100, nh=8)
    total_directed = sum(len(v) for v in lat.neighbor_ids)
    expected_undirected = 2 * L * (L - 1) + 2 * (L - 1) * (L - 1)
    assert total_directed == 2 * expected_undirected


def test_neighbor_relation_is_symmetric():
    lat = Lattice(nn=100, nh=8)
    for i, nbrs in enumerate(lat.neighbor_ids):
        for j in nbrs:
            assert i in lat.neighbor_ids[j], (i, j)


def test_rowcol_roundtrip_column_major():
    L = 10
    idx = np.arange(100)
    row, col = bird_to_rowcol(idx, L)
    back = rowcol_to_bird(row, col, L)
    assert np.array_equal(back, idx)
