"""Unit tests for common_67.py's 60/20/20 trajectory-level split (task brief
section 2): determinism, disjointness, and no-future-leakage (never reads an
index > t)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from common_67 import build_window_dataset3  # noqa: E402


def _fake_reps(n_rep=100, nt=25, n_bird=10, seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 4, size=(n_rep, nt + 1, n_bird))


def test_split_is_disjoint_and_covers_all_replicates():
    z = _fake_reps()
    wds = build_window_dataset3(z, t=20)
    train, val, test = set(wds.train_ids), set(wds.val_ids), set(wds.test_ids)
    assert train.isdisjoint(val)
    assert train.isdisjoint(test)
    assert val.isdisjoint(test)
    assert train | val | test == set(range(100))


def test_split_fractions_approximate_60_20_20():
    z = _fake_reps(n_rep=100)
    wds = build_window_dataset3(z, t=20)
    assert wds.n_rep_train == 60
    assert wds.n_rep_val == 20
    assert wds.n_rep_test == 20


def test_split_is_deterministic():
    z = _fake_reps()
    wds1 = build_window_dataset3(z, t=20, split_seed=42)
    wds2 = build_window_dataset3(z, t=20, split_seed=42)
    assert wds1.train_ids == wds2.train_ids
    assert wds1.val_ids == wds2.val_ids
    assert wds1.test_ids == wds2.test_ids


def test_never_reads_future_beyond_t():
    """Corrupt every state strictly after t; the resulting dataset must be
    byte-identical to one built from data that was never corrupted."""
    z = _fake_reps(n_rep=20, nt=25)
    t = 15
    z_corrupted = z.copy()
    z_corrupted[:, t + 1:, :] = -999  # poison future states
    wds_clean = build_window_dataset3(z, t=t, split_seed=0)
    wds_dirty = build_window_dataset3(z_corrupted, t=t, split_seed=0)
    assert np.array_equal(wds_clean.train_prev, wds_dirty.train_prev)
    assert np.array_equal(wds_clean.train_next, wds_dirty.train_next)
    assert np.array_equal(wds_clean.val_prev, wds_dirty.val_prev)
    assert np.array_equal(wds_clean.test_prev, wds_dirty.test_prev)


def test_effective_window_capped_at_W():
    z = _fake_reps(n_rep=10, nt=50)
    wds = build_window_dataset3(z, t=30, W=10)
    assert wds.effective_window == 10
    # each of the (n_rep) trajectories contributes effective_window-1 = 9 transitions
    assert wds.train_prev.shape[0] == wds.n_rep_train * 9


def test_small_t_shrinks_window_gracefully():
    z = _fake_reps(n_rep=10, nt=50)
    wds = build_window_dataset3(z, t=3, W=10)
    assert wds.effective_window == 4  # states [0..3]
