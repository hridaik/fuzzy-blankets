"""Task brief section 33, "Predictive metrics"."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common_66 import lattice_100, K_BOUNDARY_BUDGET  # noqa: E402
from predictive_cache import PredictiveCache, G_and_L  # noqa: E402
from boundary_search import select_boundary  # noqa: E402

CANONICAL_I0 = np.array([7, 8, 9, 16, 17, 18, 19, 26, 27, 28, 29, 36, 37, 38, 39, 47, 48, 49, 58, 59])
SMALL_CORE = np.array([44, 45, 54, 55])   # away from any lattice edge


@pytest.fixture(scope="module")
def lattice():
    return lattice_100()


@pytest.fixture(scope="module")
def synthetic_data():
    """Deterministic synthetic heading trajectories (not a real simulator
    rollout) -- fine for testing the mask-subset/cache MACHINERY, which does
    not care where prev/next came from."""
    rng = np.random.default_rng(42)
    prev = rng.integers(0, 4, size=(400, 100))
    nxt = rng.integers(0, 4, size=(400, 100))
    return prev[:280], nxt[:280], prev[280:], nxt[280:]


def test_mask_ordering_subset_chain(lattice, synthetic_data):
    train_prev, train_next, val_prev, val_next = synthetic_data
    cache = PredictiveCache(lattice, train_prev, train_next, val_prev, val_next)
    I = CANONICAL_I0
    B = np.array([5, 6, 15, 25, 35, 45, 46, 56, 57, 67, 68, 69])  # canonical B^D_0
    for i in I[:6]:
        mB = cache.mask_B(int(i), B)
        mIB = cache.mask_IB(int(i), I, B)
        mFull = cache.mask_full(int(i))
        assert mB.issubset(mIB)
        assert mIB.issubset(mFull)


def test_full_neighbour_model_is_reference(lattice, synthetic_data):
    """L_i = ell_i(mask_IB) - ell_i(mask_full): mask_full is always the
    complete neighbour set, regardless of I/B, so L_i measures excess loss
    relative to using literally everything the model structure allows."""
    train_prev, train_next, val_prev, val_next = synthetic_data
    cache = PredictiveCache(lattice, train_prev, train_next, val_prev, val_next)
    i = int(SMALL_CORE[0])
    assert cache.mask_full(i) == frozenset(int(j) for j in lattice.neighbor_ids[i])


def test_full_structural_shell_gives_exactly_zero_leakage(lattice, synthetic_data):
    """Task brief section 5's own structural claim: "the true full structural
    Moore shell would make one-step leakage exactly zero by construction."
    For a compact core whose |S(I)| <= K, boundary_search must select
    B = S(I), which makes mask_IB(i) == mask_full(i) for every i in I
    (every neighbour of every interior bird is either in I or in S(I)),
    hence L_i == 0 EXACTLY (same cached value), not merely "near-zero"."""
    train_prev, train_next, val_prev, val_next = synthetic_data
    cache = PredictiveCache(lattice, train_prev, train_next, val_prev, val_next)
    result = select_boundary(cache, lattice, SMALL_CORE, K_BOUNDARY_BUDGET)
    assert result["used_full_shell"] is True
    assert result["structural_shell_size"] <= K_BOUNDARY_BUDGET
    gl = G_and_L(cache, SMALL_CORE, result["B"])
    assert gl["L_I"] == pytest.approx(0.0, abs=0.0)
    for v in gl["per_bird"].values():
        assert v["L_i"] == pytest.approx(0.0, abs=0.0)


def test_candidate_evaluation_is_deterministic(lattice, synthetic_data):
    train_prev, train_next, val_prev, val_next = synthetic_data
    B = np.array([5, 6, 15, 25, 35, 45, 46, 56, 57, 67, 68, 69])
    results = []
    for _ in range(2):
        cache = PredictiveCache(lattice, train_prev, train_next, val_prev, val_next)
        results.append(G_and_L(cache, CANONICAL_I0, B))
    assert results[0]["G_I"] == results[1]["G_I"]
    assert results[0]["L_I"] == results[1]["L_I"]


def test_negative_finite_sample_estimates_are_not_zero_clamped(lattice):
    """With a tiny, noisy synthetic dataset, some G_i/L_i will be genuinely
    negative (a smaller conditioning set can, by sampling noise, outperform
    a larger one on the held-out fold). The cache must preserve that, only
    snapping values within machine-epsilon of zero."""
    rng = np.random.default_rng(7)
    prev = rng.integers(0, 4, size=(40, 100))
    nxt = rng.integers(0, 4, size=(40, 100))  # fully independent of prev -> pure noise
    cache = PredictiveCache(lattice, prev[:28], nxt[:28], prev[28:], nxt[28:])
    B = np.array([5, 6, 15, 25, 35, 45, 46, 56, 57, 67, 68, 69])
    gl = G_and_L(cache, CANONICAL_I0, B)
    # under pure noise, held-out log-loss differences fluctuate around 0 in
    # both directions -- at least one of G/L should show a genuine negative
    # per-bird value across this many (20) birds.
    any_negative = any(v["G_i"] < -1e-9 or v["L_i"] < -1e-9 for v in gl["per_bird"].values())
    assert any_negative, "expected at least one genuine (non-machine-eps) negative finite-sample estimate"
