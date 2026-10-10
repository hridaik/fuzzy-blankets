"""Stage 6.11 simulator correctness. EVALUATION-SIDE test.

The load-bearing test is `test_default_path_reproduces_stage_6_9_exactly`: the
two additions are only defensible as *additions* if switching them off leaves
Stage 6.9 untouched, so that is checked bit-for-bit rather than by tolerance.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

STAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE / "code"))

from common_611 import ModelParams, UV4                      # noqa: E402
from moving_flock import MovingFlock                          # noqa: E402
from moving_flock_611 import MovingFlock611, MOORE_DEGREE     # noqa: E402

# 90-degree CCW rotation of the four-heading lattice: up->left, down->right,
# left->down, right->up. Derived from UV4, not assumed (see test below).
ROT90 = np.array([2, 3, 1, 0])

CONFIGS = [dict(N=120, L=14.0, R=1.6, v=0.5), dict(N=250, L=24.0, R=0.9, v=0.28)]


def _config(mf, seed=0):
    rng = np.random.default_rng(seed)
    return rng.random((mf.N, 2)) * mf.L, rng.integers(0, 4, mf.N)


def _rotate(r, L):
    """Rotate positions 90 degrees CCW about the box centre. A square torus
    maps onto itself under this, so it is a symmetry of the whole geometry."""
    c = L / 2.0
    d = r - c
    return (np.stack([-d[:, 1], d[:, 0]], axis=1) + c) % L


# ------------------------------------------------------------------ defaults
@pytest.mark.parametrize("cfg", CONFIGS)
@pytest.mark.parametrize("seed", [0, 1, 7])
def test_default_path_reproduces_stage_6_9_exactly(cfg, seed):
    a = MovingFlock(**cfg).run(nt=80, seed=seed)
    b = MovingFlock611(**cfg).run(nt=80, seed=seed)
    assert np.array_equal(a.z_hist, b.z_hist), "headings diverge from Stage 6.9"
    assert np.array_equal(a.r_hist, b.r_hist), "positions diverge from Stage 6.9"


def test_default_G_is_identical_to_stage_6_9():
    old, new = MovingFlock(**CONFIGS[0]), MovingFlock611(**CONFIGS[0])
    r, z = _config(old, 5)
    assert np.array_equal(old.compute_G(r, z), new.compute_G(r, z))


@pytest.mark.parametrize("kw", [dict(), dict(social="normalized"), dict(cohesion=1.0),
                                dict(social="normalized", cohesion=0.7)])
def test_step_cached_is_exactly_step(kw):
    """The position cache stays a speedup, not an approximation, for the new
    terms too -- they are computed inside the same helper."""
    mf = MovingFlock611(**CONFIGS[0], **kw)
    r, _ = _config(mf, 4)
    cache = mf.position_cache(r)
    for seed in range(4):
        z = np.random.default_rng(seed).integers(0, 4, mf.N)
        a = mf.step(r, z, np.random.default_rng(99))
        b = mf.step_cached(cache, z, np.random.default_rng(99))
        assert np.array_equal(a[1], b[1])
        assert np.allclose(a[0], b[0])


def test_bad_flags_are_rejected():
    with pytest.raises(ValueError):
        MovingFlock611(social="mean")
    with pytest.raises(ValueError):
        MovingFlock611(cohesion=-1.0)


# ------------------------------------------------------- addition 1: degree
def test_normalized_is_exactly_kref_over_degree_times_raw():
    raw = MovingFlock611(**CONFIGS[1])
    nrm = MovingFlock611(**CONFIGS[1], social="normalized")
    r, z = _config(raw, 3)
    deg = raw.in_degree(r, z).astype(float)
    Graw, Gnrm = raw.compute_G(r, z), nrm.compute_G(r, z)
    nz = deg > 0
    assert np.allclose(Gnrm[nz], Graw[nz] * MOORE_DEGREE / deg[nz][:, None])
    assert np.all(Gnrm[~nz] == 0.0), "a bird with no partners must keep G = 0"
    assert np.all(Graw[~nz] == 0.0)


def test_policy_posterior_is_approximately_scale_invariant():
    """Recorded because it is the reason section N's normalization does NOT
    decouple decision gain from degree (see logs/model_validation_611.txt, V3).

    `policy_posterior` refits W = alpha / (spm_beta - u.G) from W = 0 every
    step, so for |u.G| >> spm_beta it behaves like W ~ 1/|G| and the softmax
    argument W*G barely notices a rescaling of G. A per-bird scalar therefore
    cannot be the instrument that changes decision sharpness.
    """
    from flock_sim.active_inference import build_model, policy_posterior
    pm = build_model(ModelParams())
    G = np.random.default_rng(0).normal(-30.0, 10.0, (256, 4))
    gains = [float(policy_posterior(pm, c * G).max(axis=1).mean()) for c in (1.0, 2.0, 4.0, 8.0)]
    assert max(gains) - min(gains) < 0.05, gains


def test_raw_decision_gain_still_rises_with_degree():
    """The phenomenon section N was aimed at, on a real clustered configuration
    rather than a uniform one: more partners means a sharper policy."""
    mf = MovingFlock611(N=250, L=24.0, R=0.9, v=0.28)
    res = mf.run(nt=120, seed=0)
    r, z = res.r_hist[-1], res.z_hist[-1]
    gains = [float(MovingFlock611(N=250, L=24.0, R=R, v=0.28).policy(r, z).max(axis=1).mean())
             for R in (0.6, 1.2, 2.4)]
    assert gains[-1] > gains[0], gains


# ----------------------------------------------------- addition 2: cohesion
def test_cohesion_off_changes_nothing():
    a = MovingFlock611(**CONFIGS[0], cohesion=0.0)
    b = MovingFlock611(**CONFIGS[0])
    r, z = _config(a, 2)
    assert np.array_equal(a.compute_G(r, z), b.compute_G(r, z))


def test_cohesion_prefers_the_heading_toward_the_local_centroid():
    """Partners placed due north of a north-facing bird must make 'up' the
    action the cohesion term favours -- and only the cohesion term."""
    mf0 = MovingFlock611(N=5, L=20.0, R=3.0, v=0.1, cohesion=0.0)
    mf1 = MovingFlock611(N=5, L=20.0, R=3.0, v=0.1, cohesion=1.0)
    r = np.array([[10.0, 10.0], [9.5, 12.0], [10.0, 12.5], [10.6, 11.7], [10.2, 12.2]])
    z = np.zeros(5, dtype=int)                     # everyone facing up
    delta = mf1.compute_G(r, z)[0] - mf0.compute_G(r, z)[0]
    assert int(np.argmax(delta)) == 0, delta       # 0 == up in UV4
    assert delta[1] == pytest.approx(-delta[0])    # down is the exact opposite


def test_cohesion_delta_is_bounded_by_its_strength():
    """<unit bearing, unit heading> in [-1, 1], so each partner can move G by at
    most 2*fc_pos -- the term cannot silently dominate the existing physics."""
    fc_pos = 0.9
    a = MovingFlock611(**CONFIGS[0])
    b = MovingFlock611(**CONFIGS[0], cohesion=fc_pos)
    r, z = _config(a, 6)
    deg = a.in_degree(r, z)
    delta = np.abs(b.compute_G(r, z) - a.compute_G(r, z))
    assert np.all(delta <= 2.0 * fc_pos * deg[:, None] + 1e-9)


# ------------------------------------------- addition 3 (none): no steering
def test_rot90_permutation_is_the_one_UV4_implies():
    for h in range(4):
        x, y = UV4[h]
        assert np.allclose(UV4[ROT90[h]], [-y, x])


@pytest.mark.parametrize("kw", [dict(), dict(social="normalized"), dict(cohesion=1.0),
                                dict(social="normalized", cohesion=1.0)])
def test_isotropy_under_90_degree_rotation(kw):
    """Nothing added prefers a direction: rotating the world 90 degrees
    permutes G's columns and does nothing else."""
    mf = MovingFlock611(**CONFIGS[0], **kw)
    r, z = _config(mf, 11)
    G = mf.compute_G(r, z)
    G_rot = mf.compute_G(_rotate(r, mf.L), ROT90[z])
    assert np.abs(G_rot[:, ROT90] - G).max() < 1e-9


@pytest.mark.parametrize("kw", [dict(), dict(social="normalized"), dict(cohesion=1.0),
                                dict(social="normalized", cohesion=1.0)])
def test_agent_locality_under_relabelling(kw):
    """Nothing added references a bird index: relabelling the birds permutes
    G's rows and does nothing else."""
    mf = MovingFlock611(**CONFIGS[0], **kw)
    r, z = _config(mf, 12)
    perm = np.random.default_rng(0).permutation(mf.N)
    G = mf.compute_G(r, z)
    G_perm = mf.compute_G(r[perm], z[perm])
    assert np.abs(G_perm - G[perm]).max() < 1e-9


@pytest.mark.parametrize("kw", [dict(social="normalized"), dict(cohesion=1.0)])
def test_translation_invariance_on_the_torus(kw):
    """No absolute position enters G."""
    mf = MovingFlock611(**CONFIGS[0], **kw)
    r, z = _config(mf, 13)
    shift = np.array([3.7, -8.1])
    assert np.abs(mf.compute_G((r + shift) % mf.L, z) - mf.compute_G(r, z)).max() < 1e-9
