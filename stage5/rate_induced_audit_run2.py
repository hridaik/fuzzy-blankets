"""
Rate-induced-loss audit, part 2 of orchestration: ramp-shape robustness (Part 12),
numerical convergence (Part 15), precision-lag decomposition (Part 10) for the
representative two-bump case, and quasi-static-vs-actual decomposition (Part 13).
"""
import sys, os, csv, time
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import core5
import integrity as I
import rate_induced_audit_core as aud

AUDIT_DIR = aud.AUDIT_DIR
T_RELAX_PRIMARY = 8.0


def _worker_shape(args):
    T_ramp, shape = args
    res, T_total = aud.run_extended(T_ramp, T_relax=T_RELAX_PRIMARY, shape=shape,
                                     n_eval=1200, rtol=1e-9, atol=1e-11)
    analysis = aud.analyze_run(res, T_ramp, T_RELAX_PRIMARY, Ks=(3,))
    L3 = analysis["LK"][3]
    peaks = aud.peak_summary(res["t"], L3, T_ramp, T_RELAX_PRIMARY)
    return dict(T_ramp=T_ramp, shape=shape, **peaks)


def part12_shape_robustness(log, workers=8):
    log("=== PART 12: ramp-shape robustness (linear / smoothstep / smootherstep), K=3 ===")
    # reduced grid vs the primary 94-pt sweep (documented compute-budget reduction),
    # log-spaced, covering the same T_ramp range, fixed BEFORE looking at shape results
    grid = sorted(set(np.round(np.logspace(-3, np.log10(16), 24), 6).tolist()))
    log(f"Grid ({len(grid)} points, reduced from the primary 94-pt smoothstep grid for compute "
        f"budget -- fixed before running, not chosen post hoc): {grid}")
    jobs = [(T, shape) for shape in ["linear", "smoothstep", "smootherstep"] for T in grid]
    rows = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_worker_shape, j): j for j in jobs}
        for fut in as_completed(futs):
            rows.append(fut.result())
    log(f"Shape-robustness sweep done in {time.time()-t0:.1f}s ({len(jobs)} runs).")
    rows.sort(key=lambda r: (r["shape"], r["T_ramp"]))

    csv_path = os.path.join(AUDIT_DIR, "shape_robustness_table.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    log(f"Saved {csv_path}")

    for shape in ["linear", "smoothstep", "smootherstep"]:
        sub = [r for r in rows if r["shape"] == shape]
        sub.sort(key=lambda r: r["T_ramp"])
        Ts = np.array([r["T_ramp"] for r in sub])
        Lfull = np.array([r["L_max_full"] for r in sub])
        i_peak = int(np.argmax(Lfull))
        # is it monotone decreasing (within small numerical tolerance) or does an interior max exist?
        decreasing_after_plateau = all(Lfull[i + 1] <= Lfull[i] + 1e-8 for i in range(i_peak, len(Lfull) - 1))
        log(f"  shape={shape}: max_t Lambda_3 full-event peak = {Lfull[i_peak]:.4e} at T_ramp={Ts[i_peak]:.4g}; "
            f"T_ramp->0 plateau value = {Lfull[0]:.4e}; monotone-nonincreasing after the peak index: "
            f"{decreasing_after_plateau}")
    log("")
    return rows


def part15_convergence(log):
    log("=== PART 15: numerical convergence cross-check ===")
    log("NOTE: an earlier version of this check (naive rtol/atol tightening with NO max_step cap) "
        "found a spurious 100% collapse at T_ramp=0.02/0.2/0.25 -- traced to RK45's adaptive step "
        "control occasionally ALIASING OVER the narrow forced transient entirely when unconstrained "
        "(fewer function evaluations at the 'tighter' tolerance than at baseline is the signature of "
        "this failure mode). Fixed by capping max_step at T_ramp/20 (baseline) and T_ramp/100 "
        "(refinement) -- see rate_induced_audit_core.run_extended and dynamics.integrate's new "
        "additive max_step parameter (default None, so ALL other Stage-5 code is unaffected).")
    test_Ts = [0.02, 0.2, 0.25, 1, 8]
    rows = []
    for T_ramp in test_Ts:
        baseline_res, _ = aud.run_extended(T_ramp, T_relax=T_RELAX_PRIMARY, shape="smoothstep",
                                            n_eval=2000, rtol=1e-9, atol=1e-11, max_step_ramp=max(T_ramp / 20, 1e-4))
        tight_res, _ = aud.run_extended(T_ramp, T_relax=T_RELAX_PRIMARY, shape="smoothstep",
                                         n_eval=2000, rtol=1e-10, atol=1e-12, max_step_ramp=max(T_ramp / 100, 1e-5))
        dense_res, _ = aud.run_extended(T_ramp, T_relax=T_RELAX_PRIMARY, shape="smoothstep",
                                         n_eval=4000, rtol=1e-9, atol=1e-11, max_step_ramp=max(T_ramp / 20, 1e-4))
        L_base = aud.analyze_run(baseline_res, T_ramp, T_RELAX_PRIMARY, Ks=(3,))["LK"][3]
        L_tight = aud.analyze_run(tight_res, T_ramp, T_RELAX_PRIMARY, Ks=(3,))["LK"][3]
        L_dense = aud.analyze_run(dense_res, T_ramp, T_RELAX_PRIMARY, Ks=(3,))["LK"][3]
        m_base, m_tight, m_dense = L_base.max(), L_tight.max(), L_dense.max()
        row = dict(T_ramp=T_ramp, max_baseline=m_base, max_tighter_tol=m_tight, max_denser_grid=m_dense,
                   abs_diff_tol=abs(m_tight - m_base), abs_diff_grid=abs(m_dense - m_base),
                   rel_diff_tol=abs(m_tight - m_base) / max(m_base, 1e-300),
                   rel_diff_grid=abs(m_dense - m_base) / max(m_base, 1e-300))
        rows.append(row)
        log(f"  T_ramp={T_ramp}: baseline={m_base:.6e}  tighter_tol(1e-10/1e-12)={m_tight:.6e} "
            f"(absdiff={row['abs_diff_tol']:.2e}, reldiff={row['rel_diff_tol']:.2e})  "
            f"denser_grid(4000pt)={m_dense:.6e} (absdiff={row['abs_diff_grid']:.2e}, "
            f"reldiff={row['rel_diff_grid']:.2e})")
    csv_path = os.path.join(AUDIT_DIR, "numerical_convergence_table.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    log(f"Saved {csv_path}\n")
    return rows


def part10_precision_lag(log):
    log("=== PART 10: conditional-precision decomposition at the two-bump peaks (T_ramp=0.2) ===")
    T_ramp = 0.2
    res, T_total = aud.run_extended(T_ramp, T_relax=T_RELAX_PRIMARY, shape="smoothstep",
                                     n_eval=2000, rtol=1e-9, atol=1e-11)
    analysis = aud.analyze_run(res, T_ramp, T_RELAX_PRIMARY, Ks=(1, 2, 3, 4))
    L3 = analysis["LK"][3]
    t = res["t"]
    # locate the two local maxima (primary near ramp end, secondary shortly after)
    from scipy.signal import argrelmax
    idx = argrelmax(L3, order=5)[0]
    idx = [i for i in idx if L3[i] > 1e-8]  # drop machine-noise "peaks" in the deep-relaxed tail
    idx = sorted(idx, key=lambda i: -L3[i])[:2]
    idx = sorted(idx, key=lambda i: t[i])
    labels = ["primary (near ramp end)", "secondary (post-ramp echo)"]
    I_idx = core5.I_IDX
    rows = []
    for label, i in zip(labels, idx):
        Sigma_t = res["Sigma"][i]
        K_t = np.linalg.inv(Sigma_t)
        Om_z = core5.Omega_of_z(res["z"][i])
        DeltaK = K_t - Om_z
        winners3 = analysis["winnersK"][3][i]
        B_star = winners3[0]
        E_star = [n for n in core5.U_NODES if n not in B_star]
        E_idx = [core5.idx[n] for n in E_star]
        # dominant I-E entries of Delta K for the minimizing B
        entries = []
        for ii in I_idx:
            for jj in E_idx:
                entries.append((ii, jj, DeltaK[ii, jj]))
        entries.sort(key=lambda e: -abs(e[2]))
        log(f"  {label}: t={t[i]:.4f} z={res['z'][i]:+.4f} Kdelta={analysis['Kdelta'][i]} "
            f"L1={analysis['LK'][1][i]:.3e} L2={analysis['LK'][2][i]:.3e} L3={L3[i]:.3e} "
            f"L4={analysis['LK'][4][i]:.3e}  minimizing B(K=3)={B_star}")
        log(f"    dominant |Delta K|_{{I,E}} entries (node_i, node_j, value), for E={E_star}:")
        for ii, jj, val in entries[:6]:
            ni = ii + 1; nj = jj + 1
            log(f"      ({ni},{nj}): {val:.4e}")
            rows.append(dict(peak=label, t=t[i], node_i=ni, node_j=nj, DeltaK_ij=val))
    csv_path = os.path.join(AUDIT_DIR, "precision_lag_peak_table.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    log(f"Saved {csv_path}\n")
    return idx, res, analysis


def part13_quasistatic_decomposition(log, T_ramp=0.5):
    log(f"=== PART 13: actual vs quasi-static Lambda_2/Lambda_3, representative T_ramp={T_ramp} ===")
    res, T_total = aud.run_extended(T_ramp, T_relax=T_RELAX_PRIMARY, shape="smoothstep",
                                     n_eval=1000, rtol=1e-9, atol=1e-11)
    analysis = aud.analyze_run(res, T_ramp, T_RELAX_PRIMARY, Ks=(2, 3))
    n = len(res["t"])
    L2_star = np.zeros(n)
    L3_star = np.zeros(n)
    for i in range(n):
        Om_z = core5.Omega_of_z(res["z"][i])
        L2_star[i], _ = I.Lambda_K(Om_z, 2)
        L3_star[i], _ = I.Lambda_K(Om_z, 3)
    dL2 = analysis["LK"][2] - L2_star
    dL3 = analysis["LK"][3] - L3_star
    log(f"  max_t Delta-Lambda_2 (actual - quasi-static) = {dL2.max():.4e}")
    log(f"  max_t Delta-Lambda_3 (actual - quasi-static) = {dL3.max():.4e} "
        f"(quasi-static Lambda_3^*=0 along this path, so Delta_Lambda_3 = actual leakage exactly)")
    np.savez(os.path.join(AUDIT_DIR, "quasistatic_decomposition.npz"), t=res["t"], z=res["z"],
             L2_actual=analysis["LK"][2], L2_star=L2_star, L3_actual=analysis["LK"][3], L3_star=L3_star,
             T_ramp=T_ramp)
    log(f"Saved quasistatic_decomposition.npz\n")
    return res, analysis, L2_star, L3_star


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip12", action="store_true")
    args = ap.parse_args()

    logf = open(os.path.join(AUDIT_DIR, "audit_log.txt"), "a")
    def log(s=""):
        print(s, flush=True)
        logf.write(s + "\n")
        logf.flush()

    if not args.skip12:
        part12_shape_robustness(log, workers=8)
    part15_convergence(log)
    part10_precision_lag(log)
    part13_quasistatic_decomposition(log)
    logf.close()
    print("rate_induced_audit_run2.py complete.")
