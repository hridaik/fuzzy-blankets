"""Task brief section 33, "Geometry"."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common_66 import (  # noqa: E402
    lattice_100, is_connected, structural_shell, near_exterior, distant_exterior,
    graph_distance_from_set, K_INTERIOR, K_BOUNDARY_BUDGET,
)
from candidates import generate_candidate_landbank  # noqa: E402
from boundary_search import select_boundary  # noqa: E402
from predictive_cache import PredictiveCache  # noqa: E402


@pytest.fixture(scope="module")
def lattice():
    return lattice_100()


@pytest.fixture(scope="module")
def small_core():
    # 2x2 block of interior lattice ids, matching v3_refinement's fixture
    # convention (an easy-to-reason-about fully-8-connected core).
    return np.array([44, 45, 54, 55])


CANONICAL_I0 = np.array([7, 8, 9, 16, 17, 18, 19, 26, 27, 28, 29, 36, 37, 38, 39, 47, 48, 49, 58, 59])


def test_candidates_have_exactly_k(lattice):
    rng = np.random.default_rng(0)
    z = rng.integers(0, 4, size=100)
    cands = generate_candidate_landbank(lattice, z, z[None].repeat(5, axis=0), CANONICAL_I0,
                                         K_INTERIOR, target_total=120, rng=rng)
    assert len(cands) > 0
    for c in cands:
        assert len(c.nodes) == K_INTERIOR, (c.source, len(c.nodes))


def test_candidates_are_moore_connected(lattice):
    rng = np.random.default_rng(1)
    z = rng.integers(0, 4, size=100)
    cands = generate_candidate_landbank(lattice, z, z[None].repeat(5, axis=0), CANONICAL_I0,
                                         K_INTERIOR, target_total=120, rng=rng)
    for c in cands:
        assert is_connected(lattice, c.nodes), (c.source, sorted(c.nodes))


def test_candidates_are_unique(lattice):
    rng = np.random.default_rng(2)
    z = rng.integers(0, 4, size=100)
    cands = generate_candidate_landbank(lattice, z, z[None].repeat(5, axis=0), CANONICAL_I0,
                                         K_INTERIOR, target_total=200, rng=rng)
    keys = [c.key for c in cands]
    assert len(keys) == len(set(keys))


def test_second_ring_definition(lattice, small_core):
    dist = graph_distance_from_set(lattice, small_core, nn=100)
    E_near = near_exterior(lattice, small_core)
    assert set(E_near.tolist()) == set(np.where(dist == 2)[0].tolist())
    shell = structural_shell(lattice, small_core)
    assert set(shell.tolist()) == set(np.where(dist == 1)[0].tolist())
    # near exterior must be disjoint from the core and its one-hop shell
    assert set(E_near.tolist()).isdisjoint(set(small_core.tolist()))
    assert set(E_near.tolist()).isdisjoint(set(shell.tolist()))


def test_distant_exterior_is_everything_beyond_ring_two(lattice, small_core):
    dist = graph_distance_from_set(lattice, small_core, nn=100)
    far = distant_exterior(lattice, small_core)
    assert set(far.tolist()) == set(np.where(dist >= 3)[0].tolist())


def test_selected_boundary_subset_of_structural_shell(lattice):
    rng = np.random.default_rng(3)
    z = rng.integers(0, 4, size=100)
    prev = rng.integers(0, 4, size=(60, 100))
    nxt = rng.integers(0, 4, size=(60, 100))
    cache = PredictiveCache(lattice, prev[:40], nxt[:40], prev[40:], nxt[40:])
    for I in (CANONICAL_I0, np.arange(30, 50)):
        S = structural_shell(lattice, I)
        result = select_boundary(cache, lattice, I, K_BOUNDARY_BUDGET)
        assert set(result["B"].tolist()).issubset(set(S.tolist()))


def test_boundary_size_never_exceeds_K(lattice):
    rng = np.random.default_rng(4)
    prev = rng.integers(0, 4, size=(60, 100))
    nxt = rng.integers(0, 4, size=(60, 100))
    cache = PredictiveCache(lattice, prev[:40], nxt[:40], prev[40:], nxt[40:])
    for I in (CANONICAL_I0, np.arange(0, 20), np.arange(40, 60)):
        result = select_boundary(cache, lattice, I, K_BOUNDARY_BUDGET)
        assert result["boundary_size"] <= K_BOUNDARY_BUDGET
        assert result["boundary_size"] == min(K_BOUNDARY_BUDGET, result["structural_shell_size"])
