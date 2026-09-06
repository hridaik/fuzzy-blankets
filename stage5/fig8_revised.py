"""Figure 8 (REVISED per final-patch Part 2): genuine organization-aware control.

Problem with the original fig8: it compared formulation A (task-only) against
formulation D with lambda_org=0, which is the SAME optimization problem as A (the
D_org penalty term vanishes), so any trajectory differences were solver noise, not a
scientific effect. This version compares:
  A  : task-only (lambda_org=0, already computed in the baseline sweep)
  D1 : formulation D, lambda_org=1    (already computed in the lambda_org grid)
  D2 : formulation D, lambda_org=100  (NOT in the completed grid -- run here, once,
                                        with the same optimizer protocol as Stage 5;
                                        lambda_org is NOT adjusted after seeing results)
at T=2, rho_z=1, coordinated control -- the most trustworthy Stage-5 horizon (the
12-vs-20-knot convergence check found T=2 stable, T=1 was not; T=0.5 was infeasible).
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import control_results_lib as lib
import control as ctl

T_REP = 2
RHO_Z = 1.0
DELTA = 0.01
LAMBDA_D2 = 100.0
TIGHT_RTOL, TIGHT_ATOL = 1e-8, 1e-9
N_EVAL_TIGHT = 200

if __name__ == "__main__":
    log = []
    def p(s=""):
        print(s); log.append(s)

    p("=== Figure 8 revision: genuine organization-aware control (D1=lambda_org=1, "
      f"D2=lambda_org={LAMBDA_D2}) at T={T_REP}, rho_z={RHO_Z}, coordinated ===")

    recs = lib.load_all()

    def build_res_from_rec(rec):
        d = lib.load_traj(rec)
        x = d["x"]
        n_knots = len(x) // 2 if len(x) > 12 else len(x)  # coordinated => 2*n_knots
        n_knots = rec.get("n_knots", 12)
        uy, uz = ctl.unpack_x(x, phenotype_only=False)
        return dict(uy=uy, uz=uz, T=rec["T"], rho_z=rec["rho_z"], n_knots=n_knots,
                     E_total=rec["E_total"], y_T=rec["y_T"], cM_T=rec["cM_T"],
                     formulation=rec["formulation"], lambda_org=rec["lambda_org"])

    rec_A = lib.find(recs, "A", False, T_REP, rho_z=RHO_Z, lambda_org=0.0)
    rec_D1 = lib.find(recs, "D", False, T_REP, rho_z=RHO_Z, lambda_org=1.0)
    if rec_A is None or rec_D1 is None:
        raise SystemExit("Missing baseline A or D1(lambda_org=1) in control_results.jsonl -- "
                          "these should already exist from the completed Stage-5 sweeps.")
    res_A = build_res_from_rec(rec_A)
    res_D1 = build_res_from_rec(rec_D1)
    p(f"Loaded A: E={res_A['E_total']:.4f} y(T)={res_A['y_T']:.4f} cM(T)={res_A['cM_T']:.4f}")
    p(f"Loaded D1(lambda_org=1): E={res_D1['E_total']:.4f} y(T)={res_D1['y_T']:.4f} cM(T)={res_D1['cM_T']:.4f}")

    p(f"\nRunning D2 (lambda_org={LAMBDA_D2}), NOT previously computed -- same optimizer "
      f"protocol as Stage 5 (n_knots=12, n_starts=3, maxiter=30, formulation D pathwise "
      f"constraint delta={DELTA}):")
    res_D2_full = ctl.optimize_protocol(T=T_REP, rho_z=RHO_Z, phenotype_only=False,
                                         formulation="D", delta=DELTA, lambda_org=LAMBDA_D2,
                                         n_knots=12)
    if res_D2_full.get("x") is None:
        raise SystemExit("D2 (lambda_org=100) optimization produced no usable solution at all.")
    res_D2 = dict(uy=res_D2_full["uy"], uz=res_D2_full["uz"], T=T_REP, rho_z=RHO_Z, n_knots=12,
                   E_total=res_D2_full["E_total"], y_T=res_D2_full["traj"]["y"][-1],
                   cM_T=float(ctl.C_VEC @ res_D2_full["traj"]["m"][-1]),
                   formulation="D", lambda_org=LAMBDA_D2)
    p(f"D2 done: E={res_D2['E_total']:.4f} y(T)={res_D2['y_T']:.4f} cM(T)={res_D2['cM_T']:.4f} "
      f"feasible={res_D2_full['feasible']} dense_feasible={res_D2_full['dense_feasible']}")

    # tight dense revalidation for all three, plus release phase from the revalidated end-state
    protocols = {"A": res_A, "D1": res_D1, "D2": res_D2}
    tight = {}
    release = {}
    for name, res in protocols.items():
        rv = ctl.revalidate_tight(res, n_eval=N_EVAL_TIGHT, rtol=TIGHT_RTOL, atol=TIGHT_ATOL)
        tight[name] = rv
        traj = rv["traj"]
        rel = ctl.dyn.integrate(traj["y"][-1], traj["z"][-1], traj["m"][-1], traj["Sigma"][-1],
                                 ctl.T_RELEASE, n_eval=N_EVAL_TIGHT)
        Dorg_rel = np.array([ctl.dyn.D_org(rel["m"][i], rel["Sigma"][i], rel["y"][i], rel["z"][i])[0]
                              for i in range(N_EVAL_TIGHT)])
        L3_rel, _ = ctl.lambda3_series(rel["Sigma"])
        Om_pB = ctl.core5.Omega_of_z(1.0)
        v_pB = ctl.v_of_z(1.0); mu_pB = v_pB * 1.0
        KL_rel = []
        for i in range(N_EVAL_TIGHT):
            dm = rel["m"][i] - mu_pB
            S = rel["Sigma"][i]
            OmS = Om_pB @ S
            sign, ld = np.linalg.slogdet(OmS)
            KL_rel.append(0.5 * (np.trace(OmS) + dm @ Om_pB @ dm - ctl.N - ld) if sign > 0 else np.nan)
        release[name] = dict(t=rel["t"], y=rel["y"], z=rel["z"], m=rel["m"], Sigma=rel["Sigma"],
                              Dorg=Dorg_rel, L3=L3_rel, KL=np.array(KL_rel))

    p(f"\nRevalidated all three at rtol={TIGHT_RTOL:.0e}, atol={TIGHT_ATOL:.0e}, "
      f"n_eval={N_EVAL_TIGHT} checkpoints (control phase); release phase re-integrated from "
      f"the revalidated control-end state at the same tolerance/grid density.")

    rows = []
    for name, res in protocols.items():
        traj = tight[name]["traj"]
        Dorg_ctrl = np.array([ctl.dyn.D_org(traj["m"][i], traj["Sigma"][i], traj["y"][i], traj["z"][i])[0]
                               for i in range(N_EVAL_TIGHT)])
        A_org_ctrl = float(np.trapezoid(Dorg_ctrl, traj["t"]))
        A_org_release = float(np.trapezoid(release[name]["Dorg"], release[name]["t"]))
        max_Dorg = float(max(Dorg_ctrl.max(), release[name]["Dorg"].max()))
        max_L3 = float(tight[name]["max_L3"])
        y_T_tight = float(traj["y"][-1])
        cM_T_tight = float(ctl.C_VEC @ traj["m"][-1])
        final_KL = float(release[name]["KL"][-1])
        row = dict(protocol=name, lambda_org=res["lambda_org"], E_total=res["E_total"],
                   A_org_ctrl=A_org_ctrl, A_org_release=A_org_release, max_Dorg=max_Dorg,
                   max_L3=max_L3, y_T=y_T_tight, cM_T=cM_T_tight,
                   task_resid_y=abs(y_T_tight - 1.0), task_resid_cM=abs(cM_T_tight - 1.0),
                   final_KL_to_pB=final_KL)
        rows.append(row)
        tight[name]["Dorg_ctrl"] = Dorg_ctrl
        p(f"  {name} (lambda_org={res['lambda_org']}): E={res['E_total']:.4f}  "
          f"A_org_ctrl={A_org_ctrl:.5f}  A_org_release={A_org_release:.5f}  max_Dorg={max_Dorg:.5f}  "
          f"max_L3={max_L3:.3e}  y(T)={y_T_tight:.4f}  cM(T)={cM_T_tight:.4f}  "
          f"final_KL_to_pB={final_KL:.5f}")

    TASK_TOL = 1e-3
    for r in rows:
        if r["task_resid_y"] > TASK_TOL or r["task_resid_cM"] > TASK_TOL:
            p(f"CAVEAT: protocol {r['protocol']} did NOT satisfy the task constraints tightly "
              f"(|y(T)-1|={r['task_resid_y']:.4f}, |cM(T)-1|={r['task_resid_cM']:.4f}, tol={TASK_TOL}) "
              f"-- its energy/organization numbers are 'best found' for an INFEASIBLE task solve, not "
              f"a like-for-like comparison against A/D1. This is reported, not hidden or re-tuned.")

    d1_reduces = rows[1]["A_org_ctrl"] < rows[0]["A_org_ctrl"]
    d2_reduces = rows[2]["A_org_ctrl"] < rows[0]["A_org_ctrl"]
    d2_vs_d1 = rows[2]["A_org_ctrl"] < rows[1]["A_org_ctrl"]
    p(f"\nDoes D1 reduce A_org_ctrl vs A (task-only)? {d1_reduces}")
    p(f"Does D2 reduce A_org_ctrl vs A (task-only)? {d2_reduces}")
    p(f"Does D2 reduce A_org_ctrl further than D1? {d2_vs_d1}")
    if not (d1_reduces and d2_reduces):
        p("NOTE: organization-aware formulations did NOT uniformly reduce accumulated "
          "organizational departure relative to task-only at this (T,rho_z) -- reported "
          "as observed, lambda_org values were not changed after seeing this.")

    outcsv = os.path.join(os.path.dirname(__file__), "data", "fig8_revised_summary.csv")
    with open(outcsv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    p(f"\nSaved summary table to {outcsv}")

    # --- figure ---
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    colors = {"A": fs.COLOR_EXTERIOR, "D1": fs.COLOR_ACCENT2, "D2": fs.COLOR_ACCENT}
    labels = {"A": "A: task-only", "D1": "D1: lambda_org=1", "D2": f"D2: lambda_org={LAMBDA_D2:g}"}

    ax = axes[0]
    for name in ["A", "D1", "D2"]:
        traj = tight[name]["traj"]
        ax.plot(traj["t"], tight[name]["Dorg_ctrl"], color=colors[name], lw=2, label=labels[name])
        ax.plot(release[name]["t"] + T_REP, release[name]["Dorg"], color=colors[name], lw=2, ls=":")
    ax.axvspan(T_REP, T_REP + ctl.T_RELEASE, color="gray", alpha=0.08)
    ax.axvline(T_REP, color="black", lw=0.8, ls="--", alpha=0.6)
    ax.set_xlabel("t  (shaded: release period)")
    ax.set_ylabel(r"$D_{\rm org}(t)$ (nats)")
    ax.set_title("Panel A: organizational departure")
    for i, r in enumerate(rows):
        infeasible_tag = "  [TASK NOT MET]" if (r["task_resid_y"] > 1e-3 or r["task_resid_cM"] > 1e-3) else ""
        ax.annotate(f"{r['protocol']}: A_ctrl={r['A_org_ctrl']:.3f}, E={r['E_total']:.2f}{infeasible_tag}",
                    xy=(0.02, 0.95 - 0.08 * i), xycoords="axes fraction", fontsize=7.5,
                    color=colors[r["protocol"]], fontweight=("bold" if infeasible_tag else "normal"))
    ax.legend(fontsize=8, loc="lower right")

    ax = axes[1]
    for name in ["A", "D1", "D2"]:
        traj = tight[name]["traj"]
        ax.plot(traj["t"], tight[name]["L3_dense"], color=colors[name], lw=2, label=labels[name])
        ax.plot(release[name]["t"] + T_REP, release[name]["L3"], color=colors[name], lw=2, ls=":")
    ax.axhline(DELTA, color="gray", ls=":", lw=1.2, label=f"delta={DELTA}")
    ax.axvline(T_REP, color="black", lw=0.8, ls="--", alpha=0.6)
    ax.set_xlabel("t")
    ax.set_ylabel(r"$\Lambda_3(t)$ (nats)")
    ax.set_title("Panel B: pathwise leakage")
    ax.legend(fontsize=8)

    ax = axes[2]
    lam_vals = [0.0, 0.01, 0.1, 1.0, 10.0, 100.0]
    for phen, marker in [(False, "o")]:
        Es, Aorgs = [], []
        for lam in lam_vals:
            if lam == 0.0:
                r = rec_A
            elif lam == LAMBDA_D2:
                Es.append(rows[2]["E_total"]); Aorgs.append(rows[2]["A_org_ctrl"]); continue
            else:
                r = lib.find(recs, "D", phen, T_REP, rho_z=RHO_Z, lambda_org=lam)
            if r is None:
                continue
            dtraj = lib.load_traj(r)
            Dorg_c = np.array([ctl.dyn.D_org(dtraj["m"][i], dtraj["Sigma"][i], dtraj["y"][i], dtraj["z"][i])[0]
                                for i in range(len(dtraj["t"]))])
            Es.append(float(r["E_total"] if isinstance(r, dict) else r["E_total"]))
            Aorgs.append(float(np.trapezoid(Dorg_c, dtraj["t"])))
        order = np.argsort(Es)
        ax.plot(np.array(Es)[order], np.array(Aorgs)[order], "-o", color=fs.COLOR_INTERIOR)
        for lam, e, a in zip(lam_vals, Es, Aorgs):
            ax.annotate(f"{lam:g}", (e, a), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("control energy E")
    ax.set_ylabel(r"$A_{\rm org}^{\rm ctrl}$")
    ax.set_title("Panel C: energy-vs-organization tradeoff\n(all completed lambda_org values, T=2, coordinated)",
                 fontsize=9.5)

    any_infeasible = any(r["task_resid_y"] > 1e-3 or r["task_resid_cM"] > 1e-3 for r in rows)
    subtitle = ("\n[TASK NOT MET] flags a protocol whose 'best found' solution did not satisfy the "
                "hard task constraints tightly -- its E/D_org numbers are not directly comparable to "
                "a feasible solution's." if any_infeasible else "")
    fig.suptitle(f"Genuine organization-aware control: task-only vs. lambda_org=1 vs. "
                 f"lambda_org={LAMBDA_D2:g}  (T={T_REP}, rho_z={RHO_Z}, coordinated){subtitle}",
                 fontsize=10.5 if any_infeasible else 11.5, y=1.06 if any_infeasible else 1.04)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig8_revised")
    fs.save_all(fig, outpath)
    plt.close(fig)
    p(f"\nSaved {outpath}.png/.pdf/.svg")

    with open(os.path.join(os.path.dirname(__file__), "data", "fig8_revised_log.txt"), "w") as f:
        f.write("\n".join(log))
