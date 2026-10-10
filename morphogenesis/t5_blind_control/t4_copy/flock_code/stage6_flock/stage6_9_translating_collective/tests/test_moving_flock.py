"""Moving-flock simulator correctness. EVALUATION-SIDE test."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stage6_8_dynamic_interactions" / "code"))

from common_69 import ModelParams, UV4
from moving_flock import MovingFlock, OCTANT_TO_SLOT
from common_68 import SLOT_VEC


def _mf():
    return MovingFlock(N=120, L=14.0, R=1.6, v=0.5, params=ModelParams())


def test_octant_map_is_the_identity_on_the_slot_directions():
    """Each Moore slot's own direction must map back to that slot."""
    for s in range(8):
        ang = np.arctan2(SLOT_VEC[s, 1], SLOT_VEC[s, 0]) % (2 * np.pi)
        assert OCTANT_TO_SLOT[int(np.round(ang / (np.pi / 4))) % 8] == s


def test_step_cached_is_exactly_step():
    """The position cache is a speedup, not an approximation."""
    mf = _mf()
    rng0 = np.random.default_rng(4)
    r = rng0.random((mf.N, 2)) * mf.L
    cache = mf.position_cache(r)
    for seed in range(5):
        z = np.random.default_rng(seed).integers(0, 4, mf.N)
        a = mf.step(r, z, np.random.default_rng(99))
        b = mf.step_cached(cache, z, np.random.default_rng(99))
        assert np.array_equal(a[1], b[1]), "next headings differ"
        assert np.allclose(a[0], b[0]), "next positions differ"


def test_fov_holds_for_every_live_edge():
    mf = _mf()
    rng = np.random.default_rng(0)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)
    recv, src, dvec = mf.live_edges(r, z)
    assert len(recv) > 0
    assert np.all((dvec * UV4[z[recv]]).sum(-1) >= -1e-12), "a live edge violates the FOV rule"
    D = np.sqrt((dvec ** 2).sum(-1))
    assert np.all(D <= mf.R + 1e-12), "a live edge exceeds the interaction radius"


def test_interaction_is_directed():
    mf = _mf()
    rng = np.random.default_rng(2)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)
    recv, src, _ = mf.live_edges(r, z)
    pairs = set(zip(recv.tolist(), src.tolist()))
    assert any((b, a) not in pairs for a, b in pairs), "the live graph is symmetric"


def test_torus_wrapping_is_minimum_image():
    mf = _mf()
    r = np.array([[0.1, 0.1], [mf.L - 0.1, mf.L - 0.1]])
    d = mf.wrap(r[1] - r[0])
    assert np.allclose(np.abs(d), 0.2), d


def test_oracle_B_D_is_the_directed_in_neighbourhood():
    mf = _mf()
    rng = np.random.default_rng(7)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)
    I = np.arange(10)
    recv, src, _ = mf.live_edges(r, z)
    brute = {int(j) for i, j in zip(recv, src) if i in set(I.tolist()) and j not in set(I.tolist())}
    assert set(mf.oracle_B_D(r, z, I).tolist()) == brute


def test_flock_does_not_disperse():
    """The pilot's precondition: the minimal moving extension must form groups
    rather than spreading uniformly (task brief 26)."""
    mf = MovingFlock(N=400, L=24.0, R=1.6, v=0.5, params=ModelParams())
    res = mf.run(nt=80, seed=0)
    r = res.r_hist[-1]
    D = np.sqrt((mf.displacements(r) ** 2).sum(-1))
    np.fill_diagonal(D, np.inf)
    mean_nn = float(np.sort(D, axis=1)[:, :4].mean())
    uniform_nn = 0.5 / np.sqrt(mf.N / mf.L ** 2)
    assert mean_nn < uniform_nn, f"mean 4-NN distance {mean_nn:.2f} is not below uniform {uniform_nn:.2f}"
