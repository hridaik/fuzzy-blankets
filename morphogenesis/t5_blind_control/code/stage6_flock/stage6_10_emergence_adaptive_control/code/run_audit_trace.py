"""Stage 6.10 Part A, phase 1 -- instrumented replay of the frozen Stage 6.8
control episodes.

Calls Stage 6.8's OWN `adaptive_control.run_arm` so the trajectory is the frozen
one by construction, asserts the replayed `final_target_fraction` against
`stage6_8/data/control.json`, and then re-derives the per-step quantities the
science run never stored. Nothing is written back into Stage 6.8's data.

Per timestep per arm this records:
  detected interior I_t              structural interface B^struct
  exact effective causal B^do        sampled causal interface
  actuators, |A_t|                   per-actuator KL effect
  predicted one-step target gain     realized one-step target gain
  multi-step target gain             lineage metrics (size, J, turnover,
                                     Q_clump, cardinal components)

"Predicted gain" is the EXACT expected change in target alignment at tau=2
under the actuator set actually chosen -- the quantity a controller ought to be
maximizing -- computed with common random numbers against the no-action
baseline at the same state.
"""
from __future__ import annotations

import sys
import time

import numpy as np

from common_610 import (DATA_DIR, S68_DATA, dump_json, load_json, target_alignment)
from episode_data import make_simulator, run_episode, observation_record
import candidate_detection as cd
import adaptive_control as ac
import reference_truth as rt
from morphology import morphology

AUTH_TAU = 2          # first horizon at which an exterior actuator can act
AUTH_ROLL = 96        # rollouts for the sampled-horizon authority
TRACE_EVERY = 1       # per-step for the cheap quantities


def rederive_interiors(sim, z_hist, warm_prefix, t_control):
    """Reproduce run_arm's own online detection/continuation on its z_hist.

    run_arm re-detects every step and continues the lineage by maximum overlap;
    this replays exactly that, so I_t is the interior the controller actually
    used, not a fresh guess. Verified against the recorded I_size.
    """
    n_pre = warm_prefix.shape[0]
    hist = np.concatenate([warm_prefix, np.asarray(z_hist)[1:]], axis=0)
    out, I_t = [], None
    for step in range(t_control):
        cur = n_pre - 1 + step
        obs = observation_record(sim, hist[:cur + 1], cur)
        ok, _ = cd.propose(obs)
        if ok:
            I_t = (max(ok, key=lambda c: c.size).members if I_t is None
                   else max(ok, key=lambda c: len(set(c.members.tolist()) & set(I_t.tolist()))).members)
        if I_t is None:
            I_t = np.arange(sim.nn)[:20]
        out.append(np.array(sorted(int(x) for x in I_t)))
    return out


