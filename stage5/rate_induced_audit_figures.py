"""Generate Audit Figures A-F for the rate-induced-loss audit, from saved data only."""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import rate_induced_audit_core as aud

AUDIT_DIR = aud.AUDIT_DIR
DELTA = 0.01


def load_peak_table():
    rows = []
    with open(os.path.join(AUDIT_DIR, "full_event_peak_table.csv")) as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Fig A: existing window vs full relaxation, absolute time
# ---------------------------------------------------------------------------
def fig_A():
    d = np.load(os.path.join(AUDIT_DIR, "full_event_sweep_smoothstep.npz"), allow_pickle=True)
    reps = ["0p02", "0p1", "0p2", "0p5", "1", "2"]
    labels = ["T=0.02", "T=0.1", "T=0.2", "T=0.5", "T=1", "T=2"]
    Tvals = [0.02, 0.1, 0.2, 0.5, 1, 2]
    fig, ax = plt.subplots(1, 1, figsize=(9, 5.5))
    cmap = plt.cm.viridis
    for i, (tag, lab, Tv) in enumerate(zip(reps, labels, Tvals)):
        if f"t_{tag}" not in d.files:
            continue
        t = d[f"t_{tag}"]; L3 = d[f"L3_{tag}"]
        mask = t <= 3.0
        ax.plot(t[mask], L3[mask], color=cmap(i / (len(reps) - 1)), lw=1.8, label=lab)
        ax.axvline(Tv, color=cmap(i / (len(reps) - 1)), ls=":", lw=1, alpha=0.6)
    ax.axhline(DELTA, color="gray", ls="--", lw=1, alpha=0.5, label="delta=0.01 (for scale)")
    ax.set_xlabel("absolute time t")
    ax.set_ylabel(r"$\Lambda_3(t)$ (nats)")
    ax.set_title("Audit Fig A: existing [0,T_ramp] window (dotted lines) vs full relaxation\n"
                 "(the old Fig-3 right panel only ever looked at t <= T_ramp)")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fs.save_all(fig, os.path.join(AUDIT_DIR, "audit_fig_A"))
    plt.close(fig)
    print("Saved audit_fig_A")


# ---------------------------------------------------------------------------
# Fig B: three peak definitions vs T_ramp (THE key figure)
# ---------------------------------------------------------------------------
def fig_B():
    rows = [r for r in load_peak_table() if r["K"] == "3"]
    rows.sort(key=lambda r: float(r["T_ramp"]))
    Ts = np.array([float(r["T_ramp"]) for r in rows])
    L_ramp = np.array([float(r["L_max_ramp"]) for r in rows])
    L_post = np.array([float(r["L_max_post"]) for r in rows])
    L_full = np.array([float(r["L_max_full"]) for r in rows])

    inst = np.load(os.path.join(AUDIT_DIR, "instantaneous_jump.npz"), allow_pickle=True)
    inst_max = inst["L3"].max()

    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    ax.semilogx(Ts, L_ramp, "-o", ms=3, color=fs.COLOR_EXTERIOR, label=r"during-ramp max $L_{\max}^{\rm ramp}$")
    ax.semilogx(Ts, L_post, "-s", ms=3, color=fs.COLOR_BOUNDARY, label=r"post-ramp max $L_{\max}^{\rm post}$")
    ax.semilogx(Ts, L_full, "-^", ms=4, color=fs.COLOR_ACCENT, lw=2.2, label=r"FULL-EVENT max $L_{\max}^{\rm full}$")
    ax.axhline(inst_max, color="black", ls=":", lw=1.3,
               label=f"true T_ramp->0 limit (instantaneous jump) = {inst_max:.3e}")
    ax.axvline(0.2, color="gray", ls="--", lw=1, alpha=0.6, label="old claimed peak T_ramp~0.2")
    ax.set_xlabel(r"$T_{\rm ramp}$ (log scale)")
    ax.set_ylabel(r"$\max \Lambda_3$ (nats)")
    ax.set_title("Audit Fig B (KEY FIGURE): three definitions of peak leakage vs ramp duration")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fs.save_all(fig, os.path.join(AUDIT_DIR, "audit_fig_B"))
    plt.close(fig)
    print("Saved audit_fig_B")


