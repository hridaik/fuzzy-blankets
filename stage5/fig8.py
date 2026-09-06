"""Figure 8: Natural organization (D_org) and functional identity (Lambda_3) are
different quantities -- plotted together for representative protocols, formulation A
(task-only, no D_org penalty) vs formulation D (pathwise + endogenous-naturality
penalty), at T=2, coordinated control."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import control_results_lib as lib
import control as ctl
import dynamics as dyn

T_REP = 2

if __name__ == "__main__":
    recs = lib.load_all()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharex=True)
    colors = dict(A=fs.COLOR_EXTERIOR, D=fs.COLOR_ACCENT2)
    labels = dict(A="Task-only (A)", D="Pathwise + naturality (D, lambda_org=0)")
    for f in ["A", "D"]:
        k = lib.key(f, False, T_REP, lambda_org=0.0)
        if k not in recs:
            continue
        d = lib.load_traj(recs[k])
        t, y, z, m, Sigma = d["t"], d["y"], d["z"], d["m"], d["Sigma"]
        Dorg = np.array([dyn.D_org(m[i], Sigma[i], y[i], z[i])[0] for i in range(len(t))])
        L3, _ = ctl.lambda3_series(Sigma)
        axes[0].plot(t, Dorg, color=colors[f], lw=2, label=labels[f])
        axes[1].plot(t, L3, color=colors[f], lw=2, label=labels[f])
    axes[1].axhline(0.01, color="gray", ls=":", lw=1)
    axes[0].set_ylabel(r"$D_{\rm org}(t)$ (nats)")
    axes[1].set_ylabel(r"$\Lambda_3(t)$ (nats)")
    for ax in axes:
        ax.set_xlabel("t"); ax.legend(fontsize=8.5)
    fig.suptitle(f"Endogenous-organization departure vs. functional (blanket) leakage, T={T_REP}\n"
                 "(both formulations here use lambda_org=0 -- see the lambda_org sweep for the "
                 "explicit D_org-penalized case)", fontsize=10, y=1.05)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig8_organization_vs_identity")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
