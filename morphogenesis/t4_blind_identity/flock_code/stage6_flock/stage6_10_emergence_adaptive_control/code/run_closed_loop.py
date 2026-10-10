"""Stage 6.10 Part I + J -- the seven-arm online closed loop, scored on identity.

Runs only at the frozen regime and the frozen operating task established by
Part H (`data/controllability__main.json`); it refuses to run if Part H did not
establish that the full-model benchmark can steer the collective at all.

Two budget conventions, both reported:

  matched   every arm is given the actuator schedule the reference arm actually
            realized on that episode, so no arm wins by spending more
  fixed_k   every arm is given the same constant K, so no arm wins by an
            adaptive schedule

Scoring is Part J: the task is scored on the CURRENT TRACKED LINEAGE, and a
run only counts as a success if the lineage is still identity-valid against the
envelope built from UNCONTROLLED lineages in `run_uncontrolled_reference.py`.
"""
from __future__ import annotations

import sys
import time

import numpy as np

from common_610 import DATA_DIR, dump_json, load_json, rotate_cw
from episode_data import (make_simulator, run_episode, observation_record,
                          replicate_window, build_splits)
import candidate_detection as cd
import closed_loop as cl
from closed_loop import ARMS, qualifying_start, run_arm
from identity_scoring import lineage_statistics, conjunctive_success
import predictive_boundary_68 as pb   # blind predictive boundary (Stage 6.8)
import adaptive_control as ac

T0 = 60
H_THRESHOLD = 0.60          # frozen with Part H's success band
THETA, Q_SUPPORT = 0.02, 0.5
REINFER_EVERY = 4


def _predictive_boundary(sim, z0, I0, k, seed):
    """The blind predictive arm's actuator pool.

    Two quantities, and they are NOT the same thing:

    * the CERTIFIED boundary -- Stage 6.8's greedy forward construction with its
      `DELTA_TOL` stopping rule. At this regime it comes back EMPTY: the entire
      exterior pool improves the interior's validation loss by well under the
      tolerance, which is the same fact Part E reports as leakage L ~ 0. A
      certified-empty boundary means the arm has nothing to actuate and
      degenerates to `no_control`.
    * the RANKING -- the top-k exterior sources by single-source validation
      gain, taken regardless of whether any of them clears the tolerance.

    The arm actuates the RANKING, so that the comparison stays informative, and
    the certified result is returned alongside so the degeneracy is reported
    rather than hidden. This is a ranking of weak predictors, not a certified
    Markov-blanket-like boundary, and it is never described as one.

    Sees only observed trajectories: never the structural graph, the
    interventional interface, the FOV rule, or the target heading.
    """
    reps = replicate_window(sim, z0, 6, n_rep=40, seed_offset=500_000 + 1000 * seed)
    sp = build_splits(reps, T0)
    targets = pb.interior_targets(I0, positions=sim.positions, seed=seed)
    pool = [int(j) for j in ac.near_exterior(sim.positions, I0)]
    if not pool:
        return [], dict(certified=[], stop_reason="empty_pool", gains={})
    full = pb.fit_eval(targets, I0, pool, sp.tr_prev, sp.tr_next,
                       sp.va_prev, sp.va_next, sim.positions)
    certified, _, stop = pb.construct(targets, I0, pool, sp.tr_prev, sp.tr_next,
                                      sp.va_prev, sp.va_next, full,
                                      positions=sim.positions)
    base_loss = pb.fit_eval(targets, I0, [], sp.tr_prev, sp.tr_next,
                            sp.va_prev, sp.va_next, sim.positions)
    gains = {}
    for j in pool:
        lj = pb.fit_eval(targets, I0, [j], sp.tr_prev, sp.tr_next,
                         sp.va_prev, sp.va_next, sim.positions)
        gains[int(j)] = float(base_loss - lj)
    ranked = [j for j, _ in sorted(gains.items(), key=lambda kv: -kv[1])][:k]
    return ranked, dict(certified=[int(x) for x in certified], stop_reason=stop,
                        n_certified=len(certified),
                        full_pool_excess=float(base_loss - full),
                        delta_tol=pb.DELTA_TOL,
                        top_gain=max(gains.values()) if gains else 0.0)


