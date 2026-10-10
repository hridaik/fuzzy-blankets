"""Stage 6.10 Part I -- the online closed loop.

Per step:   X_t -> Ihat_t -> Bhat_t -> u_t -> X_{t+1}
BOTH the interior and the interface are updated online.

Arms (Part I):
  no_control              floor
  predictive              actuate the blind predictive boundary
  random_matched          uniform draw, budget matched to the reference arm
  frozen_causal           sampled causal interface fixed at t0
  adaptive_causal         sampled causal interface re-inferred online   <- method
  full_info_heuristic     exact influence + multicover  (the arm Stage 6.8 called
                          `adaptive_oracle`; renamed everywhere per PLAN.md)
  full_model_benchmark    explicitly optimizes the control objective

The detector is blind: it never sees the target heading, the true graph, the
true interface, future states, or which arm is running. The controller may not
optimize membership -- it only chooses actuators.
"""
from __future__ import annotations

import numpy as np

from common_610 import target_alignment, rotate_cw
from episode_data import observation_record
from morphology import morphology
import candidate_detection as cd
import adaptive_control as ac
import reference_truth as rt
import full_model_benchmark as fmb
import probing
from intervention_api_68 import FiniteProbe

ARMS = ["full_model_benchmark", "adaptive_causal", "full_info_heuristic",
        "frozen_causal", "predictive", "random_matched", "no_control"]

PROBE_ROLLOUTS = 40
PROBE_REPEATS = 3
# Search budget set from MEASUREMENT, not guessed: `run_benchmark_convergence.py`
# shows the objective flat (mean climb -0.0005, max +0.0017 against a 0.05
# threshold) across beam widths 4/8/16 and 32/64/128 rollouts, so the smallest
# budget on the plateau is used. tau matches the Part H gate.
BENCH_TAU = 3
BENCH_ROLL = 48
BENCH_BEAM = 4

# The qualifying start-state rule, used identically by Part H (controllability),
# Part J (the uncontrolled validity envelope) and Part I (the arms), so that all
# three are calibrated on the same population of collectives.
MIN_SIZE, MAX_SIZE = 12, 90


def qualifying_start(cands, L):
    """A moderate-size, single-component, most-clump-like detected candidate.

    Morphology only: no target heading, no arm, and no control outcome enters
    this choice. Returns None when the episode has no qualifying collective.
    """
    mod = [c for c in cands if MIN_SIZE <= c.size <= MAX_SIZE]
    if not mod:
        return None
    best = max(mod, key=lambda c: morphology(
        np.array(sorted(int(x) for x in c.members)), L)["q_clump"])
    I = np.array(sorted(int(x) for x in best.members))
    return I if morphology(I, L)["n_components"] == 1 else None


def detect(sim, hist, cur, prev_I):
    """Blind online detection + maximum-overlap lineage continuation."""
    ok, _ = cd.propose(observation_record(sim, hist[:cur + 1], cur))
    if not ok:
        return prev_I, False
    if prev_I is None:
        return np.array(sorted(int(x) for x in max(ok, key=lambda c: c.size).members)), True
    best = max(ok, key=lambda c: len(set(c.members.tolist()) & set(prev_I.tolist())))
    return np.array(sorted(int(x) for x in best.members)), True


def _sampled_causal(sim, z, I, cands, seed):
    probe = FiniteProbe(sim, n_rollouts=PROBE_ROLLOUTS, seed=seed)
    res = probing.probe_sources(probe, I, cands, [z] * PROBE_REPEATS,
                                rng=np.random.default_rng(seed))
    return probing.influence_matrix(res, I), res["B_causal"], probe.budget()


def _rank_by_influence(influence, cands):
    """Candidates ordered by total influence on the interior, strongest first.

    `influence` is the nested dict `adaptive_control` produces:
    `influence[j][i] = Chat^do_{j->i}`, NOT a matrix. Candidates absent from it
    rank last, so the ranking always covers the whole candidate pool.
    """
    tot = {int(j): float(sum(d.values())) for j, d in dict(influence).items()}
    return sorted((int(j) for j in cands), key=lambda j: -tot.get(j, 0.0))


