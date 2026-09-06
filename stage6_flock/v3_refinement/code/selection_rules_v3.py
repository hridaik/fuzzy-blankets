"""Part 1B/1D: the new rule this refinement adds (COVER), plus thin aliases
so the V3 rule names (R, DEG, LEV, COVER, PATCH) map onto V2's frozen,
unmodified implementations (rule_D_random, rule_A_degree, rule_B_leverage,
rule_C_patch respectively) without duplicating logic."""
from __future__ import annotations

import numpy as np

from selection_rules import rule_A_degree, rule_B_leverage, rule_C_patch, rule_D_random  # noqa: F401

rule_R_random = rule_D_random
rule_DEG_degree = rule_A_degree
rule_LEV_leverage = rule_B_leverage
rule_PATCH_patch = rule_C_patch


def rule_COVER_greedy(B_D0: np.ndarray, I0: np.ndarray, lattice, k: int) -> list[int]:
    """Greedy maximum-coverage: repeatedly add the B^D_0 member covering the
    most currently-uncovered I0 birds. Ties broken by highest raw I0-degree,
    then by bird index (deterministic, matches rule_A_degree's tie-break
    convention). This directly targets Gamma(A), not simulated outcome --
    it never runs the simulator."""
    I0_set = set(I0.tolist())
    neighbor_sets = {b: set(lattice.neighbor_ids[b].tolist()) & I0_set for b in B_D0.tolist()}
    raw_degree = {b: len(s) for b, s in neighbor_sets.items()}

    uncovered = set(I0_set)
    chosen: list[int] = []
    remaining = set(B_D0.tolist())
    while remaining and len(chosen) < k and uncovered:
        best = max(remaining, key=lambda b: (len(neighbor_sets[b] & uncovered), raw_degree[b], -b))
        chosen.append(best)
        uncovered -= neighbor_sets[best]
        remaining.discard(best)

    if len(chosen) < k and remaining:
        # I0 already fully covered (or shell exhausted): fill out the budget
        # by remaining raw I0-degree, same tie-break as rule_A_degree, so a
        # fixed-k comparison against the other rules is still well-defined.
        rest = sorted(remaining, key=lambda b: (-raw_degree[b], b))
        chosen.extend(rest[: k - len(chosen)])

    return chosen[:k]


def greedy_multicover_order(B_D0: np.ndarray, I0: np.ndarray, lattice, q: int = 1) -> list[int]:
    """Generalizes rule_COVER_greedy from single-coverage (q=1, i.e. Gamma) to
    q-fold coverage: greedily add the B^D_0 member maximizing total capped
    coverage progress sum_i min(m_i+1, q) - min(m_i, q) over I0 (a standard
    monotone-submodular greedy for multiset multicover, with the usual
    (1-1/e) approximation guarantee). Returns the FULL greedy order (not
    truncated to any k) so callers can take any prefix."""
    I0_list = I0.tolist()
    neighbor_sets = {b: set(lattice.neighbor_ids[b].tolist()) & set(I0_list) for b in B_D0.tolist()}
    raw_degree = {b: len(s) for b, s in neighbor_sets.items()}
    count = {i: 0 for i in I0_list}

    remaining = set(B_D0.tolist())
    order: list[int] = []
    while remaining:
        def gain(b):
            return sum(1 for i in neighbor_sets[b] if count[i] < q)
        best = max(remaining, key=lambda b: (gain(b), raw_degree[b], -b))
        order.append(best)
        for i in neighbor_sets[best]:
            count[i] += 1
        remaining.discard(best)
    return order


def q_coverage_fraction(A: list[int], I0: np.ndarray, lattice, q: int) -> float:
    """Fraction of I0 with m_i(A) >= q."""
    I0_list = I0.tolist()
    A_set = set(int(a) for a in A)
    n_q = sum(1 for i in I0_list if len(A_set & set(lattice.neighbor_ids[i].tolist())) >= q)
    return n_q / len(I0_list) if I0_list else float("nan")


def min_actuators_for_multicover(B_D0: np.ndarray, I0: np.ndarray, lattice, q: int, gamma: float) -> list[int]:
    """Part 1D generalized: min |A| subset B^D_0 achieving
    frac(I0 with m_i(A) >= q) >= gamma, via the greedy multicover order above.
    Returns the smallest prefix of the greedy order reaching gamma (or the
    full order if gamma is unreachable at this q -- reported, not hidden)."""
    order = greedy_multicover_order(B_D0, I0, lattice, q=q)
    for k in range(1, len(order) + 1):
        if q_coverage_fraction(order[:k], I0, lattice, q) >= gamma:
            return order[:k]
    return order


def min_actuators_for_coverage(B_D0: np.ndarray, I0: np.ndarray, lattice, gamma: float) -> list[int]:
    """Part 1D: min |A| subset B^D_0 achieving Gamma(A) >= gamma, via the same
    greedy procedure (optimal for plain set-cover up to the standard
    log-factor bound). Returns the actuator list at the smallest prefix of
    the greedy order whose coverage first reaches gamma (or the full greedy
    order if gamma is unreachable, e.g. an I0 bird with no B^D_0 neighbor at
    all -- structurally impossible here since B^D_0 is defined as the union
    of all I0 neighbors, but guarded regardless)."""
    I0_set = set(I0.tolist())
    n_I0 = len(I0_set)
    neighbor_sets = {b: set(lattice.neighbor_ids[b].tolist()) & I0_set for b in B_D0.tolist()}
    raw_degree = {b: len(s) for b, s in neighbor_sets.items()}

    uncovered = set(I0_set)
    remaining = set(B_D0.tolist())
    chosen: list[int] = []
    while remaining and uncovered:
        best = max(remaining, key=lambda b: (len(neighbor_sets[b] & uncovered), raw_degree[b], -b))
        chosen.append(best)
        uncovered -= neighbor_sets[best]
        remaining.discard(best)
        covered_frac = (n_I0 - len(uncovered)) / n_I0 if n_I0 else 1.0
        if covered_frac >= gamma:
            return chosen
    return chosen  # exhausted B^D_0 before reaching gamma (reported, not hidden)
