import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import core
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR, COLOR_ACCENT

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

B_COLORS = {"()": COLOR_INTERIOR, "(4,)": COLOR_BOUNDARY, "(4, 5)": COLOR_EXTERIOR}
B_LABELS = {"()": r"$B=\varnothing$", "(4,)": r"$B=\{4\}$", "(4, 5)": r"$B=\{4,5\}$"}


def load_part_c():
    rows = []
    with open(os.path.join(DATADIR, "part_c_bias_table.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: (float(v) if k not in ("B",) else v) for k, v in r.items()})
    return rows


def load_part_e_selection(delta_target=0.025):
    path = os.path.join(DATADIR, "part_e_selection_table.csv")
    if not os.path.exists(path):
        return None
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


if __name__ == "__main__":
    rows = load_part_c()
    Bs = ["()", "(4,)", "(4, 5)"]
    n_list = sorted(set(r["n"] for r in rows))

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 9.5))
    axA, axB, axC, axD = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

    for Bk in Bs:
        sub = [r for r in rows if r["B"] == Bk]
        sub = sorted(sub, key=lambda r: r["n"])
        ns = [r["n"] for r in sub]
        L_pop = sub[0]["L_pop"]
        mean_raw = [r["mean_raw_bias"] + L_pop for r in sub]
        mean_corr = [r["mean_corr_bias"] + L_pop for r in sub]
        std_corr = [r["std_corr"] for r in sub]
        beta = [r["beta"] for r in sub]
        mean_raw_bias = [r["mean_raw_bias"] for r in sub]
        c = B_COLORS[Bk]; lab = B_LABELS[Bk]

        axA.plot(ns, mean_raw, "o-", color=c, label=lab)
        axA.axhline(L_pop, color=c, linestyle=":", linewidth=1.2, alpha=0.7)

        axB.errorbar(ns, mean_corr, yerr=std_corr, fmt="o-", color=c, label=lab, capsize=3)
        axB.axhline(L_pop, color=c, linestyle=":", linewidth=1.2, alpha=0.7)

        axC.plot(ns, beta, "-", color=c, label=lab + " (analytic $\\beta$)")
        axC.plot(ns, mean_raw_bias, "x", color=c, markersize=7, label=lab + " (empirical mean raw bias)")

    for ax, title in [(axA, "A: raw $\\widehat L$ mean vs. $n$ (dotted = population truth)"),
                       (axB, "B: bias-corrected $\\widetilde L$ mean $\\pm$ 1 s.d. vs. $n$")]:
        ax.set_xscale("log")
        ax.set_xlabel("n (log scale)")
        ax.set_ylabel("nats")
        ax.set_title(title)
        ax.legend(fontsize=8)

    axC.set_xscale("log"); axC.set_yscale("log")
    axC.set_xlabel("n (log scale)")
    axC.set_ylabel("bias [nats] (log scale)")
    axC.set_title("C: analytic bias $\\beta_{pqr}(n)$ vs. empirical raw bias")
    axC.legend(fontsize=7, ncol=1)

    # Panel D: probability of recovering population-optimal certified boundary vs n (Part E)
    pe_rows = load_part_e_selection()
    if pe_rows is not None:
        deltas_present = sorted(set(float(r["delta"]) for r in pe_rows))
        eps_present = sorted(set(int(r["eps"]) for r in pe_rows))
        colors_d = [COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR]
        for eps, ls in zip(eps_present, ["-", "--"]):
            for delta, c in zip(deltas_present, colors_d):
                sub = [r for r in pe_rows if int(r["eps"]) == eps and float(r["delta"]) == delta]
                sub = sorted(sub, key=lambda r: int(r["n"]))
                ns = [int(r["n"]) for r in sub]
                n_eff = [int(r["n_eff"]) for r in sub]
                prob = [int(r["population_optimal"]) / ne if ne else np.nan for r, ne in zip(sub, n_eff)]
                axD.plot(ns, prob, marker="o", linestyle=ls, color=c,
                         label=f"eps={eps}, $\\delta$={delta}")
        axD.set_xscale("log")
        axD.set_ylim(-0.05, 1.05)
        axD.set_xlabel("n (log scale)")
        axD.set_ylabel("P(recovers population-optimal certified boundary)")
        axD.set_title("D: certified-boundary recovery probability vs. n")
        axD.legend(fontsize=6.5, ncol=2)
    else:
        axD.text(0.5, 0.5, "Part E data not yet available", ha="center", va="center")
        axD.set_title("D: (pending Part E)")

    fig.suptitle("Figure 5 — Finite-sample inference: raw vs. bias-corrected leakage", y=1.0, fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    save_all(fig, os.path.join(FIGDIR, "fig5_finite_sample"))
    plt.close(fig)
    print("Figure 5 saved" + (" (with Part E panel D)" if pe_rows is not None else " (panel D pending Part E)"))
