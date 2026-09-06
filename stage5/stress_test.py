"""
Final-patch Part 3: constraint-activation stress test.

Population/control-level ONLY -- does not touch the endpoint graphs, Lambda_3
definition, or any previously-computed Stage-5 baseline/finite-data results. Uses the
additive tau_z override in dynamics.py/control.py (default None reproduces the exact
baseline; only explicit tau_z=... calls here deviate from tau_x=tau_z=1).

Phases (run via --phase):
  3a        : tau_z in {4,2,1,0.5,0.25,0.125,0.0625}, T=2, coordinated, rho_z=1,
              formulation A (task-only). Reports feasibility/energy/max Lambda_3/
              time-of-max/D_org AUC per tau_z, dense-revalidated at tight tolerance.
  3a_compare: at the tau_z selected by the FIXED rule (closest to 1 among task-feasible
              cells violating delta=0.01), run formulation C at the same tau_z and T=2,
              compare against A.
  3b_unit   : population-level constraint-LOGIC unit test (delta_unit in {1e-5,1e-6},
              baseline tau_x=tau_z=1, T=2) -- run only if 3a finds no activation.
  knots     : 12-vs-20-knot cross-check for whichever case activated.
  all       : run everything in sequence (decides 3a_compare vs 3b_unit automatically).
"""
import sys, os, csv, json, argparse, time
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import control as ctl
import integrity as I
import dynamics as dyn

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RESULTS_PATH = os.path.join(DATA_DIR, "stress_test_results.json")

TAU_Z_GRID = [4, 2, 1, 0.5, 0.25, 0.125, 0.0625]
T_REP = 2.0
RHO_Z = 1.0
DELTA = 0.01
TIGHT_RTOL, TIGHT_ATOL = 1e-8, 1e-9
N_EVAL_TIGHT = 200
UNIT_DELTAS = [1e-5, 1e-6]
# "Task-feasible" for the Part-3 activation/selection logic is judged from the DENSE
# post-hoc task residual (max(|y(T)-1|,|cM(T)-1|), already computed by dense_summary),
# NOT from optimize_protocol's internal `feasible` flag -- that flag additionally
# requires SLSQP's own res.success, which is a solver-convergence diagnostic, not a
# statement about the actual simulated trajectory, and is known from the Stage-5
# baseline (T=2 runs routinely show res.success=False despite sub-0.1% residuals) to
# be overly strict for this purpose. TASK_FEASIBLE_TOL=0.01 is a round, documented
# tolerance chosen for consistency with the primary delta=0.01 scale, decided before
# re-deriving the table below (the underlying optimizations were already run once
# under the original stricter flag; this only changes how "task-feasible" is READ
# off the same cached dense-revalidated numbers, not which solutions were computed).
TASK_FEASIBLE_TOL = 0.01


def load_results():
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH) as f:
            return json.load(f)
    return {}


def save_results(d):
    with open(RESULTS_PATH, "w") as f:
        json.dump(d, f, indent=1, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else str(o))


def dense_summary(res, tag=""):
    """Dense-revalidate a solved control.optimize_protocol result at tight tolerance,
    return a flat summary dict."""
    if res.get("x") is None:
        return dict(ok=False, tag=tag)
    rv = ctl.revalidate_tight(res, n_eval=N_EVAL_TIGHT, rtol=TIGHT_RTOL, atol=TIGHT_ATOL)
    traj = rv["traj"]
    Dorg = np.array([dyn.D_org(traj["m"][i], traj["Sigma"][i], traj["y"][i], traj["z"][i])[0]
                      for i in range(len(traj["t"]))])
    Dorg = np.clip(Dorg, 0, None)
    A_org_ctrl = float(np.trapezoid(Dorg, traj["t"]))
    L3 = rv["L3_dense"]
    max_L3 = float(L3.max())
    t_argmax = float(traj["t"][int(np.argmax(L3))])
    y_T = float(traj["y"][-1]); cM_T = float(ctl.C_VEC @ traj["m"][-1])
    task_resid = max(abs(y_T - 1.0), abs(cM_T - 1.0))
    integrated_violation = float(np.trapezoid(np.clip(L3 - res.get("delta", DELTA), 0, None) ** 2, traj["t"]))
    return dict(ok=True, tag=tag, feasible=bool(res["feasible"]), dense_feasible=bool(max_L3 <= res.get("delta", DELTA) + 1e-6)
                if res["formulation"] in ("C", "D") else True,
                E_total=float(res["E_total"]), max_L3=max_L3, t_argmax_L3=t_argmax,
                A_org_ctrl=A_org_ctrl, y_T=y_T, cM_T=cM_T, task_resid=task_resid,
                integrated_violation=integrated_violation, n_knots=res["n_knots"],
                tau_z=res.get("tau_z"), delta=res.get("delta", DELTA),
                uy=res["uy"].tolist(), uz=res["uz"].tolist() if res["uz"] is not None else None,
                t=traj["t"].tolist(), y=traj["y"].tolist(), z=traj["z"].tolist(),
                Y=(traj["m"] @ ctl.C_VEC).tolist(), L3=L3.tolist(), Dorg=Dorg.tolist())


