"""Part B gate: the structural and exact-interventional truth modules are
independent implementations of the same object and MUST agree. The stage stops
if they disagree materially -- so this is a gate, not a nicety."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

CODE = Path(__file__).resolve().parents[1] / "code"
S68 = Path(__file__).resolve().parents[2] / "stage6_8_dynamic_interactions" / "code"
sys.path.insert(0, str(CODE)); sys.path.insert(0, str(S68))

import reference_truth as rt
from episode_data import make_simulator, run_episode
import adaptive_control as ac


@pytest.fixture(scope="module")
def world():
    sim = make_simulator(400, 1.0, 1.0)
    res = run_episode(sim, 15, nt=64, record_oracle=False)
    return sim, res


def _interior(sim, res, t, n=40):
    """A compact interior, taken geometrically so this test does not depend on
    the detector."""
    P = sim.positions
    c = P[210]
    d = np.sqrt(((P - c) ** 2).sum(1))
    return np.array(sorted(np.argsort(d)[:n].tolist()))


@pytest.mark.parametrize("t", [50, 55, 60])
def test_structural_and_interventional_truth_agree(world, t):
    sim, res = world
    z = res.z_hist[t]
    I = _interior(sim, res, t)
    Bs = set(int(x) for x in rt.structural_interface(sim, z, I))
    cands = [j for j in range(sim.nn) if j not in set(I.tolist())]
    Bd, vals = rt.exact_do_interface(sim, z, I, candidates=cands)
    Bd = set(int(x) for x in Bd)
    assert Bs == Bd, (f"t={t}: structural and exact-do interfaces disagree; "
                      f"only-structural={sorted(Bs-Bd)}, only-do={sorted(Bd-Bs)}")


def test_non_interface_sources_have_exactly_zero_effect(world):
    sim, res = world
    z = res.z_hist[60]
    I = _interior(sim, res, 60)
    Bs = set(int(x) for x in rt.structural_interface(sim, z, I))
    far = [j for j in range(sim.nn) if j not in set(I.tolist()) and j not in Bs][:60]
    for j in far:
        tot, _ = rt.do_influence(sim, z, I, j, agg="sum")
        assert tot == 0.0, f"source {j} is outside B^struct but has effect {tot}"


def test_exterior_actuator_has_exactly_zero_one_step_authority(world):
    """Structural fact the audit turns on: forcing an exterior bird's ACTION at
    t fixes its heading at t+1, and an interior bird's t+1 heading is computed
    from the state at t -- so the interior cannot move until t+2. A one-step
    influence score therefore cannot be a task-authority score."""
    sim, res = world
    z = res.z_hist[60]
    I = _interior(sim, res, 60)
    B = sorted(int(x) for x in rt.structural_interface(sim, z, I))[:10]
    for j in B:
        assert rt.task_authority(sim, z, I, 0, j, tau=1) == 0.0, \
            f"exterior source {j} moved the interior at tau=1"


def test_task_authority_is_a_different_object_from_kl_influence(world):
    """KL influence is non-negative by construction; task authority is SIGNED.
    An actuator can have large influence and negative authority -- push the
    interior hard, in the wrong direction. Keeping them separate is Part B."""
    sim, res = world
    z = res.z_hist[60]
    I = _interior(sim, res, 60)
    B = sorted(int(x) for x in rt.structural_interface(sim, z, I))[:12]
    h0 = int(np.bincount(z[I], minlength=4).argmax())
    from common_610 import rotate_cw
    h_star = rotate_cw(h0)
    kls = [rt.do_influence(sim, z, I, j, agg="sum")[0] for j in B]
    auth = [rt.task_authority(sim, z, I, h_star, j, tau=2, n_roll=192) for j in B]
    assert all(k >= 0 for k in kls), "KL influence must be non-negative"
    assert any(a > 0 for a in auth), "no source has positive tau=2 task authority"
    assert min(auth) < max(auth), "authority shows no spread"


def test_one_step_authority_is_exact_and_reproducible(world):
    sim, res = world
    z = res.z_hist[60]
    I = _interior(sim, res, 60)
    h_star = 0
    j = int(rt.structural_interface(sim, z, I)[0])
    a1 = rt.task_authority(sim, z, I, h_star, j, tau=1)
    a2 = rt.task_authority(sim, z, I, h_star, j, tau=1)
    assert a1 == a2 == 0.0, "tau=1 authority must be exact (closed form) and zero"
    # tau=2 is sampled but reproducible under common random numbers
    b1 = rt.task_authority(sim, z, I, h_star, j, tau=2, rng_seed=7, n_roll=64)
    b2 = rt.task_authority(sim, z, I, h_star, j, tau=2, rng_seed=7, n_roll=64)
    assert b1 == b2, "common random numbers must make tau=2 authority reproducible"


def test_pair_synergy_is_defined_and_finite(world):
    sim, res = world
    z = res.z_hist[60]
    I = _interior(sim, res, 60)
    B = sorted(int(x) for x in rt.structural_interface(sim, z, I))
    s = rt.pair_synergy(sim, z, I, 0, B[0], B[1], tau=2, n_roll=64)
    assert np.isfinite(s)


# --------------------------------------------------------------- hold ------
@pytest.fixture(scope="module")
def live_world():
    """The Stage 6.10 frozen regime. The `world` fixture uses the Stage 6.8
    operating point, which Part G showed is policy-locked -- there, EVERY
    intervention outcome is identically 0.0, so it cannot distinguish two
    intervention semantics from each other."""
    sim = make_simulator(400, 0.4, 0.75)
    res = run_episode(sim, 15, nt=64, record_oracle=False)
    return sim, res


def test_hold_semantics_are_distinct_and_authority_stays_one_shot(live_world):
    """A held intervention is not the same experiment as a one-shot one.

    `task_authority` must remain a ONE-SHOT quantity (force at t, then release),
    and the full-model benchmark must plan with the actuators HELD, because that
    is what it executes: `sim.step` is called with `forced_actions` on every
    step between re-plans. Planning one-shot while executing held makes the
    benchmark strictly weaker than the controller it stands for, which would
    bias a controllability gate toward declaring tasks unsteerable.
    """
    import inspect
    import full_model_benchmark as fmb

    sim, res = live_world
    z = res.z_hist[60]
    I = _interior(sim, res, 60)
    h_star = int((np.bincount(z[I], minlength=4).argmax() + 1) % 4)
    S = [int(x) for x in rt.structural_interface(sim, z, I)][:3]
    assert len(S) == 3

    # Same CRN seed, so any difference is the semantics, not sampling noise.
    one_shot = rt.rollout_alignment(sim, z, I, h_star, 4, S, seed=0, n_roll=256, hold=1)
    held = rt.rollout_alignment(sim, z, I, h_star, 4, S, seed=0, n_roll=256, hold=4)
    assert held != one_shot
    assert held >= one_shot          # holding the target heading cannot hurt it

    # Defaults: authority is one-shot; the benchmark holds for its horizon.
    assert inspect.signature(rt.rollout_alignment).parameters["hold"].default == 1
    assert inspect.signature(rt._expected_alignment_after).parameters["hold"].default == 1
    assert inspect.signature(fmb.optimize).parameters["hold"].default is None
