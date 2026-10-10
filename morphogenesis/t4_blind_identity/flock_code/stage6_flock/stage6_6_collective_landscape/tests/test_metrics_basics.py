"""Task brief section 33, "Metric basics"."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from metrics_66 import (  # noqa: E402
    coherence_C, jensen_shannon_divergence, local_contrast_D,
    external_entropy_H, directional_opposition,
)


def test_coherence_full_agreement_is_one():
    z = np.zeros(100, dtype=int)
    I = np.arange(20)
    assert coherence_C(z, I) == pytest.approx(1.0)


def test_coherence_partial_agreement():
    z = np.zeros(100, dtype=int)
    I = np.arange(20)
    z[I[:15]] = 2   # 15/20 share heading 2, remaining 5 stay at 0
    assert coherence_C(z, I) == pytest.approx(15 / 20)


def test_contrast_zero_when_identical_distributions():
    z = np.zeros(100, dtype=int)
    I = np.arange(20)
    z[I] = 1
    E = np.arange(20, 40)
    z[E] = 1
    assert local_contrast_D(z, I, E) == pytest.approx(0.0, abs=1e-12)


def test_contrast_bounded_0_1():
    rng = np.random.default_rng(0)
    for _ in range(50):
        z = rng.integers(0, 4, size=100)
        I = np.arange(20)
        E = np.arange(20, 40)
        d = local_contrast_D(z, I, E)
        assert -1e-9 <= d <= 1.0 + 1e-9


def test_contrast_maximal_for_disjoint_supports():
    z = np.zeros(100, dtype=int)
    I = np.arange(20)
    z[I] = 0
    E = np.arange(20, 40)
    z[E] = 1   # disjoint one-hot supports -> maximal JSD
    d = local_contrast_D(z, I, E)
    assert d == pytest.approx(1.0, abs=1e-9)


def test_jsd_symmetric_and_nonnegative():
    rng = np.random.default_rng(1)
    for _ in range(20):
        p = rng.dirichlet(np.ones(4))
        q = rng.dirichlet(np.ones(4))
        a = jensen_shannon_divergence(p, q)
        b = jensen_shannon_divergence(q, p)
        assert a == pytest.approx(b, abs=1e-10)
        assert a >= -1e-12
        assert a <= np.log(2.0) + 1e-9


def test_external_entropy_near_one_for_balanced_assignment():
    z = np.zeros(100, dtype=int)
    E = np.arange(20, 40)   # 20 nodes, 5 per heading
    z[E[0:5]] = 0
    z[E[5:10]] = 1
    z[E[10:15]] = 2
    z[E[15:20]] = 3
    h = external_entropy_H(z, E)
    assert h == pytest.approx(1.0, abs=1e-9)


def test_external_entropy_zero_for_uniform_single_heading():
    z = np.zeros(100, dtype=int)
    E = np.arange(20, 40)
    z[E] = 2
    h = external_entropy_H(z, E)
    assert h == pytest.approx(0.0, abs=1e-9)


def test_directional_opposition_aligned_vs_opposite():
    z = np.zeros(100, dtype=int)
    I = np.arange(20)
    E = np.arange(20, 40)
    z[I] = 0   # up
    z[E] = 0   # up: fully aligned
    d_aligned = directional_opposition(z, I, E)
    assert d_aligned["opposition"] == pytest.approx(0.0, abs=1e-9)
    assert d_aligned["cosine_similarity"] == pytest.approx(1.0, abs=1e-9)

    z[E] = 1   # down: fully opposite of up
    d_opp = directional_opposition(z, I, E)
    assert d_opp["opposition"] == pytest.approx(1.0, abs=1e-9)
    assert d_opp["cosine_similarity"] == pytest.approx(-1.0, abs=1e-9)
