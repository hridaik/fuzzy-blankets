"""Guidance experiment runner (task brief §§35-37).

Runs only on gate-passing episodes, and only after `run_boundary_69.py` has
shown that detection and interface inference work on the moving model.

Learning Stage 6.8's lesson explicitly: a FEASIBILITY check on the oracle arm
alone comes first, so that a failure of the whole task at this scale is not
mistaken for a failure of the inferred interface.
"""
from __future__ import annotations

import sys

import numpy as np

from common_69 import (ModelParams, dump_json, load_json, DATA_DIR, N_BIRDS, L_BOX,
                       R_RADIUS, V_SPEED, BETA, RHO, OMEGA)
from moving_flock import MovingFlock
import detect_69 as det
import guidance as g

T_CONTROL = 60
ARMS = ["adaptive_causal", "no_control", "adaptive_oracle", "random_matched",
        "interior_forcing"]
FEASIBILITY_GRID = [(12, 40), (24, 40), (24, 60), (36, 60)]
FEASIBILITY_TARGET_RADII = 3.0     # oracle arm's mean path error must beat this


def _setup(mf, seed, t0):
    res = mf.run(nt=t0 + 2, seed=seed)
    r0, z0 = res.r_hist[t0], res.z_hist[t0]
    zw = res.z_hist[max(0, t0 - det.W_AFFINITY + 1):t0 + 1]
    cands = det.propose(r0, zw, mf.L)
    if not cands:
        return None
    I0 = cands[0]
    from identity_69 import centroid
    c0 = centroid(r0[I0], mf.L)
    return r0, z0, I0, c0


def main(mode="run"):
    gate = load_json(DATA_DIR / "translation_gate.json")
    passing = [e for e in gate["episodes"] if e["passes"]]
    if not passing:
        raise SystemExit("translation gate did not pass; no guidance experiment is run")
    mf = MovingFlock(N=N_BIRDS, L=L_BOX, R=R_RADIUS, v=V_SPEED,
                     params=ModelParams(beta=BETA, precB=RHO, precC=OMEGA))
    seeds = [e["seed"] for e in passing]
    # Scope reduction, declared here: 3 development + 3 held-out episodes rather
    # than 4 + 4. The adaptive_causal arm re-probes online and costs ~10 min of
    # simulator time per episode; at 5 arms this is the difference between a
    # 2.5-hour and a 1.5-hour run. It reduces power, which is stated in
    # RESULTS_6_9.md, and it is applied to every arm equally.
    dev, held = seeds[0::2][:3], seeds[1::2][:3]

    if mode == "feasibility":
        rows = []
        for k_act, horizon in FEASIBILITY_GRID:
            errs = []
            for seed in dev:
                ep = next(e for e in gate["episodes"] if e["seed"] == seed)
                s = _setup(mf, seed, ep["t_start"] + 10)
                if s is None:
                    continue
                r0, z0, I0, c0 = s
                path = g.l_shaped_path(c0, mf.L, n1=horizon // 2, n2=horizon, speed=V_SPEED)
                out = g.run_arm(mf, r0, z0, "adaptive_oracle", seed, path, horizon,
                                k_act=k_act)
                if out.get("ok"):
                    errs.append(out["mean_path_error_radii"])
            m = float(np.mean(errs)) if errs else float("nan")
            rows.append(dict(k_act=k_act, horizon=horizon, oracle_mean_path_error_radii=m,
                             n=len(errs)))
            print(f"K_act={k_act:<3} horizon={horizon:<3} oracle_mean_path_error="
                  f"{m:.2f} R", flush=True)
        feas = [r for r in rows if r["oracle_mean_path_error_radii"] < FEASIBILITY_TARGET_RADII]
        chosen = min(feas, key=lambda r: (r["k_act"], r["horizon"])) if feas else None
        dump_json(dict(grid=rows, target_radii=FEASIBILITY_TARGET_RADII, chosen=chosen,
                       rule="smallest (K_act, horizon) whose oracle mean path error beats "
                            "the target; only the oracle arm was run"),
                  DATA_DIR / "guidance_feasibility.json")
        print("chosen:", chosen)
        return

    feas = load_json(DATA_DIR / "guidance_feasibility.json")
    chosen, below = feas["chosen"], False
    if chosen is None:
        chosen = min(feas["grid"], key=lambda r: r["oracle_mean_path_error_radii"])
        below = True
    k_act, horizon = chosen["k_act"], chosen["horizon"]

    out = dict(protocol="stage6_9 guidance experiment", model=gate["model"],
               setting=chosen, below_feasibility_threshold=below, arms=ARMS,
               t_control=horizon, k_act=k_act, dev_seeds=dev, heldout_seeds=held,
               runs=[])
    for split, ss in (("dev", dev), ("heldout", held)):
        for seed in ss:
            ep = next(e for e in gate["episodes"] if e["seed"] == seed)
            s = _setup(mf, seed, ep["t_start"] + 10)
            if s is None:
                print(f"seed {seed}: no candidate at control start, skipped", flush=True)
                continue
            r0, z0, I0, c0 = s
            path = g.l_shaped_path(c0, mf.L, n1=horizon // 2, n2=horizon, speed=V_SPEED)
            schedule = None
            for arm in ARMS:
                res = g.run_arm(mf, r0, z0, arm, seed, path, horizon, k_act=k_act,
                                budget_schedule=(None if arm in ("adaptive_oracle",
                                                                 "adaptive_causal")
                                                else schedule))
                if arm == "adaptive_oracle":
                    schedule = res.get("actuator_schedule")
                res.update(split=split, path=path.tolist() if arm == "adaptive_oracle" else None)
                out["runs"].append(res)
                if res.get("ok"):
                    print(f"[{split}] seed {seed:<3} {arm:<17} path_err="
                          f"{res['mean_path_error_radii']:5.2f}R R_F={res['mean_R_F']:.2f} "
                          f"R_M={res['final_R_M']:.2f} size={res['mean_size']:.0f} "
                          f"act={res['mean_actuators']:.1f} "
                          f"S_full={res['S_full']} "
                          f"[{'split ' if res['failure_splitting'] else ''}"
                          f"{'break ' if res['failure_destruction_and_replacement'] else ''}"
                          f"{'shrink ' if res['failure_shrink_to_win'] else ''}"
                          f"{'matonly' if res['failure_material_only_persistence'] else ''}]",
                          flush=True)
                dump_json(out, DATA_DIR / "guidance.json")
    dump_json(out, DATA_DIR / "guidance.json")
    print("wrote", DATA_DIR / "guidance.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "run")
