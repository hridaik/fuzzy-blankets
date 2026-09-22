"""ForwardMaterialTrace611 -- Step 2's minimal forward material-continuity
identity tracker. AUDIT-ONLY. Never wired into run_online_control_611.py or
any controller/authority code. A comparator, exactly like lineage_v2_611,
but deliberately simpler: no probabilistic branch-history mass, no global
MAP over a hypothesis tree, no target-heading/actuator/outcome dependence
anywhere in its scoring.

Central principle (verbatim from the task brief): once a target is
selected, identity follows that target forward. A materially unrelated
candidate must not inherit the task merely because a probabilistic tracker
later assigns it higher mass, looks more coherent, or happens to face the
requested heading. This tracker enforces that by construction: at every
step, the ONLY candidates that can ever become "the target" are candidates
that pass an explicit material-overlap gate against the immediately
preceding accepted target. There is no branching probability tree to be
overtaken by an independent thread -- if nothing overlaps enough, the
tracker says so (`unresolved`) rather than picking the best-looking
alternative.

States (task brief §8): `continuing`, `unresolved`, `dead`, `split`,
`merge`. `split`/`merge` are ADVISORY flags attached to a `continuing`
decision (the task brief asks to "flag" them, not necessarily halt), never
silently treated as ordinary continuation without the flag being visible.

This module operates at the abstract level of member-ID-set sequences: it
takes, at each step, a set of raw detector candidates (already computed by
whatever detector is in use -- for this audit, always the real, unmodified
`detect_69.propose`) and returns a decision. Geometry/heading/torus
handling and the actual detector call live in the thin wrappers
(`replay_real_trajectory` below, and the seed-specific scripts), keeping
this file's core logic testable on pure Python sets with no simulator
dependency at all -- exactly what the synthetic identity tests need.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


def overlap_metrics(a: frozenset, b: frozenset) -> dict:
    inter = len(a & b)
    union = len(a | b)
    return dict(
        retained=inter, lost=len(a - b), gained=len(b - a),
        R_old=(inter / len(a)) if a else None,
        R_new=(inter / len(b)) if b else None,
        jaccard=(inter / union) if union else None,
        dice=(2 * inter / (len(a) + len(b))) if (len(a) + len(b)) else None,
    )


@dataclass
class Rule:
    """One of the small predefined family of continuation rules (task
    brief §6). Exactly one boolean gate: a candidate is ACCEPTABLE as a
    continuation of the previous accepted target iff `accept(metrics)` is
    True. Nothing here ever sees target_heading, actuator identity, or any
    outcome metric -- `accept` is a pure function of set-overlap numbers."""
    name: str
    accept: "callable"

    def __call__(self, m: dict) -> bool:
        return self.accept(m)


def rule_A(min_r_old: float) -> Rule:
    return Rule(f"A_max_Rold(min={min_r_old})", lambda m: m["R_old"] is not None and m["R_old"] >= min_r_old)


def rule_B(min_jaccard: float) -> Rule:
    return Rule(f"B_max_jaccard(min={min_jaccard})", lambda m: m["jaccard"] is not None and m["jaccard"] >= min_jaccard)


def rule_C(min_r_old: float, min_r_new: float) -> Rule:
    return Rule(f"C_two_sided(Rold>={min_r_old},Rnew>={min_r_new})",
                lambda m: m["R_old"] is not None and m["R_old"] >= min_r_old
                and m["R_new"] is not None and m["R_new"] >= min_r_new)


def rule_D(min_dice: float) -> Rule:
    return Rule(f"D_max_dice(min={min_dice})", lambda m: m["dice"] is not None and m["dice"] >= min_dice)


RULE_FAMILY_BUILDERS = dict(A=rule_A, B=rule_B, C=rule_C, D=rule_D)


@dataclass
class StepDecision:
    t: int
    status: str                    # continuing | unresolved | dead | (split/merge are flags, not statuses)
    accepted_members: Optional[frozenset]
    prev_members: Optional[frozenset]
    chosen_candidate_idx: Optional[int]
    all_candidate_metrics: list    # [{cand_idx, size, **overlap_metrics}, ...] vs prev_members
    n_accepting_candidates: int
    split_flag: bool
    merge_flag: bool
    reason: str                    # human-readable "why this candidate was chosen" / "why unresolved"
    steps_unresolved: int           # consecutive unresolved steps so far (0 if continuing/dead)


class ForwardMaterialTrace611:
    """Deliberately simpler than lineage_v2_611: no probability mass, no
    branch tree, no coalescing logic, no death-vs-continue softmax. Just:
    gate candidates against the immediately-preceding accepted target by
    material overlap; accept the single best passer; flag ambiguity when
    more than one passes without a decisive size gap; go unresolved (not
    switch) when nothing passes, up to a bounded horizon; declare dead
    after that horizon.

    SPLIT: >=2 accepting candidates each retaining a "substantial" share
    (`split_min_share` of `prev`'s absolute size) of the previous target --
    flagged, and the tracker continues on the candidate with the larger
    ABSOLUTE retained count (a material, not behavioral, tie-break), never
    on the one that happens to face the target heading or contain the
    actuated birds (this tracker never receives that information at all).

    MERGE: the accepted candidate retains nearly all of `prev` (R_old high)
    but `prev` is now only a small fraction of the new candidate (R_new
    below `merge_max_r_new`, size ratio above `merge_min_size_ratio`) --
    flagged, continuation still proceeds (per task brief: "flag ... rather
    than treating this automatically as ordinary continuation" -- flagging,
    not blocking, since the previous material demonstrably persists inside
    the new candidate).
    """

    def __init__(self, rule: Rule, missed_detection_horizon: int = 3,
                 split_min_share: float = 0.30, merge_max_r_new: float = 0.40,
                 merge_min_size_ratio: float = 1.8):
        self.rule = rule
        self.missed_detection_horizon = missed_detection_horizon
        self.split_min_share = split_min_share
        self.merge_max_r_new = merge_max_r_new
        self.merge_min_size_ratio = merge_min_size_ratio
        self.accepted: Optional[frozenset] = None
        self.status = "uninitialized"
        self.steps_unresolved = 0
        self.history: list[StepDecision] = []

    def start(self, t: int, members) -> StepDecision:
        self.accepted = frozenset(int(x) for x in members)
        self.status = "continuing"
        self.steps_unresolved = 0
        d = StepDecision(t=t, status="continuing", accepted_members=self.accepted,
                          prev_members=None, chosen_candidate_idx=None,
                          all_candidate_metrics=[], n_accepting_candidates=0,
                          split_flag=False, merge_flag=False,
                          reason="seed target at qualification", steps_unresolved=0)
        self.history.append(d)
        return d

    def step(self, t: int, candidates: list) -> StepDecision:
        if self.status == "dead":
            d = StepDecision(t=t, status="dead", accepted_members=None, prev_members=self.accepted,
                              chosen_candidate_idx=None, all_candidate_metrics=[], n_accepting_candidates=0,
                              split_flag=False, merge_flag=False,
                              reason="tracker already declared dead; no further re-acquisition", steps_unresolved=self.steps_unresolved)
            self.history.append(d)
            return d

        prev = self.accepted
        cand_sets = [frozenset(int(x) for x in c) for c in candidates]
        metrics = [dict(cand_idx=i, size=len(c), **overlap_metrics(prev, c)) for i, c in enumerate(cand_sets)]
        accepting = [(i, cand_sets[i], m) for i, m in enumerate(metrics) if self.rule(m)]

        if not accepting:
            self.steps_unresolved += 1
            if self.steps_unresolved > self.missed_detection_horizon:
                self.status = "dead"
                self.accepted = None
                reason = (f"no candidate passed {self.rule.name} for "
                          f"{self.steps_unresolved} consecutive steps (horizon={self.missed_detection_horizon}); declared dead")
                d = StepDecision(t=t, status="dead", accepted_members=None, prev_members=prev,
                                  chosen_candidate_idx=None, all_candidate_metrics=metrics, n_accepting_candidates=0,
                                  split_flag=False, merge_flag=False, reason=reason, steps_unresolved=self.steps_unresolved)
            else:
                self.status = "unresolved"
                # accepted membership PINNED (not switched) while unresolved
                reason = (f"no candidate passed {self.rule.name} this step "
                          f"({self.steps_unresolved}/{self.missed_detection_horizon} consecutive); "
                          f"holding last accepted membership, NOT switching")
                d = StepDecision(t=t, status="unresolved", accepted_members=self.accepted, prev_members=prev,
                                  chosen_candidate_idx=None, all_candidate_metrics=metrics, n_accepting_candidates=0,
                                  split_flag=False, merge_flag=False, reason=reason, steps_unresolved=self.steps_unresolved)
            self.history.append(d)
            return d

        self.steps_unresolved = 0
        # Split check: >=2 accepting candidates each retaining a substantial
        # absolute share of prev, and NOT near-duplicates of each other.
        substantial = [(i, c, m) for i, c, m in accepting if m["retained"] >= self.split_min_share * len(prev)]
        distinct_substantial = []
        for i, c, m in substantial:
            if not any(c == c2 for _, c2, _ in distinct_substantial):
                distinct_substantial.append((i, c, m))
        split_flag = len(distinct_substantial) >= 2

        # choose winner: largest ABSOLUTE retained count (material, not
        # behavioral, tie-break) -- ties broken by candidate size (bigger =
        # more of prev's organization is present) then by candidate index
        # (deterministic, arbitrary among truly-tied material evidence).
        winner_i, winner_set, winner_m = max(accepting, key=lambda t: (t[2]["retained"], t[2]["size"], -t[0]))

        merge_flag = (winner_m["R_old"] is not None and winner_m["R_old"] >= 0.70
                      and winner_m["R_new"] is not None and winner_m["R_new"] <= self.merge_max_r_new
                      and winner_m["size"] >= self.merge_min_size_ratio * len(prev))

        self.accepted = winner_set
        self.status = "continuing"
        reason_bits = [f"{self.rule.name} accepted candidate {winner_i} "
                        f"(retained={winner_m['retained']}, R_old={winner_m['R_old']:.3f}, "
                        f"R_new={winner_m['R_new']:.3f}, jaccard={winner_m['jaccard']:.3f})"]
        if len(accepting) > 1:
            reason_bits.append(f"{len(accepting)} candidates passed the gate; chose max absolute retained count")
        if split_flag:
            reason_bits.append(f"SPLIT FLAG: {len(distinct_substantial)} distinct candidates each retain "
                                f">= {self.split_min_share:.0%} of the previous target")
        if merge_flag:
            reason_bits.append(f"MERGE FLAG: candidate retains {winner_m['R_old']:.0%} of previous target but "
                                f"previous target is only {winner_m['R_new']:.0%} of the new candidate "
                                f"(size ratio {winner_m['size']/len(prev):.2f}x)")
        d = StepDecision(t=t, status="continuing", accepted_members=self.accepted, prev_members=prev,
                          chosen_candidate_idx=winner_i, all_candidate_metrics=metrics,
                          n_accepting_candidates=len(accepting), split_flag=split_flag, merge_flag=merge_flag,
                          reason="; ".join(reason_bits), steps_unresolved=0)
        self.history.append(d)
        return d
