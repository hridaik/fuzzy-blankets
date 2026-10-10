"""Stage 6.10 Part C -- the FULL-MODEL CONTROL BENCHMARK.

The reference controller the whole stage is judged against. Unlike the Stage 6.8
`adaptive_oracle` arm (renamed here the **full-info causal heuristic**), this one
does not rank actuators by a task-agnostic influence score and then hope. It
explicitly optimizes the control objective:

    maximise   A_S = E[ H*(I_t, t+tau) | do(u_j = h* for j in S) ]
                     - E[ H*(I_t, t+tau) | no action ]

over actuator subsets S of the current causal interface, subject to |S| <= K.

Search:
  * `exhaustive`  -- every subset of size <= K when C(n, K) is small enough.
    Only then is the result an actual optimum, and only then may the word
    "optimum" be used.
  * `beam`        -- beam search over subset size, width W.
  * `cem`         -- cross-entropy method over inclusion probabilities.
Convergence is checked across search budgets AND random seeds
(`convergence_check`), because a search that has not converged is not a
benchmark.

Every objective evaluation uses COMMON RANDOM NUMBERS: the same `rng_seed`
drives the baseline and every candidate subset at a given state, so subsets are
compared on the same noise draw.
"""
from __future__ import annotations

import itertools
import math

import numpy as np

import reference_truth as rt

DEFAULT_TAU = 4
DEFAULT_ROLL = 96
EXHAUSTIVE_MAX_SUBSETS = 20000


def _obj(sim, z, I, h_star, S, tau, rng_seed, n_roll, baseline, hold):
    a = rt._expected_alignment_after(sim, z, I, h_star, tau, list(S), rng_seed,
                                     n_roll, hold=hold)
    return float(a - baseline)


def _baseline(sim, z, I, h_star, tau, rng_seed, n_roll):
    # No actuators, so `hold` is irrelevant to the baseline.
    return rt._expected_alignment_after(sim, z, I, h_star, tau, [], rng_seed, n_roll)


def n_subsets(n, k):
    return sum(math.comb(n, r) for r in range(1, k + 1))


def optimize(sim, z, I, h_star, candidates, k_act, tau=DEFAULT_TAU,
             n_roll=DEFAULT_ROLL, rng_seed=0, method="auto", beam_width=12,
             cem_iters=8, cem_pop=40, cem_elite=8, rng=None, hold=None):
    """Return (best_set, best_value, info). `info.method` records what actually
    ran and `info.is_optimum` is True ONLY for a completed exhaustive search."""
    cands = [int(j) for j in candidates]
    rng = rng or np.random.default_rng(rng_seed)
    # Actuators are held for the whole planning horizon, matching execution.
    hold = tau if hold is None else int(hold)
    base = _baseline(sim, z, I, h_star, tau, rng_seed, n_roll)
    ev = lambda S: _obj(sim, z, I, h_star, S, tau, rng_seed, n_roll, base, hold)

    if not cands or k_act <= 0:
        return [], 0.0, dict(method="empty", n_eval=0, is_optimum=True)

    if method == "auto":
        method = "exhaustive" if n_subsets(len(cands), k_act) <= EXHAUSTIVE_MAX_SUBSETS else "beam"

    n_eval = 0
    if method == "exhaustive":
        best, bv = [], 0.0
        for r in range(1, k_act + 1):
            for S in itertools.combinations(cands, r):
                v = ev(S); n_eval += 1
                if v > bv:
                    best, bv = list(S), v
        return sorted(best), bv, dict(method="exhaustive", n_eval=n_eval, is_optimum=True,
                                      n_candidates=len(cands), k_act=k_act)

    if method == "beam":
        beam = [([], 0.0)]
        best, bv = [], 0.0
        for _ in range(k_act):
            nxt = []
            for S, _v in beam:
                for j in cands:
                    if j in S:
                        continue
                    T = sorted(S + [j])
                    v = ev(T); n_eval += 1
                    nxt.append((T, v))
            if not nxt:
                break
            nxt.sort(key=lambda x: -x[1])
            # de-duplicate identical subsets before truncating the beam
            seen, dedup = set(), []
            for T, v in nxt:
                key = tuple(T)
                if key in seen:
                    continue
                seen.add(key); dedup.append((T, v))
            beam = dedup[:beam_width]
            if beam[0][1] > bv:
                best, bv = beam[0][0], beam[0][1]
        return sorted(best), bv, dict(method="beam", n_eval=n_eval, is_optimum=False,
                                      beam_width=beam_width, n_candidates=len(cands), k_act=k_act)

    if method == "cem":
        p = np.full(len(cands), min(1.0, k_act / max(1, len(cands))))
        best, bv = [], 0.0
        for _ in range(cem_iters):
            pop = []
            for _s in range(cem_pop):
                pick = [c for c, u in zip(cands, rng.random(len(cands))) if u < p[cands.index(c)]] \
                    if False else [cands[i] for i in range(len(cands)) if rng.random() < p[i]]
                if len(pick) > k_act:
                    pick = list(rng.choice(pick, size=k_act, replace=False))
                v = ev(pick); n_eval += 1
                pop.append((sorted(int(x) for x in pick), v))
                if v > bv:
                    best, bv = sorted(int(x) for x in pick), v
            pop.sort(key=lambda x: -x[1])
            elite = pop[:cem_elite]
            newp = np.zeros(len(cands))
            for S, _v in elite:
                for i, c in enumerate(cands):
                    if c in S:
                        newp[i] += 1
            p = 0.3 * p + 0.7 * (newp / max(1, len(elite)))
            p = np.clip(p, 0.02, 0.98)
        return sorted(best), bv, dict(method="cem", n_eval=n_eval, is_optimum=False,
                                      iters=cem_iters, pop=cem_pop,
                                      n_candidates=len(cands), k_act=k_act)

    raise ValueError(f"unknown method {method!r}")


def convergence_check(sim, z, I, h_star, candidates, k_act, tau=DEFAULT_TAU,
                      budgets=((6, 48), (12, 96), (20, 192)), seeds=(0, 1, 2)):
    """Does the search agree with itself across budgets and seeds?

    Reports the best value found at each (beam_width, n_roll) budget and each
    seed. A benchmark whose value keeps climbing with budget has not converged
    and must not be called a benchmark.
    """
    rows = []
    for bw, nr in budgets:
        for sd in seeds:
            S, v, info = optimize(sim, z, I, h_star, candidates, k_act, tau=tau,
                                  n_roll=nr, rng_seed=sd, method="beam", beam_width=bw)
            rows.append(dict(beam_width=bw, n_roll=nr, seed=sd, value=v,
                             size=len(S), n_eval=info["n_eval"], best=S))
    vals = np.array([r["value"] for r in rows], float)
    by_budget = {}
    for bw, nr in budgets:
        v = [r["value"] for r in rows if r["beam_width"] == bw and r["n_roll"] == nr]
        by_budget[f"bw{bw}_roll{nr}"] = dict(mean=float(np.mean(v)), sd=float(np.std(v)))
    top = max(rows, key=lambda r: r["value"])
    return dict(rows=rows, by_budget=by_budget, spread=float(vals.max() - vals.min()),
                best_value=float(vals.max()), best_set=top["best"])
