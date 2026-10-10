"""The Part H gate and the Part I benchmark arm must be the SAME run.

The gate defines the primary episode stratum by whether the full-model benchmark
steers an episode. If the gate's benchmark differs from Part I's in any way that
touches its decisions, episodes get admitted on the strength of a run the
comparison never reproduces -- which is exactly what happened twice (different
candidate pool, rollout count and CRN seed; and before that, a different tracked
collective). This test pins them together.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

CODE = Path(__file__).resolve().parents[1] / "code"
S68 = Path(__file__).resolve().parents[2] / "stage6_8_dynamic_interactions" / "code"
sys.path.insert(0, str(CODE)); sys.path.insert(0, str(S68))

import common_610  # noqa: F401
from common_610 import rotate_cw
from episode_data import make_simulator, run_episode, observation_record
import candidate_detection as cd
import closed_loop as cl
import reference_truth as rt
import run_controllability as rc
import run_closed_loop as rcl


@pytest.fixture(scope="module")
def case():
    sim = make_simulator(400, 0.4, 0.75)
    res = run_episode(sim, 1, nt=rc.T0 + 2, record_oracle=False)
    ok, _ = cd.propose(observation_record(sim, res.z_hist, rc.T0))
    I0 = cl.qualifying_start(ok, 20)
    assert I0 is not None
    h_star = rotate_cw(int(np.bincount(res.z_hist[rc.T0][I0], minlength=4).argmax()))
    return sim, res, I0, h_star


def test_gate_delegates_rather_than_reimplementing():
    import inspect
    src = inspect.getsource(rc.run_benchmark_episode)
    assert "cl.run_arm" in src, "the gate must call Part I's loop, not its own copy"


def test_gate_and_part_i_constants_agree():
    assert rc.REINFER_EVERY == rcl.REINFER_EVERY
    assert rc.THETA == rcl.THETA and rc.Q_SUPPORT == rcl.Q_SUPPORT
    assert rc.T0 == rcl.T0
    assert rc.SUCCESS_HI == rcl.H_THRESHOLD


def test_gate_reproduces_the_part_i_benchmark_arm(case):
    """Same episode, same settings, same stream -> identical per-step alignment.

    Part I runs the benchmark arm first with `budget_schedule=None`, so at a
    common seed the two calls must coincide exactly. The gate's PRODUCTION seed
    is offset (`rc.gate_seed`) so that selection and evaluation use independent
    draws; that is a deliberate choice about randomness, not about code, and
    this test passes the gate's own seed in so it still checks the code path.
    """
    sim, res, I0, h_star = case
    # A short horizon suffices: equivalence is a property of the code path, not
    # of how long it runs, and a 24-step version costs ~7 minutes.
    horizon, frac = 4, 0.5
    gate_recs, _ = rc.run_benchmark_episode(sim, res, I0, h_star, horizon, frac, 1, 20)

    k_act = max(1, int(round(frac * len(rt.structural_interface(
        sim, res.z_hist[rc.T0], I0)))))
    arm = cl.run_arm(sim, res.z_hist[:rc.T0 + 1], "full_model_benchmark",
                     rc.gate_seed(1), h_star,
                     horizon, k_act, I0, rcl.THETA, rcl.Q_SUPPORT,
                     budget_schedule=None, reinfer_every=rcl.REINFER_EVERY,
                     I_init=I0)
    assert len(gate_recs) == len(arm["records"])
    for g, a in zip(gate_recs, arm["records"]):
        assert g["H"] == a["H_current"]
        assert g["I_size"] == a["I_size"]
        assert g["n_act"] == a["n_act"]
