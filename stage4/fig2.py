import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import core
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_ACCENT
from organization_core import s_scalar, v_vec, Q_perp
from steering_core import C_VEC

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")

if __name__ == "__main__":
    rng = np.random.default_rng(20260820)
    labels = []
    raw_vals = []
    y_terms = []
    dperp_terms = []

    cases = {
        "$m=0$": np.zeros(8),
        "$m=v$ (Y=1, on-manifold)": v_vec.copy(),
        "$m=2v$ (Y=2, on-manifold)": 2 * v_vec,
    }
    rng2 = np.random.default_rng(7)
    r_rand = rng2.standard_normal(8)
    r_rand = r_rand - (C_VEC @ r_rand) * v_vec / (C_VEC @ v_vec)  # project onto c^T r=0 (v already has c^Tv=1)
    r_rand = r_rand - (C_VEC @ r_rand) * v_vec
    cases["$m=v + r$ (Y=1, off-manifold)"] = v_vec + 0.6 * r_rand

    for label, m in cases.items():
        y = C_VEC @ m
        r = m - v_vec * y
        raw = 0.5 * m @ core.Omega0 @ m
        yterm = y**2 / (2 * s_scalar)
        dperp = 0.5 * r @ core.Omega0 @ r
        labels.append(label)
        raw_vals.append(raw)
        y_terms.append(yterm)
        dperp_terms.append(dperp)
        assert abs(raw - (yterm + dperp)) < 1e-8

    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(labels))
    ax.bar(x, y_terms, color=COLOR_BOUNDARY, label=r"$Y^2/2s$ (desired-movement cost)")
    ax.bar(x, dperp_terms, bottom=y_terms, color=COLOR_ACCENT, label=r"$D_\perp$ (excess distortion)")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=9)
    ax.set_ylabel(r"$\frac{1}{2}m^\top\Omega_0 m$ [nats-like energy units]")
    ax.set_title("Stage-4 Figure 2 — Raw displacement vs. excess distortion")
    ax.legend(fontsize=9)
    for i, (rv, yt) in enumerate(zip(raw_vals, y_terms)):
        ax.text(i, rv + 0.05 * max(raw_vals), f"total={rv:.3f}", ha="center", fontsize=8)

    save_all(fig, os.path.join(FIGDIR, "fig2_raw_vs_excess"))
    plt.close(fig)
    print("Figure 2 saved. Verified 1/2 m'Om m = Y^2/2s + D_perp exactly for all cases.")
    print("Key point: the two on-manifold cases (m=v, m=2v) have D_perp=0 despite large raw ",
          "1/2 m'Om m -- raw KL-type distance wrongly counts desired movement toward the target",
          "as if it were disruption.")
