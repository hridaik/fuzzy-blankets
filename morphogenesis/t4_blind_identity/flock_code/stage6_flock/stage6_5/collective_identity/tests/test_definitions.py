"""Unit tests for the three identity-tracking definitions (Part 3).
Run: pytest stage6_5/collective_identity/tests/ -q (from stage6_flock/)"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from flock_sim.lattice import Lattice  # noqa: E402
from definitions import (  # noqa: E402
    material_track, lineage_track, functional_track, jaccard, MIN_SELF_COHERENCE,
)


def test_jaccard_basic():
    assert jaccard([1, 2, 3], [1, 2, 3]) == 1.0
    assert jaccard([1, 2], [3, 4]) == 0.0
    assert jaccard([], []) == 1.0
    assert jaccard([1, 2, 3], [2, 3, 4]) == pytest.approx(2 / 4)


def test_material_track_is_constant():
    I0 = np.array([1, 2, 3])
    track = material_track(I0, n_steps=5)
    assert len(track) == 5
    for I_t in track:
        assert np.array_equal(I_t, np.array([1, 2, 3]))
    # mutating one element must not alias into I0
    track[0][0] = 99
    assert I0[0] == 1


@pytest.fixture
def lattice():
    return Lattice(nn=100, nh=8)


def test_functional_track_recovers_perfectly_coherent_connected_block(lattice):
    """If a spatially-connected block of birds holds one heading throughout,
    and nothing else does, I^F should identify exactly that block. The
    block's full Moore-neighbor ring is pinned to a DIFFERENT heading
    (deterministically, not randomly) so a connected path can never leak
    into the block by chance -- otherwise, with a short TW=5 window, some
    fraction of 96 iid-random exterior birds will pass the >=60%
    self-coherence bar purely by chance and could accidentally chain onto
    the block, which is a real (and separately worth noting) property of
    short-window functional identity, not what this test is checking."""
    from flock_sim.lattice import rowcol_to_bird
    rows = np.array([4, 4, 5, 5])
    cols = np.array([4, 5, 4, 5])
    I0 = np.sort(rowcol_to_bird(rows, cols, lattice.L))
    ring = sorted(set(int(j) for i in I0.tolist() for j in lattice.neighbor_ids[i].tolist()) - set(I0.tolist()))

    n_time = 8
    z_hist = np.random.default_rng(0).integers(0, 4, size=(n_time + 1, 100))
    z_hist[:, I0] = 0    # the block holds heading 0 throughout
    z_hist[:, ring] = 1  # its entire boundary ring deterministically holds a DIFFERENT heading

    track = functional_track(z_hist, I0, t_start=0, t_end=n_time - 1, lattice=lattice)
    assert len(track) == n_time
    # after the window fills (t >= TW-1), the block should be exactly recovered
    assert np.array_equal(track[-1], np.sort(I0))


def test_lineage_track_length_and_start():
    from flock_sim.lattice import rowcol_to_bird
    rows = np.array([4, 4, 5, 5])
    cols = np.array([4, 5, 4, 5])
    I0 = np.sort(rowcol_to_bird(rows, cols, Lattice(nn=100).L))
    n_time = 6
    z_hist = np.random.default_rng(1).integers(0, 4, size=(n_time + 1, 100))
    track = lineage_track(z_hist, I0, t_start=0, t_end=n_time - 1)
    assert len(track) == n_time
    assert np.array_equal(track[0], np.sort(I0))


def test_functional_track_is_causal_not_lookahead(lattice):
    """Perturbing z_hist strictly AFTER time t must not change I_t^F -- the
    definition must be a function of the trailing window ending at t only."""
    from flock_sim.lattice import rowcol_to_bird
    rows = np.array([4, 4, 5, 5])
    cols = np.array([4, 5, 4, 5])
    I0 = np.sort(rowcol_to_bird(rows, cols, lattice.L))
    n_time = 10
    rng = np.random.default_rng(2)
    z_hist = rng.integers(0, 4, size=(n_time + 1, 100))
    z_hist[:, I0] = 0

    t_check = 5
    track_a = functional_track(z_hist, I0, t_start=0, t_end=t_check, lattice=lattice)

    z_hist_b = z_hist.copy()
    z_hist_b[t_check + 1:] = rng.integers(0, 4, size=z_hist_b[t_check + 1:].shape)
    track_b = functional_track(z_hist_b, I0, t_start=0, t_end=t_check, lattice=lattice)

    assert np.array_equal(track_a[t_check], track_b[t_check])
