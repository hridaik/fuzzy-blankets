"""
Stage 5, Sections 10-14: checkpointable/resumable control-optimization grid runner.

Each (formulation, phenotype_only, T, rho_z, lambda_org, n_knots) configuration is one
"job". Completed jobs are appended to data/control_results.jsonl (one JSON record per
line) and to data/control_results/<job_key>.npz (full trajectories, for figures). On
rerun, jobs already present in the jsonl index are skipped -- safe to Ctrl-C and resume.

USAGE (see bottom of file / README note printed at end of core5 run):
    python3 stage5/control_sweep.py --stage baseline     # 4 formulations x 2 modes x 4 T, rho_z=1
    python3 stage5/control_sweep.py --stage rho_z        # rho_z in {0.25,4} sensitivity, subset
    python3 stage5/control_sweep.py --stage lambda_org    # formulation D, lambda_org grid
    python3 stage5/control_sweep.py --stage convergence  # 20-knot cross-check, representative cases
    python3 stage5/control_sweep.py --stage all          # everything, in the order above
Resumable: just rerun the same command; completed jobs are skipped.
"""
import sys, os, json, argparse, time, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import control as ctl
import integrity as intg

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RESULT_DIR = os.path.join(DATA_DIR, "control_results")
INDEX_PATH = os.path.join(DATA_DIR, "control_results.jsonl")
os.makedirs(RESULT_DIR, exist_ok=True)

DELTA = ctl.DELTA_PRIMARY
HORIZONS = [0.5, 1, 2, 4]
FORMULATIONS = ["A", "B", "C", "D"]
MODES = [True, False]  # phenotype_only True/False
LAMBDA_ORG_GRID = [0.0, 0.01, 0.1, 1.0, 10.0]
RHO_Z_SENS = [0.25, 4.0]


def job_key(formulation, phenotype_only, T, rho_z, lambda_org, n_knots):
    mode = "phen" if phenotype_only else "coord"
    return f"F{formulation}_{mode}_T{T}_rho{rho_z}_lam{lambda_org}_k{n_knots}"


def load_index():
    done = {}
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                done[rec["key"]] = rec
    return done


def append_index(rec):
    with open(INDEX_PATH, "a") as f:
        f.write(json.dumps(rec) + "\n")


def compute_job(job):
    formulation, phenotype_only, T, rho_z, lambda_org, n_knots = job
    key = job_key(formulation, phenotype_only, T, rho_z, lambda_org, n_knots)
    t0 = time.time()
    try:
        res = ctl.optimize_protocol(T=T, rho_z=rho_z, phenotype_only=phenotype_only,
                                     formulation=formulation, delta=DELTA, lambda_org=lambda_org,
                                     n_knots=n_knots)
    except Exception as e:
        rec = dict(key=key, formulation=formulation, phenotype_only=phenotype_only, T=T,
                   rho_z=rho_z, lambda_org=lambda_org, n_knots=n_knots, error=str(e),
                   traceback=traceback.format_exc(), wall_time=time.time() - t0, ok=False)
        return rec

    dt = time.time() - t0
    if res.get("x") is None:
        rec = dict(key=key, formulation=formulation, phenotype_only=phenotype_only, T=T,
                   rho_z=rho_z, lambda_org=lambda_org, n_knots=n_knots, infeasible=True,
                   wall_time=dt, ok=False)
        return rec

    traj = res["traj"]
    rel = ctl.release_phase(res)
    npz_path = os.path.join(RESULT_DIR, key + ".npz")
    np.savez(npz_path, x=res["x"], t=traj["t"], y=traj["y"], z=traj["z"], m=traj["m"],
             Sigma=traj["Sigma"], E_cum=traj["E"], L3_dense=res["L3_dense"],
             rel_t=rel["t"], rel_y=rel["y"], rel_z=rel["z"], rel_L3=rel["L3"],
             rel_Dorg=rel["Dorg"], rel_KL=rel["KL_to_pB"])
    task_resid = res["attempts"][0].get("task_resid") if res["attempts"] else None
    integrated_violation = float(np.trapezoid(np.clip(res["L3_dense"] - DELTA, 0, None) ** 2, traj["t"]))
    Kdelta_max = 0
    time_Kgt3 = 0.0
    for i in range(len(traj["t"])):
        Kd, _ = intg.K_delta(traj["Sigma"][i], DELTA, from_precision=False)
        Kd = Kd if Kd is not None else 4
        Kdelta_max = max(Kdelta_max, Kd)
        if Kd > 3 and i > 0:
            time_Kgt3 += traj["t"][i] - traj["t"][i - 1]

    rec = dict(key=key, formulation=formulation, phenotype_only=phenotype_only, T=T,
               rho_z=rho_z, lambda_org=lambda_org, n_knots=n_knots,
               feasible=bool(res["feasible"]), dense_feasible=bool(res["dense_feasible"]),
               E_total=float(res["E_total"]), Dorg_total=(float(res["Dorg_total"]) if res["Dorg_total"] is not None else None),
               max_L3=float(res["max_L3"]), integrated_violation=integrated_violation,
               Kdelta_max=int(Kdelta_max), time_Kgt3=float(time_Kgt3),
               y_T=float(traj["y"][-1]), cM_T=float(ctl.C_VEC @ traj["m"][-1]),
               relaxes_to_B=bool(rel["relaxes_to_B"]), final_KL_to_pB=float(rel["final_KL_to_pB"]),
               guard_active=bool(traj["guard_active"]), wall_time=dt, npz=npz_path, ok=True)
    return rec


