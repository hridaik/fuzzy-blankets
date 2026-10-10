"""Evidence-recovery audit, Step 1. Visualization only -- reads the derived
CSVs from `derive_material_retention.py` plus the unmodified production
`data/viz_bundle_611__seed{n}.json`. No tracker/controller/world code is
touched. Deterministic given the same inputs.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AUDIT_DIR = Path(__file__).resolve().parents[2]
STAGE_DIR = AUDIT_DIR.parent
OUT_DIR = Path(__file__).resolve().parents[1]
DATA_OUT = OUT_DIR / "data"
PLOT_OUT = OUT_DIR / "plots"

SEEDS = [500, 501, 502, 503, 504]


def load_retention(seed):
    path = DATA_OUT / f"material_retention_seed{seed}.csv"
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("R_old_displayed", "R_new_displayed", "jaccard_displayed"):
            r[k] = float(r[k]) if r[k] not in ("", "None") else None
        r["t"] = int(r["t"])
        r["overlap_zero_displayed"] = r["overlap_zero_displayed"] == "True"
        r["flagged_unusual_transition_lineage_forensics"] = r["flagged_unusual_transition_lineage_forensics"] == "True"
    return rows


def load_frames(seed):
    d = json.load(open(STAGE_DIR / "data" / f"viz_bundle_611__seed{seed}.json"))
    return d["frames"]


def frac_at_target(frame):
    th = frame.get("target_heading")
    interior = frame.get("interior") or []
    if th is None or not interior:
        return None
    z = frame["z"]
    return sum(1 for i in interior if z[i] == th) / len(interior)


def control_release_bounds(frames):
    control_ts = [f["t"] for f in frames if f["phase"] == "control"]
    release_ts = [f["t"] for f in frames if f["phase"] == "release"]
    c = (min(control_ts), max(control_ts)) if control_ts else None
    r = (min(release_ts), max(release_ts)) if release_ts else None
    return c, r


def plot_seed(seed):
    rows = load_retention(seed)
    frames = load_frames(seed)
    control_bounds, release_bounds = control_release_bounds(frames)

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    ax0, ax1 = axes

    ts = [r["t"] for r in rows]
    ax0.plot(ts, [r["R_old_displayed"] for r in rows], label="R_old (displayed)", color="#1f77b4", lw=1.2)
    ax0.plot(ts, [r["R_new_displayed"] for r in rows], label="R_new (displayed)", color="#ff7f0e", lw=1.2)
    ax0.plot(ts, [r["jaccard_displayed"] for r in rows], label="Jaccard (displayed)", color="#2ca02c", lw=1.2)

    zero_ts = [r["t"] for r in rows if r["overlap_zero_displayed"]]
    for zt in zero_ts:
        ax0.axvline(zt, color="red", alpha=0.5, lw=1.5, ls="--")
    flagged_ts = [r["t"] for r in rows if r["flagged_unusual_transition_lineage_forensics"]]
    for ft in flagged_ts:
        ax0.axvline(ft, color="grey", alpha=0.35, lw=1.0, ls=":")

    if control_bounds:
        ax0.axvspan(control_bounds[0], control_bounds[1], color="purple", alpha=0.08, label="control window")
        ax1.axvspan(control_bounds[0], control_bounds[1], color="purple", alpha=0.08)
    if release_bounds:
        ax0.axvspan(release_bounds[0], release_bounds[1], color="green", alpha=0.06, label="release window")
        ax1.axvspan(release_bounds[0], release_bounds[1], color="green", alpha=0.06)

    # Explicit markers for the audit's named transitions of interest.
    named = []
    if seed == 500:
        named = [(20, 21, "t=20->21 (flagged, LINEAGE_FORENSICS_6_11.md #1.1)"),
                 (46, 47, "t=46->47 (visual-inspection claim; NOT flagged, overlap=full)")]
    for t_a, t_b, label in named:
        ax0.annotate(label, xy=(t_b, 0.02), xytext=(t_b, -0.28),
                     fontsize=7, rotation=90, ha="center", va="bottom",
                     arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    ax0.set_ylim(-0.05, 1.35)
    ax0.set_ylabel("membership overlap fraction")
    ax0.legend(loc="upper right", fontsize=7, ncol=3)
    ax0.set_title(f"Seed {seed}: material-retention diagnostics (displayed interior, frame-to-frame)\n"
                   f"red dashed = zero-overlap transition; grey dotted = flagged by lineage_forensics_611 (any criterion)")

    fat = [frac_at_target(f) for f in frames]
    ftt = [f["t"] for f in frames]
    ax1.plot(ftt, fat, color="black", lw=1.2, label="fraction of v1 interior at target heading")
    ax1.set_ylabel("frac at target heading")
    ax1.set_xlabel("t")
    ax1.set_ylim(-0.05, 1.05)
    ax1.legend(loc="upper right", fontsize=7)

    fig.tight_layout()
    out = PLOT_OUT / f"seed{seed}_material_retention_and_heading.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", out)


def plot_distribution_overview():
    """Empirical distribution of R_old (displayed) at ordinary steps vs at
    flagged/zero-overlap transitions, across all 5 seeds -- exploratory
    only, no threshold recommended (per task instructions)."""
    ordinary, flagged = [], []
    per_seed_points = {}
    for seed in SEEDS:
        rows = load_retention(seed)
        for r in rows:
            if r["R_old_displayed"] is None:
                continue
            if r["flagged_unusual_transition_lineage_forensics"]:
                flagged.append(r["R_old_displayed"])
            else:
                ordinary.append(r["R_old_displayed"])
        per_seed_points[seed] = [r["R_old_displayed"] for r in rows if r["R_old_displayed"] is not None]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(ordinary, bins=30, alpha=0.6, label=f"ordinary consecutive steps (n={len(ordinary)})", color="#1f77b4", density=True)
    ax.hist(flagged, bins=15, alpha=0.6, label=f"flagged unusual transitions (n={len(flagged)})", color="#d62728", density=True)
    ax.set_xlabel("R_old (displayed), consecutive-step material retention")
    ax.set_ylabel("density")
    ax.set_title("EXPLORATORY sensitivity view -- not a validated threshold\n"
                 "R_old distribution: ordinary steps vs. lineage_forensics-flagged transitions, all 5 seeds")
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = PLOT_OUT / "R_old_distribution_ordinary_vs_flagged.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", out)


def main():
    PLOT_OUT.mkdir(exist_ok=True)
    for seed in SEEDS:
        plot_seed(seed)
    plot_distribution_overview()


if __name__ == "__main__":
    main()
