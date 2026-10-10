"""Static figures for the closure deliverables (matplotlib, headless)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_closure as C  # noqa: E402


def fig_class_comparison():
    analysis = json.load(open(C.DATA_DIR / "closure_analysis_summary.json"))
    ci = analysis["closureA"]["class_level_ci_minus_j"]
    classes = ["core_member", "boundary_member", "live_exterior_parent", "near_exterior_non_parent"]
    labels = ["Core", "Boundary", "Live parent", "Non-parent"]
    means = [ci.get(c, {}).get("mean") or 0 for c in classes]
    los = [ci.get(c, {}).get("lo") or 0 for c in classes]
    his = [ci.get(c, {}).get("hi") or 0 for c in classes]
    ns = [ci.get(c, {}).get("n") or 0 for c in classes]
    err_lo = [max(0, m - lo) for m, lo in zip(means, los)]
    err_hi = [max(0, hi - m) for m, hi in zip(means, his)]

    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ["#6fa3e0", "#7c5cbf", "#b3298c", "#8a8fa3"]
    ax.bar(labels, means, yerr=[err_lo, err_hi], color=colors, capsize=4)
    for i, n in enumerate(ns):
        ax.text(i, means[i] + err_hi[i] + 0.001, f"n={n}", ha="center", fontsize=9)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("mean ΔJ_conservative (A_minus_j-corrected, state-paired, 90% CI)")
    ax.set_title("Closure A: organizational-class effect")
    plt.tight_layout()
    plt.savefig(C.FIG_DIR / "closureA_class_comparison.png", dpi=150)
    plt.close()


def fig_geometric_vs_directed():
    analysis = json.load(open(C.DATA_DIR / "closure_analysis_summary.json"))
    gvd = analysis["closureB"]["geometric_vs_directed"]
    labels = ["Geometric\ncontact", "Live directed\naccess", "Temporal\nreachability (≤3 hop)"]
    keys = ["geometric_ci", "live_directed_ci", "temporal_reach_ci"]
    means = [gvd[k]["mean"] or 0 for k in keys]
    los = [gvd[k]["lo"] or 0 for k in keys]
    his = [gvd[k]["hi"] or 0 for k in keys]
    err_lo = [max(0, m - lo) for m, lo in zip(means, los)]
    err_hi = [max(0, hi - m) for m, hi in zip(means, his)]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, means, yerr=[err_lo, err_hi], color=["#c77d1e", "#14802e", "#2a9d8f"], capsize=4)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("median per-state Spearman ρ with ΔJ_conservative (90% CI over states)")
    ax.set_title("Closure B: association strength with intervention effect")
    plt.tight_layout()
    plt.savefig(C.FIG_DIR / "closureB_geometric_vs_directed.png", dpi=150)
    plt.close()


def fig_timing():
    rows = json.load(open(C.DATA_DIR / "closureC_timing_rollouts.json"))
    by_state_onset = {}
    for r in rows:
        by_state_onset.setdefault(r["state_id"], {}).setdefault(r["onset_offset"], []).append(r["delta_J_conservative"])

    fig, ax = plt.subplots(figsize=(6.5, 4))
    for sid, d in by_state_onset.items():
        onsets = sorted(d.keys())
        means = [float(np.mean(d[o])) for o in onsets]
        ax.plot(onsets, means, marker="o", label=sid.replace("sclosure_", "s"))
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("onset offset (real steps)")
    ax.set_ylabel("mean ΔJ_conservative")
    ax.set_title("Closure C: effect vs intervention onset")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(C.FIG_DIR / "closureC_timing.png", dpi=150)
    plt.close()


def main():
    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig_class_comparison()
    fig_geometric_vs_directed()
    fig_timing()
    print("wrote figures to", C.FIG_DIR)


if __name__ == "__main__":
    main()
