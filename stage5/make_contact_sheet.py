import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

FIGURES = [
    ("fig1_changing_interface", "Fig 1: One collective, changing interface"),
    ("fig2_quasistatic_landscape", "Fig 2: Quasi-static blanket landscape"),
    ("fig3_rate_induced_loss", "Fig 3: Rate-induced loss of screening"),
    ("fig4_what_is_controlled", "Fig 4: What is being controlled?"),
    ("fig5_endpoint_vs_pathwise", "Fig 5: Endpoint validity can hide pathwise failure"),
    ("fig6_revised", "Fig 6 (revised): minimum-cardinality boundary membership"),
    ("fig7_cost_of_integrity", "Fig 7: Cost of preserving collective integrity"),
    ("fig8_revised", "Fig 8 (revised): genuine organization-aware control"),
    ("fig9_phenotype_vs_coordinated", "Fig 9: Phenotype-only vs coordinated control"),
    ("fig10_finite_data_recovery", "Fig 10: Finite-data recovery"),
    ("fig11_classification", "Fig 11: Finite-data integrity classification"),
    ("fig12_constraint_activation", "Fig 12: Pathwise constraint activation (unit test)"),
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
    fig.suptitle("Contact sheet — Stage 5 (moving-interface Markov-blanket steering)", fontsize=15, y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    outpath = os.path.join(FIGDIR, "contact_sheet_stage5")
    fig.savefig(outpath + ".png", bbox_inches="tight", dpi=150)
    fig.savefig(outpath + ".pdf", bbox_inches="tight")
    plt.close(fig)
    print("Contact sheet saved to", outpath + ".png/.pdf")
