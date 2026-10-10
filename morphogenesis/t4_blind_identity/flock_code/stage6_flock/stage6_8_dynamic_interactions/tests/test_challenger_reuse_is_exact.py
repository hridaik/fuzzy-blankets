"""`InteriorModel.fit_reusing` must be numerically identical to a full refit.

It is a pure speedup of the challenger's scan over residual exterior sources
(a target's conditioning set is spatially restricted, so adding a distant
source cannot change that target's model). A speedup that changed a number
would silently alter the certification verdict, so it is asserted, not assumed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE))

from predictive_boundary_68 import InteriorModel


def _data(seed=0, n=900, L=8):
    rng = np.random.default_rng(seed)
    nn = L * L
    prev = rng.integers(0, 4, (n, nn))
    nxt = np.zeros_like(prev)
    for i in range(nn):
        nxt[:, i] = np.where(rng.random(n) < 0.8, prev[:, (i + 1) % nn], rng.integers(0, 4, n))
    pos = np.stack([np.repeat(np.arange(L), L), np.tile(np.arange(L), L)], 1).astype(float)
    return prev, nxt, pos


TARGETS = np.array([9, 10, 11, 17, 18])
I = [9, 10, 11, 17, 18, 19]
B = [8]


def test_fit_reusing_matches_full_refit():
    prev, nxt, pos = _data()
    base = InteriorModel(TARGETS, I, B, pos).fit(prev, nxt)
    for j in (2, 12, 26, 40, 55):
        full = InteriorModel(TARGETS, I, B + [j], pos).fit(prev, nxt)
        fast = InteriorModel(TARGETS, I, B + [j], pos).fit_reusing(base, prev, nxt)
        assert np.isclose(full.mean_logloss(prev, nxt), fast.mean_logloss(prev, nxt), atol=1e-12), \
            f"reuse changed the loss for added source {j}"
        assert np.allclose(np.nan_to_num(full.per_row_logloss(prev, nxt)),
                           np.nan_to_num(fast.per_row_logloss(prev, nxt)), atol=1e-12)


def test_reuse_actually_reuses_and_refits_the_right_targets():
    prev, nxt, pos = _data()
    base = InteriorModel(TARGETS, I, B, pos).fit(prev, nxt)
    far = InteriorModel(TARGETS, I, B + [55], pos).fit_reusing(base, prev, nxt)
    assert all(far.models_[int(i)] is base.models_[int(i)] for i in TARGETS), \
        "a far-away added source must leave every target's model untouched"
    near = InteriorModel(TARGETS, I, B + [12], pos).fit_reusing(base, prev, nxt)
    assert any(near.models_[int(i)] is not base.models_[int(i)] for i in TARGETS), \
        "a nearby added source must force a refit somewhere"


def test_spatial_restriction_keeps_every_live_source():
    """r_pool must be comfortably wider than the Moore interaction geometry, or
    the restriction would be doing inference rather than saving compute."""
    from predictive_boundary_68 import R_POOL
    assert R_POOL >= 2.0 * np.sqrt(2), "r_pool must exceed the Moore diagonal by a clear margin"
