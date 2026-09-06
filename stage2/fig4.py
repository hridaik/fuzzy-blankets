import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import core
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")


def marginalize(Omega, hidden_nodes, observed_nodes):
    H = [core.idx[n] for n in hidden_nodes]
    O = [core.idx[n] for n in observed_nodes]
    Omega_OO = Omega[np.ix_(O, O)]
    Omega_OH = Omega[np.ix_(O, H)]
    Omega_HO = Omega[np.ix_(H, O)]
    Omega_HH = Omega[np.ix_(H, H)]
    return Omega_OO - Omega_OH @ np.linalg.inv(Omega_HH) @ Omega_HO, O


if __name__ == "__main__":
    cases = []
    # fully observed exact boundary
    I_idx = core.I_IDX
    B_idx = [core.idx[4], core.idx[5]]
    E_idx = [core.idx[6], core.idx[7], core.idx[8]]
    L_full = core.L_cmi_precision(core.Omega0, I_idx, B_idx, E_idx)
    cases.append(("fully observed\n$B=\\{4,5\\}$", L_full, None))

    observed5 = [1, 2, 3, 4, 6, 7, 8]
    Omega_obs5, O = marginalize(core.Omega0, [5], observed5)
    pos = {n: i for i, n in enumerate(observed5)}
    I5 = [pos[n] for n in [1, 2, 3]]; B5 = [pos[4]]; E5 = [pos[n] for n in [6, 7, 8]]
    L_hide5 = core.L_cmi_precision(Omega_obs5, I5, B5, E5)
    block5 = Omega_obs5[np.ix_(I5, E5)]
    cases.append(("hide node 5\n$B=\\{4\\}$", L_hide5, block5))

    observed4 = [1, 2, 3, 5, 6, 7, 8]
    Omega_obs4, O2 = marginalize(core.Omega0, [4], observed4)
    pos2 = {n: i for i, n in enumerate(observed4)}
    I4 = [pos2[n] for n in [1, 2, 3]]; B4 = [pos2[5]]; E4 = [pos2[n] for n in [6, 7, 8]]
    L_hide4 = core.L_cmi_precision(Omega_obs4, I4, B4, E4)
    block4 = Omega_obs4[np.ix_(I4, E4)]
    cases.append(("hide node 4\n$B=\\{5\\}$", L_hide4, block4))

    expected = [0.0, 0.5*np.log(1369/1360), 0.5*np.log(841/805)]
    for (label, Lval, _), exp in zip(cases, expected):
        assert abs(Lval - exp) < 1e-9, f"mismatch for {label}: {Lval} vs {exp}"

    fig = plt.figure(figsize=(11, 4.5))
    gs = fig.add_gridspec(1, 4, width_ratios=[2.2, 1, 1, 1])
    ax0 = fig.add_subplot(gs[0, 0])
    labels = [c[0] for c in cases]
    vals = [c[1] for c in cases]
    colors = [COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR]
    ax0.bar(labels, vals, color=colors, edgecolor="black")
    ax0.set_ylabel(r"$I(X_I;X_E\mid X_B)$ [nats]")
    ax0.set_title("A: representation-dependent leakage")
    for i, v in enumerate(vals):
        ax0.text(i, v + 0.0005, f"{v:.5f}", ha="center", fontsize=8)

    for k, (label, Lval, block) in enumerate(cases[1:], start=1):
        axk = fig.add_subplot(gs[0, k])
        im = axk.imshow(block, cmap="cividis")
        axk.set_title(label.replace("\n", ", "), fontsize=9)
        axk.set_xticks(range(3)); axk.set_xticklabels([6, 7, 8])
        axk.set_yticks(range(3)); axk.set_yticklabels([1, 2, 3])
        for (i, j), v in np.ndenumerate(block):
            axk.text(j, i, f"{v:.4f}", ha="center", va="center", fontsize=7,
                     color="white" if v < block.mean() else "black")
        fig.colorbar(im, ax=axk, fraction=0.046, pad=0.04)
    axes_labels = ["B", "C"]
    for k, lab in zip([1, 2], axes_labels):
        fig.axes[k].set_ylabel("core node")

    fig.suptitle("Figure 4 — Observer/representation dependence of the inferred blanket", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "fig4_hidden_variable"))
    plt.close(fig)

    with open(os.path.join(DATADIR, "fig4_data.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "L"])
        for label, Lval, _ in cases:
            w.writerow([label.replace("\n", " "), Lval])
    print("Figure 4 saved. All three CMI values verified exactly against Part 7 analytic expectations.")
