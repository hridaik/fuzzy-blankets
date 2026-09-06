"""Assembles R1-R6 into one contact sheet, matching the existing project
convention in python/figures/make_contact_sheet.py."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from common_v3 import V3_DIR

FIG_DIR = V3_DIR / "figures"
NAMES = [
    "R1_coverage_predicts_control", "R2_distributed_vs_patch", "R3_minimal_sufficient_interface",
    "R4_transition_aware_integrity", "R5_predictive_permeability", "R6_final_control_story",
]


def main():
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    for ax, name in zip(axes.flat, NAMES):
        img = mpimg.imread(FIG_DIR / f"{name}.png")
        ax.imshow(img)
        ax.axis("off")
    fig.suptitle("V3 refinement — contact sheet (R1-R6)", fontsize=14)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "contact_sheet.png", dpi=130)
    fig.savefig(FIG_DIR / "contact_sheet.pdf")
    print("wrote", FIG_DIR / "contact_sheet.png")


if __name__ == "__main__":
    main()