def run_one_tauz(tau_z):
    t0 = time.time()
    res = ctl.optimize_protocol(T=T_REP, rho_z=RHO_Z, phenotype_only=False, formulation="A",
                                 delta=DELTA, tau_z=tau_z, n_knots=12)
    summ = dense_summary(res, tag=f"tauz{tau_z}")
    summ["wall_time"] = time.time() - t0
    summ["tau_z"] = tau_z
    return summ


def phase_3a(workers=7):
    results = load_results()
    if "3a" in results:
        print("3a already computed, loading cached results.")
        return results["3a"]
    print(f"Running Part 3A: tau_z sweep {TAU_Z_GRID}, T={T_REP}, formulation A (task-only), "
          f"coordinated, rho_z={RHO_Z}...")
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_one_tauz, tz): tz for tz in TAU_Z_GRID}
        for fut in as_completed(futs):
            r = fut.result()
            rows.append(r)
            print(f"  tau_z={r['tau_z']:<7} feasible(task)={r.get('feasible')} "
                  f"E={r.get('E_total', float('nan')):.4f} max_L3={r.get('max_L3', float('nan')):.3e} "
                  f"t_argmax={r.get('t_argmax_L3', float('nan')):.3f} A_org_ctrl={r.get('A_org_ctrl', float('nan')):.4f} "
                  f"[{r['wall_time']:.1f}s]")
    rows.sort(key=lambda r: r["tau_z"])
    results["3a"] = rows
    save_results(results)
    return rows


def task_ok(r, tol=TASK_FEASIBLE_TOL):
    return r.get("ok") and r.get("task_resid", 1e9) <= tol


def select_activation(rows_3a):
    """Fixed selection rule (stated BEFORE seeing results): among TASK-FEASIBLE cells
    with max_L3 > delta, choose tau_z closest to baseline tau_z=1. Task-feasibility here
    uses the dense-revalidated residual (see TASK_FEASIBLE_TOL note above)."""
    violating = [r for r in rows_3a if task_ok(r) and r["max_L3"] > DELTA]
    if not violating:
        return None
    violating.sort(key=lambda r: abs(r["tau_z"] - 1.0))
    return violating[0]


def phase_3a_compare(tau_z, workers=1):
    results = load_results()
    key = f"3a_compare_tauz{tau_z}"
    if key in results:
        print(f"{key} already computed.")
        return results[key]
    print(f"\nPart 3A comparison: formulation C at tau_z={tau_z}, T={T_REP}, delta={DELTA}...")
    resA = ctl.optimize_protocol(T=T_REP, rho_z=RHO_Z, phenotype_only=False, formulation="A",
                                  delta=DELTA, tau_z=tau_z, n_knots=12)
    resC = ctl.optimize_protocol(T=T_REP, rho_z=RHO_Z, phenotype_only=False, formulation="C",
                                  delta=DELTA, tau_z=tau_z, n_knots=12)
    summA = dense_summary(resA, tag="A")
    summC = dense_summary(resC, tag="C") if resC.get("x") is not None else dict(ok=False, tag="C",
                                                                                  infeasible=True,
                                                                                  attempts=len(resC["attempts"]))
    out = dict(tau_z=tau_z, A=summA, C=summC)
    results[key] = out
    save_results(results)
    print(f"  A: max_L3={summA['max_L3']:.4e}  E={summA['E_total']:.4f}  feasible={summA['feasible']}")
    if summC.get("ok"):
        print(f"  C: max_L3={summC['max_L3']:.4e}  E={summC['E_total']:.4f}  feasible={summC['feasible']}  "
              f"dense_feasible={summC['dense_feasible']}")
        changed = abs(summC["E_total"] - summA["E_total"]) > 1e-3 or summC["max_L3"] < summA["max_L3"] * 0.5
        print(f"  Does C's protocol differ materially from A's (energy or leakage)? {changed}")
    else:
        print(f"  C: reported INFEASIBLE by the multi-start optimizer (attempts={summC.get('attempts')}) "
              f"-- constraint is active (task+pathwise jointly infeasible at this tau_z).")
    return out