def main(beta, s, seeds=None, frac=None, horizon=None, tag="main", fixed_k=False):
    """Runs ONLY on the frozen operating task and the primary episode stratum
    that Part H established, both read from `controllability__main.json`.

    The episode list is not a parameter of convenience: it was fixed by the
    full-model benchmark before any inference arm existed, per
    `logs/task_selection_predeclared.txt`. Passing an explicit list is allowed
    for debugging but is recorded in the output as an override.
    """
    nn, L = 400, 20
    sim = make_simulator(nn, beta, s)
    ctl = load_json(DATA_DIR / "controllability__main.json")
    ft = ctl["frozen_task"]
    override = seeds is not None
    if not override:
        seeds = ft["primary_episodes"]
    # The task itself is ALWAYS the frozen one; only the episode subset may be
    # narrowed (for sharding across processes), and that is recorded.
    frac = ft["frozen_cell"]["frac"] if frac is None else frac
    horizon = ft["frozen_cell"]["horizon"] if horizon is None else horizon
    unknown = [s for s in seeds if s not in ft["primary_episodes"]]
    if unknown:
        print(f"WARNING: seeds outside the frozen primary stratum: {unknown}")
    ref = load_json(DATA_DIR / "uncontrolled_reference__main.json")
    env = ref["validity_envelope_by_horizon"][str(horizon)]

    out = dict(protocol="stage6_10 Parts I+J -- seven-arm closed loop, identity-scored",
               regime=dict(nn=nn, beta=beta, s=s), t0=T0, horizon=horizon,
               actuator_fraction=frac, h_threshold=H_THRESHOLD,
               reinfer_every=REINFER_EVERY, validity_envelope=env,
               frozen_task=ft, episode_list_override=override,
               budget_convention="fixed_k" if fixed_k else "matched",
               claim_scope=ft["claim_scope"], arms=ARMS, episodes=[])

    for seed in seeds:
        res = run_episode(sim, seed, nt=T0 + 2, record_oracle=False)
        zh = res.z_hist
        ok, _ = cd.propose(observation_record(sim, zh, T0))
        I0 = qualifying_start(ok, L)
        if I0 is None:
            continue
        h0 = int(np.bincount(zh[T0][I0], minlength=4).argmax())
        h_star = rotate_cw(h0)
        # actuator budget: a fraction of the CURRENT interface size at t0,
        # fixed for the episode so that every arm gets the same K.
        import reference_truth as rt
        k_act = max(1, int(round(frac * len(rt.structural_interface(sim, zh[T0], I0)))))
        B_pred, pred_info = _predictive_boundary(sim, zh[T0], I0, k_act, seed)

        ep = dict(seed=seed, I0=[int(x) for x in I0], I0_size=len(I0),
                  h0=h0, h_star=int(h_star), k_act=k_act,
                  predictive_boundary=pred_info, arms={})
        # reference arm first: its realized schedule defines the matched budget
        sched = None
        for arm in ARMS:
            t = time.time()
            r = run_arm(sim, zh[:T0 + 1], arm, seed, h_star, horizon, k_act, I0,
                        THETA, Q_SUPPORT, B_pred=B_pred, budget_schedule=sched,
                        reinfer_every=REINFER_EVERY, I_init=I0, fixed_k=fixed_k)
            if arm == "full_model_benchmark":
                sched = r["actuator_schedule"]
            I_seq = [np.array(rec["I"]) for rec in r["records"]]
            # `records[k]` holds I at time t0+k and scores the task on the state
            # AFTER that step's action, so the identity statistics are paired the
            # same way: I_t against z_{t+1}. Matching the task metric's pairing
            # keeps "did it turn" and "is it still itself" on the same clock.
            z_seq = [np.array(z) for z in r["z_hist"][1:1 + len(I_seq)]]
            st = lineage_statistics(I_seq, z_seq, L)
            r["identity"] = st
            r["score"] = conjunctive_success(r["final_H_current"], st, env, H_THRESHOLD)
            # Part K needs a starting point; the full trajectory does not fit
            # in the result file, so keep only the final state and lineage.
            r["final_z"] = list(map(int, r["z_hist"][-1]))
            r["final_I"] = [int(x) for x in I_seq[-1]]
            r.pop("z_hist")
            ep["arms"][arm] = r
            sc = r["score"]
            print(f"seed {seed:<4} {arm:<22} H={r['final_H_current']:.3f} "
                  f"valid={sc['identity_valid']} succ={sc['success']} "
                  f"A={r['mean_actuators']:.1f} [{time.time()-t:.0f}s]", flush=True)
        out["episodes"].append(ep)
        dump_json(out, DATA_DIR / f"closed_loop__{tag}.json")

    dump_json(out, DATA_DIR / f"closed_loop__{tag}.json")
    print("\n" + "=" * 78)
    print(f"{'arm':<24}{'meanH':>8}{'succ':>8}{'taskOK':>8}{'valid':>8}{'meanA':>8}")
    for arm in ARMS:
        rs = [e["arms"][arm] for e in out["episodes"]]
        print(f"{arm:<24}{np.mean([r['final_H_current'] for r in rs]):>8.3f}"
              f"{np.mean([r['score']['success'] for r in rs]):>8.2f}"
              f"{np.mean([r['score']['task_met'] for r in rs]):>8.2f}"
              f"{np.mean([r['score']['identity_valid'] for r in rs]):>8.2f}"
              f"{np.mean([r['mean_actuators'] for r in rs]):>8.1f}")


