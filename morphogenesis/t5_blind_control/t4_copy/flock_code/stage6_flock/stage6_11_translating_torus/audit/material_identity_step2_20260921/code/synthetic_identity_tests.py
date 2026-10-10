"""Step 2, identity_validation.md's known-history identity tests (task
brief §7, tests A-G). These operate directly on ForwardMaterialTrace611's
abstract candidate-set interface (no simulator dependency needed for A/B/C/
E/F/G; D additionally checks that the underlying set-based rule is immune
to a torus-wrap-style relabeling, since it never looks at position at all).

These are NOT calibration data (calibration is `calibrate_identity_rule.py`,
using real uncontrolled trajectories) -- they are a small, hand-constructed
suite expressing the identity THEORY directly, run against the FROZEN rule
(loaded from `identity_rule_calibration.json` after `calibrate_identity_rule.py`
has run), to confirm the frozen rule actually implements the stated
behavioral contract before it is ever applied to the five historical seeds.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forward_material_trace_611 import ForwardMaterialTrace611, RULE_FAMILY_BUILDERS

OUT = Path(__file__).resolve().parents[1] / "data"


def base_population(n=40, offset=0):
    return set(range(offset, offset + n))


def run_test(name, rule, steps, expect_check):
    """`steps` is a list of candidate-list-per-step (each a list of sets).
    Returns (passed, detail)."""
    tr = ForwardMaterialTrace611(rule)
    tr.start(0, steps[0][0])  # seed from the first step's designated true target (index 0 by convention)
    decisions = [tr.history[0]]
    for t, cands in enumerate(steps[1:], start=1):
        d = tr.step(t, cands)
        decisions.append(d)
    ok, detail = expect_check(decisions)
    return ok, detail, decisions


def test_A_stable_continuation(rule):
    """Same ~40-bird flock, small detector noise (+-2 members) each step,
    for 10 steps. Expected: continuation preserved throughout."""
    pop = base_population(40, 0)
    steps = []
    import random
    rng = random.Random(1)
    cur = set(pop)
    for t in range(10):
        noisy = set(cur)
        # +-2 member jitter (detector noise), never full replacement
        drop = rng.sample(sorted(noisy), 2) if len(noisy) > 2 else []
        for x in drop:
            noisy.discard(x)
        add_candidates = set(range(1000 + t * 10, 1000 + t * 10 + 2))
        noisy |= add_candidates
        steps.append([noisy])   # single candidate per step
        cur = noisy

    def check(decisions):
        ok = all(d.status == "continuing" for d in decisions)
        return ok, f"statuses={[d.status for d in decisions]}"
    return run_test("A_stable_continuation", rule, steps, check)


def test_B_gradual_turnover(rule):
    """40-bird flock, loses 4 and gains 4 members per step (10% turnover),
    for 20 steps -- cumulative overlap with the ORIGINAL cohort eventually
    drops below any reasonable single-step threshold, but STEP-TO-STEP
    overlap stays high throughout. Expected: local (step-to-step)
    continuation preserved at every step."""
    pop = set(range(0, 40))
    steps = []
    cur = set(pop)
    next_id = 10000
    for t in range(20):
        nxt = set(cur)
        losers = sorted(nxt)[:4]
        for x in losers:
            nxt.discard(x)
        gainers = set(range(next_id, next_id + 4))
        next_id += 4
        nxt |= gainers
        steps.append([nxt])
        cur = nxt

    def check(decisions):
        ok = all(d.status == "continuing" for d in decisions)
        cumulative_overlap_with_origin = len(pop & decisions[-1].accepted_members) / len(pop)
        detail = (f"statuses={[d.status for d in decisions]}; "
                  f"cumulative overlap with t=0 cohort at t=19: {cumulative_overlap_with_origin:.2f} (expected low)")
        return ok, detail
    return run_test("B_gradual_turnover", rule, steps, check)


def test_C_abrupt_replacement(rule):
    """At t=1, the true flock vanishes; a DIFFERENT, same-size, zero-overlap
    flock appears alongside nothing else. Expected: must NOT inherit the
    target label (either unresolved or dead, never `continuing` onto the
    unrelated set)."""
    true_flock = set(range(0, 40))
    unrelated_flock = set(range(500, 540))
    steps = [[true_flock], [unrelated_flock]]

    def check(decisions):
        d1 = decisions[1]
        ok = d1.status != "continuing"
        return ok, f"t=1 status={d1.status} (must not be 'continuing' onto the unrelated set)"
    return run_test("C_abrupt_replacement", rule, steps, check)


def test_D_toroidal_crossing(rule):
    """Pure membership rule: torus wrapping affects POSITIONS, not bird IDs
    or set membership, so a materially-identical flock crossing the
    periodic boundary must be indistinguishable, at this rule's level, from
    ordinary continuation -- demonstrating (not merely asserting) that a
    membership-first rule is immune to a class of display artifact that a
    naive centroid-distance rule would not be immune to."""
    pop = set(range(0, 40))
    steps = [[pop], [pop], [pop]]  # identical membership; "crossing" is a position-only event, not modeled at this layer

    def check(decisions):
        ok = all(d.status == "continuing" and d.accepted_members == pop for d in decisions[1:])
        return ok, f"membership identical to origin at every step; statuses={[d.status for d in decisions]}"
    return run_test("D_toroidal_crossing", rule, steps, check)


def test_E_temporary_missed_detection(rule):
    """Target absent from candidate output for 2 steps (within the
    tracker's missed_detection_horizon=3), then reappears with mild
    turnover. Expected: `unresolved` during the gap, `continuing` again
    once a qualifying candidate reappears -- NOT a silent switch to
    whatever unrelated candidate WAS present during the gap."""
    true_flock = set(range(0, 40))
    distractor = set(range(700, 730))
    steps = [
        [true_flock],
        [distractor],       # miss 1 -- true flock not detected this step
        [distractor],       # miss 2
        [true_flock - {0, 1} | {900, 901}],  # reappears, mild turnover
    ]

    def check(decisions):
        ok = (decisions[1].status == "unresolved" and decisions[2].status == "unresolved"
              and decisions[3].status == "continuing"
              and decisions[3].accepted_members != distractor)
        return ok, f"statuses={[d.status for d in decisions]}"
    return run_test("E_temporary_missed_detection", rule, steps, check)


def test_F_split(rule):
    """Previous target materially splits into two substantial candidates
    (each retaining >=40% of the original 40-bird cohort). Expected:
    split_flag=True on the winning decision; the tracker still names ONE
    continuation (largest absolute retained count) but the ambiguity must
    be visible, not silently hidden."""
    prev = set(range(0, 40))
    half_a = set(range(0, 22))       # 22/40 retained
    half_b = set(range(18, 40))      # 22/40 retained (overlaps half_a slightly, both substantial)
    steps = [[prev], [half_a, half_b]]

    def check(decisions):
        d1 = decisions[1]
        ok = d1.split_flag and d1.status == "continuing"
        return ok, f"t=1 split_flag={d1.split_flag}, status={d1.status}, chosen_size={len(d1.accepted_members or [])}"
    return run_test("F_split", rule, steps, check)


def test_G_merge(rule):
    """Previous target (40 birds) is fully retained (R_old=1.0) inside a
    much larger new candidate (200 birds) -- an independently-existing
    group of ~160 was incorporated. Expected: merge_flag=True; continuation
    still proceeds (the previous material demonstrably persists), but
    flagged as a merge event, not silent ordinary continuation."""
    prev = set(range(0, 40))
    merged = set(range(0, 200))
    steps = [[prev], [merged]]

    def check(decisions):
        d1 = decisions[1]
        ok = d1.merge_flag and d1.status == "continuing"
        return ok, f"t=1 merge_flag={d1.merge_flag}, status={d1.status}, R_old/R_new of winner in metrics"
    return run_test("G_merge", rule, steps, check)


TESTS = [test_A_stable_continuation, test_B_gradual_turnover, test_C_abrupt_replacement,
         test_D_toroidal_crossing, test_E_temporary_missed_detection, test_F_split, test_G_merge]


def build_frozen_rule():
    calib = json.load(open(OUT / "identity_rule_calibration.json"))
    frozen = calib["frozen_rule"]
    letter = frozen["letter"]
    params = frozen["params"]
    return RULE_FAMILY_BUILDERS[letter](**params), frozen


def main():
    rule, frozen = build_frozen_rule()
    print(f"testing frozen rule: {rule.name}  (spec: {frozen})")
    results = []
    all_ok = True
    for test_fn in TESTS:
        ok, detail, decisions = test_fn(rule)
        all_ok &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {test_fn.__name__}: {detail}")
        results.append(dict(test=test_fn.__name__, passed=bool(ok), detail=detail,
                             decisions=[dict(t=d.t, status=d.status, split_flag=d.split_flag,
                                              merge_flag=d.merge_flag, reason=d.reason,
                                              n_accepted=len(d.accepted_members or []))
                                        for d in decisions]))
    json.dump(dict(rule=rule.name, frozen_rule_spec=frozen, all_passed=bool(all_ok), results=results),
               open(OUT / "synthetic_identity_test_results.json", "w"), indent=2)
    print(f"\nALL PASSED: {all_ok}")
    print("wrote", OUT / "synthetic_identity_test_results.json")


if __name__ == "__main__":
    main()