def phase_3b_unit():
    results = load_results()
    if "3b_unit" in results:
        print("3b_unit already computed.")
        return results["3b_unit"]
    print(f"\nPart 3B: population-level constraint-LOGIC unit test (NOT a biological claim), "
          f"baseline tau_x=tau_z=1, T={T_REP}, delta_unit in {UNIT_DELTAS}...")
    out = {}
    for du in UNIT_DELTAS:
        resA = ctl.optimize_protocol(T=T_REP, rho_z=RHO_Z, phenotype_only=False, formulation="A",
                                      delta=du, tau_z=None, n_knots=12)
        summA = dense_summary(resA, tag=f"A_unit_{du}")
        activated = task_ok(summA) and summA["max_L3"] > du
        print(f"  delta_unit={du:.0e}: A task-feasible={summA.get('feasible')} max_L3={summA.get('max_L3'):.3e} "
              f"activated={activated}")
        entry = dict(delta_unit=du, A=summA, activated=bool(activated))
        if activated:
            resC = ctl.optimize_protocol(T=T_REP, rho_z=RHO_Z, phenotype_only=False, formulation="C",
                                          delta=du, tau_z=None, n_knots=12)
            summC = dense_summary(resC, tag=f"C_unit_{du}") if resC.get("x") is not None else \
                dict(ok=False, tag=f"C_unit_{du}", infeasible=True)
            entry["C"] = summC
            print(f"    C at delta_unit={du:.0e}: " +
                  (f"max_L3={summC['max_L3']:.3e} E={summC['E_total']:.4f} feasible={summC['feasible']}"
                   if summC.get("ok") else "INFEASIBLE (multi-start)"))
            if summC.get("ok") and not summC["feasible"]:
                print(f"    T=2 pathwise infeasible at delta_unit={du:.0e} -- testing T=4 once...")
                resC4 = ctl.optimize_protocol(T=4.0, rho_z=RHO_Z, phenotype_only=False, formulation="C",
                                               delta=du, tau_z=None, n_knots=12)
                summC4 = dense_summary(resC4, tag=f"C_unit_{du}_T4") if resC4.get("x") is not None else \
                    dict(ok=False, tag=f"C_unit_{du}_T4", infeasible=True)
                entry["C_T4"] = summC4
                print(f"    T=4: " + (f"max_L3={summC4['max_L3']:.3e} feasible={summC4['feasible']}"
                                       if summC4.get("ok") else "still INFEASIBLE"))
        out[str(du)] = entry
    results["3b_unit"] = out
    save_results(results)
    return out


