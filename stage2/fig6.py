import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_BOUNDARY, COLOR_EXTERIOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

rest_nodes = [4, 5, 6, 7, 8]
NODE_COLOR = {4: COLOR_BOUNDARY, 5: COLOR_BOUNDARY, 6: COLOR_EXTERIOR, 7: COLOR_EXTERIOR, 8: COLOR_EXTERIOR}
NODE_MARKER = {4: "o", 5: "s", 6: "o", 7: "s", 8: "^"}
NODE_LS = {4: "-", 5: "--", 6: "-", 7: "--", 8: ":"}

if __name__ == "__main__":
    path = os.path.join(DATADIR, "part_f_membership_raw.csv")
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append(r)

    eps_list = sorted(set(int(r["eps"]) for r in rows))
    deltas = sorted(set(float(r["delta"]) for r in rows))

    fig, axes = plt.subplots(len(eps_list), len(deltas), figsize=(4.2 * len(deltas), 3.8 * len(eps_list)),
                              sharey=True, sharex=True)
    for i, eps in enumerate(eps_list):
        for j, delta in enumerate(deltas):
            ax = axes[i, j] if len(eps_list) > 1 else axes[j]
            sub = [r for r in rows if int(r["eps"]) == eps and float(r["delta"]) == delta]
            sub = sorted(sub, key=lambda r: int(r["n"]))
            ns = [int(r["n"]) for r in sub]
            for node in rest_nodes:
                m_k = [int(r[f"m_{node}_raw_count"]) / int(r["n_eff"]) if int(r["n_eff"]) else float("nan")
                       for r in sub]
                ax.plot(ns, m_k, marker=NODE_MARKER[node], linestyle=NODE_LS[node], markersize=6,
                        color=NODE_COLOR[node], linewidth=1.8, label=f"node {node}")
            ax.set_xscale("log")
            ax.set_ylim(-0.05, 1.05)
            if i == 0:
                ax.set_title(f"$\\delta={delta}$")
            if j == 0:
                ax.set_ylabel(f"$\\varepsilon={eps}$\n$m_k(\\delta)$")
            if i == len(eps_list) - 1:
                ax.set_xlabel("n (log)")
    axes[0, -1].legend(fontsize=8, loc="upper right") if len(eps_list) > 1 else axes[-1].legend(fontsize=8)

    fig.suptitle("Figure 6 — Graded membership as statistical selection stability (fixed-interior problem)",
                 y=1.02, fontsize=12.5)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    save_all(fig, os.path.join(FIGDIR, "fig6_graded_membership"))
    plt.close(fig)
    print("Figure 6 saved.")
    print("Caption: m_k(delta) is the empirical frequency with which node k is included in the")
    print("delta-tolerant, 95%-certified minimal boundary across independent finite datasets --")
    print("a statement about SELECTION STABILITY under sampling, not an intrinsic property of node k.")
