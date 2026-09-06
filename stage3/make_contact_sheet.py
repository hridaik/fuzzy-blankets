import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

FIGURES = [
    ("sfig1_control_setup", "SFig 1: What are we controlling?"),
    ("sfig2_deltaJ_heatmap", "SFig 2: Full dynamical change with q"),
    ("sfig3_impulse_atlas", "SFig 3: Impulse-response atlas"),
    ("sfig4_static_leverage", "SFig 4: Static leverage vs. circulation"),
    ("sfig5_energy_vs_horizon", "SFig 5: Min energy vs. time horizon"),
    ("sfig6_crossover", "SFig 6: Short-time crossover"),
    ("sfig7_actuator_phase_diagram", "SFig 7: Actuator phase diagram"),
    ("sfig8_statistical_vs_control", "SFig 8: Statistical vs. control"),
    ("sfig9_steering_examples", "SFig 9: Steering examples"),
    ("calibration_figure", "Calibration: high-precision coverage"),
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
    fig.suptitle("Contact sheet — Track 1/2 (steering + calibration) figures", fontsize=15, y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    outpath = os.path.join(FIGDIR, "contact_sheet_stage3")
    fig.savefig(outpath + ".png", bbox_inches="tight", dpi=150)
    fig.savefig(outpath + ".pdf", bbox_inches="tight")
    plt.close(fig)
    print("Contact sheet saved to", outpath + ".png/.pdf")
