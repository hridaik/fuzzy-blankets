"""Stage 6.10 Part C/H -- has the full-model benchmark's search converged?

Part H uses the benchmark to decide whether a task is controllable at all, so
the benchmark's own search budget has to be shown not to be the binding
constraint. At this interface size an exhaustive search is out of reach
(C(25,6) = 177,100 > EXHAUSTIVE_MAX_SUBSETS), so Part H runs a beam search, and
its value is therefore a LOWER BOUND on what full-model control can achieve.

That asymmetry matters and is stated wherever the result is used:
  * "the task IS controllable" is only strengthened by a lower bound;
  * "the task is NOT controllable" would be weakened by it, so that conclusion
    is only drawn where the objective has stopped climbing with search budget.

This script re-optimizes the same states across beam widths, rollout counts and
random seeds, and reports the spread.
"""
from __future__ import annotations

import sys

import numpy as np

from common_610 import DATA_DIR, dump_json, load_json, rotate_cw
from episode_data import make_simulator, run_episode, observation_record
import candidate_detection as cd
import reference_truth as rt
import full_model_benchmark as fmb
from closed_loop import qualifying_start

T0 = 60
BUDGETS = ((4, 32), (8, 64), (16, 128))
SEEDS_SEARCH = (0, 1, 2)


def main(beta, s, seeds, frac, tau=3, tag="main"):
    nn, L = 400, 20
    sim = make_simulator(nn, beta, s)
    out = dict(protocol="stage6_10 -- full-model benchmark search convergence",
               regime=dict(nn=nn, beta=beta, s=s), t0=T0, tau=tau,
               actuator_fraction=frac, budgets=[list(b) for b in BUDGETS],
               search_seeds=list(SEEDS_SEARCH), states=[])
    for seed in seeds:
        res = run_episode(sim, seed, nt=T0 + 2, record_oracle=False)
        ok, _ = cd.propose(observation_record(sim, res.z_hist, T0))
        I0 = qualifying_start(ok, L)
        if I0 is None:
            continue
        z = res.z_hist[T0]
        h_star = rotate_cw(int(np.bincount(z[I0], minlength=4).argmax()))
        B = [int(x) for x in rt.structural_interface(sim, z, I0)]
        k = max(1, int(round(frac * len(B))))
        rows = []
        for bw, nr in BUDGETS:
            for sd in SEEDS_SEARCH:
                S, v, info = fmb.optimize(sim, z, I0, h_star, B, k, tau=tau,
                                          n_roll=nr, rng_seed=sd, method="beam",
                                          beam_width=bw)
                rows.append(dict(beam_width=bw, n_roll=nr, seed=sd, value=float(v),
                                 n_eval=info["n_eval"], size=len(S)))
        by = {}
        for bw, nr in BUDGETS:
            v = [r["value"] for r in rows if r["beam_width"] == bw]
            by[f"bw{bw}"] = dict(mean=float(np.mean(v)), sd=float(np.std(v)))
        means = [by[f"bw{bw}"]["mean"] for bw, _ in BUDGETS]
        out["states"].append(dict(seed=seed, n_interface=len(B), k_act=k,
                                  h_star=int(h_star), rows=rows, by_budget=by,
                                  climb_smallest_to_largest=float(means[-1] - means[0]),
                                  n_subsets_exhaustive=fmb.n_subsets(len(B), k)))
        print(f"seed {seed:<4} |B|={len(B):<3} k={k:<2} " +
              "  ".join(f"bw{bw}={by[f'bw{bw}']['mean']:+.3f}" for bw, _ in BUDGETS) +
              f"   climb={means[-1]-means[0]:+.3f}", flush=True)
        dump_json(out, DATA_DIR / f"benchmark_convergence__{tag}.json")

    climbs = [st["climb_smallest_to_largest"] for st in out["states"]]
    out["mean_climb"] = float(np.mean(climbs)) if climbs else float("nan")
    out["max_climb"] = float(np.max(climbs)) if climbs else float("nan")
    out["converged"] = bool(out["max_climb"] < 0.05)
    dump_json(out, DATA_DIR / f"benchmark_convergence__{tag}.json")
    print(f"\nmean climb {out['mean_climb']:+.4f}  max {out['max_climb']:+.4f}  "
          f"converged={out['converged']} (threshold 0.05 objective units)")


if __name__ == "__main__":
    main(0.4, 0.75, list(range(6)), float(sys.argv[1]) if len(sys.argv) > 1 else 0.5)
