"""Unit tests for Part 3.5/4/4.1/4.2 membership, boundary, and
target-heading-decomposition metrics. Run: pytest stage6_5/collective_identity/tests/ -q
(from stage6_flock/)"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from flock_sim.lattice import Lattice  # noqa: E402
from identity_metrics import (  # noqa: E402
    retention_fraction, recruit_fraction, turnover, track_membership_metrics,
    track_boundary_metrics, target_heading_decomposition, per_definition_trajectory_report,
)


def test_retention_and_recruit_fraction():
    I0 = np.array([1, 2, 3, 4])
    I_t = np.array([2, 3, 5, 6])
    assert retention_fraction(I0, I_t) == pytest.approx(2 / 4)
    assert recruit_fraction(I0, I_t) == pytest.approx(2 / 4)


def test_retention_full_when_identical():
    I0 = np.array([1, 2, 3])
    assert retention_fraction(I0, I0) == 1.0
    assert recruit_fraction(I0, I0) == 0.0


def test_turnover_symmetric_difference():
    a, b = np.array([1, 2, 3]), np.array([2, 3, 4])
    assert turnover(a, b) == 2  # {1,4} symmetric difference


def test_track_membership_metrics_shapes():
    I0 = np.array([1, 2, 3])
    track = [np.array([1, 2, 3]), np.array([1, 2, 4]), np.array([1, 4])]
    m = track_membership_metrics(I0, track)
    assert m["size"] == [3, 3, 2]
    assert m["turnover"][0] == 0
    assert m["turnover"][1] == 2  # {3} out, {4} in
    assert m["turnover"][2] == 1  # {2} out


def test_track_boundary_metrics_matches_dynamical_shell():
    from flock_sim.lattice import rowcol_to_bird
    lattice = Lattice(nn=100, nh=8)
    rows, cols = np.array([4, 4]), np.array([4, 5])
    I0 = np.sort(rowcol_to_bird(rows, cols, lattice.L))
    m = track_boundary_metrics([I0], lattice)
    assert m["size"][0] > 0
    assert m["turnover"][0] == 0


def test_target_heading_decomposition_all_recruited_and_retained():
    z = np.zeros(10, dtype=int)
    z[[1, 2]] = 3  # target heading 3
    I0 = np.array([1, 2, 3, 4])
    I_t = np.array([1, 5, 6])  # retains {1}, recruits {5,6}
    d = target_heading_decomposition(z, I0, I_t, h_star=3)
    assert d["n_retained"] == 1 and d["n_recruited"] == 2
    assert d["H_retained"] == 1.0   # bird 1 is at heading 3
    assert d["H_recruited"] == 0.0  # birds 5,6 are at heading 0


def test_identity_gaming_signal_detected():
    """If success is driven entirely by recruiting already-aligned birds
    while the retained core is NOT at the target, the decomposition must
    show that -- H_retained low, H_recruited high, H_full misleadingly OK."""
    nu_state, h_star = 0, 1
    z = np.zeros(10, dtype=int)
    z[[5, 6, 7]] = h_star  # only the recruits are aligned
    I0 = np.array([1, 2, 3])       # none of these are at h_star
    I_t = np.array([1, 5, 6, 7])   # kept 1 of 3 original, recruited 3 aligned birds
    d = target_heading_decomposition(z, I0, I_t, h_star)
    assert d["H_retained"] == 0.0
    assert d["H_recruited"] == 1.0
    assert d["H_full"] == pytest.approx(3 / 4)  # looks "mostly successful" in aggregate


def test_per_definition_trajectory_report_success_and_persistence():
    I0 = np.array([0, 1])
    I_track = [I0, I0, I0]
    h_star = 2
    z_hist = np.zeros((3, 5), dtype=int)
    z_hist[:, [0, 1]] = h_star  # always at target
    report = per_definition_trajectory_report(z_hist, I0, I_track, h_star, T_u=1, T_r=1)
    assert report["success"] is True
    assert report["persistence"] is True
    assert report["recovery_time"] == 0
