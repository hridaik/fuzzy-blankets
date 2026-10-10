"""Adaptive control on the dynamic interface (task brief sections 20-21).

EVALUATION-SIDE driver. It composes blind inference modules with the simulator;
the inference modules themselves stay blind (they only ever receive an
`Observation` and a black-box probe).

Control loop, per step:
    1. re-detect the current candidate collective I_t (blind, online)
    2. every REINFER_EVERY steps, re-estimate the causal interface Bhat_t^causal
       and the influence matrix Chat^do_{j->i} (black-box probing)
    3. choose actuators by CAUSAL WEIGHTED MULTICOVER
    4. force those birds' headings; observe the next state; repeat

Causal weighted multicover (task brief section 21) replaces neighbour COUNT
with inferred INFLUENCE:

    s_i(A_t, t) = sum_{j in A_t} Chat^do_{j->i}(t)

An interior bird is *supported* when s_i >= THETA. Actuators are added greedily
to maximize newly supported interior mass until a predeclared fraction
`Q_SUPPORT` of the current interior is supported or the budget `K_ACT` is
exhausted. THETA and Q_SUPPORT are calibrated on DEVELOPMENT seeds only and
applied unchanged to held-out seeds; neither is tuned on control success.

Arms (task brief section 21):
    no_control         no actuators at all -- the floor
    frozen_causal      Bhat^causal computed once at t0 and never updated
    adaptive_causal    Bhat^causal re-inferred online          <- the method
    adaptive_oracle    B_t^D + exact influence (upper bound)
    predictive         Bhat^pred actuated instead
    random_matched     uniform draw of the same actuator-set size
"""
from __future__ import annotations

import numpy as np

from common_68 import rotate_cw
from episode_data import observation_record
from intervention_api_68 import FiniteProbe, ExactPropagator

import candidate_detection as cd
import probing

T_CONTROL = 16
REINFER_EVERY = 6
K_ACT = 10                 # actuator budget, matched across every arm
PROBE_NEAR_RADIUS = 2.0
# The control loop re-probes ONLINE at every re-inference step, so it runs on a
# smaller, separately declared probe budget than the offline boundary pipeline
# (which uses 50 rollouts x 6 repeats). This is an online-cost decision fixed
# before the arms were compared, applied identically to every arm that probes,
# and it is a handicap on the inferred arms relative to `adaptive_oracle`,
# never an advantage.
PROBE_ROLLOUTS = 25
PROBE_REPEATS = 2
THETA_DEFAULT = 0.02       # support threshold (calibrated on dev seeds)
Q_SUPPORT_DEFAULT = 0.5    # fraction of the interior that must be supported


def near_exterior(positions, I, radius=PROBE_NEAR_RADIUS):
    I = np.asarray(sorted(int(x) for x in I))
    ext = np.setdiff1d(np.arange(positions.shape[0]), I)
    d = np.sqrt(((positions[ext][:, None, :] - positions[I][None, :, :]) ** 2).sum(-1)).min(axis=1)
    return [int(j) for j, x in zip(ext, d) if x <= radius]


def reachable_interior(influence: dict, I) -> list[int]:
    """Interior birds that ANY candidate actuator has nonzero estimated
    influence on. In a large candidate most members are several steps from the
    exterior and cannot be moved in one step at all, so a support target stated
    over the whole interior is unsatisfiable by construction and would make the
    multicover degenerate. The reachable subset is computed from the influence
    ESTIMATES alone -- no oracle, no control outcome."""
    I = [int(i) for i in I]
    return [i for i in I if any(influence[j].get(i, 0.0) > 0.0 for j in influence)]


def multicover(influence: dict, I, k_act=K_ACT, theta=THETA_DEFAULT,
               q_support=Q_SUPPORT_DEFAULT) -> tuple[list, float]:
    """Greedy causal weighted multicover over the REACHABLE interior.
    `influence[j][i] = Chat^do_{j->i}`."""
    I = reachable_interior(influence, I)
    if not I:
        return [], 0.0
    s = {i: 0.0 for i in I}
    A, avail = [], sorted(influence.keys())
    need = int(np.ceil(q_support * len(I)))
    while avail and len(A) < k_act:
        supported = sum(1 for i in I if s[i] >= theta)
        if supported >= need:
            break
        best, best_gain = None, -np.inf
        for j in avail:
            g = 0.0
            for i in I:
                if s[i] < theta:
                    g += min(theta, s[i] + influence[j].get(i, 0.0)) - s[i]
            if g > best_gain:
                best, best_gain = j, g
        if best is None or best_gain <= 0:
            break
        A.append(int(best)); avail.remove(best)
        for i in I:
            s[i] += influence[best].get(i, 0.0)
    return sorted(A), float(np.mean([s[i] >= theta for i in I])) if I else 0.0


def _exact_influence(sim, z_t, I, cands) -> dict:
    ep = ExactPropagator(sim)
    out = {}
    for j in cands:
        acc = {int(i): 0.0 for i in I}
        others = [h for h in range(4) if h != int(z_t[int(j)])]
        for zp in others:
            r = ep.exact(I, int(j), zp, z_t)
            for i, v in r["per_bird_kl"].items():
                acc[int(i)] += v / len(others)
        out[int(j)] = acc
    return out


def _sampled_influence(sim, z_t, I, cands, seed) -> tuple[dict, list, dict]:
    probe = FiniteProbe(sim, n_rollouts=PROBE_ROLLOUTS, seed=seed)
    res = probing.probe_sources(probe, I, cands, [z_t] * PROBE_REPEATS,
                                rng=np.random.default_rng(seed))
    return probing.influence_matrix(res, I), res["B_causal"], probe.budget()


