"""Unit + synthetic-recovery tests for the inference-side pipeline
(nodewise_model, greedy_selection, bootstrap). Uses a hand-constructed
synthetic categorical Markov process with a KNOWN true dependency set, so
correctness is checked against ground truth we ourselves designed -- not
against the flock simulator (that recovery check is Part 1.8, done on real
flock data in run_part1_boundary_inference.py). Part 1.5's instruction
("do not assume greedy selection will work perfectly, test it") is taken
literally: this includes a case where greedy is expected to fail (a fully
independent exterior) and a case where it is expected to succeed.

Run: pytest stage6_5/boundary_inference/tests/ -q (from stage6_flock/)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from nodewise_model import NodewiseModel, flatten_transitions, design_matrix, NU  # noqa: E402
from greedy_selection import fit_eval, screen_candidates, greedy_forward_select  # noqa: E402
from bootstrap import bootstrap_membership  # noqa: E402


def test_flatten_transitions_shapes_and_alignment():
    n_traj, n_time, n_bird = 4, 6, 5
    z = np.arange(n_traj * (n_time + 1) * n_bird).reshape(n_traj, n_time + 1, n_bird) % NU
    prev, nxt = flatten_transitions(z)
    assert prev.shape == (n_traj * n_time, n_bird)
    assert nxt.shape == (n_traj * n_time, n_bird)
    # first row of prev/nxt should be z[0,0,:] -> z[0,1,:]
    assert np.array_equal(prev[0], z[0, 0])
    assert np.array_equal(nxt[0], z[0, 1])
    # row n_time (start of 2nd trajectory) should be z[1,0,:] -> z[1,1,:]
    assert np.array_equal(prev[n_time], z[1, 0])
    assert np.array_equal(nxt[n_time], z[1, 1])


def test_design_matrix_onehot_shape():
    prev = np.array([[0, 1, 2], [3, 0, 1]])
    X = design_matrix(prev, cond_set=[0, 2])
    assert X.shape == (2, 2 * NU)
    assert X[0].sum() == 2  # exactly one "1" per conditioned bird
    assert X[0, 0] == 1  # bird 0 state=0 -> first one-hot slot
    assert X[0, NU + 2] == 1  # bird 2 state=2 -> slot index 2 within its (2nd) block


def _make_synthetic(n_bird=10, n_traj=40, n_time=12, dep_bird=5, seed=0, noise=0.05):
    """z_0's next state tracks exterior bird `dep_bird`'s CURRENT state with
    probability (1-noise); every other bird (including I0 members 1,2) is an
    independent random walk uncorrelated with anything else. True boundary
    for I0={0,1,2} is therefore exactly {dep_bird}."""
    rng = np.random.default_rng(seed)
    z = rng.integers(0, NU, size=(n_traj, n_time + 1, n_bird))
    for tr in range(n_traj):
        for t in range(n_time):
            if rng.random() < 1 - noise:
                z[tr, t + 1, 0] = z[tr, t, dep_bird]
            else:
                z[tr, t + 1, 0] = rng.integers(0, NU)
    return z


def test_screening_ranks_true_dependency_highest():
    z = _make_synthetic()
    rng = np.random.default_rng(1)
    idx = rng.permutation(40)
    train, val = z[idx[:24]], z[idx[24:]]
    from nodewise_model import flatten_transitions
    train_prev, train_next = flatten_transitions(train)
    val_prev, val_next = flatten_transitions(val)
    I0 = [0, 1, 2]
    candidates = [j for j in range(10) if j not in I0]
    _, gains = screen_candidates(I0, candidates, train_prev, train_next, val_prev, val_next)
    best = max(gains, key=lambda k: gains[k])
    assert best == 5, f"expected bird 5 (the true dependency) to screen highest, got {best}: {gains}"
    assert gains[5] > 0, "true dependency should show positive held-out gain"


def test_greedy_forward_select_recovers_synthetic_boundary():
    z = _make_synthetic()
    rng = np.random.default_rng(2)
    idx = rng.permutation(40)
    train, val = z[idx[:24]], z[idx[24:]]
    train_prev, train_next = flatten_transitions(train)
    val_prev, val_next = flatten_transitions(val)
    I0 = [0, 1, 2]
    candidates = [j for j in range(10) if j not in I0]
    full_loss = fit_eval(I0, candidates, train_prev, train_next, val_prev, val_next)
    B, trace = greedy_forward_select(I0, candidates, train_prev, train_next, val_prev, val_next,
                                      full_loss=full_loss, delta_tol=0.01, min_gain=0.005)
    assert B == [5], f"expected exact recovery of {{5}} on this easy synthetic case, got {B}"
    assert trace[-1]["stop_reason"] in ("delta_tol_reached", "no_candidate_above_min_gain")


def test_greedy_forward_select_stops_on_fully_independent_exterior():
    """Negative-control case: NO exterior bird carries any information about
    I0's next state. Greedy must select nothing (empty B), not overfit to
    noise -- this is the min_gain complexity-control stopping rule being
    exercised, not just the delta_tol one."""
    rng = np.random.default_rng(3)
    n_bird, n_traj, n_time = 10, 40, 12
    z = rng.integers(0, NU, size=(n_traj, n_time + 1, n_bird))  # fully independent everywhere
    idx = rng.permutation(n_traj)
    train, val = z[idx[:24]], z[idx[24:]]
    train_prev, train_next = flatten_transitions(train)
    val_prev, val_next = flatten_transitions(val)
    I0 = [0, 1, 2]
    candidates = [j for j in range(n_bird) if j not in I0]
    full_loss = fit_eval(I0, candidates, train_prev, train_next, val_prev, val_next)
    B, trace = greedy_forward_select(I0, candidates, train_prev, train_next, val_prev, val_next,
                                      full_loss=full_loss, delta_tol=0.01, min_gain=0.005)
    assert B == [], f"expected empty boundary on fully independent exterior, got {B}"


def test_bootstrap_membership_is_high_for_true_dependency():
    z = _make_synthetic(n_traj=50)
    rng = np.random.default_rng(4)
    idx = rng.permutation(50)
    train, val = z[idx[:30]], z[idx[30:]]
    I0 = [0, 1, 2]
    candidates = [j for j in range(10) if j not in I0]
    membership, sets = bootstrap_membership(I0, candidates, train, val, n_boot=8, shortlist_k=7,
                                             delta_tol=0.01, min_gain=0.005, rng=np.random.default_rng(5))
    assert membership[5] >= 0.5, f"true dependency should be selected in most bootstrap replicates, got {membership}"
    for k in candidates:
        if k != 5:
            assert membership[k] <= membership[5]


def test_nodewise_model_constant_target_handled():
    """A bird whose observed next-state never varies must not crash fitting
    (sklearn's LogisticRegression requires >=2 classes)."""
    n_traj, n_time, n_bird = 3, 5, 4
    prev = np.zeros((n_traj * n_time, n_bird), dtype=int)
    nxt = np.zeros((n_traj * n_time, n_bird), dtype=int)  # everything constant at 0
    m = NodewiseModel(I0=[0, 1], cond_extra=[2]).fit(prev, nxt)
    losses = m.per_bird_logloss(prev, nxt)
    assert losses[0] < 0.01 and losses[1] < 0.01
