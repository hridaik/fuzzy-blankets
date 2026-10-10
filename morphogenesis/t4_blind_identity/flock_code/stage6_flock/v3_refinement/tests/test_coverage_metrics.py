"""Unit tests for Part 1A/1D's new structural quantities and rules, on the
real 10x10 Moore lattice (same fixture style as tests/test_lattice.py).
Run: pytest v3_refinement/tests/ -q (from stage6_flock/)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))

from flock_sim.lattice import Lattice  # noqa: E402
from common_v2 import dynamical_shell  # noqa: E402
from coverage_metrics import core_coverage, multiplicities, multiplicity_summary, concentration_metrics  # noqa: E402
from selection_rules_v3 import (  # noqa: E402
    rule_COVER_greedy, greedy_multicover_order, q_coverage_fraction, min_actuators_for_multicover,
)


@pytest.fixture
def lattice():
    return Lattice(nn=100, nh=8)


@pytest.fixture
def small_core(lattice):
    # A compact 2x2 interior block, away from any boundary, so every member
    # has a full 8-neighbor Moore neighborhood -- an easy-to-reason-about
    # fixture (rows/cols 4-5 on a 10x10 grid, 0-based).
    from flock_sim.lattice import rowcol_to_bird
    rows = np.array([4, 4, 5, 5])
    cols = np.array([4, 5, 4, 5])
    return rowcol_to_bird(rows, cols, lattice.L)


def test_core_coverage_empty_actuators_is_zero(lattice, small_core):
    assert core_coverage([], small_core, lattice) == 0.0


def test_core_coverage_full_shell_is_one(lattice, small_core):
    B_D0 = dynamical_shell(lattice, small_core)
    assert core_coverage(B_D0, small_core, lattice) == 1.0


def test_multiplicities_match_manual_count(lattice, small_core):
    B_D0 = dynamical_shell(lattice, small_core)
    # Forcing the full shell: every core bird's multiplicity should equal
    # its number of shell (non-core) neighbors.
    m = multiplicities(B_D0, small_core, lattice)
    core_set = set(small_core.tolist())
    expected = [len(set(lattice.neighbor_ids[i].tolist()) - core_set) for i in small_core.tolist()]
    assert m.tolist() == expected


def test_multiplicity_summary_monotone_in_budget(lattice, small_core):
    B_D0 = dynamical_shell(lattice, small_core)
    rng = np.random.default_rng(0)
    small_A = rng.choice(B_D0, size=2, replace=False)
    full_summary = multiplicity_summary(B_D0, small_core, lattice)
    small_summary = multiplicity_summary(small_A, small_core, lattice)
    # More actuators can only weakly increase mean multiplicity.
    assert full_summary["mean_m"] >= small_summary["mean_m"]


def test_cover_greedy_beats_or_matches_random_on_coverage(lattice, small_core):
    B_D0 = dynamical_shell(lattice, small_core)
    k = max(1, len(B_D0) // 2)
    cover_set = rule_COVER_greedy(B_D0, small_core, lattice, k)
    rng = np.random.default_rng(1)
    best_random_gamma = 0.0
    for _ in range(20):
        rand_set = rng.choice(B_D0, size=k, replace=False)
        best_random_gamma = max(best_random_gamma, core_coverage(rand_set, small_core, lattice))
    assert core_coverage(cover_set, small_core, lattice) >= best_random_gamma


def test_cover_greedy_is_deterministic(lattice, small_core):
    B_D0 = dynamical_shell(lattice, small_core)
    a = rule_COVER_greedy(B_D0, small_core, lattice, k=3)
    b = rule_COVER_greedy(B_D0, small_core, lattice, k=3)
    assert a == b


def test_concentration_patch_lower_entropy_than_full_shell(lattice, small_core):
    B_D0 = dynamical_shell(lattice, small_core)
    # A single lattice neighbor "patch": just the top-row shell members
    # (already known to be graph-connected among themselves).
    from flock_sim.lattice import bird_to_rowcol
    rows, cols = bird_to_rowcol(B_D0, lattice.L)
    patch = B_D0[rows == rows.min()]
    full_metrics = concentration_metrics(B_D0, B_D0, small_core, lattice)
    patch_metrics = concentration_metrics(patch, B_D0, small_core, lattice)
    assert full_metrics["sector_entropy"] >= patch_metrics["sector_entropy"]


def test_greedy_multicover_q1_equals_cover_greedy_order_gamma(lattice, small_core):
    B_D0 = dynamical_shell(lattice, small_core)
    order = greedy_multicover_order(B_D0, small_core, lattice, q=1)
    assert set(order) == set(B_D0.tolist())
    assert q_coverage_fraction(order, small_core, lattice, q=1) == 1.0


def test_min_actuators_for_multicover_reaches_target_or_exhausts_shell(lattice, small_core):
    B_D0 = dynamical_shell(lattice, small_core)
    A = min_actuators_for_multicover(B_D0, small_core, lattice, q=2, gamma=0.5)
    achieved = q_coverage_fraction(A, small_core, lattice, q=2)
    assert achieved >= 0.5 or set(A) == set(B_D0.tolist())
    assert len(A) <= len(B_D0)


def test_q2_requires_at_least_as_many_actuators_as_q1(lattice, small_core):
    B_D0 = dynamical_shell(lattice, small_core)
    a1 = min_actuators_for_multicover(B_D0, small_core, lattice, q=1, gamma=1.0)
    a2 = min_actuators_for_multicover(B_D0, small_core, lattice, q=2, gamma=1.0)
    assert len(a2) >= len(a1)
