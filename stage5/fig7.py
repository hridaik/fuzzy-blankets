"""Figure 7: Cost of preserving collective integrity.
Row 1: baseline grid (rho_z=1, lambda_org=0) -- control energy vs max Lambda_3,
       phenotype-only vs coordinated, one panel per horizon.
Row 2: rho_z sensitivity (coordinated only, rho_z in {0.25,1,4}, T in {1,2}) -- does
       penalizing u_z more heavily change the energy/leakage tradeoff?
Row 3: lambda_org sensitivity (formulation D only, T in {1,2}) -- energy vs D_org
       tradeoff as the naturality penalty is swept.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import control_results_lib as lib

HORIZONS = [0.5, 1, 2, 4]
FORMULATIONS = ["A", "B", "C", "D"]
RHO_Z_SENS = [0.25, 1.0, 4.0]
LAMBDA_ORG_GRID = [0.0, 0.01, 0.1, 1.0, 10.0]
markers = dict(A="o", B="s", C="^", D="D")

if __name__ == "__main__":
    recs = lib.load_all()
    fig = plt.figure(figsize=(4.3 * len(HORIZONS), 13.5))
    gs = fig.add_gridspec(3, len(HORIZONS), height_ratios=[1, 1, 1], hspace=0.55, wspace=0.3)

    # --- Row 1: baseline grid ---
    row1_axes = [fig.add_subplot(gs[0, i]) for i in range(len(HORIZONS))]
    for ax, T in zip(row1_axes, HORIZONS):
        for phen, marker_fill in [(False, "full"), (True, "none")]:
            for f in FORMULATIONS:
                r = lib.find(recs, f, phen, T)
                if r is None or not r.get("ok"):
                    continue
                mfc = fs.COLOR_ACCENT if marker_fill == "full" else "white"
                ax.scatter(r["E_total"], max(r["max_L3"], 1e-9), marker=markers[f], s=70,
                           facecolor=mfc, edgecolor=fs.COLOR_ACCENT if marker_fill == "full" else fs.COLOR_INTERIOR,
                           linewidth=1.4)
        ax.axhline(0.01, color="gray", ls=":", lw=1)
        ax.set_yscale("log")
        ax.set_xlabel("control energy E")
        ax.set_title(f"T={T}", fontsize=10)
    row1_axes[0].set_ylabel(r"$\max_t \Lambda_3(t)$ (log)")
    handles = [plt.Line2D([], [], marker=markers[f], color="gray", ls="", label=f"formulation {f}") for f in FORMULATIONS]
    handles += [plt.Line2D([], [], marker="o", color=fs.COLOR_ACCENT, ls="", label="coordinated"),
                plt.Line2D([], [], marker="o", mfc="white", color=fs.COLOR_INTERIOR, ls="", label="phenotype-only")]
    row1_axes[-1].legend(handles=handles, fontsize=7, loc="upper right", bbox_to_anchor=(1.55, 1.05))
    fig.text(0.01, 0.97, "Row 1: baseline grid (rho_z=1, lambda_org=0)", fontsize=10, fontweight="bold")

    # --- Row 2: rho_z sensitivity (coordinated only) ---
    row2_axes = [fig.add_subplot(gs[1, i]) for i in range(2)]
    for ax, T in zip(row2_axes, [1.0, 2.0]):
        cmap = plt.cm.plasma
        for f in FORMULATIONS:
            for i, rho in enumerate(RHO_Z_SENS):
                r = lib.find(recs, f, False, T, rho_z=rho)
                if r is None or not r.get("ok"):
                    continue
                ax.scatter(r["E_total"], max(r["max_L3"], 1e-9), marker=markers[f], s=80,
                           color=cmap(i / (len(RHO_Z_SENS) - 1)), edgecolor="black", linewidth=0.6)
        ax.axhline(0.01, color="gray", ls=":", lw=1)
        ax.set_yscale("log")
        ax.set_xlabel("control energy E")
        ax.set_title(f"T={T} (coordinated only)", fontsize=10)
    row2_axes[0].set_ylabel(r"$\max_t \Lambda_3(t)$ (log)")
    rho_handles = [plt.Line2D([], [], marker="o", color=plt.cm.plasma(i / (len(RHO_Z_SENS) - 1)), ls="",
                               label=f"rho_z={rho}") for i, rho in enumerate(RHO_Z_SENS)]
    row2_axes[-1].legend(handles=rho_handles, fontsize=7.5, loc="upper right", bbox_to_anchor=(1.5, 1.05))
    fig.text(0.01, 0.65, "Row 2: rho_z sensitivity (u_z cost weight), formulations A-D",
             fontsize=10, fontweight="bold")

    # --- Row 3: lambda_org sensitivity (formulation D only) ---
    row3_axes = [fig.add_subplot(gs[2, i]) for i in range(2)]
    for ax, T in zip(row3_axes, [1.0, 2.0]):
        cmap = plt.cm.viridis
        for phen, ls_marker in [(False, "o"), (True, "^")]:
            Es, Dorgs = [], []
            for i, lam in enumerate(LAMBDA_ORG_GRID):
                r = lib.find(recs, "D", phen, T, lambda_org=lam)
                if r is None or not r.get("ok"):
                    continue
                Es.append(r["E_total"]); Dorgs.append(r["Dorg_total"])
                ax.scatter(r["E_total"], r["Dorg_total"], marker=ls_marker, s=80,
                           color=cmap(i / (len(LAMBDA_ORG_GRID) - 1)), edgecolor="black", linewidth=0.6)
            order = np.argsort(Es) if Es else []
            if len(Es) > 1:
                Es_s = np.array(Es)[order]; Dorgs_s = np.array(Dorgs)[order]
                ax.plot(Es_s, Dorgs_s, color="gray", lw=1, alpha=0.5, zorder=0,
                        ls="-" if not phen else "--")
        ax.set_xlabel("control energy E")
        ax.set_title(f"T={T}, formulation D only", fontsize=10)
    row3_axes[0].set_ylabel(r"$\int D_{\rm org}(t)\,dt$ (total)")
    lam_handles = [plt.Line2D([], [], marker="o", color=plt.cm.viridis(i / (len(LAMBDA_ORG_GRID) - 1)), ls="",
                               label=f"lambda_org={lam}") for i, lam in enumerate(LAMBDA_ORG_GRID)]
    lam_handles += [plt.Line2D([], [], marker="o", color="gray", ls="", label="coordinated"),
                    plt.Line2D([], [], marker="^", color="gray", ls="", label="phenotype-only")]
    row3_axes[-1].legend(handles=lam_handles, fontsize=7, loc="upper right", bbox_to_anchor=(1.55, 1.05))
    fig.text(0.01, 0.33, "Row 3: lambda_org sensitivity (formulation D: E + lambda_org * integral(D_org))",
             fontsize=10, fontweight="bold")

    fig.suptitle("Cost of preserving pathwise integrity and endogenous naturality", fontsize=13, y=1.005)
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig7_cost_of_integrity")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
