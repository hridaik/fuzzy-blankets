"""Synthetic scenario tests for lineage_v2 (Stage 6.11B item 1). Hand-built
torus configurations, not real simulator trajectories -- each isolates one
qualitative behaviour the repaired tracker must (or must not) exhibit.
Run with: pytest audit/test_lineage_v2_611.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))
import common_611  # noqa: E402,F401  (bootstraps flock_sim/6.8/6.9 onto sys.path)

from flock_sim.model import UV4  # noqa: E402
from lineage_v2_611 import LineageTrackerV2  # noqa: E402

L = 24.0
N = 400   # matches the real system's population density (local_scale is a
          # function of ALL birds' nearest-neighbour spacing, not just the
          # candidate's own members, so a low-N synthetic world understates
          # density and over-states local_scale relative to production)


def base_positions(rng, n=N):
    return rng.random((n, 2)) * L


def blob(rng, centre, n, spread=1.5):
    return (centre + rng.normal(scale=spread, size=(n, 2))) % L


def make_world(rng, member_ids, member_pos, heading=0):
    r = base_positions(rng)
    z = np.zeros(N, dtype=int)
    r[member_ids] = member_pos
    z[member_ids] = heading
    return r, z


def test_ordinary_translation():
    """Same members, small consistent shift -> continues, high prob, no death."""
    rng = np.random.default_rng(1)
    members = np.arange(20)
    tr = LineageTrackerV2(L=L, uv4=UV4)
    r0, z0 = make_world(rng, members, blob(rng, [10, 10], 20))
    tr.start(members, r0, z0, 0)
    r1, z1 = make_world(rng, members, blob(rng, [10.3, 10.1], 20))
    tr.update([members], r1, z1, 1)
    assert len(tr.lineages) == 1
    assert tr.lineages[0].prob > 0.9
    assert tr.lineages[0].dwell == 2
    # SOME death mass is expected even for a clean continuation (p_continue<1
    # almost always under a sigmoid calibration) -- the fix is that it must be
    # SMALL for an obviously-good match, not that it must be exactly zero.
    assert len(tr.dead) <= 1
    if tr.dead:
        assert tr.dead[0].prob < 0.15


def test_gradual_recruitment():
    """Old members fully retained, candidate grows -> continues, high prob."""
    rng = np.random.default_rng(2)
    old = np.arange(15)
    grown = np.arange(18)
    tr = LineageTrackerV2(L=L, uv4=UV4)
    r0, z0 = make_world(rng, old, blob(rng, [5, 5], 15))
    tr.start(old, r0, z0, 0)
    r1, z1 = make_world(rng, grown, blob(rng, [5.1, 5.0], 18))
    tr.update([grown], r1, z1, 1)
    assert len(tr.lineages) == 1
    assert tr.lineages[0].prob > 0.9
    assert set(tr.lineages[0].members.tolist()) == set(grown.tolist())


def test_contraction():
    """Candidate is a pure subset -> R_retain=1 for the subset, continues."""
    rng = np.random.default_rng(3)
    old = np.arange(20)
    shrunk = np.arange(12)
    tr = LineageTrackerV2(L=L, uv4=UV4)
    r0, z0 = make_world(rng, old, blob(rng, [12, 12], 20))
    tr.start(old, r0, z0, 0)
    r1, z1 = make_world(rng, shrunk, blob(rng, [12.1, 12.0], 12))
    tr.update([shrunk], r1, z1, 1)
    assert len(tr.lineages) == 1
    assert tr.lineages[0].prob > 0.85


def test_complete_replacement_with_continuous_field():
    """ZERO material overlap, but the new candidate sits exactly where the
    old field's own bulk motion predicts, with a matching co-moving shape:
    must remain trackable (transport-consistency eligibility), not die."""
    rng = np.random.default_rng(4)
    old = np.arange(20)
    new = np.arange(20, 40)
    tr = LineageTrackerV2(L=L, uv4=UV4)
    centre0 = np.array([8.0, 8.0])
    r0, z0 = make_world(rng, old, blob(rng, centre0, 20, spread=1.2))
    tr.start(old, r0, z0, 0)
    bulk_delta = np.array([0.5, 0.2])
    r1, z1 = make_world(rng, new, blob(rng, centre0 + bulk_delta, 20, spread=1.2))
    tr.update([new], r1, z1, 1)
    assert len(tr.lineages) == 1, "a continuously-translating zero-overlap field must remain trackable"
    lin = tr.lineages[0]
    assert set(lin.members.tolist()) == set(new.tolist())
    assert lin.records[-1]["R_retain_step"] == 0.0
    assert lin.records[-1]["R_F"] > R_F_MIN_TRANSPORT_FOR_TEST


R_F_MIN_TRANSPORT_FOR_TEST = 0.3   # looser than the module's own 0.5 eligibility floor, just to assert "clearly good"


def test_unrelated_spatial_jump_does_not_inherit_identity():
    """ZERO material overlap AND no relation to bulk translation (jumps to
    a random unrelated location, unrelated shape): must NOT be treated as a
    continuation -- the lineage must die instead of teleporting."""
    rng = np.random.default_rng(5)
    old = np.arange(20)
    unrelated = np.arange(20, 35)
    tr = LineageTrackerV2(L=L, uv4=UV4)
    r0, z0 = make_world(rng, old, blob(rng, [3.0, 3.0], 20, spread=1.0))
    tr.start(old, r0, z0, 0)
    # unrelated candidate: far away, uncorrelated with old's bulk motion, and
    # given the OPPOSITE heading so its co-moving field orientation differs too
    r1, z1 = make_world(rng, unrelated, blob(rng, [18.0, 18.0], 15, spread=1.0), heading=1)
    old_lid = tr.lineages[0].lid
    tr.update([unrelated], r1, z1, 1)
    # the ORIGINAL lineage (by lid) must be recorded as dead, with (nearly)
    # its full prior mass -- it must NOT show up continuing as `unrelated`.
    assert len(tr.dead) == 1 and tr.dead[0].lid == old_lid
    assert tr.dead[0].prob > 0.9, "almost all prior mass should route to death, not to the unrelated candidate"
    # `unrelated` MAY still start a fresh lineage (a new lid, dwell=1,
    # genealogy=new_birth) -- that is the intended "unmatched candidates may
    # begin new lineages" behaviour, and is NOT the same as inheriting the
    # old lineage's identity/dwell/genealogy.
    if tr.lineages:
        assert tr.lineages[0].lid != old_lid
        assert tr.lineages[0].dwell == 1
        assert tr.lineages[0].genealogy == [("new_birth", 0.0)]


def test_split():
    """One prior lineage, two viable candidates this step -> branches into
    two DISTINCT live lineages (not coalesced, since their member sets differ),
    total probability conserved (modulo any death share)."""
    rng = np.random.default_rng(6)
    old = np.arange(30)
    half_a = np.arange(15)
    half_b = np.arange(15, 30)
    tr = LineageTrackerV2(L=L, uv4=UV4)
    r0, z0 = make_world(rng, old, blob(rng, [10, 10], 30, spread=2.0))
    tr.start(old, r0, z0, 0)
    r1, z1 = make_world(rng, np.concatenate([half_a, half_b]),
                          np.concatenate([blob(rng, [9.5, 10], 15, spread=0.8),
                                           blob(rng, [10.5, 10], 15, spread=0.8)]))
    tr.update([half_a, half_b], r1, z1, 1)
    assert len(tr.lineages) == 2
    # `self.lineages` is a distribution CONDITIONAL ON the lineage having
    # survived (renormalized among live branches, as in lineage_611, for
    # comparability) -- the point of the death mechanism is not that this
    # sums to <1 including dead, but that dwell/qualification distinguish a
    # confident split from a forced one; see test_ordinary_translation's
    # death-mass check and DWELL_CONTINUITY_MIN for that.
    total = sum(l.prob for l in tr.lineages)
    assert abs(total - 1.0) < 1e-6


def test_merge():
    """Two DIFFERENT prior lineages both match the SAME present candidate
    this step -> coalesced into ONE lineage, prob = sum of both parents'
    contributions, genealogy records both parents."""
    rng = np.random.default_rng(7)
    a_members = np.arange(10)
    b_members = np.arange(10, 20)
    merged = np.arange(20)
    tr_a = LineageTrackerV2(L=L, uv4=UV4)
    r0, z0 = make_world(rng, a_members, blob(rng, [5, 5], 10, spread=0.8))
    tr_a.start(a_members, r0, z0, 0)
    tr_b = LineageTrackerV2(L=L, uv4=UV4)
    tr_b.lineages = [tr_a._spawn(b_members, r0, z0, 0, prob=1.0, genealogy=[("root", 1.0)])]

    # simulate one combined tracker holding both as live lineages pre-merge
    tr = LineageTrackerV2(L=L, uv4=UV4)
    tr.lineages = [
        tr_a._spawn(a_members, r0, z0, 0, prob=0.6, genealogy=[("root", 0.6)]),
        tr_a._spawn(b_members, r0, z0, 0, prob=0.4, genealogy=[("root", 0.4)]),
    ]
    r1, z1 = make_world(rng, merged, blob(rng, [5.2, 5.1], 20, spread=1.0))
    tr.update([merged], r1, z1, 1)
    assert len(tr.lineages) == 1
    lin = tr.lineages[0]
    assert set(lin.members.tolist()) == set(merged.tolist())
    assert len(lin.genealogy) == 2
    assert abs(lin.prob - 1.0) < 0.05   # both parents' mass, minus any small death share


def test_temporary_missed_detection():
    """One step with ZERO candidates at all (detector hiccup) -> lineage
    carried forward unchanged, not killed."""
    rng = np.random.default_rng(8)
    members = np.arange(20)
    tr = LineageTrackerV2(L=L, uv4=UV4)
    r0, z0 = make_world(rng, members, blob(rng, [7, 7], 20))
    tr.start(members, r0, z0, 0)
    prob_before = tr.lineages[0].prob
    tr.update([], r0, z0, 1)
    assert len(tr.lineages) == 1
    assert tr.lineages[0].prob == prob_before
    assert tr.lineages[0].status == "active"

    # detector recovers next step, ordinary continuation resumes normally
    r2, z2 = make_world(rng, members, blob(rng, [7.3, 7.1], 20))
    tr.update([members], r2, z2, 2)
    assert len(tr.lineages) == 1
    assert tr.lineages[0].prob > 0.85


def test_unmatched_candidate_starts_new_lineage():
    """A candidate ineligible for every existing lineage seeds a fresh one
    (prob starts at 0, competes on equal footing from the next step on)."""
    rng = np.random.default_rng(9)
    old = np.arange(15)
    unrelated_new = np.arange(15, 30)
    tr = LineageTrackerV2(L=L, uv4=UV4)
    r0, z0 = make_world(rng, old, blob(rng, [2.0, 2.0], 15, spread=0.8))
    tr.start(old, r0, z0, 0)
    r1, z1 = make_world(rng, np.concatenate([old, unrelated_new]),
                          np.concatenate([blob(rng, [2.1, 2.0], 15, spread=0.8),
                                           blob(rng, [20.0, 20.0], 15, spread=0.8)]))
    old_cont = old  # continues normally
    tr.update([old_cont, unrelated_new], r1, z1, 1)
    assert len(tr.lineages) == 2
    ids = {frozenset(int(x) for x in l.members): l for l in tr.lineages}
    new_key = frozenset(int(x) for x in unrelated_new)
    assert new_key in ids, "the unrelated candidate must survive as ITS OWN lineage, not vanish"
    new_lin = ids[new_key]
    assert new_lin.genealogy == [("new_birth", 0.0)], (
        "an unrelated-location, same-heading blob can still pass the loose "
        "R_F>=0.5 shape-similarity eligibility bar by coincidence (R_F is a "
        "centroid-relative SHAPE comparison, not a displacement-magnitude "
        "check) -- if this fires, the transport-magnitude gate did not "
        "reject it; see transport_ok in the eval table for this pair.")


def test_coalescing_duplicate_present_states():
    """If two branch-histories of ONE tree would independently reach the
    SAME present member set, they must be merged into a single lineage with
    summed probability -- never reported as two competing hypotheses."""
    rng = np.random.default_rng(10)
    a = np.arange(12)
    b = np.arange(12, 24)   # a sibling branch of the SAME tree, different current members
    same_target = np.arange(30, 42)   # both a and b happen to viably match this exact candidate
    tr = LineageTrackerV2(L=L, uv4=UV4)
    r0, z0 = make_world(rng, np.concatenate([a, b]),
                          np.concatenate([blob(rng, [1.0, 1.0], 12, spread=0.5),
                                           blob(rng, [1.0, 1.0], 12, spread=0.5)]))
    tr.lineages = [
        tr._spawn(a, r0, z0, 0, prob=0.7, genealogy=[("root", 0.7)]),
        tr._spawn(b, r0, z0, 0, prob=0.3, genealogy=[("root", 0.3)]),
    ]
    # force both to have identical (rho, m, centre, d_norm) so they score
    # identically against the same target -- simplest way to guarantee both
    # independently find it viable
    tr.lineages[1].rho, tr.lineages[1].m = tr.lineages[0].rho, tr.lineages[0].m
    tr.lineages[1].centre, tr.lineages[1].d_norm = tr.lineages[0].centre, tr.lineages[0].d_norm
    r1, z1 = make_world(rng, same_target, blob(rng, [1.1, 1.0], 12, spread=0.5))
    tr.update([same_target], r1, z1, 1)
    assert len(tr.lineages) == 1
    assert len(tr.lineages[0].genealogy) == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
