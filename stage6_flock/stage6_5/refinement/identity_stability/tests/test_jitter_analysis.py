"""Unit tests for C1's D_X(t)/T_I(t) computation and jitter flagging."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from jitter_analysis import physical_change_series, turnover_series, jitter_report  # noqa: E402


def test_physical_change_series_all_static():
    z_hist = np.zeros((5, 10), dtype=int)
    D_X = physical_change_series(z_hist)
    assert np.all(D_X == 0.0)
    assert len(D_X) == 4


def test_physical_change_series_half_flip():
    z_hist = np.zeros((2, 10), dtype=int)
    z_hist[1, :5] = 1  # half the birds change heading
    D_X = physical_change_series(z_hist)
    assert D_X[0] == 0.5


def test_turnover_series_matches_identity_metrics():
    track = [np.array([0, 1, 2]), np.array([0, 1, 2]), np.array([0, 1, 3])]
    T_I = turnover_series(track)
    assert T_I.tolist() == [0, 2]  # step0->1: no change; step1->2: {2}<->{3} symmetric diff = 2


def test_jitter_flags_large_turnover_during_quiet_physical_state():
    """Construct a case where identity turnover spikes once while the
    physical state never moves at all -- the canonical detector-jitter
    signature: a single, unambiguous outlier well above the rest."""
    n = 20
    z_hist = np.zeros((n, 10), dtype=int)  # completely static physical state throughout
    track = [np.array([0, 1, 2, 3, 4])]
    for t in range(1, n):
        if t == 10:
            track.append(np.array([5, 6, 7, 8, 9]))  # one huge, spurious membership swap
        else:
            track.append(np.array([0, 1, 2, 3, 4]))  # otherwise perfectly stable
    report = jitter_report(z_hist, track)
    assert report["D_X_median"] == 0.0
    assert report["n_low_DX_high_TI"] > 0
