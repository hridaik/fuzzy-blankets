"""
Rate-induced-loss audit orchestration. Additive only -- does not modify rate_induced.py,
Figure 3, or any previously saved Stage-5 result. Outputs go to
stage5/data/rate_induced_audit/.
"""
import sys, os, csv, json, argparse, time
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import core5
import integrity as I
import dynamics as dyn
import rate_induced_audit_core as aud
from reference import v_of_z
import rate_induced as ri_orig  # the EXISTING Stage-5 module, read-only, for Part 1 reproduction

AUDIT_DIR = aud.AUDIT_DIR
T_RELAX_PRIMARY = 8.0
N_EVAL_PRIMARY = 2000
RTOL_PRIMARY, ATOL_PRIMARY = 1e-9, 1e-11
KS_PRIMARY = (1, 2, 3, 4)


def build_grid():
    log_grid = np.logspace(-3, np.log10(16), 80)
    explicit = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25,
                0.5, 1, 2, 4, 8, 16]
    full = sorted(set(np.round(np.concatenate([log_grid, explicit]), 8).tolist()))
    return full


# ---------------------------------------------------------------------------
# Part 1: reproduce the existing Figure-3 curve exactly
# ---------------------------------------------------------------------------
def part1_reproduce(log):
    log("=== PART 1: reconstruct the existing Figure-3 / rate_induced.py calculation ===")
    log("Exact ramp function z(t): z(t) = -1 + 2*smoothstep(t/T_ramp), smoothstep(r)=3r^2-2r^3, "
        "clipped to r in [0,1] (quasistatic.py:smoothstep). Forced open-loop via u_z chosen so "
        "z(t) tracks this EXACTLY regardless of the y-z coupling (quasistatic.slow_ramp_run).")
    log("Initial state: y(0)=-1, z(0)=-1, m(0)=v(-1)*(-1) [=mu*(-1,-1)], Sigma(0)=Omega(-1)^-1 "
        "[=Sigma*(-1), the endpoint-A equilibrium].")
    log("y is NOT held fixed: u_y=0 identically, so y evolves freely under y'=y-y^3+u_y=y-y^3 "
        "(coupled to z through mu*(y,z) inside the moment ODE, and through the u_z formula which "
        "subtracts (y-z) to force z's trajectory -- so y's free evolution DOES feed back into what "
        "u_z must be, but z(t) itself is still forced to the prescribed smoothstep exactly).")
    log("ODE integrated for Sigma(t): dSigma/dt = -(Omega(z(t))@Sigma + Sigma@Omega(z(t)) - 2I)/tau_x, "
        "tau_x=1 (dynamics.moment_rhs), via dynamics.integrate -> scipy.solve_ivp RK45.")
    log(f"Time interval simulated: EXACTLY [0, T_ramp] -- dyn.integrate(y0,z0,m0,Sigma0,T_ramp,...) "
        f"in quasistatic.slow_ramp_run; there is NO post-ramp continuation in the original code.")
    log(f"Time interval over which max_t Lambda_3(t) was computed in the original right panel: "
        f"EXACTLY [0, T_ramp] as well -- rate_induced.run_ramp() calls slow_ramp_run(T_ramp, n_eval) "
        f"and takes res['L3'].max() over that SAME [0,T_ramp] array. CONFIRMED: the old maximum was "
        f"computed ONLY during the ramp, never after it. (Answers audit Q1: YES.)")
    log(f"Number of output timepoints: n_eval=300 (rate_induced.run_ramp default) for the primary "
        f"RAMP_DURATIONS set, n_eval=200 for the FINE_DURATIONS diagnostic sweep -- both far below "
        f"this audit's 2000-point / refined-peak protocol.")
    log(f"ODE tolerances: dynamics.integrate defaults rtol=1e-9, atol=1e-11 (already tight; unchanged "
        f"here for the reproduction step).")
    log(f"Candidate blankets: core5.enumerate_candidates() = all subsets of {{4,5,6,7}} (node 8 fixed "
        f"external anchor, never a candidate), sizes 0..4; integrity.Lambda_K filters to |B|<=K.")
    log(f"Ties: Lambda_K's RETURNED VALUE is the exact minimum over the filtered candidates (not "
        f"affected by tie tolerance); the tie tolerance (1e-6) only affects which B are reported as "
        f"'winners' alongside that exact minimum. The PLOTTED Lambda_3(t) curve is this exact minimum.")

    # numerically reproduce the saved curve
    saved = np.load(os.path.join(os.path.dirname(__file__), "data", "part9_rate_induced.npz"))
    max_diffs = {}
    for T_ramp in ri_orig.RAMP_DURATIONS:
        res = ri_orig.run_ramp(T_ramp)  # calls the UNMODIFIED original function
        saved_L3 = saved[f"L3_{T_ramp}"]
        diff = np.max(np.abs(res["L3"] - saved_L3))
        max_diffs[T_ramp] = diff
        log(f"  T_ramp={T_ramp}: reproduced vs saved max|diff| = {diff:.3e} "
            f"(reproduced max_t L3 = {res['L3'].max():.6e}, saved = {saved_L3.max():.6e})")
    all_match = all(d < 1e-10 for d in max_diffs.values())
    log(f"Reproduction of the exact published Figure-3 curve: {'EXACT MATCH' if all_match else 'MISMATCH -- STOP AND INVESTIGATE'}")
    assert all_match, "Part 1 reproduction failed -- audit cannot proceed reliably"
    log("")
    return max_diffs


