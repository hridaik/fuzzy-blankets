"""Tests for the B6 flock-level bootstrap CI -- resamples flocks, not
replicates, and degrades gracefully on edge cases."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from aggregate import per_flock_deltas, bootstrap_ci_over_flocks  # noqa: E402


def test_per_flock_deltas_computed_correctly():
    rows = [
        dict(seed=1, inferred=dict(p_success=0.8), random_matched=dict(p_success=0.1)),
        dict(seed=2, inferred=dict(p_success=0.3), random_matched=dict(p_success=0.3)),
    ]
    deltas = per_flock_deltas(rows)
    assert deltas[1] == 0.8 - 0.1
    assert deltas[2] == 0.0


def test_bootstrap_ci_contains_true_mean_on_constant_deltas():
    deltas = {i: 0.5 for i in range(10)}
    rng = np.random.default_rng(0)
    ci = bootstrap_ci_over_flocks(deltas, n_boot=500, rng=rng)
    assert abs(ci["mean"] - 0.5) < 1e-9
    assert ci["ci_lo"] == ci["ci_hi"] == 0.5


def test_bootstrap_ci_widens_with_variance():
    rng = np.random.default_rng(0)
    deltas_tight = {i: 0.5 + 0.001 * ((-1) ** i) for i in range(20)}
    deltas_wide = {i: 0.5 + 0.4 * ((-1) ** i) for i in range(20)}
    ci_tight = bootstrap_ci_over_flocks(deltas_tight, n_boot=2000, rng=np.random.default_rng(1))
    ci_wide = bootstrap_ci_over_flocks(deltas_wide, n_boot=2000, rng=np.random.default_rng(1))
    assert (ci_wide["ci_hi"] - ci_wide["ci_lo"]) > (ci_tight["ci_hi"] - ci_tight["ci_lo"])


def test_empty_input_handled():
    ci = bootstrap_ci_over_flocks({}, n_boot=100)
    assert ci["n_flocks"] == 0
