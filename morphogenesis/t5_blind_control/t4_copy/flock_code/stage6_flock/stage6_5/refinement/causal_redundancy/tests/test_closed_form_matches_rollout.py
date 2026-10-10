"""Numerical cross-check: the closed-form one-step distribution (natural and
do-intervened) matches empirical frequencies from literal stochastic
rollouts of the real simulator, within Monte-Carlo tolerance. A4/A5 frame
exactness as conditional ("if the exact/MC distributions make KL stable"),
so this test is the evidence that condition holds here.

IMPORTANT semantic note: `do(z_j := z'_j)` here means bird j's CURRENT
heading at time t is counterfactually different (so its neighbours react to
a different observed heading) -- matching A2's "create counterfactual states
by independently changing its heading while holding the rest of X_t fixed."
This is NOT the same as `flock_sim.simulation.run_simulation`'s own
`interventions={t: {bird: forced_action}}` mechanism, which forces bird j's
chosen ACTION (i.e. controls j's OWN next heading via Bu[:, forced_action],
an actuation used for control elsewhere in this repo) and leaves j's
CURRENT heading -- and hence what j's neighbours react to -- untouched. The
correct Monte-Carlo cross-check for a state counterfactual is therefore to
run the simulator from a modified INITIAL state with no forced actions at
all, which is what this test does.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from flock_sim.lattice import Lattice  # noqa: E402
from flock_sim.model import ModelParams  # noqa: E402
from flock_sim.simulation import run_simulation  # noqa: E402
from exact_intervention import default_precomputed_model, next_heading_dist_all, do_next_heading_dist_all  # noqa: E402

N_ROLLOUT = 2000
TOL = 0.06  # ~5 sigma at N=2000 for a worst-case Bernoulli(0.5) cell


def _empirical_dist(samples: np.ndarray, nu: int = 4) -> np.ndarray:
    counts = np.bincount(samples, minlength=nu).astype(float)
    return counts / counts.sum()


def test_natural_closed_form_matches_rollout_frequencies():
    lattice = Lattice(nn=100, nh=8)
    pm = default_precomputed_model(ModelParams())
    rng = np.random.default_rng(1)
    z = rng.integers(0, 4, size=100)
    I0 = np.array([44, 45, 54, 55])

    closed_form = next_heading_dist_all(pm, lattice, z)[I0]

    next_samples = np.zeros((N_ROLLOUT, len(I0)), dtype=int)
    for r in range(N_ROLLOUT):
        res = run_simulation(nn=100, nt=1, seed=500_000 + r, init_z=z, lattice=lattice)
        next_samples[r] = res.z_hist[1][I0]

    for k in range(len(I0)):
        emp = _empirical_dist(next_samples[:, k])
        assert np.max(np.abs(emp - closed_form[k])) < TOL, (emp, closed_form[k])


def test_do_intervention_closed_form_matches_rollout_frequencies():
    lattice = Lattice(nn=100, nh=8)
    pm = default_precomputed_model(ModelParams())
    rng = np.random.default_rng(2)
    z = rng.integers(0, 4, size=100)
    I0 = np.array([44, 45, 54, 55])
    j, z_prime = 43, int((z[43] + 1) % 4)  # a true lattice-neighbor of bird 44

    closed_form = do_next_heading_dist_all(pm, lattice, z, j, z_prime)[I0]

    z_do = z.copy()
    z_do[j] = z_prime
    next_samples = np.zeros((N_ROLLOUT, len(I0)), dtype=int)
    for r in range(N_ROLLOUT):
        res = run_simulation(nn=100, nt=1, seed=600_000 + r, init_z=z_do, lattice=lattice)
        next_samples[r] = res.z_hist[1][I0]

    for k in range(len(I0)):
        emp = _empirical_dist(next_samples[:, k])
        assert np.max(np.abs(emp - closed_form[k])) < TOL, (emp, closed_form[k])
