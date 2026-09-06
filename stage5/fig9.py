"""Figure 9: Does supporting the interface help?
Row 1: phenotype-only vs coordinated, 4 metrics, averaged over formulations A-D, at
       the baseline rho_z=1 (bar chart per horizon).
Row 2: rho_z sensitivity -- how coordinated control's energy/leakage tradeoff changes
       as u_z is penalized more heavily (rho_z in {0.25,1,4}), with the (rho_z-
       independent) phenotype-only baseline as a horizontal reference.
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

if __name__ == "__main__":
    recs = lib.load_all()
    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 4, height_ratios=[1, 1], hspace=0.5, wspace=0.35)

    metrics = ["E_total", "max_L3", "Dorg_total", "final_KL_to_pB"]
    titles = ["control energy E", r"$\max_t\Lambda_3$", "D_org total (formulation D only)",
              "release-end KL to p*_{+1,+1}"]
    row1_axes = [fig.add_subplot(gs[0, i]) for i in range(4)]
    for ax, metric, title in zip(row1_axes, metrics, titles):
        width = 0.35
        xs = np.arange(len(HORIZONS))
        for i, phen in enumerate([False, True]):
            vals = []
            for T in HORIZONS:
                cell = []
                for f in FORMULATIONS:
                    r = lib.find(recs, f, phen, T)
                    if r is not None and r.get("ok") and r.get(metric) is not None:
                        cell.append(r[metric])
                vals.append(np.mean(cell) if cell else np.nan)
            ax.bar(xs + (i - 0.5) * width, vals, width=width,
                   color=(fs.COLOR_INTERIOR if not phen else fs.COLOR_BOUNDARY),
                   label="coordinated" if not phen else "phenotype-only")
        ax.set_xticks(xs); ax.set_xticklabels([f"T={T}" for T in HORIZONS])
        ax.set_title(title, fontsize=10)
        if metric == "max_L3":
            ax.set_yscale("symlog", linthresh=1e-6)
    row1_axes[0].legend(fontsize=8.5)
    fig.text(0.01, 0.96, "Row 1: baseline (rho_z=1), averaged over formulations A-D",
             fontsize=10, fontweight="bold")

    # Row 2: rho_z sensitivity for coordinated control, vs the (rho_z-independent)
    # phenotype-only baseline
    row2_axes = [fig.add_subplot(gs[1, i]) for i in range(2)]
    for ax, T in zip(row2_axes, [1.0, 2.0]):
        E_by_rho, L3_by_rho = [], []
        for rho in RHO_Z_SENS:
            cell_E, cell_L3 = [], []
            for f in FORMULATIONS:
                r = lib.find(recs, f, False, T, rho_z=rho)
                if r is not None and r.get("ok"):
                    cell_E.append(r["E_total"]); cell_L3.append(r["max_L3"])
            E_by_rho.append(np.mean(cell_E) if cell_E else np.nan)
            L3_by_rho.append(np.mean(cell_L3) if cell_L3 else np.nan)
        phen_E = [lib.find(recs, f, True, T)["E_total"] for f in FORMULATIONS
                  if lib.find(recs, f, True, T) is not None and lib.find(recs, f, True, T).get("ok")]
        phen_E_mean = np.mean(phen_E) if phen_E else np.nan

        ax2 = ax.twinx()
        ax.plot(RHO_Z_SENS, E_by_rho, "-o", color=fs.COLOR_INTERIOR, label="coordinated E (mean over A-D)")
        ax.axhline(phen_E_mean, color=fs.COLOR_BOUNDARY, ls="--", label="phenotype-only E (rho_z-independent)")
        ax2.plot(RHO_Z_SENS, L3_by_rho, "-s", color=fs.COLOR_ACCENT, label=r"coordinated $\max\Lambda_3$")
        ax2.set_yscale("symlog", linthresh=1e-6)
        ax.set_xscale("log")
        ax.set_xlabel("rho_z (u_z cost weight)")
        ax.set_ylabel("control energy E", color=fs.COLOR_INTERIOR)
        ax2.set_ylabel(r"$\max_t\Lambda_3$", color=fs.COLOR_ACCENT)
        ax.set_title(f"T={T}: does penalizing u_z erase coordinated control's advantage?", fontsize=9.5)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="best")
    fig.text(0.01, 0.46, "Row 2: rho_z sensitivity (coordinated control only; formulations A-D averaged)",
             fontsize=10, fontweight="bold")

    fig.suptitle("Phenotype-only vs. coordinated control, and sensitivity to the u_z cost weight",
                 fontsize=12, y=1.01)
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig9_phenotype_vs_coordinated")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
