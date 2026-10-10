"""Task A (spec S5.4): hard synthetic identity tests H-O, extending Step 2's
known-history suite (A-G, material_identity_step2_20260921/code/
synthetic_identity_tests.py, imported and re-run unmodified alongside these
for a single combined report). Same style/contract: hand-constructed
candidate-set sequences with an explicit expected genealogy and strict-
identity outcome, run against the FROZEN rule (never retuned here).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

STEP2_CODE = Path(__file__).resolve().parents[2] / "material_identity_step2_20260921" / "code"
sys.path.insert(0, str(STEP2_CODE))
from forward_material_trace_611 import ForwardMaterialTrace611, RULE_FAMILY_BUILDERS  # noqa: E402
import synthetic_identity_tests as S1  # noqa: E402  (tests A-G, re-run unmodified)

OUT = Path(__file__).resolve().parents[1] / "data"
FROZEN_JSON = STEP2_CODE.parent / "data" / "identity_rule_calibration.json"


def run_test(name, rule, steps, expect_check):
    tr = ForwardMaterialTrace611(rule)
    tr.start(0, steps[0][0])
    decisions = [tr.history[0]]
    for t, cands in enumerate(steps[1:], start=1):
        d = tr.step(t, cands)
        decisions.append(d)
    ok, detail = expect_check(decisions)
    return ok, detail, decisions


def test_H_two_flocks_passing_near(rule):
    """Two independent flocks, never overlapping in membership, whose
    candidate positions are irrelevant at this set-only layer (proximity is
    handled by hard_negative_validation.py's position-aware analysis; here
    we test the pure membership question: does close co-presence, with zero
    membership overlap, ever cause a switch?). Target flock A continues with
    mild turnover for 6 steps; flock B (disjoint IDs) is ALSO present at
    every step as a second candidate, of similar or larger size, at every
    single step -- i.e. a persistent, not one-off, distractor. Expected:
    A's trace must continue on A throughout, never switch onto B merely
    because B is present, bigger, or persistent."""
    a = set(range(0, 40))
    b = set(range(900, 960))  # bigger, persistent distractor, zero overlap always
    steps = [[a]]
    cur = a
    for t in range(6):
        nxt = set(cur)
        losers = sorted(nxt)[:2]
        for x in losers:
            nxt.discard(x)
        nxt |= {2000 + t * 2, 2000 + t * 2 + 1}
        steps.append([nxt, b])
        cur = nxt

    def check(decisions):
        ok = all(d.status == "continuing" and (d.accepted_members & b) == set() for d in decisions[1:])
        return ok, f"statuses={[d.status for d in decisions]}; ever touched b={any((d.accepted_members or set()) & b for d in decisions[1:])}"
    return run_test("H_two_flocks_passing_near", rule, steps, check)


def test_I_similar_size_zero_overlap(rule):
    """Two flocks with IDENTICAL size and, in this abstract layer, standing
    in for 'similar heading' (heading is not modeled here -- deliberately;
    this test isolates the pure-membership question, per S5.4's framing that
    the hard case is 'same size/heading, zero overlap'). Expected: a
    same-size, zero-overlap replacement candidate must never be accepted as
    continuation, at any threshold reachable by the frozen rule (jaccard=0
    regardless of size match)."""
    true_flock = set(range(0, 50))
    same_size_unrelated = set(range(5000, 5050))
    steps = [[true_flock], [same_size_unrelated]]

    def check(decisions):
        d1 = decisions[1]
        ok = d1.status != "continuing"
        return ok, f"t=1 status={d1.status} (same size 50/50, jaccard=0.0)"
    return run_test("I_similar_size_zero_overlap", rule, steps, check)


def test_J_turnover_with_distractor(rule):
    """Gradual turnover (as in Step 2's test B) while a same-episode,
    never-overlapping distractor of comparable size is present at EVERY
    step. Expected: continuing throughout, on the turning-over flock, never
    onto the distractor, and cumulative turnover behaves exactly as in the
    distractor-free case (S1's test B) -- i.e. the distractor's mere
    presence must not perturb the accepted trajectory at all."""
    pop = set(range(0, 40))
    distractor = set(range(8000, 8040))
    steps = [[pop]]
    cur = set(pop)
    next_id = 10000
    for t in range(15):
        nxt = set(cur)
        losers = sorted(nxt)[:4]
        for x in losers:
            nxt.discard(x)
        nxt |= set(range(next_id, next_id + 4))
        next_id += 4
        steps.append([nxt, distractor])
        cur = nxt

    def check(decisions):
        ok = all(d.status == "continuing" and (d.accepted_members & distractor) == set() for d in decisions[1:])
        final_overlap_origin = len(pop & decisions[-1].accepted_members) / len(pop)
        return ok, f"statuses all continuing={ok}; final overlap w/ t=0 cohort={final_overlap_origin:.2f} (expected low, ordinary turnover)"
    return run_test("J_turnover_with_distractor", rule, steps, check)


def test_K_partial_merge_dilution(rule):
    """Target fully retained (R_old=1.0) inside a candidate 6x larger --
    the SAME shape as Step 2's test G (merge), repeated here explicitly
    under Task B/S4.4's framing as 'partial merge / dilution', to confirm
    the known, disclosed limitation (jaccard penalizes size dilution
    symmetrically with membership loss) is stable and not a one-off
    artifact of test G's specific numbers. Expected result documented, not
    silently hidden: EXPECTED TO FAIL under the frozen pure-Jaccard rule
    (goes unresolved, not continuing+merge_flag) -- same disclosed
    limitation as test G, at a different size ratio."""
    prev = set(range(0, 30))
    merged = set(range(0, 180))  # prev fully inside, 6x larger
    steps = [[prev], [merged]]

    def check(decisions):
        d1 = decisions[1]
        # Documented expectation: FAILS the same way test G does (jaccard=30/180=0.167<0.30).
        expected_fail = d1.status == "unresolved"
        return expected_fail, f"t=1 status={d1.status} (EXPECTED 'unresolved' -- same disclosed Jaccard-dilution limitation as test G; jaccard={30/180:.3f}<0.30)"
    return run_test("K_partial_merge_dilution", rule, steps, check)


def test_L_two_way_split_persistence(rule):
    """Split into two substantial daughters, and BOTH daughters persist
    (with their own mild turnover) for several further steps, rather than
    Step 2's test F which only checked the single split step. Expected:
    split_flag=True at the split step; the trace follows ONE daughter
    (larger absolute retained count) and that daughter must show ordinary
    'continuing' status for all subsequent steps -- i.e. persistence of the
    UNFOLLOWED daughter must not cause the trace to waver or re-flag."""
    prev = set(range(0, 40))
    daughter_a = set(range(0, 22))   # followed (larger overlap by 0 tie... see below)
    daughter_b = set(range(18, 40))
    steps = [[prev], [daughter_a, daughter_b]]
    cur_a, cur_b = daughter_a, daughter_b
    for t in range(5):
        na = set(cur_a); na.discard(sorted(na)[0]); na.add(90000 + t)
        nb = set(cur_b); nb.discard(sorted(nb)[0]); nb.add(91000 + t)
        steps.append([na, nb])
        cur_a, cur_b = na, nb

    def check(decisions):
        split_step = decisions[1]
        later = decisions[2:]
        ok = (split_step.split_flag and split_step.status == "continuing"
              and all(d.status == "continuing" for d in later))
        return ok, (f"split_step: split_flag={split_step.split_flag}, chosen_size={len(split_step.accepted_members or [])}; "
                    f"later statuses={[d.status for d in later]}")
    return run_test("L_two_way_split_persistence", rule, steps, check)


def test_M_split_then_remerge(rule):
    """Split, then the two daughters recombine into a single candidate
    retaining both (R_old high vs the FOLLOWED daughter, but the candidate
    also contains the other daughter's IDs -- i.e. re-fusion). Expected:
    the trace follows one daughter through the split (split_flag), then on
    re-fusion accepts the recombined candidate (it retains the followed
    daughter's members with high R_old) -- and this SHOULD trip the
    merge_flag (the followed daughter is now a small fraction of the
    recombined candidate, if the size ratio and R_new clear the diagnostic
    merge thresholds), documented explicitly either way (flag is
    diagnostic-only, per identity_rule_spec.md -- this test checks the
    behavior IS visible and consistent with that disclosed status, not that
    it is independently validated)."""
    prev = set(range(0, 40))
    daughter_a = set(range(0, 22))
    daughter_b = set(range(18, 40))
    recombined = set(range(0, 40)) | set(range(500, 520))  # re-fused, plus some new members
    steps = [[prev], [daughter_a, daughter_b], [recombined]]

    def check(decisions):
        d1, d2 = decisions[1], decisions[2]
        followed = d1.accepted_members
        recombined_contains_followed = followed.issubset(d2.accepted_members) if d2.accepted_members else False
        detail = (f"split_flag={d1.split_flag}; followed_daughter_size={len(followed)}; "
                  f"remerge status={d2.status}, merge_flag={d2.merge_flag}, "
                  f"followed_daughter_subset_of_remerged={recombined_contains_followed}")
        ok = d1.split_flag and d2.status == "continuing" and recombined_contains_followed
        return ok, detail
    return run_test("M_split_then_remerge", rule, steps, check)


def test_N_temporary_over_segmentation(rule):
    """A single, physically-coherent 60-bird group is (mis-)detected as two
    ~30-member fragments for 3 consecutive steps (candidate-generator
    over-segmentation, NOT a physical split -- both fragments are always
    co-present, always summing near the true total, and the split never
    resolves into two independently-persisting daughters), then the
    detector re-fuses them into one 60-member candidate again. Expected:
    split_flag fires at the FIRST fragmentation transition (prev=60-member
    whole, both ~31-member fragments clear the substantial-share floor --
    the moment of genuine ambiguity). On SUBSEQUENT frag-to-frag steps,
    once the trace has locked onto one fragment (frag_a), frag_b is no
    longer "substantial" relative to frag_a specifically (frag_a/frag_b
    overlap only at their 2-member boundary, far below the 30%-of-prev
    floor) -- so split_flag correctly does NOT re-fire every step; it is a
    per-transition ambiguity signal, not a persistent state, and this test
    checks that distinction explicitly rather than assuming naive
    re-firing. On re-fusion, whether the recombined candidate is
    recognized as a continuation (with or without tripping the
    diagnostic-only merge flag) is documented, not asserted as
    correct/incorrect -- this exposes the exact ambiguity between
    'over-segmentation' and 'genuine merge' that Task B is about."""
    prev = set(range(0, 60))
    frag_a = set(range(0, 31))
    frag_b = set(range(29, 60))
    steps = [[prev]]
    for t in range(3):
        steps.append([frag_a, frag_b])
    steps.append([set(range(0, 60)) | {700, 701}])  # re-fused

    def check(decisions):
        frag_steps = decisions[1:4]
        refuse_step = decisions[4]
        ok = (frag_steps[0].status == "continuing" and frag_steps[0].split_flag
              and all(d.status == "continuing" for d in frag_steps[1:])
              and refuse_step.status == "continuing")
        detail = (f"frag statuses/split_flags={[(d.status, d.split_flag) for d in frag_steps]} "
                  f"(split_flag expected True only at first fragmentation, not re-fired while locked onto one fragment); "
                  f"refuse status={refuse_step.status}, merge_flag={refuse_step.merge_flag}")
        return ok, detail
    return run_test("N_temporary_over_segmentation", rule, steps, check)


def test_O_repeated_missed_detections_near_horizon(rule):
    """Target missed for exactly `missed_detection_horizon` (3) consecutive
    steps -- the boundary case Step 2's test E did not probe (E used 2,
    strictly inside the horizon). At exactly the horizon, the tracker must
    still be `unresolved` (not yet `dead`) on the 3rd miss, then EITHER
    recover (if a qualifying candidate reappears at step 4) or die (if a
    4th miss occurs, exceeding the horizon) -- both sub-cases checked."""
    true_flock = set(range(0, 40))
    distractor = set(range(7000, 7040))

    steps_recover = [[true_flock], [distractor], [distractor], [distractor],
                      [true_flock - {0, 1, 2} | {8000, 8001, 8002}]]

    def check_recover(decisions):
        ok = (decisions[1].status == "unresolved" and decisions[2].status == "unresolved"
              and decisions[3].status == "unresolved" and decisions[4].status == "continuing")
        return ok, f"statuses={[d.status for d in decisions]} (recovers exactly at horizon+1)"
    ok1, detail1, dec1 = run_test("O_repeated_missed_detections_recover", rule, steps_recover, check_recover)

    steps_die = [[true_flock], [distractor], [distractor], [distractor], [distractor]]

    def check_die(decisions):
        ok = (decisions[1].status == "unresolved" and decisions[2].status == "unresolved"
              and decisions[3].status == "unresolved" and decisions[4].status == "dead")
        return ok, f"statuses={[d.status for d in decisions]} (dies on 4th consecutive miss, horizon=3)"
    ok2, detail2, dec2 = run_test("O_repeated_missed_detections_die", rule, steps_die, check_die)

    ok = ok1 and ok2
    detail = f"recover-branch: {detail1} | die-branch: {detail2}"
    return ok, detail, dec1 + dec2


TESTS_H_O = [test_H_two_flocks_passing_near, test_I_similar_size_zero_overlap,
             test_J_turnover_with_distractor, test_K_partial_merge_dilution,
             test_L_two_way_split_persistence, test_M_split_then_remerge,
             test_N_temporary_over_segmentation, test_O_repeated_missed_detections_near_horizon]


def build_frozen_rule():
    calib = json.load(open(FROZEN_JSON))
    frozen = calib["frozen_rule"]
    return RULE_FAMILY_BUILDERS[frozen["letter"]](**frozen["params"]), frozen


def main():
    rule, frozen = build_frozen_rule()
    print(f"testing frozen rule: {rule.name}  (spec: {frozen['params']})")

    results = []
    all_ok = True

    print("\n-- re-running Step 2's tests A-G unmodified, for one combined report --")
    for test_fn in S1.TESTS:
        ok, detail, decisions = test_fn(rule)
        expected_to_fail = (test_fn.__name__ == "test_G_merge")
        all_ok &= (ok or expected_to_fail)
        print(f"  [{'PASS' if ok else 'FAIL (disclosed, see identity_rule_spec.md)'}] {test_fn.__name__}: {detail}")
        results.append(dict(test=test_fn.__name__, passed=bool(ok), detail=detail, expected_to_fail=expected_to_fail))

    print("\n-- new hard tests H-O --")
    for test_fn in TESTS_H_O:
        ok, detail, decisions = test_fn(rule)
        expected_to_fail = "K_partial_merge_dilution" in test_fn.__name__
        pass_label = "PASS" if ok else ("EXPECTED-FAIL (disclosed)" if expected_to_fail else "FAIL")
        all_ok &= (ok or expected_to_fail)
        print(f"  [{pass_label}] {test_fn.__name__}: {detail}")
        results.append(dict(test=test_fn.__name__, passed=bool(ok), detail=detail, expected_to_fail=expected_to_fail))

    json.dump(dict(rule=rule.name, frozen_rule_spec=frozen["params"], all_passed_or_expected=bool(all_ok), results=results),
              open(OUT / "hard_synthetic_test_results_H_O.json", "w"), indent=2)
    print(f"\nALL PASSED OR EXPECTED-FAIL: {all_ok}")
    print("wrote", OUT / "hard_synthetic_test_results_H_O.json")


if __name__ == "__main__":
    main()
