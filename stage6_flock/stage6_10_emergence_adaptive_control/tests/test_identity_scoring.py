"""Part J -- the validity envelope must actually catch the four failure modes.

Each test plants a lineage exhibiting exactly one failure mode and asserts that
the conjunctive score rejects it EVEN THOUGH the task was achieved. A scoring
rule that only checks the heading would pass every one of these.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import common_610  # noqa: F401  (sets sys.path)
import identity_scoring as isc

L = 20
H_OK = 0.95          # every planted lineage "achieves" the heading target
THRESH = 0.60


def block(r0, c0, h, w):
    return np.array(sorted(int(c * L + r) for r in range(r0, r0 + h)
                           for c in range(c0, c0 + w)))


def zfull(members, heading=1, other=0):
    z = np.full(L * L, other, dtype=int)
    z[members] = heading
    return z


def lineage(seqs, heading=1):
    return isc.lineage_statistics(seqs, [zfull(s, heading) for s in seqs], L)


@pytest.fixture
def env():
    """Envelope from 'uncontrolled' lineages that drift materially but stay a
    single coherent clump of stable size -- the behaviour actually observed at
    the frozen regime."""
    ref = []
    for k in range(20):
        seqs = [block(4 + (t + k) % 3, 4 + t // 2, 6, 6) for t in range(12)]
        ref.append(lineage(seqs))
    return isc.build_envelope(ref)


def test_intact_lineage_passes(env):
    seqs = [block(4 + t % 3, 4 + t // 2, 6, 6) for t in range(12)]
    sc = isc.conjunctive_success(H_OK, lineage(seqs), env, THRESH)
    assert sc["task_met"] and sc["identity_valid"] and sc["success"]


def test_shrink_to_win_is_rejected(env):
    """Contracts onto an easy core while holding the heading."""
    seqs = [block(4, 4, 6, 6)] + [block(4, 4, max(2, 6 - t), max(2, 6 - t))
                                  for t in range(1, 12)]
    sc = isc.conjunctive_success(H_OK, lineage(seqs), env, THRESH)
    assert sc["task_met"] and not sc["success"]
    assert "shrink-to-win" in sc["failure_modes"]


def test_splitting_is_rejected(env):
    """Fragments into two cardinally disconnected pieces."""
    whole = block(4, 4, 6, 6)
    split = np.array(sorted(set(block(4, 4, 6, 2).tolist()) | set(block(4, 10, 6, 2).tolist())))
    seqs = [whole] * 6 + [split] * 6
    sc = isc.conjunctive_success(H_OK, lineage(seqs), env, THRESH)
    assert sc["task_met"] and not sc["success"]
    assert "splitting" in sc["failure_modes"]


def test_destruction_and_replacement_is_rejected(env):
    """The tracked label jumps to a disjoint set of the same size and shape."""
    seqs = [block(2, 2, 6, 6)] * 6 + [block(12, 12, 6, 6)] * 6
    st = lineage(seqs)
    sc = isc.conjunctive_success(H_OK, st, env, THRESH)
    assert sc["task_met"] and not sc["success"]
    # caught by the step-continuity chain: the jump step has Jaccard 0
    assert st["min_step_jaccard"] == 0.0
    assert "lineage discontinuity" in sc["failure_modes"]


def test_material_only_persistence_is_rejected(env):
    """Membership is perfectly preserved but the collective is incoherent."""
    seqs = [block(4, 4, 6, 6)] * 12
    z_seq = []
    rng = np.random.default_rng(0)
    for s in seqs:
        z = np.zeros(L * L, dtype=int)
        z[s] = rng.integers(0, 4, size=len(s))     # headings scattered
        z_seq.append(z)
    st = isc.lineage_statistics(seqs, z_seq, L)
    sc = isc.conjunctive_success(H_OK, st, env, THRESH)
    assert sc["task_met"] and not sc["success"]
    assert "material-only persistence" in sc["failure_modes"]


def test_task_failure_alone_is_reported_separately(env):
    """A valid lineage that missed the heading is a task failure, not an
    identity failure -- the two must not be collapsed."""
    seqs = [block(4 + t % 3, 4 + t // 2, 6, 6) for t in range(12)]
    sc = isc.conjunctive_success(0.10, lineage(seqs), env, THRESH)
    assert not sc["task_met"] and sc["identity_valid"] and not sc["success"]
    assert sc["failure_modes"] == []


def test_envelope_is_one_sided(env):
    """Being MORE coherent than uncontrolled lineages is never penalised."""
    seqs = [block(4, 4, 6, 6)] * 12
    st = lineage(seqs)
    assert isc.identity_valid(st, env)["valid"]
