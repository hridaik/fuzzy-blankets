"""Figure 3: Rate-induced loss of screening."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import rate_induced as ri

if __name__ == "__main__":
    d = np.load(os.path.join(os.path.dirname(__file__), "data", "part9_rate_induced.npz"))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
    cmap = plt.cm.viridis
    for i, T in enumerate(ri.RAMP_DURATIONS):
        prog = d[f"progress_{T}"]
        L3 = d[f"L3_{T}"]
        ax1.plot(prog, L3, color=cmap(i / (len(ri.RAMP_DURATIONS) - 1)), lw=1.8,
                 label=f"T={T}")
    ax1.axhline(0.0, color="black", lw=1.2, ls="--", label="instantaneous-equilibrium (=0)")
    ax1.set_xlabel("normalized transition progress  t / T_ramp")
    ax1.set_ylabel(r"actual $\Lambda_3(t)$ (nats)")
    ax1.set_title("Actual transient leakage vs. progress, by ramp duration")
    ax1.legend(fontsize=8, ncol=2)

    ax2.semilogx(d["fine_T_ramp"], d["fine_max_L3"], "o-", color=fs.COLOR_ACCENT, ms=4)
    ax2.scatter(d["T_ramp"], d["max_L3"], color=fs.COLOR_INTERIOR, zorder=5, s=45,
                label="spec-requested set")
    peak_i = int(np.argmax(d["fine_max_L3"]))
    ax2.annotate(f"peak at T={d['fine_T_ramp'][peak_i]:.2f}",
                 xy=(d["fine_T_ramp"][peak_i], d["fine_max_L3"][peak_i]),
                 xytext=(0.3, d["fine_max_L3"][peak_i] * 0.7), fontsize=8.5,
                 arrowprops=dict(arrowstyle="->", lw=1))
    ax2.set_xlabel("ramp duration T_ramp (log scale)")
    ax2.set_ylabel(r"$\max_t \Lambda_3(t)$ (nats)")
    ax2.set_title("Peak transient leakage vs. ramp duration (non-monotone)")
    ax2.legend(fontsize=8.5)

    fig.suptitle("Every frozen configuration along the path has a valid compact (|B| <= 3) exact\n"
                 "blanket, yet moving at finite rate transiently and reversibly elevates leakage above 0.",
                 fontsize=10, y=1.06)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig3_rate_induced_loss")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
