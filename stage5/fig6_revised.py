"""Figure 6 (REVISED per final-patch Part 1): boundary membership among MINIMUM-
CARDINALITY leakage-acceptable boundaries, not arbitrary zero-leakage supersets.

Problem with the original fig6: it visualized membership among ALL boundaries with
|B|<=3 achieving (near-)minimal Lambda_3, which includes unnecessary zero-leakage
supersets (e.g. {4,5,6} at endpoint B, where {5,6} alone already suffices and node 4
was moved into B for no reason). This version instead uses, at each time t:

    K_delta(t) = min{|B| : L_B(t) <= delta}
    B_min,delta(t) = {B : |B| = K_delta(t), L_B(t) <= delta}

i.e. only the SMALLEST boundaries that satisfy the leakage tolerance are counted as
"interface membership". delta=0.01 (Stage-5 primary tolerance), tie tolerance stated
explicitly below (TIE_TOL = 1e-6, same declared tolerance as integrity.py).
"""
import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import control_results_lib as lib
import integrity as I

T_REP = 2
DELTA = 0.01
TIE_TOL = I.TIE_TOL
NODES = [4, 5, 6, 7, 8]

if __name__ == "__main__":
    log = []
    def p(s=""):
        print(s); log.append(s)

    recs = lib.load_all()
    k = lib.key("C", False, T_REP)
    rec = recs[k]
    d = lib.load_traj(rec)
    t_ctrl, Sigma_ctrl = d["t"], d["Sigma"]
    t_rel = d["rel_t"] + T_REP
    # release-period Sigma is NOT saved in the control_results npz (only L3/Dorg/KL were
    # saved for the release phase) -- recompute it here via control.release_phase's same
    # underlying integrator (dynamics.integrate), using the saved control-end state as
    # the release initial condition. This reproduces exactly what control.release_phase
    # already computed; we just also need Sigma(t) itself, not only Lambda_3(t) from it.
    import dynamics as dyn
    y_T, z_T, m_T, Sigma_T = d["y"][-1], d["z"][-1], d["m"][-1], d["Sigma"][-1]
    rel = dyn.integrate(y_T, z_T, m_T, Sigma_T, 4.0, n_eval=len(t_rel))
    Sigma_rel = rel["Sigma"]

    t_all = np.concatenate([t_ctrl, t_rel])
    Sigma_all = np.concatenate([Sigma_ctrl, Sigma_rel], axis=0)
    phase = np.array(["control"] * len(t_ctrl) + ["release"] * len(t_rel))

    p(f"=== Figure 6 revision: minimum-cardinality boundary family, delta={DELTA}, "
      f"tie_tol={TIE_TOL:.0e} ===")
    p(f"Trajectory: formulation C (pathwise-integrity), T={T_REP}, coordinated control, "
      f"same representative solution as the original Figure 6, plus its release period.")

    Kdelta_series = np.zeros(len(t_all), dtype=object)
    families = []
    membership = np.zeros((len(NODES), len(t_all)))
    no_compact = np.zeros(len(t_all), dtype=bool)

    for i in range(len(t_all)):
        Kd, achievers = I.K_delta(Sigma_all[i], DELTA, from_precision=False, tie_tol=TIE_TOL)
        if Kd is None:
            no_compact[i] = True
            Kdelta_series[i] = None
            families.append([])
            continue
        Kdelta_series[i] = Kd
        families.append(achievers)
        for j, n in enumerate(NODES):
            membership[j, i] = np.mean([1.0 if n in B else 0.0 for B in achievers])

    if np.any(no_compact):
        p(f"WARNING: {no_compact.sum()} timepoints have NO compact (|B|<=4 within the "
          f"candidate pool {{4,5,6,7}}) boundary satisfying delta={DELTA} -- marked explicitly, "
          f"not filled in with an arbitrary larger set.")
    else:
        p("No timepoints lacked a compact acceptable boundary (Kdelta well-defined throughout).")

    # audit prints: initial, a few intermediate, control end, release end
    audit_idx = [0, len(t_ctrl) // 4, len(t_ctrl) // 2, 3 * len(t_ctrl) // 4,
                 len(t_ctrl) - 1, len(t_all) - 1]
    p("\nAudit: boundary families at representative times")
    for i in sorted(set(audit_idx)):
        tag = "control-end" if i == len(t_ctrl) - 1 else ("release-end" if i == len(t_all) - 1 else phase[i])
        p(f"  t={t_all[i]:.3f} [{tag}]  K_delta={Kdelta_series[i]}  families={families[i]}")

    # reference-endpoint sanity note (NOT forced): compare to {4,5} near A / {5,6} near B
    p(f"\nReference note (not enforced): initial state family = {families[0]} "
      f"(quasi-static endpoint-A reference is {{(4,5)}}); this trajectory starts at "
      f"endpoint-A equilibrium so exact agreement is expected here. Final release-end "
      f"family = {families[-1]} (endpoint-B reference is {{(5,6)}}, expected only once "
      f"the system has actually relaxed close to endpoint B -- not asserted a priori).")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 5.6), sharex=True,
                                    gridspec_kw=dict(height_ratios=[3, 1]))
    im = ax1.imshow(membership, aspect="auto", cmap="YlOrRd", vmin=0, vmax=1,
                     extent=[t_all[0], t_all[-1], len(NODES) - 0.5, -0.5])
    for i in np.where(no_compact)[0]:
        ax1.axvline(t_all[i], color="blue", alpha=0.15, lw=1)
    ax1.axvline(T_REP, color="black", lw=1, ls="--", alpha=0.6)
    ax1.set_yticks(range(len(NODES)))
    ax1.set_yticklabels([f"node {n}" for n in NODES])
    ax1.set_title(f"Minimum-cardinality boundary membership m_k(t)  (delta={DELTA}, T={T_REP}, "
                   "formulation C + release)", fontsize=10.5)
    cbar = fig.colorbar(im, ax=ax1, fraction=0.03, pad=0.02)
    cbar.set_label("fraction of tied minimal boundaries containing node k")

    Kd_plot = np.array([np.nan if v is None else v for v in Kdelta_series])
    ax2.step(t_all, Kd_plot, where="mid", color=fs.COLOR_INTERIOR, lw=2)
    ax2.axvline(T_REP, color="black", lw=1, ls="--", alpha=0.6)
    ax2.set_ylabel(r"$K_\delta(t)$")
    ax2.set_xlabel("t  (dashed line: control ends / release begins)")
    ax2.set_yticks([1, 2, 3, 4])
    ax2.set_ylim(0.5, 4.5)

    fig.suptitle("Boundary membership is defined among the smallest boundaries that satisfy the\n"
                 "leakage tolerance, so unnecessary zero-leakage supersets are not counted as\n"
                 "interface membership.", fontsize=9.5, y=1.08)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig6_revised")
    fs.save_all(fig, outpath)
    plt.close(fig)
    p(f"\nSaved {outpath}.png/.pdf/.svg")

    # save data
    outcsv = os.path.join(os.path.dirname(__file__), "data", "fig6_revised_membership.csv")
    with open(outcsv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "phase", "Kdelta", "families"] + [f"m_{n}" for n in NODES])
        for i in range(len(t_all)):
            w.writerow([t_all[i], phase[i], Kdelta_series[i], json.dumps(families[i])] +
                       [membership[j, i] for j in range(len(NODES))])
    np.savez(os.path.join(os.path.dirname(__file__), "data", "fig6_revised_data.npz"),
             t=t_all, phase=phase, Kdelta=Kd_plot, membership=membership,
             no_compact=no_compact, T_rep=T_REP, delta=DELTA)
    with open(os.path.join(os.path.dirname(__file__), "data", "fig6_revised_log.txt"), "w") as f:
        f.write("\n".join(log))
    p(f"Saved {outcsv} and fig6_revised_data.npz")
