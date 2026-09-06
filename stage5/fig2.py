"""Figure 2: Quasi-static blanket landscape -- Lambda_1,2,3(z) plus K_delta(z)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs

if __name__ == "__main__":
    d = np.load(os.path.join(os.path.dirname(__file__), "data", "part8_quasistatic.npz"))
    z = d["z_grid"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 6.6), sharex=True,
                                    gridspec_kw=dict(height_ratios=[2.2, 1]))
    ax1.plot(z, d["L1"], label=r"$\Lambda_1^\star(z)$", color=fs.COLOR_EXTERIOR, lw=2)
    ax1.plot(z, d["L2"], label=r"$\Lambda_2^\star(z)$", color=fs.COLOR_BOUNDARY, lw=2)
    ax1.plot(z, d["L3"], label=r"$\Lambda_3^\star(z)$", color=fs.COLOR_ACCENT, lw=2.5)
    ax1.axhline(0.01, color="gray", ls=":", lw=1, label=r"$\delta=0.01$")
    ax1.annotate("{4,5}\nminimizes $\\Lambda_2$", xy=(-1, 0.0), xytext=(-0.95, 0.06),
                 fontsize=8.5, ha="left")
    ax1.annotate("{4,5,6} exact\n(size 3)", xy=(0, 0.0), xytext=(-0.25, 0.06),
                 fontsize=8.5, ha="left")
    ax1.annotate("{5,6}\nminimizes $\\Lambda_2$", xy=(1, 0.0), xytext=(0.45, 0.06),
                 fontsize=8.5, ha="left")
    ax1.set_ylabel("leakage (nats)")
    ax1.legend(loc="upper center", ncol=4, fontsize=8.5, frameon=False)
    ax1.set_title("Quasi-static (instantaneous-equilibrium) boundary-capacity leakage")

    ax2.step(z, d["Kdelta"], where="mid", color=fs.COLOR_INTERIOR, lw=2)
    ax2.set_ylabel(r"$K_\delta^\star(z)$" + "\n" + r"($\delta=0.01$)")
    ax2.set_xlabel("z (endpoint A = -1  ...  endpoint B = +1)")
    ax2.set_yticks([1, 2, 3])
    ax2.set_ylim(0.5, 3.5)

    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig2_quasistatic_landscape")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