def main(limit_episodes=None):
    ctl = load_json(S68_DATA / "control.json")
    op, cal = ctl["operating_point"], ctl["calibration"]
    arms, k_act, horizon = ctl["arms"], ctl["K_ACT"], ctl["T_CONTROL"]
    t0 = ctl["t0"]
    sim = make_simulator(op["nn"], op["beta"], op["s"])
    L = int(round(sim.nn ** 0.5))
    snap = load_json(S68_DATA / "boundary_inference__snapshot.json")

    seeds = sorted({r["seed"] for r in ctl["runs"]})
    if limit_episodes:
        seeds = seeds[:limit_episodes]
    out = dict(protocol="stage6_10 Part A -- instrumented replay of frozen stage 6.8 control",
               source="stage6_8_dynamic_interactions/data/control.json",
               operating_point=op, arms=arms, k_act=k_act, horizon=horizon, t0=t0,
               auth_tau=AUTH_TAU, auth_rollouts=AUTH_ROLL,
               naming=dict(adaptive_oracle="Full-info causal heuristic (frozen arm name kept verbatim)"),
               episodes=[])

    for seed in seeds:
        rows = {r["arm"]: r for r in ctl["runs"] if r["seed"] == seed}
        if set(rows) != set(arms):
            continue
        Bpred = next((r["predictive"]["B_pred"] for r in snap["runs"]
                      if r["seed"] == seed and r["method"] == "affinity_louvain" and r["t"] == t0), None)
        res = run_episode(sim, seed, nt=t0 + 2, record_oracle=False)
        z_prefix = res.z_hist[:t0 + 1]
        obs = observation_record(sim, res.z_hist, t0)
        ok, _ = cd.propose(obs)
        I0 = np.array(sorted(max(ok, key=lambda c: c.size).members))
        h_star = ac.target_heading(res.z_hist[t0], I0)

        ep = dict(seed=seed, split=rows[arms[0]]["split"], h_star=int(h_star),
                  I0=[int(x) for x in I0], arms={})
        schedule = None
        for arm in arms:
            t_start = time.time()
            r = ac.run_arm(sim, z_prefix, arm, seed, h_star, B_pred=Bpred,
                           theta=cal["theta"], q_support=cal["q_support"],
                           t_control=horizon, k_act=k_act, I0=I0,
                           budget_schedule=(None if arm == "adaptive_causal" else schedule))
            if arm == "adaptive_causal":
                schedule = r["actuator_schedule"]
            assert abs(r["final_target_fraction"] - rows[arm]["final_target_fraction"]) < 1e-12, \
                f"replay diverged: seed {seed} arm {arm}"
            zh = np.array(r.pop("z_hist"))
            Is = rederive_interiors(sim, zh, z_prefix, horizon)

            steps = []
            for k, rec in enumerate(r["records"]):
                I_t = Is[k]
                assert len(I_t) == rec["I_size"], f"interior re-derivation mismatch at step {k}"
                z_t = zh[k]
                A = [int(x) for x in rec["actuators"]]
                cands = ac.near_exterior(sim.positions, I_t)
                Bs = [int(x) for x in rt.structural_interface(sim, z_t, I_t)]
                Bdo, dovals = rt.exact_do_interface(sim, z_t, I_t, candidates=cands)
                kl_per_act = {int(j): float(dovals.get(int(j), 0.0)) for j in A}
                pred_gain = (rt.set_authority(sim, z_t, I_t, h_star, A, tau=AUTH_TAU,
                                              rng_seed=100000 + 97 * k, n_roll=AUTH_ROLL)
                             if A else 0.0)
                realized = (target_alignment(zh[k + 1], I_t, h_star)
                            - target_alignment(z_t, I_t, h_star)) if k + 1 < len(zh) else float("nan")
                multi = (target_alignment(zh[min(k + AUTH_TAU, len(zh) - 1)], I_t, h_star)
                         - target_alignment(z_t, I_t, h_star))
                prev = Is[k - 1] if k else I_t
                sa, sb = set(I_t.tolist()), set(prev.tolist())
                m = morphology(I_t, L)
                steps.append(dict(
                    step=k, I_size=len(I_t), I=[int(x) for x in I_t],
                    B_struct_size=len(Bs), B_do_size=int(len(Bdo)),
                    B_struct=Bs, B_do=[int(x) for x in Bdo],
                    n_cands=len(cands), actuators=A, n_act=len(A),
                    kl_per_actuator=kl_per_act,
                    kl_total=float(sum(kl_per_act.values())),
                    pred_gain_tau=pred_gain,
                    realized_gain_1=realized,
                    multi_gain_tau=float(multi),
                    H_star_current=target_alignment(z_t, I_t, h_star),
                    H_star_I0=target_alignment(z_t, I0, h_star),
                    jaccard_prev=len(sa & sb) / max(1, len(sa | sb)),
                    turnover=len(sa - sb) / max(1, len(sa)),
                    q_clump=m["q_clump"], n_components=m["n_components"],
                ))
            ep["arms"][arm] = dict(
                final_target_fraction=r["final_target_fraction"],
                final_target_fraction_current_interior=r["final_target_fraction_current_interior"],
                mean_actuators=r["mean_actuators"], steps=steps,
                elapsed_s=round(time.time() - t_start, 1))
            print(f"seed {seed:<4} {arm:<18} final={r['final_target_fraction']:.3f} "
                  f"meanA={r['mean_actuators']:.1f} "
                  f"[{time.time()-t_start:.0f}s]", flush=True)
        out["episodes"].append(ep)
        dump_json(out, DATA_DIR / "audit_trace.json")
    dump_json(out, DATA_DIR / "audit_trace.json")
    print("wrote", DATA_DIR / "audit_trace.json")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
