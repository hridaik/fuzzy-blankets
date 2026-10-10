"""Blind detector, comparator and tracker behaviour on synthetic data."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE))

import observer, candidate_detection as cd, spectral_proposal as sp, tracker
from louvain import louvain, modularity


def _planted(nn_side=12, seed=0, T=30, drift=0.0):
    """Two spatial blocks with different headings. `drift` moves the block
    boundary rightwards over time, so the communities keep their identity while
    exchanging members -- the situation the tracker has to survive."""
    rng = np.random.default_rng(seed)
    L = nn_side
    pos = np.stack([np.repeat(np.arange(L), L), np.tile(np.arange(L), L)], 1).astype(float)
    truth = (pos[:, 0] < L / 2).astype(int)
    z = []
    for t in range(T):
        cut = L / 2 + drift * t
        block = (pos[:, 0] < cut).astype(int)
        z.append(np.where(rng.random(L * L) < 0.92, block, rng.integers(0, 4, L * L)))
    return pos, np.array(z), truth


def test_louvain_is_deterministic_and_finds_planted_blocks():
    rng = np.random.default_rng(0)
    lab = np.repeat([0, 1, 2], 10)
    W = (rng.random((30, 30)) < np.where(lab[:, None] == lab[None, :], 0.85, 0.05)).astype(float)
    W = np.triu(W, 1); W = W + W.T
    p = louvain(W)
    assert np.array_equal(p, louvain(W))              # deterministic
    assert len(np.unique(p)) == 3
    assert modularity(W, p) > 0.4


def test_affinity_uses_a_smooth_kernel_not_an_adjacency_indicator():
    """The spatial kernel must be smooth -- if it were the Moore/FOV predicate
    it would take only two values."""
    d = np.linspace(0.25, 5.0, 40)
    D = np.zeros((41, 41)); D[0, 1:] = d; D[1:, 0] = d
    K = cd.gaussian_kernel(D)
    row = K[0, 1:]
    inside = row[d <= cd.KERNEL_CUTOFF]
    assert len(np.unique(np.round(inside, 6))) > 10   # smooth, not a 2-valued indicator
    assert np.all(np.diff(inside) < 0)                # strictly decreasing in distance
    assert np.all(row[d > cd.KERNEL_CUTOFF] == 0.0)   # hard cutoff beyond KERNEL_CUTOFF


def test_detector_recovers_planted_spatial_communities():
    pos, z, truth = _planted()
    obs = observer.Observation(pos, z, 20)
    ok, _ = cd.propose(obs)
    assert len(ok) >= 1
    best = max(ok, key=lambda c: len(set(c.members.tolist()) & set(np.where(truth == truth[0])[0].tolist())))
    tgt = set(np.where(truth == truth[best.members[0]])[0].tolist())
    got = set(best.members.tolist())
    assert len(got & tgt) / len(got | tgt) > 0.5


def test_detector_returns_multiple_candidates_not_one_winner():
    pos, z, _ = _planted()
    obs = observer.Observation(pos, z, 20)
    _, allc = cd.propose(obs)
    assert len(allc) >= 2


def test_spectral_comparator_runs_and_is_labelled_as_a_proposal():
    pos, z, _ = _planted()
    obs = observer.Observation(pos, z, 20)
    ok, allc = sp.propose(obs)
    assert all(c.method == "spectral_coherence" for c in allc)
    src = (CODE / "spectral_proposal.py").read_text().lower()
    assert "markov blanket" in src, "the module must explicitly disclaim the term"
    assert "not a markov blanket" in src or "is not a markov blanket" in src


def test_spectral_split_matches_the_frozen_upstream_implementation():
    """The comparator's Fiedler machinery must agree with
    python/flock_sim/spectral.py, which is left untouched."""
    sys.path.insert(0, str(CODE.parents[2] / "python"))
    from flock_sim import spectral as upstream
    pos, z, _ = _planted(seed=2)
    obs = observer.Observation(pos, z, 20)
    A_mine = sp.coheading_adjacency(obs, W=cd.W_AFFINITY)
    A_up = upstream.build_adjacency(obs.window(cd.W_AFFINITY))
    assert np.allclose(A_mine, A_up)
    c1, c2, y, ev = sp.fiedler_split(A_mine)
    L, eigvals, fr, fn, *_ = upstream.compute_fiedler(A_up)
    assert np.allclose(np.sort(ev), np.sort(eigvals))
    assert np.allclose(np.abs(y), np.abs(fn))          # sign is solver-arbitrary


def test_tracker_survives_membership_change_without_exact_equality():
    pos, z, _ = _planted(T=40, drift=0.12)
    tr = tracker.LineageTracker("affinity_louvain")
    obs = observer.Observation(pos, z, 10)
    for t in range(10, 35):
        tr.update(cd.propose(obs.advanced_to(t))[0])
    s = tr.summary()
    assert any(l["duration"] >= 5 for l in s), "no lineage survived 5 frames"
    long = [l for l in s if l["duration"] >= 5]
    assert any(l["mean_jaccard"] < 1.0 for l in long), \
        "material identity was effectively imposed as exact equality"


def test_actuator_budget_is_actually_honoured():
    """`K_ACT` is a module constant used as a default argument, so it is bound
    at import time; a caller that varies the budget must pass it explicitly.
    This asserts the budget really changes the returned actuator set, which a
    silently-ignored budget would not."""
    import adaptive_control as ac
    rng = np.random.default_rng(0)
    I = list(range(40))
    influence = {100 + j: {i: float(rng.random() * 0.1) for i in I} for j in range(30)}
    sizes = [len(ac.multicover(influence, I, k_act=k, theta=1.0, q_support=0.99)[0])
             for k in (3, 8, 15)]
    assert sizes == [3, 8, 15], sizes            # budget binds, and it is honoured
    # and it still stops early when its own coverage rule is satisfied first
    assert len(ac.multicover(influence, I, k_act=30, theta=0.05, q_support=0.5)[0]) < 30
