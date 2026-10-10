"""One-page contact sheet of figures 1-8."""
from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

FIG_DIR = Path(__file__).resolve().parents[2] / "figures"
NAMES = [
    "fig01_baseline_macroagent.png", "fig02_spectral_identification.png",
    "fig03_actuator_response_map.png", "fig04_leverage_comparison.png",
    "fig05_before_during_after.png", "fig06_steering_trajectory.png",
    "fig07_sparse_requirement.png", "fig08_release_comparison.png",
]


def main():
    fig, axes = plt.subplots(4, 2, figsize=(14, 22))
    for ax, name in zip(axes.flat, NAMES):
        img = mpimg.imread(FIG_DIR / name)
        ax.imshow(img)
        ax.axis("off")
        ax.set_title(name, fontsize=8)
    fig.suptitle("Stage 6 (flock) Experiment 1 — contact sheet (primary finding: negative)", fontsize=14)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "contact_sheet.png", dpi=110)
    fig.savefig(FIG_DIR / "contact_sheet.pdf")
    print("Contact sheet written to", FIG_DIR / "contact_sheet.png")


if __name__ == "__main__":
    main()
