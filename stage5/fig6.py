"""Figure 6: Boundary membership through the transition, time-by-node (4-8), for the
pathwise-integrity protocol at T=2. Shows the optimal B_t and near-optimal ties -- a
moving interface around a fixed interior, not identity loss."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import control_results_lib as lib
import control as ctl

T_REP = 2
NODES = [4, 5, 6, 7, 8]

if __name__ == "__main__":
    recs = lib.load_all()
    k = lib.key("C", False, T_REP)
    rec = recs[k]
    d = lib.load_traj(rec)
    t, Sigma = d["t"], d["Sigma"]
    L3, winners = ctl.lambda3_series(Sigma)

    membership = np.zeros((len(NODES), len(t)))
    optimal_only = np.zeros((len(NODES), len(t)))
    for i, w in enumerate(winners):
        all_nodes_in_ties = set()
        for B in w:
            all_nodes_in_ties.update(B)
        opt_nodes = set(w[0])
        for j, n in enumerate(NODES):
            membership[j, i] = 1.0 if n in all_nodes_in_ties else 0.0
            optimal_only[j, i] = 1.0 if n in opt_nodes else 0.0

    fig, ax = plt.subplots(1, 1, figsize=(9, 4.2))
    combo = membership + optimal_only  # 0=never, 1=tied-only, 2=in the reported optimum
    im = ax.imshow(combo, aspect="auto", cmap="YlOrRd", vmin=0, vmax=2,
                    extent=[t[0], t[-1], len(NODES) - 0.5, -0.5])
    ax.set_yticks(range(len(NODES)))
    ax.set_yticklabels([f"node {n}" for n in NODES])
    ax.set_xlabel("t")
    ax.set_title(f"Boundary membership through the pathwise-integrity transition (T={T_REP})\n"
                 "dark = in reported optimal B_t; light = in a tied near-optimal boundary; white = exterior/never")
    cbar = fig.colorbar(im, ax=ax, ticks=[0, 1, 2])
    cbar.ax.set_yticklabels(["never", "tied", "optimal B_t"])
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig6_boundary_membership")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
