import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from flock_sim.lattice import Lattice
from flock_sim.model import ModelParams
from flock_sim.active_inference import build_model, compute_G, policy_posterior, step
from flock_sim.simulation import run_simulation, init_headings


def test_G_prefers_action_matching_unanimous_neighbors():
    lat = Lattice(nn=9, nh=8)
    pm = build_model(ModelParams())
    center = 4  # 3x3 grid, center bird (0-based row1,col1 -> linear = 1*3+1=4)
    z = np.zeros(9, dtype=int)
    z[:] = 3  # everyone (including center) heading "right"=3, arbitrary baseline
    z[lat.neighbor_ids[center]] = 3  # all neighbors heading right
    G = compute_G(pm, lat, z)
    assert np.argmax(G[center]) == 3, "center bird's EFE should favor matching its neighbors' unanimous heading"


def test_G_independent_of_own_current_heading():
    # Structural property verified analytically in active_inference.py docstring:
    # G(u) must not depend on the bird's own current heading (only on neighbors').
    lat = Lattice(nn=9, nh=8)
    pm = build_model(ModelParams())
    center = 4
    z1 = np.zeros(9, dtype=int)
    z1[lat.neighbor_ids[center]] = 2
    z1[center] = 0
    z2 = z1.copy()
    z2[center] = 3  # change ONLY the center bird's own heading
    G1 = compute_G(pm, lat, z1)
    G2 = compute_G(pm, lat, z2)
    assert np.allclose(G1[center], G2[center])


def test_policy_posterior_sums_to_one():
    pm = build_model(ModelParams())
    G = np.random.default_rng(1).normal(size=(20, 4))
    ut = policy_posterior(pm, G)
    assert np.allclose(ut.sum(axis=1), 1.0)
    assert np.all(ut >= 0)


def test_step_reproducible_with_same_seed():
    lat = Lattice(nn=25, nh=8)
    pm = build_model(ModelParams())
    rng1 = np.random.default_rng(42)
    z = init_headings(25, 4, rng1)
    out1 = step(pm, lat, z, np.random.default_rng(7))

    rng2 = np.random.default_rng(42)
    z2 = init_headings(25, 4, rng2)
    out2 = step(pm, lat, z2, np.random.default_rng(7))
    assert np.array_equal(out1["z_new"], out2["z_new"])
    assert np.array_equal(out1["natural_action"], out2["natural_action"])


def test_intervention_overrides_applied_action_but_not_natural():
    lat = Lattice(nn=25, nh=8)
    pm = build_model(ModelParams())
    rng = np.random.default_rng(3)
    z = init_headings(25, 4, rng)
    forced = {0: 2, 1: 2}
    out = step(pm, lat, z, np.random.default_rng(9), forced_actions=forced)
    assert out["applied_action"][0] == 2 and out["applied_action"][1] == 2
    assert out["was_overridden"][0] and out["was_overridden"][1]
    assert not out["was_overridden"][2]


def test_full_simulation_runs_and_is_reproducible():
    res1 = run_simulation(nn=25, nt=20, seed=123)
    res2 = run_simulation(nn=25, nt=20, seed=123)
    assert np.array_equal(res1.z_hist, res2.z_hist)
    res3 = run_simulation(nn=25, nt=20, seed=124)
    assert not np.array_equal(res1.z_hist, res3.z_hist)


def test_forced_pulse_pulls_actuator_toward_target():
    from flock_sim.interventions import make_pulse
    lat = Lattice(nn=25, nh=8)
    forced = make_pulse(actuators=[0, 1, 2], h_star=1, t0=0, t_u=10)
    res = run_simulation(nn=25, nt=10, seed=5, interventions=forced, lattice=lat)
    # actuator birds should be heading 1 (down) at the end of the pulse most of the time
    assert (res.z_hist[-1, [0, 1, 2]] == 1).mean() >= 2 / 3
