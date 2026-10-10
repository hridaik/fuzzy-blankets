"""Task brief section 33, "Control"."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common_66 import lattice_100, make_pulse, rotate_cw, rotate_ccw  # noqa: E402
from archetypes import opposite_heading, balanced_rotating_targets, build_condition, CONDITIONS  # noqa: E402
from windowed_data import run_condition_replicates  # noqa: E402
import flock_sim.active_inference as ai  # noqa: E402
from flock_sim.active_inference import build_model  # noqa: E402
from flock_sim.model import ModelParams  # noqa: E402

CANONICAL_I0 = np.array([7, 8, 9, 16, 17, 18, 19, 26, 27, 28, 29, 36, 37, 38, 39, 47, 48, 49, 58, 59])


def test_geometric_opposite_mapping_matches_uv4():
    # up(0)<->down(1), left(2)<->right(3) -- hand-derived from UV4, NOT (h+2)%4.
    assert opposite_heading(0) == 1
    assert opposite_heading(1) == 0
    assert opposite_heading(2) == 3
    assert opposite_heading(3) == 2


def test_naive_index_arithmetic_is_not_the_opposite():
    # (h+2)%4 for h=0 gives 2 (left), which is NOT down -- the exact failure
    # mode task brief section 11.D warns against. On this heading map naive
    # modular arithmetic disagrees with the true geometric opposite for
    # every h (up/down and left/right are adjacent index pairs, not
    # antipodal ones).
    for h in range(4):
        naive = (h + 2) % 4
        assert naive != opposite_heading(h), f"h={h}: naive {naive} accidentally matches true opposite"


def test_opposite_is_involution():
    for h in range(4):
        assert opposite_heading(opposite_heading(h)) == h


def test_opposite_equals_double_rotation():
    for h in range(4):
        assert opposite_heading(h) == rotate_cw(rotate_cw(h))
        assert opposite_heading(h) == rotate_ccw(rotate_ccw(h))


def test_balanced_rotating_targets_approximately_uniform():
    nodes = np.arange(20)
    sched = balanced_rotating_targets(nodes, t0=0, t_u=20)
    for t, assignment in sched.items():
        counts = np.bincount(list(assignment.values()), minlength=4)
        assert counts.max() - counts.min() <= 1   # 20 nodes / 4 headings = exactly 5 each
        assert counts.sum() == len(nodes)


def test_balanced_rotating_targets_each_node_cycles_all_headings():
    nodes = np.arange(8)
    sched = balanced_rotating_targets(nodes, t0=0, t_u=8)
    for n in nodes:
        seen = {sched[t][int(n)] for t in range(8)}
        assert seen == {0, 1, 2, 3}


def test_control_hook_overrides_applied_action_not_z_new_directly():
    """Reuses flock_sim.active_inference.step directly (the same function
    V1-V3 use). A forced bird's applied_action must equal the forced
    heading exactly every time. z_new is still SAMPLED through the noisy
    transition kernel Bu[:, applied_action] rather than being a raw
    overwrite of z -- but at the frozen precB=15, Bu's columns are so
    sharply peaked that z_new==forced_heading in practice on almost every
    draw, so asserting empirical variation across ~60 samples would be a
    flaky, precision-dependent test. Instead verify the mechanism directly:
    (a) applied_action is exactly the forced value every time and is
    distinct from the bird's own free-energy-driven natural_action when
    those differ; (b) Bu[:, forced] is a genuine (if extremely peaked)
    probability distribution, not a hard one-hot -- i.e. the sampling step
    is still present, only numerically close to deterministic."""
    lattice = lattice_100()
    pm = build_model(ModelParams())
    forced = {0: 3}   # force bird 0 toward heading 3 ("right")
    natural_ever_differs_from_applied = False
    for seed in range(60):
        rng = np.random.default_rng(seed)
        z = np.random.default_rng(seed + 1000).integers(0, 4, size=100)
        out = ai.step(pm, lattice, z, rng, forced_actions=forced)
        assert out["applied_action"][0] == 3
        assert out["was_overridden"][0]
        if out["natural_action"][0] != out["applied_action"][0]:
            natural_ever_differs_from_applied = True
    assert natural_ever_differs_from_applied, (
        "the bird's own free-energy-derived natural_action was always already 3 -- "
        "cannot distinguish an override from a coincidence in this sample")

    col = pm.Bu[:, 3]
    assert col.sum() == pytest.approx(1.0)
    assert col[3] < 1.0, "Bu[:,forced] is a hard one-hot -- z_new would be a deterministic overwrite"
    assert (col[np.arange(4) != 3] > 0).all(), "off-target categories should retain nonzero (if tiny) mass"


def test_build_condition_reuses_make_pulse_for_shell_only():
    lattice = lattice_100()
    cond = build_condition(lattice, CANONICAL_I0, h_star=0, condition="shell_only", t0=0, t_u=20)
    expected = make_pulse(cond["shell"], 0, t0=0, t_u=20)
    assert cond["interventions"] == expected


def test_common_random_numbers_pairing_is_deterministic_and_reproducible():
    lattice = lattice_100()
    z0 = np.zeros(100, dtype=int)
    a = run_condition_replicates(z0, lattice, None, nt=10, n_rep=5, seed_offset=999_000)
    b = run_condition_replicates(z0, lattice, None, nt=10, n_rep=5, seed_offset=999_000)
    assert np.array_equal(a, b)


def test_all_conditions_defined_and_buildable():
    lattice = lattice_100()
    for condition in CONDITIONS:
        cond = build_condition(lattice, CANONICAL_I0, h_star=0, condition=condition, f_E=1.0)
        assert cond["condition"] == condition
