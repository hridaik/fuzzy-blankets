"""Stage 6.10 Part A / H1 -- the fixed-K control.

H1 says the full-information arm may simply be spending more actuators. The
trace can show the spend difference but cannot settle the hypothesis, because
each arm's policy chooses its own count. This re-runs the two arms with the
actuator count FORCED EQUAL at several K, so budget cannot explain any ordering
that survives.

Uses Stage 6.8's own `run_arm` with `budget_schedule` pinned to a constant K,
on the same episodes and starting conditions. Frozen Stage 6.8 data is read
only.
"""
from __future__ import annotations

import numpy as np

from common_610 import DATA_DIR, S68_DATA, dump_json, load_json
from episode_data import make_simulator, run_episode, observation_record
import candidate_detection as cd
import adaptive_control as ac

K_GRID = (4, 8, 12, 16)
ARMS = ["adaptive_causal", "adaptive_oracle"]     # frozen arm names


def main():
    ctl = load_json(S68_DATA / "control.json")
    op, cal = ctl["operating_point"], ctl["calibration"]
    horizon, t0 = ctl["T_CONTROL"], ctl["t0"]
    sim = make_simulator(op["nn"], op["beta"], op["s"])
    snap = load_json(S68_DATA / "boundary_inference__snapshot.json")
    seeds = sorted({r["seed"] for r in ctl["runs"]})

    out = dict(protocol="stage6_10 Part A / H1 -- fixed-K comparison",
               naming=dict(adaptive_oracle="Full-info causal heuristic"),
               k_grid=list(K_GRID), horizon=horizon, arms=ARMS, runs=[])
    for K in K_GRID:
        for seed in seeds:
            Bpred = next((r["predictive"]["B_pred"] for r in snap["runs"]
                          if r["seed"] == seed and r["method"] == "affinity_louvain"
                          and r["t"] == t0), None)
            res = run_episode(sim, seed, nt=t0 + 2, record_oracle=False)
            z_prefix = res.z_hist[:t0 + 1]
            ok, _ = cd.propose(observation_record(sim, res.z_hist, t0))
            if not ok:
                continue
            I0 = np.array(sorted(max(ok, key=lambda c: c.size).members))
            h_star = ac.target_heading(res.z_hist[t0], I0)
            sched = [K] * horizon
            for arm in ARMS:
                r = ac.run_arm(sim, z_prefix, arm, seed, h_star, B_pred=Bpred,
                               theta=cal["theta"], q_support=cal["q_support"],
                               t_control=horizon, k_act=K, I0=I0,
                               budget_schedule=sched)
                r.pop("z_hist")
                out["runs"].append(dict(K=K, seed=seed, arm=arm,
                                        final=r["final_target_fraction"],
                                        mean_actuators=r["mean_actuators"]))
            print(f"K={K:<3} seed={seed:<4} " + "  ".join(
                f"{a}={[x for x in out['runs'] if x['K']==K and x['seed']==seed and x['arm']==a][0]['final']:.3f}"
                for a in ARMS), flush=True)
        dump_json(out, DATA_DIR / "audit_fixed_k.json")
    # summary
    summ = {}
    for K in K_GRID:
        row = {}
        for a in ARMS:
            v = [x["final"] for x in out["runs"] if x["K"] == K and x["arm"] == a]
            act = [x["mean_actuators"] for x in out["runs"] if x["K"] == K and x["arm"] == a]
            row[a] = dict(mean=float(np.mean(v)), sd=float(np.std(v)), n=len(v),
                          mean_actuators=float(np.mean(act)))
        d = np.array([x["final"] for x in out["runs"] if x["K"] == K and x["arm"] == ARMS[0]]) - \
            np.array([x["final"] for x in out["runs"] if x["K"] == K and x["arm"] == ARMS[1]])
        row["paired_diff_mean"] = float(d.mean())
        row["paired_diff_sd"] = float(d.std(ddof=1)) if len(d) > 1 else float("nan")
        summ[str(K)] = row
    out["summary"] = summ
    dump_json(out, DATA_DIR / "audit_fixed_k.json")
    print("\nwrote", DATA_DIR / "audit_fixed_k.json")
    for K, row in summ.items():
        print(f"K={K}: adaptive_causal {row['adaptive_causal']['mean']:.3f} | "
              f"full-info heuristic {row['adaptive_oracle']['mean']:.3f} | "
              f"paired diff {row['paired_diff_mean']:+.3f}")


if __name__ == "__main__":
    main()
