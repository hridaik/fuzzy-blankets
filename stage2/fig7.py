import sys, os, itertools, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import core
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

free_nodes = [2, 3, 4, 5, 6, 7]

if __name__ == "__main__":
    results8 = []
    for assignment in itertools.product([0, 1, 2], repeat=6):
        I_nodes = [1] + [free_nodes[i] for i in range(6) if assignment[i] == 0]
        B_nodes = [free_nodes[i] for i in range(6) if assignment[i] == 1]
        E_nodes = [8] + [free_nodes[i] for i in range(6) if assignment[i] == 2]
        I_idx = [core.idx[n] for n in I_nodes]
        B_idx = [core.idx[n] for n in B_nodes]
        E_idx = [core.idx[n] for n in E_nodes]
        L = core.L_cmi_cov_joint(np.linalg.inv(core.Omega_amb), I_idx, B_idx, E_idx)
        results8.append((tuple(sorted(B_nodes)), len(B_nodes), L))

    zero8 = [r for r in results8 if abs(r[2]) < core.TOL]
    min_size = min(r[1] for r in zero8)
    mins8 = sorted(set(r[0] for r in zero8 if r[1] == min_size))
    expected9 = [(2, 3), (2, 4), (2, 6), (3, 5), (3, 7), (4, 5), (4, 7), (5, 6), (6, 7)]
    assert sorted(mins8) == sorted(expected9), f"mismatch: {mins8} vs {expected9}"

    all_nodes = list(range(2, 8))
    M = np.zeros((len(mins8), len(all_nodes)))
    for i, B in enumerate(mins8):
        for node in B:
            M[i, all_nodes.index(node)] = 1

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), width_ratios=[1.4, 1])
    ax0 = axes[0]
    im = ax0.imshow(M, cmap="Greys", vmin=0, vmax=1, aspect="auto")
    ax0.set_xticks(range(len(all_nodes))); ax0.set_xticklabels(all_nodes)
    ax0.set_yticks(range(len(mins8))); ax0.set_yticklabels(["{" + ",".join(map(str, b)) + "}" for b in mins8])
    ax0.set_xlabel("free node")
    ax0.set_title("A: the 9 exact minimum separators\n(anchored $1\\in I$, $8\\in E$, $|B|=2$)")
    for i in range(len(mins8)):
        for j in range(len(all_nodes)):
            if M[i, j]:
                ax0.text(j, i, "1", ha="center", va="center", color="white", fontsize=9)

    ax1 = axes[1]
    node_counts = M.sum(axis=0)
    colors = [COLOR_INTERIOR if n in (2, 3) else COLOR_BOUNDARY if n in (4, 5) else COLOR_EXTERIOR
              for n in all_nodes]
    ax1.bar([str(n) for n in all_nodes], node_counts, color=colors, edgecolor="black")
    ax1.set_ylabel("# of the 9 minimum separators containing node")
    ax1.set_xlabel("free node")
    ax1.set_title("B: per-node occurrence count\n(NOT a measure of \"correctness\")")
    ax1.set_ylim(0, 9)

    fig.suptitle("Figure 7 — Structural ambiguity is not sampling uncertainty (infinite-data result)",
                 y=1.04, fontsize=12.5)
    save_all(fig, os.path.join(FIGDIR, "fig7_ambiguity"))
    plt.close(fig)

    with open(os.path.join(DATADIR, "fig7_data.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["boundary_set"] + [str(n) for n in all_nodes])
        for B, row in zip(mins8, M):
            w.writerow([str(B)] + list(row.astype(int)))

    print(f"Figure 7 saved. 9 minimum separators verified exactly: {mins8}")
    print("Caption: all 9 sets achieve EXACT L=0 with infinite data; this is structural")
    print("non-identifiability of the minimal separator, not a finite-sample estimation problem.")
    print("The per-node occurrence count in panel B must NOT be read as ranking node 'importance'.")
