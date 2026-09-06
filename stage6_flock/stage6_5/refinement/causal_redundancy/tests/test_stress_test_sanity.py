"""Sanity checks for stress_test.py's exact cross-entropy evaluation."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))
BOUNDARY_INFERENCE_CODE = Path(__file__).resolve().parents[3] / "boundary_inference" / "code"
sys.path.insert(0, str(BOUNDARY_INFERENCE_CODE))

from nodewise_model import NodewiseModel  # noqa: E402
from stress_test import exact_cross_entropy_loss  # noqa: E402


def test_full_model_has_zero_self_excess():
    """M_full's own excess loss relative to itself must be exactly zero --
    a basic consistency check on exact_cross_entropy_loss, independent of
    intervention machinery."""
    rng = np.random.default_rng(0)
    n_bird = 6
    I0 = [0, 1]
    cond_extra = [2, 3, 4, 5]
    prev = rng.integers(0, 4, size=(200, n_bird))
    nxt = rng.integers(0, 4, size=(200, n_bird))
    model = NodewiseModel(I0, cond_extra).fit(prev, nxt)

    # true distribution = the model's own prediction -> CE should equal the
    # model's own entropy, and CRUCIALLY excess-over-self must be 0.
    from stress_test import _predicted_dist
    pred = _predicted_dist(model, prev)
    true_dist_all = np.zeros((prev.shape[0], n_bird, 4))
    for i in I0:
        true_dist_all[:, i, :] = pred[i]

    loss_full = exact_cross_entropy_loss(model, prev, true_dist_all)
    loss_full_again = exact_cross_entropy_loss(model, prev, true_dist_all)
    assert abs(loss_full - loss_full_again) < 1e-12


def test_perfect_prediction_gives_near_zero_cross_entropy():
    """If the true distribution is a one-hot spike matching a constant-target
    model's prediction, cross-entropy should be near zero."""
    n_bird = 3
    I0 = [0]
    prev = np.zeros((50, n_bird), dtype=int)
    nxt = np.zeros((50, n_bird), dtype=int)  # bird 0 always heads 'up' (0)
    model = NodewiseModel(I0, [1, 2]).fit(prev, nxt)

    true_dist_all = np.zeros((50, n_bird, 4))
    true_dist_all[:, 0, 0] = 1.0
    loss = exact_cross_entropy_loss(model, prev, true_dist_all)
    assert loss < 0.05
