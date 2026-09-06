import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR, COLOR_ACCENT

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

if __name__ == "__main__":
    rows = []
    with open(os.path.join(DATADIR, "track1_highprec_coverage.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: (v if k == "B" else float(v)) for k, v in r.items()})

    cell_labels = [f"{r['B']}, n={int(r['n'])}" for r in rows]
    x = np.arange(len(rows))

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), width_ratios=[1.5, 1])
    ax0 = axes[0]
    methods = [("basic", COLOR_BOUNDARY, "basic (error-inversion, deployable)"),
               ("percentile", COLOR_EXTERIOR, "percentile (deployable)"),
               ("oracle", COLOR_INTERIOR, "oracle (NOT deployable; diagnostic only)")]
    offsets = [-0.2, 0.0, 0.2]
    for (method, color, label), off in zip(methods, offsets):
        cov = np.array([r[f"coverage_{method}"] for r in rows])
        lo = np.array([r[f"coverage_{method}_wilson_lo"] for r in rows])
        hi = np.array([r[f"coverage_{method}_wilson_hi"] for r in rows])
        yerr = np.vstack([cov - lo, hi - cov])
        ax0.errorbar(x + off, cov, yerr=yerr, fmt="o", color=color, markersize=5,
                     capsize=3, label=label)
    ax0.axhline(0.95, color="black", linestyle=":", linewidth=1.3, label="nominal 0.95")
    ax0.set_xticks(x); ax0.set_xticklabels(cell_labels, rotation=30, ha="right", fontsize=8)
    ax0.set_ylabel("empirical one-sided coverage (95% target)")
    ax0.set_title(f"A: high-precision coverage (R_outer=5000, M_boot=1000)\nWilson 95% CIs shown")
    ax0.legend(fontsize=7.5, loc="lower left")
    ax0.set_ylim(0.5, 1.02)

    # Part 1E: certification probability vs margin
    ax1 = axes[1]
    margin_rows = []
    with open(os.path.join(DATADIR, "track1_partE_margin.csv")) as f:
        for r in csv.DictReader(f):
            margin_rows.append({k: (v if k == "B" else float(v)) for k, v in r.items()})
    for Bkey, color in [("(4, 5)", COLOR_BOUNDARY), ("(4,)", COLOR_EXTERIOR), ("()", COLOR_INTERIOR)]:
        for n, alpha, marker in [(200, 0.4, "s"), (1000, 0.7, "o"), (5000, 1.0, "^")]:
            sub = [r for r in margin_rows if r["B"] == Bkey and r["n"] == n]
            sub = sorted(sub, key=lambda r: r["margin"])
            m = [r["margin"] for r in sub]
            cp = [r["cert_prob"] for r in sub]
            ax1.plot(m, cp, marker=marker, color=color, alpha=alpha, markersize=4, linewidth=1.2,
                    label=f"B={Bkey}, n={n}" if Bkey == "(4, 5)" else None)
    ax1.axvline(0, color="gray", linestyle="--", linewidth=1.0)
    ax1.set_xlabel(r"certification margin $M_\delta(B) = \delta - L_{\rm pop}(B)$")
    ax1.set_ylabel("empirical certification probability")
    ax1.set_title("B: certification probability vs. margin\n(B={4,5} highlighted; small positive margin is hard)")
    ax1.legend(fontsize=7, loc="lower right")

    fig.suptitle("Stage-2/3 calibration figure — high-precision coverage reassessment", y=1.03, fontsize=12.5)
    save_all(fig, os.path.join(FIGDIR, "calibration_figure"))
    plt.close(fig)
    print("Calibration figure saved.")