# ---------------------------------------------------------------------------
# Fig C: local peak anatomy for the two-bump case (T_ramp=0.2)
# ---------------------------------------------------------------------------
def fig_C():
    d = np.load(os.path.join(AUDIT_DIR, "full_event_sweep_smoothstep.npz"), allow_pickle=True)
    tag = "0p2"
    t = d[f"t_{tag}"]; z = d[f"z_{tag}"]
    L1, L2, L3, L4 = d[f"L1_{tag}"], d[f"L2_{tag}"], d[f"L3_{tag}"], d[f"L4_{tag}"]
    Kd = d[f"Kdelta_{tag}"]
    mask = t <= 2.0

    fig, axes = plt.subplots(3, 1, figsize=(8.5, 9), sharex=True,
                              gridspec_kw=dict(height_ratios=[2, 1, 1]))
    ax = axes[0]
    ax.plot(t[mask], L1[mask], color=fs.COLOR_EXTERIOR, lw=1.3, label=r"$\Lambda_1$")
    ax.plot(t[mask], L2[mask], color=fs.COLOR_BOUNDARY, lw=1.5, label=r"$\Lambda_2$")
    ax.plot(t[mask], L3[mask], color=fs.COLOR_ACCENT, lw=2.2, label=r"$\Lambda_3$")
    ax.plot(t[mask], L4[mask], color=fs.COLOR_INTERIOR, lw=1.2, ls="--", label=r"$\Lambda_4$")
    ax.axvline(0.2, color="black", lw=0.8, ls=":")
    ax.set_ylabel("leakage (nats)")
    ax.legend(fontsize=8)
    ax.set_title(r"Audit Fig C: local peak anatomy, $T_{\rm ramp}=0.2$ (two-bump case)")

    ax2 = axes[1]
    ax2.plot(t[mask], z[mask], color="black", lw=1.5)
    ax2.axvline(0.2, color="black", lw=0.8, ls=":")
    ax2.set_ylabel("z(t)")

    ax3 = axes[2]
    ax3.step(t[mask], Kd[mask], where="mid", color=fs.COLOR_INTERIOR, lw=1.8)
    ax3.axvline(0.2, color="black", lw=0.8, ls=":")
    ax3.set_ylabel(r"$K_\delta(t)$")
    ax3.set_xlabel("t")
    ax3.set_yticks([1, 2, 3, 4])

    fig.tight_layout()
    fs.save_all(fig, os.path.join(AUDIT_DIR, "audit_fig_C"))
    plt.close(fig)
    print("Saved audit_fig_C")


# ---------------------------------------------------------------------------
# Fig D: K-sensitivity
# ---------------------------------------------------------------------------
def fig_D():
    rows_all = load_peak_table()
    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    cmap = {1: fs.COLOR_EXTERIOR, 2: fs.COLOR_BOUNDARY, 3: fs.COLOR_ACCENT, 4: fs.COLOR_INTERIOR}
    for K in (1, 2, 3, 4):
        rows = [r for r in rows_all if r["K"] == str(K)]
        rows.sort(key=lambda r: float(r["T_ramp"]))
        Ts = np.array([float(r["T_ramp"]) for r in rows])
        Lf = np.array([float(r["L_max_full"]) for r in rows])
        ax.loglog(Ts, np.clip(Lf, 1e-16, None), "-o", ms=3, color=cmap[K], label=f"K={K}")
    ax.set_xlabel(r"$T_{\rm ramp}$ (log)")
    ax.set_ylabel(r"$\max_t \Lambda_K$ (log)")
    ax.set_title("Audit Fig D: K-sensitivity of the full-event peak")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fs.save_all(fig, os.path.join(AUDIT_DIR, "audit_fig_D"))
    plt.close(fig)
    print("Saved audit_fig_D")


# ---------------------------------------------------------------------------
# Fig E: ramp-shape robustness
# ---------------------------------------------------------------------------
def fig_E():
    rows = []
    with open(os.path.join(AUDIT_DIR, "shape_robustness_table.csv")) as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    colors = dict(linear=fs.COLOR_EXTERIOR, smoothstep=fs.COLOR_ACCENT, smootherstep=fs.COLOR_INTERIOR)
    for shape in ["linear", "smoothstep", "smootherstep"]:
        sub = [r for r in rows if r["shape"] == shape]
        sub.sort(key=lambda r: float(r["T_ramp"]))
        Ts = np.array([float(r["T_ramp"]) for r in sub])
        Lf = np.array([float(r["L_max_full"]) for r in sub])
        ax.semilogx(Ts, Lf, "-o", ms=4, color=colors[shape], label=shape)
    ax.set_xlabel(r"$T_{\rm ramp}$ (log)")
    ax.set_ylabel(r"full-event $\max_t \Lambda_3$")
    ax.set_title("Audit Fig E: ramp-shape robustness (K=3)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fs.save_all(fig, os.path.join(AUDIT_DIR, "audit_fig_E"))
    plt.close(fig)
    print("Saved audit_fig_E")


# ---------------------------------------------------------------------------
# Fig F: instantaneous-jump limit
# ---------------------------------------------------------------------------
def fig_F():
    d = np.load(os.path.join(AUDIT_DIR, "instantaneous_jump.npz"), allow_pickle=True)
    t = d["t"]
    mask = t <= 2.0
    fig, ax = plt.subplots(1, 1, figsize=(8.5, 5.5))
    ax.plot(t[mask], d["L2"][mask], color=fs.COLOR_BOUNDARY, lw=1.6, label=r"$\Lambda_2$")
    ax.plot(t[mask], d["L3"][mask], color=fs.COLOR_ACCENT, lw=2.2, label=r"$\Lambda_3$")
    ax.plot(t[mask], d["L4"][mask], color=fs.COLOR_INTERIOR, lw=1.2, ls="--", label=r"$\Lambda_4$")
    ax.set_xlabel("t (since instantaneous jump)")
    ax.set_ylabel("leakage (nats)")
    ax.set_title(r"Audit Fig F: true $T_{\rm ramp}\to0$ limit -- instantaneous structural jump")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fs.save_all(fig, os.path.join(AUDIT_DIR, "audit_fig_F"))
    plt.close(fig)
    print("Saved audit_fig_F")


if __name__ == "__main__":
    fig_A(); fig_B(); fig_C(); fig_D(); fig_E(); fig_F()
    print("All audit figures generated.")
