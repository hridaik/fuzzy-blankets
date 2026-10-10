"""Unit tests for multicover_select on a small hand-built incidence graph
(Part 2.2) -- pure graph logic, no simulation, so this is fast and exact.
Run: pytest stage6_5/boundary_inference/tests/ -q (from stage6_flock/)"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from control_compare import multicover_select  # noqa: E402


def test_multicover_q1_plain_set_cover():
    # I0 = {0,1,2}; pool = {10,11,12}; 10 covers {0,1}; 11 covers {1,2}; 12 covers {0,2}
    I0 = [0, 1, 2]
    G = {0: {10, 12}, 1: {10, 11}, 2: {11, 12}}
    A = multicover_select([10, 11, 12], I0, G, q=1, gamma=1.0)
    covered = set()
    for b in A:
        for i in I0:
            if b in G[i]:
                covered.add(i)
    assert covered == set(I0)
    assert len(A) <= 2  # any 2 of the 3 pool members achieve full q=1 coverage here


def test_multicover_q2_needs_more_actuators_than_q1():
    I0 = [0, 1, 2]
    G = {0: {10, 11, 12}, 1: {10, 11, 12}, 2: {10, 11, 12}}  # every pool member covers everyone
    A1 = multicover_select([10, 11, 12], I0, G, q=1, gamma=1.0)
    A2 = multicover_select([10, 11, 12], I0, G, q=2, gamma=1.0)
    assert len(A1) <= len(A2)
    assert len(A2) == 2  # need exactly 2 of the 3 to give everyone >=2 covering actuators


def test_multicover_unreachable_gamma_returns_full_pool():
    # bird 2 has NO incoming edge from the pool at all -- gamma=1.0 (full q=1
    # coverage) is structurally unreachable; function must return the full
    # pool rather than raising or infinite-looping.
    I0 = [0, 1, 2]
    G = {0: {10}, 1: {10}, 2: set()}
    A = multicover_select([10, 11], I0, G, q=1, gamma=1.0)
    assert set(A) == {10, 11}


def test_multicover_empty_pool():
    I0 = [0, 1]
    G = {0: set(), 1: set()}
    A = multicover_select([], I0, G, q=1, gamma=0.5)
    assert A == []
