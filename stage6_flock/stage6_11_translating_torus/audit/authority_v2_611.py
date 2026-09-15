"""Stage 6.11B item 6-8: repaired authority estimand
    A_S(tau, d) = E[H*_{t+tau} | S forced for d consecutive steps] - E[H*_{t+tau} | baseline]
as a comparator to `intervention_api_611.MultiStepAuthorityProbe` (preserved
UNCHANGED, imported for `d=1, tau=4` reproduction only -- METHODS_AUDIT_6_11.md
Section 1.5's intervention-duration mismatch: the old probe forces the
action at step 0 only, then releases, while the real online controller holds
the SAME actuator set forced for up to REINFER_AUTHORITY_EVERY=8 consecutive
real steps between refreshes).

Item 7 (K<=8 as a maximum, never an obligation) and item 8 (individual vs
set/synergy, matched-CRN across individual/greedy/beam/random comparators)
live here too, since they all consume the same `authority_set` primitive.

No MCTS (per task brief item 8's explicit instruction) -- search comparators
are limited to top-K individual, greedy marginal, and beam search.
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))
import common_611  # noqa: E402,F401

N_BOOT_CI = 300
ALPHA = 0.05


def held_rollout(mf, r_t, z_t, S, h_star, tau: int, d: int, seed) -> np.ndarray:
    """One rollout: force every bird in S to heading h_star at every step
    0..d-1 (inclusive), then evolve freely for the remaining tau-d steps,
    return z at t+tau. `d=1` reproduces the OLD one-shot-then-released
    semantics exactly (MultiStepAuthorityProbe._rollout with forced only at
    step==0); `d=tau` holds for the entire evaluation horizon, matching a
    repaired controller that holds its actuator set for the full refresh
    window."""
    r, z = r_t.copy(), z_t.copy()
    rng = np.random.default_rng(seed)
    for step in range(tau):
        fa = {int(j): int(h_star) for j in S} if step < d else None
        r, z, _ = mf.step(r, z, rng, forced_actions=fa)
    return z


def authority_set(mf, r_t, z_t, I, S, h_star: int, tau: int, d: int, n_rollouts: int,
                    seed: int = 0, n_boot: int = N_BOOT_CI, alpha: float = ALPHA) -> dict:
    """A_S(tau, d), paired-CRN across n_rollouts, with a bootstrap CI over
    per-rollout H* indicators (same nonparametric-bootstrap convention as
    probing_611/control_authority_611's own uncertainty treatment)."""
    H_do = np.zeros(n_rollouts)
    H_base = np.zeros(n_rollouts)
    for k in range(n_rollouts):
        seed_k = (abs(int(seed)), *sorted(int(x) for x in S), int(h_star), tau, d, k)
        z_do = held_rollout(mf, r_t, z_t, S, h_star, tau, d, seed_k)
        z_base = held_rollout(mf, r_t, z_t, [], h_star, tau, 0, seed_k)   # baseline: no forcing, SAME seed
        H_do[k] = float((z_do[I] == h_star).mean())
        H_base[k] = float((z_base[I] == h_star).mean())
    diff = H_do - H_base
    rng = np.random.default_rng(seed + 999)
    idx = rng.integers(0, n_rollouts, size=(n_boot, n_rollouts))
    boot_means = diff[idx].mean(axis=1)
    ci_lo, ci_hi = (float(x) for x in np.quantile(boot_means, [alpha / 2, 1 - alpha / 2]))
    return dict(S=sorted(int(x) for x in S), h_star=int(h_star), tau=tau, d=d, n_rollouts=n_rollouts,
                 A=float(diff.mean()), se=float(diff.std(ddof=1) / np.sqrt(n_rollouts)) if n_rollouts > 1 else None,
                 ci_lo=ci_lo, ci_hi=ci_hi, H_do_mean=float(H_do.mean()), H_base_mean=float(H_base.mean()))


def synergy(mf, r_t, z_t, I, S, h_star, tau, d, n_rollouts, seed=0) -> dict:
    """Gamma(S) = A_S - sum_{j in S} A_j, matched-CRN (the SAME seed_k
    convention threads through both the set call and each individual call,
    so the comparison is paired, not independently noisy)."""
    a_set = authority_set(mf, r_t, z_t, I, S, h_star, tau, d, n_rollouts, seed=seed)
    a_indiv = {j: authority_set(mf, r_t, z_t, I, [j], h_star, tau, d, n_rollouts, seed=seed) for j in S}
    gamma = a_set["A"] - sum(v["A"] for v in a_indiv.values())
    return dict(S=a_set["S"], A_S=a_set["A"], A_S_ci=(a_set["ci_lo"], a_set["ci_hi"]),
                 sum_individual_A=sum(v["A"] for v in a_indiv.values()),
                 individual=a_indiv, gamma=gamma)


# --------------------------------------------------------------- item 7: K<=8, abstention
def rank_actuators_v2(mf, r_t, z_t, I, candidates, h_star, tau, d, n_rollouts, seed=0) -> list[dict]:
    return sorted((authority_set(mf, r_t, z_t, I, [j], h_star, tau, d, n_rollouts, seed=seed)
                    for j in candidates), key=lambda res: -res["A"])


def select_actuators_v2(mf, r_t, z_t, I, candidates, h_star, tau, d, n_rollouts, k_max=8,
                          seed=0, require_positive_evidence: bool = True) -> dict:
    """K<=8 as a MAXIMUM, never an obligation: an individual actuator is
    included only if its bootstrap CI lower bound clears 0 (predeclared
    conservative rule -- 'evidence for positive expected authority'), taken
    in descending-A order up to k_max. If require_positive_evidence=False,
    reproduces the OLD unconstrained top-K-fills-regardless behaviour, kept
    as an explicit comparator per the task brief."""
    scored = rank_actuators_v2(mf, r_t, z_t, I, candidates, h_star, tau, d, n_rollouts, seed=seed)
    if require_positive_evidence:
        chosen = [s for s in scored if s["ci_lo"] > 0.0][:k_max]
    else:
        chosen = scored[:k_max]
    return dict(S=[s["S"][0] for s in chosen], scores=scored, h_star=h_star, tau=tau, d=d,
                 k_max=k_max, k_actual=len(chosen), abstained=(len(chosen) == 0),
                 require_positive_evidence=require_positive_evidence)


def greedy_marginal_search(mf, r_t, z_t, I, candidates, h_star, tau, d, n_rollouts, k_max=8,
                             seed=0, require_positive_evidence: bool = True) -> dict:
    """Greedy forward selection on MARGINAL set authority (re-evaluates the
    FULL set including everything chosen so far at each step, unlike top-K
    individual ranking, which never re-scores conditional on co-selection)."""
    chosen: list[int] = []
    pool = list(candidates)
    trace = []
    base = authority_set(mf, r_t, z_t, I, [], h_star, tau, 0, n_rollouts, seed=seed)
    cur_A = 0.0
    for step in range(k_max):
        best_j, best_res = None, None
        for j in pool:
            trial = chosen + [j]
            res = authority_set(mf, r_t, z_t, I, trial, h_star, tau, d, n_rollouts, seed=seed)
            if best_res is None or res["A"] > best_res["A"]:
                best_j, best_res = j, res
        gain = best_res["A"] - cur_A
        if require_positive_evidence and gain <= 0.0:
            trace.append(dict(step=step, added=None, stop_reason="no_positive_marginal_gain"))
            break
        chosen.append(best_j)
        pool.remove(best_j)
        cur_A = best_res["A"]
        trace.append(dict(step=step, added=best_j, set_A=cur_A, marginal_gain=gain, ci=(best_res["ci_lo"], best_res["ci_hi"])))
    final = authority_set(mf, r_t, z_t, I, chosen, h_star, tau, d, n_rollouts, seed=seed) if chosen else base
    return dict(S=sorted(chosen), A=final["A"], ci=(final["ci_lo"], final["ci_hi"]), trace=trace)


def beam_search(mf, r_t, z_t, I, candidates, h_star, tau, d, n_rollouts, k_max=8, beam_width=3,
                  seed=0) -> dict:
    """Beam search over sets, width `beam_width`, depth k_max. Stronger than
    greedy (keeps multiple partial sets alive), not exhaustive. No MCTS."""
    beams = [([], 0.0)]
    trace = []
    for step in range(k_max):
        candidates_next = []
        for S, _ in beams:
            for j in candidates:
                if j in S:
                    continue
                trial = S + [j]
                res = authority_set(mf, r_t, z_t, I, trial, h_star, tau, d, n_rollouts, seed=seed)
                candidates_next.append((trial, res["A"]))
        if not candidates_next:
            break
        candidates_next.sort(key=lambda x: -x[1])
        seen, pruned = set(), []
        for S, A in candidates_next:
            key = frozenset(S)
            if key in seen:
                continue
            seen.add(key)
            pruned.append((S, A))
            if len(pruned) >= beam_width:
                break
        if pruned[0][1] <= beams[0][1]:
            trace.append(dict(step=step, stop_reason="no_improvement"))
            break
        beams = pruned
        trace.append(dict(step=step, best_S=beams[0][0], best_A=beams[0][1]))
    best_S, best_A = beams[0]
    final = authority_set(mf, r_t, z_t, I, best_S, h_star, tau, d, n_rollouts, seed=seed) if best_S else \
        authority_set(mf, r_t, z_t, I, [], h_star, tau, 0, n_rollouts, seed=seed)
    return dict(S=sorted(best_S), A=final["A"], ci=(final["ci_lo"], final["ci_hi"]), trace=trace,
                 beam_width=beam_width)