def jobs_baseline():
    return [(f, ph, T, 1.0, 0.0, 12) for f in FORMULATIONS for ph in MODES for T in HORIZONS]


def jobs_rho_z():
    return [(f, False, T, rho, 0.0, 12) for rho in RHO_Z_SENS for f in FORMULATIONS for T in [1.0, 2.0]]


def jobs_lambda_org():
    return [("D", ph, T, 1.0, lam, 12) for lam in LAMBDA_ORG_GRID for ph in MODES for T in [1.0, 2.0]]


def jobs_convergence():
    return [(f, False, T, 1.0, 0.0, 20) for f in ["A", "C"] for T in [1.0, 2.0]]


def _report(rec, was_cached):
    tag = "[cached]" if was_cached else "[computed]"
    if rec.get("ok"):
        print(f"{tag} {rec['key']}: E={rec['E_total']:.4f} maxL3={rec['max_L3']:.2e} "
              f"feasible={rec['feasible']} dense_feasible={rec['dense_feasible']} "
              f"y(T)={rec['y_T']:.4f} cM(T)={rec['cM_T']:.4f} t={rec['wall_time']:.1f}s", flush=True)
    else:
        print(f"{tag} {rec['key']}: FAILED/INFEASIBLE -- {rec.get('error', 'infeasible')}", flush=True)


def run_jobs(all_jobs, n_workers):
    done = load_index()
    todo = []
    for job in all_jobs:
        key = job_key(*job)
        if key in done:
            _report(done[key], True)
        else:
            todo.append(job)
    if not todo:
        return
    print(f"Dispatching {len(todo)} jobs across {n_workers} worker processes...", flush=True)
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futs = {ex.submit(compute_job, job): job for job in todo}
        for fut in as_completed(futs):
            rec = fut.result()
            append_index(rec)
            _report(rec, False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["baseline", "rho_z", "lambda_org", "convergence", "all"],
                     default="baseline")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4))
    ap.add_argument("--limit", type=int, default=None, help="only run the first N jobs of the stage (debug)")
    args = ap.parse_args()
    stages = []
    if args.stage in ("baseline", "all"):
        stages.append(jobs_baseline())
    if args.stage in ("rho_z", "all"):
        stages.append(jobs_rho_z())
    if args.stage in ("lambda_org", "all"):
        stages.append(jobs_lambda_org())
    if args.stage in ("convergence", "all"):
        stages.append(jobs_convergence())
    all_jobs = [j for stage in stages for j in stage]
    if args.limit:
        all_jobs = all_jobs[:args.limit]
    run_jobs(all_jobs, args.workers)
    print("\nDone. Index at", INDEX_PATH)
