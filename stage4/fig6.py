import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR, COLOR_ACCENT
from organization_core import v_vec

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")
NODE_COLOR = {1: COLOR_INTERIOR, 2: COLOR_INTERIOR, 3: COLOR_INTERIOR,
              4: COLOR_BOUNDARY, 5: COLOR_BOUNDARY, 6: COLOR_EXTERIOR, 7: COLOR_EXTERIOR, 8: COLOR_EXTERIOR}

if __name__ == "__main__":
    rows = []
    with open(os.path.join(DATADIR, "part9_single_actuator_sweep.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: (float(v) if k != "k" else int(float(v))) for k, v in r.items()})

    k, q, T = 6, 1.0, 1.0
    sub = [r for r in rows if r["k"] == k and r["q"] == q and r["T"] == T]
    sub = sorted(sub, key=lambda r: r["lam"])
    picks = [sub[0], sub[len(sub)//2], sub[-1]]
    lam_labels = [f"$\\lambda$={r['lam']:.3g}" for r in picks]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    ax0 = axes[0]
    nodes = list(range(1, 9))
    x = np.arange(8)
    width = 0.2
    ax0.bar(x - 1.5*width, v_vec, width, color="gray", alpha=0.6, label=r"$m_{\rm nat}(1)=v$")
    for i, (r, lab, c) in enumerate(zip(picks, lam_labels, [COLOR_ACCENT, "#888800", COLOR_INTERIOR])):
        m_T = np.array([r[f"m_T_{n}"] for n in nodes])
        ax0.bar(x + (i - 0.5)*width, m_T, width, color=c, alpha=0.85, label=f"m(T), {lab}")
    ax0.set_xticks(x); ax0.set_xticklabels(nodes)
    ax0.set_xlabel("node"); ax0.set_ylabel("terminal mean state")
    ax0.set_title(f"A: m(T) vs. $m_{{\\rm nat}}(1)$, node {k}, q={q:g}, T={T:g}")
    ax0.legend(fontsize=7.5)

    ax1 = axes[1]
    for r, lab, c in zip(picks, lam_labels, [COLOR_ACCENT, "#888800", COLOR_INTERIOR]):
        m_T = np.array([r[f"m_T_{n}"] for n in nodes])
        resid = m_T - v_vec
        ax1.bar(x, resid, width=0.6, color=c, alpha=0.5, label=f"r(T), {lab}")
    ax1.axhline(0, color="black", linewidth=0.8)
    ax1.set_xticks(x); ax1.set_xticklabels(nodes)
    ax1.set_xlabel("node"); ax1.set_ylabel("residual $r(T) = m(T)-v$")
    ax1.set_title("B: terminal residual (organization distortion)")
    ax1.legend(fontsize=8)

    fig.suptitle("Stage-4 Figure 6 — Terminal configuration", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "fig6_terminal_configuration"))
    plt.close(fig)
    print("Figure 6 saved.")
