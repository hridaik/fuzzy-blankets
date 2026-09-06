import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

FIGURES = [
    ("fig1_natural_organization", "Fig 1: Natural organization at same target"),
    ("fig2_raw_vs_excess", "Fig 2: Raw displacement vs. excess distortion"),
    ("fig3_same_target_diff_trajectory", "Fig 3: Same target, different trajectories"),
    ("fig4_pareto_fronts", "Fig 4: Energy-organization Pareto fronts"),
    ("fig5_organization_aware_control", "Fig 5: Organization-aware control"),
    ("fig6_terminal_configuration", "Fig 6: Terminal configuration"),
    ("fig7_actuator_value_map", "Fig 7: Best actuator depends on values"),
    ("fig8_budget_tradeoff", "Fig 8: Energy vs. disruption budget"),
    ("fig9_multiactuator_pareto", "Fig 9: Multi-actuator Pareto (31 subsets)"),
    ("fig10_sparse_composition", "Fig 10: Composition of sparse actuator sets"),
]

if __name__ == "__main__":
    ncols = 2
    nrows = (len(FIGURES) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 5 * nrows))
    axes = axes.flatten()
    for ax, (fname, label) in zip(axes, FIGURES):
        path = os.path.join(FIGDIR, fname + ".png")
        if os.path.exists(path):
            ax.imshow(mpimg.imread(path))
        else:
            ax.text(0.5, 0.5, "MISSING: " + fname, ha="center", va="center")
        ax.set_title(label, fontsize=11)
        ax.axis("off")
    for ax in axes[len(FIGURES):]:
        ax.axis("off")
    fig.suptitle("Contact sheet — Stage 4 (organization-preserving steering)", fontsize=15, y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    outpath = os.path.join(FIGDIR, "contact_sheet_stage4")
    fig.savefig(outpath + ".png", bbox_inches="tight", dpi=150)
    fig.savefig(outpath + ".pdf", bbox_inches="tight")
    plt.close(fig)
    print("Contact sheet saved to", outpath + ".png/.pdf")