def run_arm(sim, z_prefix, arm: str, seed: int, h_star: int, B_pred=None,
            theta=THETA_DEFAULT, q_support=Q_SUPPORT_DEFAULT,
            t_control=T_CONTROL, gate_params=None, k_act: int = K_ACT,
            I0=None, budget_schedule=None) -> dict:
    """One control episode.

    `z_prefix` is the REAL pre-control history of the episode, ending at the
    control start; its last row is the control start state. The detector
    re-proposes the interior from the growing observation record at every step,
    so the controller never holds a frozen interior.

    Two evaluation controls, both necessary for the arms to be comparable:

    * `I0` -- the collective detected at the control start. Task success is
      scored on THIS fixed set, exactly as Stage 6 scored it on its frozen
      interior. Scoring each arm on its own re-detected interior would reward an
      arm that simply lets the collective drift into an already-aligned region,
      and the re-detected interiors do diverge sharply between arms (63 to 153
      birds on one development seed). The current-interior score is still
      recorded, as a secondary number.
    * `budget_schedule` -- the per-step actuator count to match. The multicover
      arms stop when their own coverage rule is satisfied, typically at ~10 of a
      20-actuator cap, so an unconstrained `random_matched` would silently get
      twice the intervention budget. Passing the causal arm's realized schedule
      makes "matched budget" mean what it says.
    """
    rng = np.random.default_rng(10_000 + seed)
    z_prefix = np.asarray(z_prefix)
    n_pre = z_prefix.shape[0]
    hist = np.zeros((n_pre + t_control, sim.nn), dtype=int)
    hist[:n_pre] = z_prefix

    gate = sim.init_gates(gate_params, rng) if gate_params is not None else None
    frozen_A, last_A, records = None, [], []
    budget_total = dict(n_probe_calls=0, n_rollouts=0)
    I_t = None
    for step in range(t_control):
        cur = n_pre - 1 + step
        obs = observation_record(sim, hist[:cur + 1], cur)
        ok, _ = cd.propose(obs)
        if ok:
            I_t = (max(ok, key=lambda c: c.size).members if I_t is None
                   else max(ok, key=lambda c: len(set(c.members.tolist()) & set(I_t.tolist()))).members)
        if I_t is None:
            I_t = np.arange(sim.nn)[:20]
        I = np.array(sorted(int(x) for x in I_t))
        cands = near_exterior(sim.positions, I)
        cov = float("nan")

        budget = k_act if budget_schedule is None else int(budget_schedule[min(step, len(budget_schedule) - 1)])
        if arm == "no_control":
            A = []
        elif arm == "random_matched":
            A = sorted(rng.choice(cands, size=min(budget, len(cands)), replace=False).tolist()) \
                if cands else []
        elif arm == "predictive":
            A = sorted(int(j) for j in (B_pred or [])[:budget])
        elif arm == "adaptive_oracle":
            A, cov = multicover(_exact_influence(sim, hist[cur], I, cands), I,
                                k_act=k_act, theta=theta, q_support=q_support)
        elif arm == "frozen_causal":
            if frozen_A is None:
                infl, _, bud = _sampled_influence(sim, hist[cur], I, cands, seed + step)
                budget_total["n_probe_calls"] += bud["n_probe_calls"]
                budget_total["n_rollouts"] += bud["n_rollouts"]
                frozen_A, cov = multicover(infl, I, k_act=k_act, theta=theta, q_support=q_support)
            A = frozen_A
        elif arm == "adaptive_causal":
            if step % REINFER_EVERY == 0:
                infl, _, bud = _sampled_influence(sim, hist[cur], I, cands, seed + step)
                budget_total["n_probe_calls"] += bud["n_probe_calls"]
                budget_total["n_rollouts"] += bud["n_rollouts"]
                last_A, cov = multicover(infl, I, k_act=k_act, theta=theta, q_support=q_support)
            A = last_A
        else:
            raise ValueError(f"unknown arm {arm!r}")

        out = sim.step(hist[cur], rng, gate=gate,
                       forced_actions={int(j): int(h_star) for j in A})
        hist[cur + 1] = out["z_new"]
        if gate is not None:
            gate = sim.advance_gates(gate, gate_params, rng)
        records.append(dict(step=step, n_actuators=len(A), actuators=list(A),
                            support_coverage=cov, I_size=len(I),
                            target_fraction=float(np.mean(hist[cur + 1][np.asarray(
                                sorted(int(x) for x in (I0 if I0 is not None else I)))] == h_star)),
                            target_fraction_current=float(np.mean(hist[cur + 1][I] == h_star))))

    I = np.array(sorted(int(x) for x in I_t))
    I0 = np.array(sorted(int(x) for x in I0)) if I0 is not None else I
    return dict(arm=arm, seed=seed, h_star=h_star, k_act=int(k_act),
                actuator_schedule=[r["n_actuators"] for r in records],
                final_target_fraction=float(np.mean(hist[-1][I0] == h_star)),
                final_target_fraction_current_interior=float(np.mean(hist[-1][I] == h_star)),
                I0_size=len(I0),
                mean_actuators=float(np.mean([r["n_actuators"] for r in records])),
                final_I_size=len(I), records=records, probe_budget=budget_total,
                z_hist=hist[n_pre - 1:].tolist())


def target_heading(z0, I) -> int:
    modal = int(np.bincount(z0[np.asarray(I)], minlength=4).argmax())
    return rotate_cw(modal)
