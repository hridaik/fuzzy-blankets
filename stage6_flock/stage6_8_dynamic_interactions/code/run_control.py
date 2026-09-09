"""Adaptive control experiment (task brief sections 20-21).

Two phases, in order:

  --calibrate   fixes THETA (the multicover support threshold) from DEVELOPMENT
                seeds only, using the empirical scale of the inferred influence
                values -- never from control success, which is not computed in
                this phase.
  --run         runs all five arms on development AND held-out seeds with the
                calibrated threshold applied unchanged.
"""
from __future__ import annotations

import sys

import numpy as np

from common_68 import dump_json, load_json, DATA_DIR
from episode_data import make_simulator, run_episode, observation_record
from fov_dynamics import GateParams

import candidate_detection as cd
import adaptive_control as ac

T0 = 60                     # control starts here (same snapshot time as the pipeline)
# adaptive_causal runs FIRST: its realized per-step actuator count is the
# budget the matched arms are then held to (see adaptive_control.run_arm).
ARMS = ["adaptive_causal", "no_control", "frozen_causal", "adaptive_oracle",
        "predictive", "random_matched"]
FEASIBILITY_GRID = [(10, 16), (20, 16), (10, 30), (20, 30), (30, 30)]
FEASIBILITY_TARGET = 0.5


def calibrate(op, sim, dev_seeds) -> dict:
    """THETA = the 25th percentile, pooled over development-seed interiors, of
    each REACHABLE interior bird's STRONGEST single-source inferred influence.
    A bird at that level is movable by roughly one well-chosen actuator, so the
    multicover's notion of 'supported' sits on the natural scale of the
    estimated influence rather than on an arbitrary constant. Restricting to
    the reachable interior (`adaptive_control.reachable_interior`) is necessary
    because in a 100+ bird candidate most members are several steps from the
    exterior and have identically zero one-step influence, which would drive the
    quantile to 0 and make every bird trivially 'supported'. Control success is
    neither computed nor available in this function."""
    vals = []
    for seed in dev_seeds:
        res = run_episode(sim, seed, nt=T0 + 2, record_oracle=False)
        obs = observation_record(sim, res.z_hist, T0)
        ok, _ = cd.propose(obs)
        if not ok:
            continue
        I = np.array(sorted(max(ok, key=lambda c: c.size).members))
        cands = ac.near_exterior(sim.positions, I)
        infl, _, _ = ac._sampled_influence(sim, res.z_hist[T0], I, cands, seed)
        for i in ac.reachable_interior(infl, I):
            vals.append(max(infl[j].get(int(i), 0.0) for j in infl))
    theta = float(np.quantile(vals, 0.25)) if vals else ac.THETA_DEFAULT
    return dict(theta=theta, q_support=ac.Q_SUPPORT_DEFAULT, n_values=len(vals),
                dev_seeds=dev_seeds,
                rule="25th percentile of per-interior-bird max single-source inferred "
                     "influence, pooled over development seeds; no control outcome used")


def feasibility(sim, dev_seeds, cal) -> dict:
    """Is the task achievable AT ALL at this stage's scale? Uses ONLY the
    adaptive_oracle arm (the upper bound) on DEVELOPMENT seeds, over a
    predeclared (K_act, horizon) grid, and takes the SMALLEST setting whose
    mean final target fraction exceeds FEASIBILITY_TARGET. The other four arms
    are neither run nor computed here, so their relative ordering cannot
    influence the choice. See logs/mesoscopic_criteria_predeclared.txt,
    ADDENDUM 6."""
    rows = []
    for k_act, horizon in FEASIBILITY_GRID:
        vals = []
        for seed in dev_seeds:
            res = run_episode(sim, seed, nt=T0 + 2, record_oracle=False)
            obs = observation_record(sim, res.z_hist, T0)
            ok, _ = cd.propose(obs)
            if not ok:
                continue
            I0 = np.array(sorted(max(ok, key=lambda c: c.size).members))
            h_star = ac.target_heading(res.z_hist[T0], I0)
            r = ac.run_arm(sim, res.z_hist[:T0 + 1], "adaptive_oracle", seed, h_star,
                           theta=cal["theta"], q_support=cal["q_support"],
                           t_control=horizon, k_act=k_act, I0=I0)
            vals.append(r["final_target_fraction"])
        m = float(np.mean(vals)) if vals else float("nan")
        rows.append(dict(k_act=k_act, horizon=horizon, oracle_mean=m, n=len(vals)))
        print(f"K_act={k_act:<3} horizon={horizon:<3} oracle_final_target_frac={m:.3f}", flush=True)
    feasible = [r for r in rows if r["oracle_mean"] > FEASIBILITY_TARGET]
    chosen = min(feasible, key=lambda r: (r["k_act"] * r["horizon"], r["k_act"])) if feasible else None
    return dict(grid=rows, target=FEASIBILITY_TARGET, chosen=chosen,
                rule="smallest (K_act, horizon) whose adaptive_oracle mean exceeds the target; "
                     "only the oracle arm was run")