def phase_knots(config):
    """12-vs-20-knot cross-check for the activated comparison config
    (dict with T, tau_z, delta, and which formulations to check)."""
    results = load_results()
    key = f"knots_{config['tag']}"
    if key in results:
        print(f"{key} already computed.")
        return results[key]
    print(f"\nPart 3C: 12-vs-20-knot cross-check for {config['tag']} "
          f"(T={config['T']}, tau_z={config['tau_z']}, delta={config['delta']})...")
    out = {}
    for nk in [12, 20]:
        for f in config["formulations"]:
            res = ctl.optimize_protocol(T=config["T"], rho_z=RHO_Z, phenotype_only=False,
                                         formulation=f, delta=config["delta"], tau_z=config["tau_z"],
                                         n_knots=nk)
            summ = dense_summary(res, tag=f"{f}_k{nk}")
            out[f"{f}_k{nk}"] = summ
            print(f"  {f} k={nk}: feasible={summ.get('feasible')} E={summ.get('E_total', float('nan')):.4f} "
                  f"max_L3={summ.get('max_L3', float('nan')):.3e} task_resid={summ.get('task_resid', float('nan')):.4f}")
    results[key] = out
    save_results(results)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["3a", "3a_compare", "3b_unit", "knots", "all"], default="all")
    ap.add_argument("--workers", type=int, default=7)
    args = ap.parse_args()

    log = []
    def p(s=""):
        print(s); log.append(s)

    rows_3a = phase_3a(workers=args.workers)
    p(f"\n=== Part 3A summary table (tau_z sweep, T={T_REP}, formulation A) ===")
    p(f"task-feasible column uses dense task_resid <= {TASK_FEASIBLE_TOL} (see TASK_FEASIBLE_TOL "
      f"note in source), NOT the stricter optimizer-internal `feasible` flag used elsewhere in "
      f"Stage 5 (which additionally requires SLSQP's own res.success).")
    p(f"{'tau_z':>8} {'task_ok':>8} {'task_resid':>11} {'E':>9} {'max_L3':>11} {'t_argmax':>9} {'A_org_ctrl':>11}")
    for r in rows_3a:
        p(f"{r['tau_z']:>8} {str(task_ok(r)):>8} {r.get('task_resid', float('nan')):>11.4f} "
          f"{r.get('E_total', float('nan')):>9.4f} "
          f"{r.get('max_L3', float('nan')):>11.3e} {r.get('t_argmax_L3', float('nan')):>9.3f} "
          f"{r.get('A_org_ctrl', float('nan')):>11.4f}")

    outlier = [r for r in rows_3a if r.get("task_resid", 0) > 0.1]
    if outlier:
        p(f"\nAnomaly: tau_z={[r['tau_z'] for r in outlier]} show large task_resid (>0.1) -- likely "
          f"optimizer non-convergence rather than genuine task infeasibility (per spec: do not call "
          f"a numerically failed optimizer 'infeasible' without multiple starts). Re-running with "
          f"more starts and a different seed as a robustness check:")
        results = load_results()
        for r in outlier:
            rkey = f"3a_robustness_tauz{r['tau_z']}"
            if rkey in results:
                rr = results[rkey]
            else:
                res2 = ctl.optimize_protocol(T=T_REP, rho_z=RHO_Z, phenotype_only=False, formulation="A",
                                              delta=DELTA, tau_z=r["tau_z"], n_knots=12, n_starts=4, seed=7)
                rr = dense_summary(res2, tag=f"tauz{r['tau_z']}_robust")
                results[rkey] = rr
                save_results(results)
            p(f"  tau_z={r['tau_z']}: original task_resid={r['task_resid']:.4f} max_L3={r['max_L3']:.3e}  "
              f"-> robustness rerun task_resid={rr.get('task_resid', float('nan')):.4f} "
              f"max_L3={rr.get('max_L3', float('nan')):.3e}")
            if task_ok(rr):
                p(f"    Robustness rerun now task-feasible; using it in place of the original row "
                  f"for the activation decision below.")
                r.update(rr)

    activation = select_activation(rows_3a)
    if activation is not None:
        p(f"\nACTIVATION FOUND at tau_z={activation['tau_z']} (max_L3={activation['max_L3']:.4e} > delta={DELTA}, "
          f"task-feasible, closest to baseline tau_z=1 among violating cells).")
        if args.phase in ("3a_compare", "all"):
            cmp_out = phase_3a_compare(activation["tau_z"], workers=1)
        if args.phase in ("knots", "all"):
            cfg = dict(tag=f"tauz{activation['tau_z']}_primary", T=T_REP, tau_z=activation["tau_z"],
                       delta=DELTA, formulations=["A", "C"])
            knots_out = phase_knots(cfg)
        case_for_fig12 = ("3a", activation["tau_z"], DELTA)
    else:
        p(f"\nNo task-feasible tau_z in the primary grid violates delta={DELTA} "
          f"-- Part 3A does NOT activate the primary threshold. Proceeding to Part 3B "
          f"(population-level constraint-logic unit test, NOT changing the physical model).")
        if args.phase in ("3b_unit", "all"):
            unit_out = phase_3b_unit()
            activated_deltas = [du for du, e in unit_out.items() if e["activated"]]
            if not activated_deltas:
                p("\nNeither unit-test threshold (1e-5, 1e-6) activates either -- Stage 5 does not "
                  "furnish an active-constraint test even under these stringent unit thresholds. "
                  "Reported as observed; NOT tuning further.")
                case_for_fig12 = None
            else:
                du_use = activated_deltas[0]
                p(f"\nActivation found via unit test at delta_unit={du_use}.")
                if args.phase in ("knots", "all"):
                    cfg = dict(tag=f"unit_{du_use}", T=T_REP, tau_z=None, delta=float(du_use),
                               formulations=["A", "C"])
                    knots_out = phase_knots(cfg)
                case_for_fig12 = ("3b", None, float(du_use))
        else:
            case_for_fig12 = None

    with open(os.path.join(DATA_DIR, "stress_test_log.txt"), "w") as f:
        f.write("\n".join(log))
    # persist the decision for fig12.py to pick up
    with open(os.path.join(DATA_DIR, "stress_test_decision.json"), "w") as f:
        json.dump(dict(case=case_for_fig12), f)
    p(f"\nDecision persisted to data/stress_test_decision.json: {case_for_fig12}")
    p("Part 3 stress test complete.")
