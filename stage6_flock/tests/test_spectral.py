import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from flock_sim.spectral import build_adjacency, compute_fiedler, classify, jaccard, align_to_reference


def test_adjacency_two_perfect_blocks():
    # 4 birds, 3 timesteps. Birds 0,1 always heading 0; birds 2,3 always heading 1.
    z_window = np.array([[0, 0, 1, 1]] * 3)
    A = build_adjacency(z_window)
    TW = 3
    expected = np.array([
        [TW, TW, 0, 0],
        [TW, TW, 0, 0],
        [0, 0, TW, TW],
        [0, 0, TW, TW],
    ], dtype=float)
    assert np.allclose(A, expected)


def test_self_loops_inert_for_laplacian():
    rng = np.random.default_rng(0)
    z_window = rng.integers(0, 4, size=(5, 12))
    A_with_self = build_adjacency(z_window)
    A_no_self = A_with_self.copy()
    np.fill_diagonal(A_no_self, 0)
    L1, *_ = compute_fiedler(A_with_self)
    L2, *_ = compute_fiedler(A_no_self)
    assert np.allclose(L1, L2), "Laplacian should be identical with/without self-loops (see audit sec 10)"


def test_two_disconnected_perfect_communities_gives_zero_gap_or_two_zero_eigs():
    # Perfectly separated communities (no cross edges at all) -> graph is
    # disconnected -> at least 2 zero eigenvalues of L.
    z_window = np.array([[0, 0, 1, 1]] * 4)
    A = build_adjacency(z_window)
    L, eigvals, fiedler_raw, fiedler_norm, l1, l2, l3, gap, ncomp = compute_fiedler(A)
    assert ncomp >= 2
    assert abs(l1) < 1e-8 and abs(l2) < 1e-8


def test_classify_fixed_threshold_matches_hand_case():
    # Construct a Fiedler-like vector directly (bypass eigensolver) to check
    # classify()'s literal percentile/threshold logic in isolation.
    y2 = np.array([1.0, 0.9, 0.8, 0.02, -0.01, -0.8, -0.9, -1.0, 0.5, -0.5])
    A = np.eye(10)
    core1, core2, boundary, active, sensory, labels = classify(A, y2, boundary_rule="fixed", fixed_threshold=0.05)
    # top 20% of 10 values (>80th pctl) and bottom 20% (<20th pctl)
    assert 0 in core1 or 1 in core1  # highest values
    assert 7 in core2 or 6 in core2  # lowest values
    assert 3 in boundary and 4 in boundary  # |y2|<0.05


def test_jaccard_basic():
    assert jaccard(np.array([1, 2, 3]), np.array([2, 3, 4])) == 2 / 4
    assert jaccard(np.array([]), np.array([])) == 1.0


def test_align_to_reference_swaps_when_core2_overlaps_more():
    core1 = np.array([0, 1, 2])
    core2 = np.array([3, 4, 5])
    refclust = np.array([3, 4])
    c1, c2 = align_to_reference(core1, core2, None, None, refclust)
    assert np.array_equal(c1, core2) and np.array_equal(c2, core1)