def main(mode: str):
    screen = load_json(DATA_DIR / "episode_screen.json")
    op = screen["ops"]["OP1"]
    sim = make_simulator(op["nn"], op["beta"], op["s"])
    dev = op["dev_seeds"][:4]
    held = op["heldout_seeds"][:4]

    if mode == "calibrate":
        cal = calibrate(op, sim, dev)
        cal["q_support"] = 0.9      # see ADDENDUM 6
        dump_json(cal, DATA_DIR / "control_calibration.json")
        print("theta =", cal["theta"], "from", cal["n_values"], "values")
        return

    if mode == "feasibility":
        cal = load_json(DATA_DIR / "control_calibration.json")
        f = feasibility(sim, dev, cal)
        dump_json(f, DATA_DIR / "control_feasibility.json")
        print("chosen:", f["chosen"])
        return

    cal = load_json(DATA_DIR / "control_calibration.json")
    theta, q = cal["theta"], cal["q_support"]
    feas = load_json(DATA_DIR / "control_feasibility.json")
    chosen, below = feas["chosen"], False
    if chosen is None:
        # Declared fallback (logs/mesoscopic_criteria_predeclared.txt, ADDENDUM 7):
        # the task is infeasible at this scale even for the oracle arm. Run the
        # comparison at the grid's best oracle setting anyway, so the ORDERING of
        # the arms is still measured, and label the absolute levels as below the
        # feasibility threshold. No absolute success is claimed.
        chosen = max(feas["grid"], key=lambda r: r["oracle_mean"])
        below = True
    k_act = chosen["k_act"]
    horizon = chosen["horizon"]
    snap = load_json(DATA_DIR / "boundary_inference__snapshot.json")
    Bpred_by_seed = {}
    for r in snap["runs"]:
        if r["method"] == "affinity_louvain" and r["t"] == T0:
            Bpred_by_seed.setdefault(r["seed"], r["predictive"]["B_pred"])

    out = dict(protocol="stage6_8 adaptive control", operating_point=op and
               {k: op[k] for k in ("nn", "beta", "s")},
               calibration=cal, feasibility=feas, setting=chosen,
               below_feasibility_threshold=below, t0=T0, arms=ARMS, K_ACT=k_act,
               T_CONTROL=horizon, REINFER_EVERY=ac.REINFER_EVERY,
               dev_seeds=dev, heldout_seeds=held, runs=[])

    for split, seeds in (("dev", dev), ("heldout", held)):
        for seed in seeds:
            res = run_episode(sim, seed, nt=T0 + 2, record_oracle=False)
            z_prefix = res.z_hist[:T0 + 1]
            z0 = res.z_hist[T0]
            obs = observation_record(sim, res.z_hist, T0)
            ok, _ = cd.propose(obs)
            if not ok:
                print(f"seed {seed}: no valid candidate at t={T0}, skipped", flush=True)
                continue
            I0 = np.array(sorted(max(ok, key=lambda c: c.size).members))
            h_star = ac.target_heading(z0, I0)
            schedule = None
            for arm in ARMS:
                r = ac.run_arm(sim, z_prefix, arm, seed, h_star,
                               B_pred=Bpred_by_seed.get(seed), theta=theta, q_support=q,
                               t_control=horizon, k_act=k_act, I0=I0,
                               budget_schedule=(None if arm == "adaptive_causal" else schedule))
                if arm == "adaptive_causal":
                    schedule = r["actuator_schedule"]
                r.pop("z_hist")
                r.update(split=split, I0_size=len(I0))
                out["runs"].append(r)
                print(f"[{split}] seed {seed:<4} {arm:<17} "
                      f"final_target_frac={r['final_target_fraction']:.3f} "
                      f"mean_actuators={r['mean_actuators']:.1f} "
                      f"|I_final|={r['final_I_size']}", flush=True)
            dump_json(out, DATA_DIR / "control.json")
    dump_json(out, DATA_DIR / "control.json")
    print("wrote", DATA_DIR / "control.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "run")