# ---------------------------------------------------------------------------
# Part 2-4, 11: extended-ramp full-event sweep (primary shape=smoothstep)
# ---------------------------------------------------------------------------
def _worker_extended(args):
    T_ramp, shape, T_relax, n_eval, rtol, atol = args
    res, T_total = aud.run_extended(T_ramp, T_relax=T_relax, shape=shape, n_eval=n_eval,
                                     rtol=rtol, atol=atol)
    analysis = aud.analyze_run(res, T_ramp, T_relax, Ks=KS_PRIMARY)
    out = dict(T_ramp=T_ramp, shape=shape, T_relax=T_relax)
    for K in KS_PRIMARY:
        L = analysis["LK"][K]
        peaks = aud.peak_summary(res["t"], L, T_ramp, T_relax)
        out[f"K{K}"] = peaks
    # SPD / nonnegativity checks
    min_eig_over_t = min(np.linalg.eigvalsh(S).min() for S in res["Sigma"][::max(1, len(res['t'])//50)])
    min_L3_over_t = analysis["LK"][3].min()
    out["min_Sigma_eig_sampled"] = float(min_eig_over_t)
    out["min_L3_over_t"] = float(min_L3_over_t)
    # local peak refinement (K=3) using the dense ODE solution
    refine = aud.refine_peak(res, res["t"], analysis["LK"][3], T_ramp, T_relax, K=3)
    out["refine"] = refine
    return out, res, analysis


def part2_4_11_sweep(log, grid, shape="smoothstep", n_eval=N_EVAL_PRIMARY, workers=8):
    log(f"=== PARTS 2-4, 11: extended-ramp full-event sweep, shape={shape}, "
        f"T_relax={T_RELAX_PRIMARY}, n_eval={n_eval}, rtol={RTOL_PRIMARY}, atol={ATOL_PRIMARY} ===")
    log(f"Grid ({len(grid)} points): {grid}")
    jobs = [(T, shape, T_RELAX_PRIMARY, n_eval, RTOL_PRIMARY, ATOL_PRIMARY) for T in grid]
    rows = []
    stored_runs = {}  # keep full trajectories only for a representative subset (memory)
    keep_full = set([grid[0], grid[len(grid)//8], grid[len(grid)//4], grid[3*len(grid)//8],
                      grid[len(grid)//2], grid[5*len(grid)//8], grid[3*len(grid)//4],
                      grid[-1]])
    # also keep anything near the previously-reported peak (T_ramp~0.2) and near 1.0
    for target in [0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 4.0]:
        keep_full.add(min(grid, key=lambda g: abs(g - target)))

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_worker_extended, j): j[0] for j in jobs}
        n_done = 0
        for fut in as_completed(futs):
            out, res, analysis = fut.result()
            rows.append(out)
            if out["T_ramp"] in keep_full:
                stored_runs[out["T_ramp"]] = dict(t=res["t"], y=res["y"], z=res["z"],
                                                    Sigma=res["Sigma"],
                                                    L1=analysis["LK"][1], L2=analysis["LK"][2],
                                                    L3=analysis["LK"][3], L4=analysis["LK"][4],
                                                    Kdelta=analysis["Kdelta"])
            n_done += 1
            if n_done % 10 == 0 or n_done == len(jobs):
                log(f"  progress: {n_done}/{len(jobs)} ({time.time()-t0:.1f}s elapsed)")
    rows.sort(key=lambda r: r["T_ramp"])
    log(f"Sweep complete in {time.time()-t0:.1f}s.")

    # sanity checks (Part 15 partial: nonnegativity/SPD, done for every point here)
    min_eig_all = min(r["min_Sigma_eig_sampled"] for r in rows)
    min_L3_all = min(r["min_L3_over_t"] for r in rows)
    log(f"SPD check: min sampled Sigma eigenvalue over ALL runs = {min_eig_all:.3e} (must be > 0)")
    log(f"Nonnegativity check: min Lambda_3(t) over ALL runs/times = {min_L3_all:.3e} (must be >= -1e-9)")
    assert min_eig_all > 0, "Sigma lost positive-definiteness somewhere in the sweep!"
    assert min_L3_all > -1e-9, "Lambda_3 went meaningfully negative somewhere -- population CMI bug!"

    # save CSV: one row per (T_ramp, K)
    csv_path = os.path.join(AUDIT_DIR, "full_event_peak_table.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["T_ramp", "K", "L_max_ramp", "t_peak_ramp", "L_max_post", "t_peak_post",
                    "L_max_full", "t_peak_full", "t_peak_full_over_Tramp", "peak_location",
                    "refine_t", "refine_L", "refine_vs_coarse_diff"])
        for r in rows:
            for K in KS_PRIMARY:
                p = r[f"K{K}"]
                rf = r["refine"] if K == 3 else dict(t_refined=np.nan, L_refined=np.nan, refine_vs_coarse_diff=np.nan)
                w.writerow([r["T_ramp"], K, p["L_max_ramp"], p["t_peak_ramp"], p["L_max_post"],
                            p["t_peak_post"], p["L_max_full"], p["t_peak_full"],
                            p["t_peak_full_over_Tramp"], p["peak_location"],
                            rf.get("t_refined"), rf.get("L_refined"), rf.get("refine_vs_coarse_diff")])
    log(f"Saved {csv_path}")

    npz_path = os.path.join(AUDIT_DIR, f"full_event_sweep_{shape}.npz")
    save_dict = dict(T_ramp_grid=np.array(grid))
    for K in KS_PRIMARY:
        save_dict[f"Lmax_full_K{K}"] = np.array([r[f"K{K}"]["L_max_full"] for r in rows])
        save_dict[f"Lmax_ramp_K{K}"] = np.array([r[f"K{K}"]["L_max_ramp"] for r in rows])
        save_dict[f"Lmax_post_K{K}"] = np.array([r[f"K{K}"]["L_max_post"] for r in rows])
        save_dict[f"tpeak_full_K{K}"] = np.array([r[f"K{K}"]["t_peak_full"] for r in rows])
    for T, run in stored_runs.items():
        tag = f"{T:.6g}".replace(".", "p")
        save_dict[f"t_{tag}"] = run["t"]
        save_dict[f"z_{tag}"] = run["z"]
        save_dict[f"y_{tag}"] = run["y"]
        save_dict[f"L1_{tag}"] = run["L1"]
        save_dict[f"L2_{tag}"] = run["L2"]
        save_dict[f"L3_{tag}"] = run["L3"]
        save_dict[f"L4_{tag}"] = run["L4"]
        save_dict[f"Kdelta_{tag}"] = run["Kdelta"]
    np.savez(npz_path, **save_dict)
    log(f"Saved {npz_path} (full trajectories retained for T_ramp in {sorted(stored_runs.keys())})")
    log("")
    return rows, stored_runs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="1_2_4_11", choices=["1_2_4_11", "test"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--test_n", type=int, default=6)
    args = ap.parse_args()

    logf = open(os.path.join(AUDIT_DIR, "audit_log.txt"), "a")
    def log(s=""):
        print(s, flush=True)
        logf.write(s + "\n")
        logf.flush()

    log(f"\n\n########## rate_induced_audit_run.py --part {args.part} started ##########")

    part1_reproduce(log)

    grid = build_grid()
    if args.part == "test":
        grid = grid[::len(grid)//args.test_n][:args.test_n]
        log(f"TEST MODE: using reduced grid {grid}")

    rows, stored_runs = part2_4_11_sweep(log, grid, shape="smoothstep", workers=args.workers)

    log("Parts 1,2,3,4,11 (primary smoothstep sweep) complete.")
    logf.close()
