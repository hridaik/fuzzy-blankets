import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

FIGURES = [
    ("fig1_anatomy", "Fig 1: Benchmark anatomy"),
    ("fig2_boundary_vs_leakage", "Fig 2: Boundary complexity vs. leakage"),
    ("fig3_epsilon_curve", "Fig 3: Exact blanket -> graded (eps sweep)"),
    ("fig4_hidden_variable", "Fig 4: Observer/representation dependence"),
    ("fig5_finite_sample", "Fig 5: Finite-sample inference"),
    ("fig6_graded_membership", "Fig 6: Graded membership stability"),
    ("fig7_ambiguity", "Fig 7: Structural ambiguity"),
    ("fig8_ou_dynamics", "Fig 8: Static blanket vs. finite-time dynamics"),
]

if __name__ == "__main__":
    fig, axes = plt.subplots(4, 2, figsize=(14, 20))
    axes = axes.flatten()
    for ax, (fname, label) in zip(axes, FIGURES):
        path = os.path.join(FIGDIR, fname + ".png")
        if os.path.exists(path):
            img = mpimg.imread(path)
            ax.imshow(img)
        else:
            ax.text(0.5, 0.5, "MISSING: " + fname, ha="center", va="center")
        ax.set_title(label, fontsize=11)
        ax.axis("off")
    fig.suptitle("Contact sheet — all benchmark figures", fontsize=15, y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    outpath = os.path.join(FIGDIR, "contact_sheet")
    fig.savefig(outpath + ".png", bbox_inches="tight", dpi=150)
    fig.savefig(outpath + ".pdf", bbox_inches="tight")
    plt.close(fig)
    print("Contact sheet saved to", outpath + ".png/.pdf")