def _pad_to_k(A, ranking, cands, budget, rng):
    """Top up an arm's selection to exactly `budget`, using that arm's own
    ranking where it has one and a uniform draw otherwise. Never removes an
    actuator the arm chose."""
    chosen = [int(j) for j in A]
    seen = set(chosen)
    for j in (ranking or []):
        if len(chosen) >= budget:
            break
        if j not in seen:
            chosen.append(j); seen.add(j)
    rest = [int(j) for j in cands if int(j) not in seen]
    if len(chosen) < budget and rest:
        extra = rng.choice(rest, size=min(budget - len(chosen), len(rest)), replace=False)
        chosen += [int(j) for j in np.atleast_1d(extra)]
    return sorted(chosen)


def run_arm(sim, z_prefix, arm, seed, h_star, t_control, k_act, I0,
            theta, q_support, B_pred=None, budget_schedule=None,
            reinfer_every=1, bench_tau=BENCH_TAU, bench_roll=BENCH_ROLL,
            record_reference=True, I_init=None, fixed_k=False):
    """One control episode for one arm. Returns per-step records and the
    trajectory. Both I_t and B_t are recomputed every step.

    Two budget conventions, because neither alone is fair:

    `fixed_k=False` (matched)  each arm may spend up to the reference arm's
        realized schedule. The multicover-based arms stop early once their
        support-coverage criterion is met, so they typically spend LESS than
        allowed -- that is a property of the method, not a handicap imposed here.
    `fixed_k=True`            every arm spends exactly `budget` actuators, the
        shortfall being padded with the next-highest-scoring candidates under
        that arm's own criterion. This removes spend as an explanation for any
        ordering, in either direction.
    """
    rng = np.random.default_rng(70_000 + seed)
    z_prefix = np.asarray(z_prefix)
    n_pre = z_prefix.shape[0]
    L = int(round(sim.nn ** 0.5))
    hist = np.zeros((n_pre + t_control, sim.nn), dtype=int)
    hist[:n_pre] = z_prefix

    I_t, recs, frozen_A, last_A = (None if I_init is None else np.asarray(I_init)), [], None, []
    last_ranking = None
    budget_total = dict(n_probe_calls=0, n_rollouts=0)
    for step in range(t_control):
        cur = n_pre - 1 + step
        if not (step == 0 and I_init is not None):
            I_t, ok = detect(sim, hist, cur, I_t)
        if I_t is None:
            break
        z = hist[cur]
        cands = ac.near_exterior(sim.positions, I_t)
        budget = k_act if budget_schedule is None else int(
            budget_schedule[min(step, len(budget_schedule) - 1)])

        B_struct = [int(x) for x in rt.structural_interface(sim, z, I_t)]
        B_do, dovals = (rt.exact_do_interface(sim, z, I_t, candidates=cands)
                        if record_reference else (np.array([], int), {}))
        B_do = [int(x) for x in B_do]

        A, extra = [], {}
        if arm == "no_control":
            A = []
        elif arm == "random_matched":
            A = sorted(rng.choice(cands, size=min(budget, len(cands)), replace=False).tolist()) if cands else []
        elif arm == "predictive":
            A = sorted(int(j) for j in (B_pred or [])[:budget])
        elif arm == "full_info_heuristic":
            infl = ac._exact_influence(sim, z, I_t, cands)
            A, cov = ac.multicover(infl, I_t, k_act=budget, theta=theta, q_support=q_support)
            extra["support_coverage"] = cov
            extra["_ranking"] = _rank_by_influence(infl, cands)
        elif arm in ("frozen_causal", "adaptive_causal"):
            need = (arm == "adaptive_causal" and step % reinfer_every == 0) or frozen_A is None
            if need and cands:
                infl, Bc, bud = _sampled_causal(sim, z, I_t, cands, seed + 17 * step)
                budget_total["n_probe_calls"] += bud["n_probe_calls"]
                budget_total["n_rollouts"] += bud["n_rollouts"]
                sel, cov = ac.multicover(infl, I_t, k_act=budget, theta=theta, q_support=q_support)
                extra["support_coverage"] = cov
                extra["_ranking"] = _rank_by_influence(infl, cands)
                last_ranking = extra["_ranking"]
                last_A = sel
                if frozen_A is None:
                    frozen_A = sel
            A = frozen_A if arm == "frozen_causal" else last_A
            if "_ranking" not in extra and last_ranking is not None:
                extra["_ranking"] = last_ranking
        elif arm == "full_model_benchmark":
            # Receding horizon, re-planned every `reinfer_every` steps -- the
            # same cadence the inference arms get, so the benchmark's advantage
            # is its objective, not a faster update rate.
            if step % reinfer_every == 0 or frozen_A is None:
                pool = B_do if B_do else cands
                S, v, info = fmb.optimize(sim, z, I_t, h_star, pool, budget, tau=bench_tau,
                                          n_roll=bench_roll, rng_seed=seed * 1000 + step,
                                          method="auto", beam_width=BENCH_BEAM)
                last_A = S
                frozen_A = S
                extra = dict(objective=v, search=info["method"],
                             is_optimum=info["is_optimum"], n_eval=info["n_eval"])
            A = [j for j in last_A if int(j) not in set(int(x) for x in I_t)]
        else:
            raise ValueError(arm)

        if fixed_k and len(A) < budget and arm != "no_control":
            A = _pad_to_k(A, extra.pop("_ranking", None), cands, budget, rng)
        out = sim.step(z, rng, forced_actions={int(j): int(h_star) for j in A})
        hist[cur + 1] = out["z_new"]
        m = morphology(I_t, L)
        prev = recs[-1]["I"] if recs else [int(x) for x in I_t]
        sa, sb = set(int(x) for x in I_t), set(prev)
        recs.append(dict(
            step=step, I=[int(x) for x in I_t], I_size=len(I_t),
            actuators=[int(x) for x in A], n_act=len(A),
            B_struct_size=len(B_struct), B_do_size=len(B_do), B_do=B_do,
            n_cands=len(cands),
            H_current=target_alignment(hist[cur + 1], I_t, h_star),
            H_I0=target_alignment(hist[cur + 1], I0, h_star),
            q_clump=m["q_clump"], n_components=m["n_components"],
            jaccard_prev=len(sa & sb) / max(1, len(sa | sb)),
            turnover=len(sa - sb) / max(1, len(sa)),
            **{k: v for k, v in extra.items() if not k.startswith("_")}))
    return dict(arm=arm, seed=seed, h_star=int(h_star), records=recs,
                z_hist=hist[n_pre - 1:].tolist(),
                actuator_schedule=[r["n_act"] for r in recs],
                probe_budget=budget_total,
                final_H_current=recs[-1]["H_current"] if recs else float("nan"),
                final_H_I0=recs[-1]["H_I0"] if recs else float("nan"),
                mean_actuators=float(np.mean([r["n_act"] for r in recs])) if recs else 0.0)


def release(sim, z_start, seed, h_star, I_t, n_steps, L):
    """Part K -- control removed. Does the lineage hold the new heading and stay
    thing-like/clump-like on its own?"""
    rng = np.random.default_rng(80_000 + seed)
    hist = [np.asarray(z_start)]
    warm = np.tile(np.asarray(z_start), (cd.W_AFFINITY, 1))
    recs, I = [], np.asarray(sorted(int(x) for x in I_t))
    for step in range(n_steps):
        full = np.concatenate([warm, np.array(hist[1:])], axis=0) if len(hist) > 1 else warm
        cur = full.shape[0] - 1
        I, ok = detect(sim, full, cur, I)
        m = morphology(I, L)
        recs.append(dict(step=step, I_size=len(I), H_current=target_alignment(hist[-1], I, h_star),
                         q_clump=m["q_clump"], n_components=m["n_components"]))
        out = sim.step(hist[-1], rng)
        hist.append(out["z_new"])
        warm = np.concatenate([warm[1:], out["z_new"][None, :]], axis=0)
    return recs
