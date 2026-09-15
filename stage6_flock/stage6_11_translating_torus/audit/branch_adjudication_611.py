"""Stage 6.11B item 9: nine-branch causal adjudication from the five real
Stage 6.11 pre-control trigger states, with common random numbers.

Branches (all from the IDENTICAL trigger snapshot, same base RNG seed per
seed so branches are paired/comparable):
  1 no_control
  2 original_reproduced          (old near_exterior(3R) oracle pool, old
                                    one-shot d=1/tau=4 authority, refreshed
                                    every 8 real steps -- the ORIGINAL
                                    pipeline's own logic, re-run from CRN)
  3 old_set_one_shot              (same set branch 2 picks at t0, forced
                                    ONCE then released -- the estimand the
                                    old authority probe actually measured)
  4 old_set_held_actual_duration  (same set, held for the full 24-step
                                    control window -- what actually happened
                                    in the real run)
  5 matched_random_blind_exterior (random same-size subset of the blind
                                    nearest-M12 pool, held 24 steps)
  6 repaired_blind_authority      (blind pool, repaired A_S(tau=4,d=4),
                                    top-K with abstention, single-shot
                                    selection at t0, held 24 steps)
  7 repaired_direct_causal_restricted (blind pool restricted to blind
                                    B_causal survivors, then repaired
                                    authority/top-K, held 24 steps)
  8 exact_direct_interface_repaired  (privileged oracle B_D as the ONLY
                                    candidate pool -- reference upper bound)
  9 beam_search_benchmark        (privileged near_exterior(3R) pool, beam
                                    search over repaired A_S -- reference
                                    upper bound, no MCTS)

Single-shot actuator selection (branches 6-9 select ONCE at t0 and hold for
the full 24-step control window, rather than re-selecting every 8 steps like
branch 2) is a disclosed compute-budget simplification for this pass --
re-planning cadence for the REPAIRED controller is a separate question
(Part I of the original audit brief), not reopened here. Branch 2 keeps the
original refresh-every-8-steps cadence because that is what is being
reproduced.

d=tau=4 (not 8) for all repaired-authority branches: a disclosed
compute-budget choice (T_control=24 with hold=8 would need re-planning to
even use its full duration meaningfully within a single-shot design) that
still repairs the OLD d=1 mismatch --  d=4 exactly matches the OLD tau=4
evaluation horizon, so this at minimum removes the "one-shot-then-released"
mismatch inside the SAME horizon the original method already used. A d=8
spot-check is reported separately, at a reduced rollout budget, in
AUTHORITY_AND_SET_EFFECT_AUDIT.md, not repeated for all 9 branches.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))
import common_611  # noqa: E402,F401

from common_611 import DATA_DIR, L_BOX, dump_json  # noqa: E402
from flock_sim.model import UV4, ROT_CCW  # noqa: E402
from detect_69 import propose  # noqa: E402
from lineage_611 import LineageTracker611  # noqa: E402
from lineage_v2_611 import LineageTrackerV2  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402
from intervention_api_611 import FiniteProbeMoving611, near_exterior  # noqa: E402
import probing_611 as PR  # noqa: E402
import control_authority_611 as CA  # noqa: E402
from blind_pool_611 import nearest_M_pool  # noqa: E402
from authority_v2_611 import select_actuators_v2, beam_search  # noqa: E402

T_CONTROL = 24
T_RELEASE = 24
M_PROBE = 12
D_TAU_PRIMARY = 4
N_ROLLOUTS_REPAIRED = 15
N_ROLLOUTS_OLD = ROC.PROBE_ROLLOUTS_ONLINE, ROC.PROBE_REPEATS_ONLINE
AUTHORITY_ROLLOUTS_OLD = ROC.AUTHORITY_ROLLOUTS_ONLINE
K_MAX = 8
BEAM_WIDTH = 2
AFFINITY_WINDOW = ROC.AFFINITY_WINDOW


def old_select_actuators(mf, r, z, interior, target_heading, seed_offset):
    """Exactly reproduces run_online_control_611.py's control-step decision
    (near_exterior(3R) oracle pool, old one-shot-then-released authority,
    old rollout budgets) for ONE refresh, from a fresh CRN seed."""
    exterior_pool = near_exterior(mf, r, interior, radius_factor=3.0)
    if not exterior_pool:
        return dict(B_C=[], B_causal=[], exterior_pool=[])
    probes = [FiniteProbeMoving611(mf, r, n_rollouts=N_ROLLOUTS_OLD[0], seed=10_000 + seed_offset + rep)
              for rep in range(N_ROLLOUTS_OLD[1])]
    rng = np.random.default_rng(20_000 + seed_offset)
    b_causal = PR.probe_sources(probes, interior, exterior_pool, z, rng, n_boot=100)
    from intervention_api_611 import MultiStepAuthorityProbe
    auth_probe = MultiStepAuthorityProbe(mf, r, z, tau=ROC.TAU_CONTROL, n_rollouts=AUTHORITY_ROLLOUTS_OLD,
                                           seed=30_000 + seed_offset)
    b_c = CA.select_actuators(auth_probe, interior, exterior_pool, target_heading, k_act=K_MAX)
    return dict(B_C=b_c["B_C"], B_causal=b_causal["B_causal"], exterior_pool=exterior_pool)


def simulate(mf, r0, z0, rng_seed, policy, T_control=T_CONTROL, T_release=T_RELEASE):
    """policy(step, r, z) -> forced dict or None. Called for every control
    step (0..T_control-1); release steps (T_control..T_control+T_release-1)
    are always unforced."""
    r, z = r0.copy(), z0.copy()
    rng = np.random.default_rng(rng_seed)
    r_hist, z_hist = [r.copy()], [z.copy()]
    for step in range(T_control):
        forced = policy(step, r, z)
        r, z, _ = mf.step(r, z, rng, forced_actions=forced)
        r_hist.append(r.copy()); z_hist.append(z.copy())
    for _ in range(T_release):
        r, z, _ = mf.step(r, z, rng, forced_actions=None)
        r_hist.append(r.copy()); z_hist.append(z.copy())
    return np.stack(r_hist), np.stack(z_hist)


def hold_policy(S, h_star, hold_steps):
    S = list(S)
    def policy(step, r, z):
        return {int(j): int(h_star) for j in S} if step < hold_steps else None
    return policy


def track_trajectory(r_hist, z_hist, seed_interior, L):
    """Runs candidate detection + BOTH trackers over a branch's own
    trajectory, seeded from the material set present at target introduction
    (item 10's fixed reference). Returns end-of-control and end-of-release
    MAP interiors for v1 and v2."""
    tracker1 = LineageTracker611(L=L, uv4=UV4)
    tracker1.start(seed_interior, r_hist[0], z_hist[0], 0)
    tracker2 = LineageTrackerV2(L=L, uv4=UV4)
    tracker2.start(seed_interior, r_hist[0], z_hist[0], 0)
    z_window = [z_hist[0]]
    snapshot = {}
    for t in range(1, len(r_hist)):
        r, z = r_hist[t], z_hist[t]
        z_window.append(z)
        if len(z_window) > AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r, z_window, L) if len(z_window) >= 2 else []
        if tracker1.hypotheses:
            tracker1.update(cands, r, z, t)
            if not tracker1.hypotheses and cands:
                tracker1 = LineageTracker611(L=L, uv4=UV4)
                tracker1.start(cands[0], r, z, t)
        if tracker2.lineages:
            tracker2.update(cands, r, z, t)
            if not tracker2.lineages and cands:
                tracker2.start(cands[0], r, z, t)
        if t == T_CONTROL:
            m1 = max(tracker1.hypotheses, key=lambda h: h.prob).members if tracker1.hypotheses else np.array([], int)
            m2 = tracker2.dominant().members if tracker2.lineages else np.array([], int)
            snapshot["end_control"] = dict(v1=m1.tolist(), v2=m2.tolist())
    m1 = max(tracker1.hypotheses, key=lambda h: h.prob).members if tracker1.hypotheses else np.array([], int)
    m2 = tracker2.dominant().members if tracker2.lineages else np.array([], int)
    snapshot["end_release"] = dict(v1=m1.tolist(), v2=m2.tolist())
    return snapshot


def field_direction_readout(r, z, members, L, radius=3.0, target_heading=None):
    """ID-independent readout: centroid of the given member set (soft
    anchor only), then the fraction of ALL nearby birds (not just tracked
    members) currently at target_heading within `radius` of that centroid."""
    from identity_69 import centroid
    from geometry_611 import torus_delta
    if len(members) == 0 or target_heading is None:
        return None
    c = centroid(r[members], L)
    d = torus_delta(r, c, L)
    D = np.sqrt((d ** 2).sum(-1))
    near = D <= radius
    if not near.any():
        return None
    return float((z[near] == target_heading).mean())


def frac_at_target(z, ids, target_heading):
    ids = np.asarray(ids, dtype=int)
    if len(ids) == 0:
        return None
    return float((z[ids] == target_heading).mean())


def run_seed(seed: int, trigger: dict, mf) -> dict:
    r0 = np.array(trigger["r"]); z0 = np.array(trigger["z"], dtype=int)
    interior0 = np.array(trigger["interior_v1"], dtype=int)
    h_star = trigger["target_heading"]
    L = L_BOX
    base_seed = 5_000_000 + seed

    blind_pool = nearest_M_pool(interior0, r0, L, M_PROBE)
    oracle_pool = near_exterior(mf, r0, interior0, radius_factor=3.0)
    B_D_true = mf.oracle_B_D(r0, z0, interior0).tolist()   # reference only

    # ---- branch 2 needs its own refresh-aware policy (stateful) ----
    def original_policy_factory():
        state = dict(B_C=[], age=999)
        def policy(step, r, z):
            if state["age"] >= 8 or step == 0:
                sel = old_select_actuators(mf, r, z, interior0, h_star, seed_offset=seed * 1000 + step)
                state["B_C"] = sel["B_C"]
                state["age"] = 0
            else:
                state["age"] += 1
            return {int(j): int(h_star) for j in state["B_C"]} if state["B_C"] else None
        return policy

    branches = {}

    # branch 1: no control
    branches["no_control"] = dict(policy=lambda step, r, z: None, meta={})

    # branch 2: original reproduced
    branches["original_reproduced"] = dict(policy=original_policy_factory(), meta={})

    # old set (computed once, reused by branches 3 and 4)
    old_sel = old_select_actuators(mf, r0, z0, interior0, h_star, seed_offset=seed * 1000)
    old_S = old_sel["B_C"]
    branches["old_set_one_shot"] = dict(policy=hold_policy(old_S, h_star, hold_steps=1),
                                          meta=dict(S=old_S, B_causal=old_sel["B_causal"]))
    branches["old_set_held_actual_duration"] = dict(policy=hold_policy(old_S, h_star, hold_steps=T_CONTROL),
                                                       meta=dict(S=old_S))

    # matched random blind set (same size as old_S, from blind pool)
    rng_rand = np.random.default_rng(base_seed + 1)
    k_rand = min(len(old_S) if old_S else K_MAX, len(blind_pool))
    rand_S = sorted(int(x) for x in rng_rand.choice(blind_pool, size=k_rand, replace=False)) if blind_pool else []
    branches["matched_random_blind_exterior"] = dict(policy=hold_policy(rand_S, h_star, hold_steps=T_CONTROL),
                                                        meta=dict(S=rand_S))

    # repaired blind authority
    sel6 = select_actuators_v2(mf, r0, z0, interior0, blind_pool, h_star, tau=D_TAU_PRIMARY, d=D_TAU_PRIMARY,
                                 n_rollouts=N_ROLLOUTS_REPAIRED, k_max=K_MAX, seed=base_seed + 2)
    branches["repaired_blind_authority"] = dict(policy=hold_policy(sel6["S"], h_star, hold_steps=T_CONTROL),
                                                   meta=dict(S=sel6["S"], abstained=sel6["abstained"],
                                                              n_scored=len(sel6["scores"])))

    # repaired, restricted to blind B_causal survivors
    probes7 = [FiniteProbeMoving611(mf, r0, n_rollouts=ROC.PROBE_ROLLOUTS_ONLINE, seed=40_000 + base_seed + rep)
                for rep in range(ROC.PROBE_REPEATS_ONLINE)]
    rng7 = np.random.default_rng(base_seed + 3)
    bcausal_blind = PR.probe_sources(probes7, interior0, blind_pool, z0, rng7, n_boot=100)
    pool7 = bcausal_blind["B_causal"]
    if pool7:
        sel7 = select_actuators_v2(mf, r0, z0, interior0, pool7, h_star, tau=D_TAU_PRIMARY, d=D_TAU_PRIMARY,
                                     n_rollouts=N_ROLLOUTS_REPAIRED, k_max=K_MAX, seed=base_seed + 4)
        S7, abst7 = sel7["S"], sel7["abstained"]
    else:
        S7, abst7 = [], True
    branches["repaired_direct_causal_restricted"] = dict(policy=hold_policy(S7, h_star, hold_steps=T_CONTROL),
                                                            meta=dict(S=S7, abstained=abst7,
                                                                       blind_B_causal_pool_size=len(pool7)))

    # exact direct-interface (privileged reference)
    if B_D_true:
        sel8 = select_actuators_v2(mf, r0, z0, interior0, B_D_true, h_star, tau=D_TAU_PRIMARY, d=D_TAU_PRIMARY,
                                     n_rollouts=N_ROLLOUTS_REPAIRED, k_max=K_MAX, seed=base_seed + 5)
        S8, abst8 = sel8["S"], sel8["abstained"]
    else:
        S8, abst8 = [], True
    branches["exact_direct_interface_repaired"] = dict(policy=hold_policy(S8, h_star, hold_steps=T_CONTROL),
                                                          meta=dict(S=S8, abstained=abst8, n_true_parents=len(B_D_true)))

    # beam-search benchmark (privileged reference)
    beam9 = beam_search(mf, r0, z0, interior0, oracle_pool, h_star, tau=D_TAU_PRIMARY, d=D_TAU_PRIMARY,
                          n_rollouts=N_ROLLOUTS_REPAIRED, k_max=K_MAX, beam_width=BEAM_WIDTH, seed=base_seed + 6)
    branches["beam_search_benchmark"] = dict(policy=hold_policy(beam9["S"], h_star, hold_steps=T_CONTROL),
                                                meta=dict(S=beam9["S"], A=beam9["A"], ci=beam9["ci"]))

    results = {}
    for name, br in branches.items():
        print(f"    branch {name} ...", flush=True)
        r_hist, z_hist = simulate(mf, r0, z0, rng_seed=base_seed, policy=br["policy"])
        tr = track_trajectory(r_hist, z_hist, interior0, L)

        end_control_z, end_release_z = z_hist[T_CONTROL], z_hist[-1]
        readouts = dict(
            v1_end_control=frac_at_target(end_control_z, tr["end_control"]["v1"], h_star),
            v1_end_release=frac_at_target(end_release_z, tr["end_release"]["v1"], h_star),
            v2_end_control=frac_at_target(end_control_z, tr["end_control"]["v2"], h_star),
            v2_end_release=frac_at_target(end_release_z, tr["end_release"]["v2"], h_star),
            original_material_end_control=frac_at_target(end_control_z, interior0, h_star),
            original_material_end_release=frac_at_target(end_release_z, interior0, h_star),
            field_direction_end_control=field_direction_readout(r_hist[T_CONTROL], end_control_z,
                                                                    tr["end_control"]["v2"] or interior0, L,
                                                                    target_heading=h_star),
            field_direction_end_release=field_direction_readout(r_hist[-1], end_release_z,
                                                                    tr["end_release"]["v2"] or interior0, L,
                                                                    target_heading=h_star),
            frac_at_target_start=frac_at_target(z0, interior0, h_star),
            interior_size_end_control=len(tr["end_control"]["v1"]),
            interior_size_end_release=len(tr["end_release"]["v1"]),
        )
        results[name] = dict(meta=br["meta"], readouts=readouts)
        print(f"      -> {readouts}", flush=True)

    return dict(seed=seed, t0=trigger["t0"], target_heading=h_star, blind_pool_size=len(blind_pool),
                 oracle_pool_size=len(oracle_pool), n_true_direct_parents=len(B_D_true),
                 branches=results)


def main():
    trigger_states = json.load(open(AUDIT_DIR / "trigger_states_611.json"))
    mf = ROC.make_flock()
    all_results = {}
    for seed_str, trigger in trigger_states.items():
        seed = int(seed_str)
        print(f"[branch_adjudication] seed {seed} (t0={trigger['t0']}) ...", flush=True)
        out = run_seed(seed, trigger, mf)
        all_results[seed] = out
        dump_json(out, AUDIT_DIR / f"branch_adjudication_611__seed{seed}.json")
    dump_json(all_results, AUDIT_DIR / "branch_adjudication_611__all.json")
    print("[branch_adjudication] done", flush=True)


if __name__ == "__main__":
    main()
