"""Figure 5: Endpoint validity can hide pathwise failure. Lambda_3(t) for task-only,
endpoint-integrity, pathwise-integrity formulations at T=2 (coordinated control)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import control_results_lib as lib

T_REP = 2
DELTA = 0.01

if __name__ == "__main__":
    recs = lib.load_all()
    fig, ax = plt.subplots(1, 1, figsize=(8, 5.2))
    colors = dict(A=fs.COLOR_EXTERIOR, B=fs.COLOR_BOUNDARY, C=fs.COLOR_ACCENT)
    labels = dict(A="Task-only", B="Endpoint-integrity", C="Pathwise-integrity")
    for f in ["A", "B", "C"]:
        k = lib.key(f, False, T_REP)
        if k not in recs:
            continue
        rec = recs[k]
        d = lib.load_traj(rec)
        t = d["t"]
        L3 = d["L3_dense"]
        rel_t = d["rel_t"] + T_REP
        rel_L3 = d["rel_L3"]
        ax.plot(t, L3, color=colors[f], lw=2, label=labels[f])
        ax.plot(rel_t, rel_L3, color=colors[f], lw=2, ls=":")
    ax.axhline(DELTA, color="gray", ls="--", lw=1.2, label=r"$\delta=0.01$")
    ax.axvline(T_REP, color="black", lw=0.8, ls="-", alpha=0.5)
    ax.annotate("control ends /\nrelease begins", xy=(T_REP, ax.get_ylim()[1] * 0.8),
                fontsize=8, ha="center")
    ax.set_xlabel("t  (dotted: zero-control release period)")
    ax.set_ylabel(r"$\Lambda_3(t)$ (actual transient leakage, nats)")
    ax.set_title(f"Pathwise leakage through control + release, T={T_REP} (coordinated control)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig5_endpoint_vs_pathwise")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