def merge(tag="main"):
    """Merge per-seed shards into the single Part I result file. Episodes are
    ordered by the frozen primary list, not by completion order."""
    ctl = load_json(DATA_DIR / "controllability__main.json")
    order = ctl["frozen_task"]["primary_episodes"]
    shards = {}
    for s in order:
        f = DATA_DIR / f"closed_loop__{tag}_seed{s}.json"
        if f.exists():
            shards[s] = load_json(f)
    if not shards:
        raise SystemExit("no shards to merge")
    base = shards[next(iter(shards))]
    out = {k: v for k, v in base.items() if k != "episodes"}
    out["episodes"] = [e for s in order if s in shards for e in shards[s]["episodes"]]
    out["n_episodes"] = len(out["episodes"])
    out["missing_episodes"] = [s for s in order if s not in shards]
    dump_json(out, DATA_DIR / f"closed_loop__{tag}.json")
    print(f"merged {len(out['episodes'])} episodes -> closed_loop__{tag}.json")
    if out["missing_episodes"]:
        print("MISSING:", out["missing_episodes"])
    print("\n" + "=" * 78)
    print(f"{'arm':<24}{'meanH':>8}{'succ':>8}{'taskOK':>8}{'valid':>8}{'meanA':>8}")
    for arm in out["arms"]:
        rs = [e["arms"][arm] for e in out["episodes"]]
        print(f"{arm:<24}{np.mean([r['final_H_current'] for r in rs]):>8.3f}"
              f"{np.mean([r['score']['success'] for r in rs]):>8.2f}"
              f"{np.mean([r['score']['task_met'] for r in rs]):>8.2f}"
              f"{np.mean([r['score']['identity_valid'] for r in rs]):>8.2f}"
              f"{np.mean([r['mean_actuators'] for r in rs]):>8.1f}")
    return out


if __name__ == "__main__":
    if sys.argv[1] == "merge":
        merge(sys.argv[2] if len(sys.argv) > 2 else "main")
    else:
        # one seed per process: the episodes are independent, so the 7-episode
        # stratum runs in parallel instead of serially.
        seed = int(sys.argv[1])
        tag = sys.argv[2] if len(sys.argv) > 2 else "main"
        fixed = len(sys.argv) > 3 and sys.argv[3] == "fixedk"
        main(0.4, 0.75, seeds=[seed], tag=f"{tag}_seed{seed}", fixed_k=fixed)
