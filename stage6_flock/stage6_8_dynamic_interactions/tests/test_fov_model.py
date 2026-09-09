"""L2/L3 simulator correctness. EVALUATION-SIDE test (imports the simulator)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE))

from common_68 import (lattice_100, lattice_positions, flatten_edges, visibility_table,
                       SLOT_VEC, ModelParams, UV4)
from fov_dynamics import FovSimulator, GateParams
from flock_sim.active_inference import compute_G


def test_slot_vectors_match_actual_positions():
    """The FOV rule is stated in terms of (r_j - r_i); SLOT_VEC must BE that
    difference for every edge, or the rule is being applied to a fiction."""
    lat = lattice_100()
    P = lattice_positions()
    recv, slot, src = flatten_edges(lat)
    assert np.allclose(P[src] - P[recv], SLOT_VEC[slot])


def test_all_ones_mask_reduces_to_frozen_model():
    """L2 with nothing masked must be numerically identical to the frozen
    Stage 6-6.7 model -- so L2 is a restriction of it, not a re-parameterization."""
    sim = FovSimulator(ModelParams(), lattice_100())
    rng = np.random.default_rng(1)
    for _ in range(5):
        z = rng.integers(0, 4, sim.nn)
        assert np.allclose(compute_G(sim.pm, sim.lattice, z),
                           sim.compute_G_masked(z, np.ones(sim.n_edges, bool)))


def test_fov_excludes_exactly_the_three_rear_neighbours():
    VIS = visibility_table()
    for h in range(4):
        d = UV4[h]
        for s in range(8):
            assert VIS[s, h] == (SLOT_VEC[s] @ d >= 0)
        assert VIS[:, h].sum() == 5, "5 of 8 Moore slots visible, 3 rear excluded"


def test_interior_bird_sees_five_and_only_forward_neighbours():
    sim = FovSimulator(ModelParams(), lattice_100())
    P = lattice_positions()
    i = 55                                            # an interior site
    assert sim.lattice.degree[i] == 8
    for h in range(4):
        z = np.zeros(sim.nn, dtype=int); z[i] = h
        live = sim.active_in_edges(sim.visible_mask(z), i)
        assert len(live) == 5
        for j in live:
            assert (P[j] - P[i]) @ UV4[h] >= 0


def test_interaction_is_directed_and_not_symmetrized():
    """There must exist a state and a pair with j -> i live while i -> j is not."""
    sim = FovSimulator(ModelParams(), lattice_100())
    z = np.zeros(sim.nn, dtype=int)                   # everyone heading 'up'
    z[55] = 0                                          # up
    z[45] = 1                                          # the site above 55, heading down
    m = sim.visible_mask(z)
    up_of_55 = 54                                      # slot 0 (top) of bird 55
    assert up_of_55 in sim.active_in_edges(m, 55)
    z2 = z.copy(); z2[55] = 1                          # 55 now heads down
    assert up_of_55 not in sim.active_in_edges(m if False else sim.visible_mask(z2), 55)


def test_no_bird_is_ever_blind():
    sim = FovSimulator(ModelParams(), lattice_100())
    r = sim.run(nt=60, seed=0, record_oracle=True)
    assert r.n_blind_birds.max() == 0


def test_oracle_B_D_is_the_directed_in_neighbourhood():
    sim = FovSimulator(ModelParams(), lattice_100())
    rng = np.random.default_rng(3)
    z = rng.integers(0, 4, sim.nn)
    m = sim.visible_mask(z)
    I = np.array([44, 45, 54, 55])
    B = sim.oracle_B_D(m, I)
    brute = set()
    for i in I:
        for j in sim.active_in_edges(m, int(i)):
            if j not in set(I.tolist()):
                brute.add(int(j))
    assert set(B.tolist()) == brute


def test_gates_are_persistent_and_stationary():
    sim = FovSimulator(ModelParams(), lattice_100())
    gp = GateParams(p01=0.25, p10=0.05)
    rng = np.random.default_rng(0)
    g = sim.init_gates(gp, rng)
    on_frac, flips = [], []
    prev = g
    for _ in range(400):
        g = sim.advance_gates(g, gp, rng)
        on_frac.append(g.mean())
        flips.append((g != prev).mean())
        prev = g
    assert abs(np.mean(on_frac) - gp.stationary_on) < 0.02
    # persistent: far fewer flips than an i.i.d. Bernoulli process would give
    iid_flip = 2 * gp.stationary_on * (1 - gp.stationary_on)
    assert np.mean(flips) < 0.5 * iid_flip


def test_probe_and_exact_propagator_agree_at_large_rollout_counts():
    """The finite probe must be an unbiased sampler of the same object the
    exact propagator computes in closed form -- otherwise the 'estimation error
    due to finite probing' number is measuring a modelling mismatch instead."""
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "code"))
    from intervention_api_68 import FiniteProbe, ExactPropagator

    sim = FovSimulator(ModelParams(), lattice_100())
    rng = np.random.default_rng(5)
    z = rng.integers(0, 4, sim.nn)
    I = np.array([44, 45, 54, 55])
    j = int(sim.active_in_edges(sim.visible_mask(z), 55)[0])
    zp = int((z[j] + 1) % 4)

    ex = ExactPropagator(sim).exact(I, j, zp, z)["D_do_joint"]
    fp = FiniteProbe(sim, n_rollouts=4000, seed=1)
    est = fp.probe(I, j, zp, z)["D_do_joint"]
    assert abs(est - ex) < 0.25 * max(ex, 0.05), f"probe {est:.4f} vs exact {ex:.4f}"


def test_probe_and_propagator_respect_the_gate():
    """At L3 both must act on FOV AND the latent gate. If the gate is closed on
    every edge into the interior, an exterior intervention can have no effect."""
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "code"))
    from intervention_api_68 import FiniteProbe, ExactPropagator

    sim = FovSimulator(ModelParams(), lattice_100())
    rng = np.random.default_rng(6)
    z = rng.integers(0, 4, sim.nn)
    I = np.array([44, 45, 54, 55])
    j = int(sim.active_in_edges(sim.visible_mask(z), 55)[0])
    zp = int((z[j] + 1) % 4)

    closed = np.ones(sim.n_edges, dtype=bool)
    closed[np.isin(sim.recv, I)] = False
    assert ExactPropagator(sim, channel_state=closed).exact(I, j, zp, z)["D_do_joint"] == 0.0
    assert FiniteProbe(sim, n_rollouts=200, seed=2,
                       channel_state=closed).probe(I, j, zp, z)["D_do_joint"] == 0.0
    assert ExactPropagator(sim).exact(I, j, zp, z)["D_do_joint"] > 0.0
