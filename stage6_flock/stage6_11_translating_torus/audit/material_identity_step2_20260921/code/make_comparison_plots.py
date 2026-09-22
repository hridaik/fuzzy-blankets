"""Step 2 comparison plots: v1 vs forward-material-trace, per seed."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parents[1]
SEEDS = [500, 501, 502, 503, 504]


def load(seed):
    with open(OUT / "data" / f"forward_material_trace_seed{seed}.csv", newline="") as f:
        return list(csv.DictReader(f))


def fnum(x):
    return float(x) if x not in ("", "None", None) else None


def plot_seed(seed):
    rows = load(seed)
    ts = [int(r["t"]) for r in rows]
    frac_v1 = [fnum(r["frac_v1_at_target"]) for r in rows]
    frac_tr = [fnum(r["frac_trace_at_target"]) for r in rows]
    n_v1 = [int(r["v1_interior_size"]) for r in rows]
    n_tr = [int(r["n_members"]) for r in rows]
    disagree_ts = [int(r["t"]) for r in rows if r["v1_vs_trace_agree"] == "False"]
    unresolved_ts = [int(r["t"]) for r in rows if r["status"] == "unresolved"]
    split_ts = [int(r["t"]) for r in rows if r["split_flag"] == "True"]
    merge_ts = [int(r["t"]) for r in rows if r["merge_flag"] == "True"]

    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    ax0.plot(ts, frac_v1, label="v1 (displayed interior)", color="#1f77b4", lw=1.4)
    ax0.plot(ts, frac_tr, label="ForwardMaterialTrace611", color="#d62728", lw=1.4, ls="--")
    for t in disagree_ts:
        ax0.axvspan(t - 0.5, t + 0.5, color="grey", alpha=0.15)
    for t in unresolved_ts:
        ax0.axvline(t, color="#b45309", alpha=0.6, lw=1.2, ls=":")
    for t in split_ts:
        ax0.plot(t, 1.02, marker="v", color="#b45309", markersize=6)
    for t in merge_ts:
        ax0.plot(t, 1.02, marker="^", color="#7c3aed", markersize=6)
    ax0.set_ylabel("fraction at target heading")
    ax0.set_ylim(-0.05, 1.1)
    ax0.legend(loc="upper left", fontsize=8)
    ax0.set_title(f"Seed {seed}: v1 vs. ForwardMaterialTrace611 (frozen rule B, Jaccard>=0.30)\n"
                   f"grey band = disagreement frame; dotted amber = unresolved; ▽ split flag; △ merge flag")

    ax1.plot(ts, n_v1, label="v1 interior size", color="#1f77b4", lw=1.2)
    ax1.plot(ts, n_tr, label="trace target size", color="#d62728", lw=1.2, ls="--")
    ax1.set_ylabel("member count")
    ax1.set_xlabel("t")
    ax1.legend(loc="upper left", fontsize=8)

    fig.tight_layout()
    out = OUT / "plots" / f"seed{seed}_v1_vs_forward_trace.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", out)


def main():
    (OUT / "plots").mkdir(exist_ok=True)
    for seed in SEEDS:
        plot_seed(seed)


if __name__ == "__main__":
    main()
