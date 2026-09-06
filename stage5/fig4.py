"""Figure 4: What is being controlled? y(t), z(t), Y(t)=c^Tm(t), u_y(t), u_z(t) for
representative task-only and pathwise-integrity-aware protocols, plus the zero-control
release period."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import control_results_lib as lib
import control as ctl

T_REP = 2

if __name__ == "__main__":
    recs = lib.load_all()
    kA = lib.key("A", False, T_REP)
    kC = lib.key("C", False, T_REP)
    if kA not in recs or kC not in recs:
        raise SystemExit(f"Missing control_sweep results for {kA} / {kC}; run control_sweep.py --stage baseline first.")

    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    for row, (label, key, color) in enumerate([("Task-only (A)", kA, fs.COLOR_EXTERIOR),
                                                 ("Pathwise-integrity (C)", kC, fs.COLOR_ACCENT)]):
        rec = recs[key]
        d = lib.load_traj(rec)
        t, y, z, m = d["t"], d["y"], d["z"], d["m"]
        Y = m @ ctl.C_VEC
        uy_knots = d["x"][:12]
        uz_knots = d["x"][12:24] if len(d["x"]) > 12 else np.zeros(12)
        knots_t = np.linspace(0, T_REP, 12)

        rel_t = d["rel_t"] + T_REP
        rel_y, rel_z = d["rel_y"], d["rel_z"]

        ax = axes[row, 0]
        ax.plot(t, y, color=fs.COLOR_INTERIOR, label="y(t)")
        ax.plot(t, z, color=fs.COLOR_BOUNDARY, label="z(t)")
        ax.plot(t, Y, color=color, label="Y(t)=c^Tm(t)")
        ax.plot(rel_t, rel_y, color=fs.COLOR_INTERIOR, ls=":")
        ax.plot(rel_t, rel_z, color=fs.COLOR_BOUNDARY, ls=":")
        ax.axvline(T_REP, color="gray", lw=0.8, ls="--")
        ax.set_title(f"{label}: state trajectory")
        ax.legend(fontsize=7.5)
        ax.set_xlabel("t  (dashed: release period)")

        ax = axes[row, 1]
        ax.step(knots_t, uy_knots, where="post", color=fs.COLOR_INTERIOR, label="u_y knots")
        ax.axvline(T_REP, color="gray", lw=0.8, ls="--")
        ax.set_title(f"{label}: u_y(t)")
        ax.set_xlabel("t")
        ax.legend(fontsize=7.5)

        ax = axes[row, 2]
        ax.step(knots_t, uz_knots, where="post", color=fs.COLOR_BOUNDARY, label="u_z knots")
        ax.axvline(T_REP, color="gray", lw=0.8, ls="--")
        ax.set_title(f"{label}: u_z(t)")
        ax.set_xlabel("t")
        ax.legend(fontsize=7.5)

    fig.suptitle(f"Representative protocols at T={T_REP} (coordinated control): task-only vs.\n"
                 "pathwise-integrity-constrained -- state trajectories and best-found piecewise-linear controls",
                 fontsize=11, y=1.03)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig4_what_is_controlled")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
