"""Stage 6.8 figures (task brief section 22). EVALUATION-SIDE: reads only
frozen JSON in data/, imports oracle_68 for the ground-truth overlays."""
from __future__ import annotations

import json
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from common_68 import load_json, DATA_DIR, FIG_DIR, lattice_positions

plt.rcParams.update({"figure.dpi": 130, "font.size": 8, "axes.titlesize": 9,
                     "axes.labelsize": 8, "legend.fontsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False})

C_INT, C_PRED, C_CAUS, C_ORACLE = "#3b6ea5", "#e08a2e", "#b3453b", "#4a4a4a"


def save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("wrote", FIG_DIR / f"{name}.png")


# ---------------------------------------------------------------- Fig 6.8-1 --
def fig1():
    """Uncontrolled phase map across temperature/precision, L1 vs L2, plus the
    finite-size scan that decided the operating point."""
    def cells(fn, keys, lvl):
        d = load_json(DATA_DIR / fn)
        out = {}
        for k in keys:
            for r in d.get(k, []):
                out[(r["beta"], r.get("s", 1.0))] = r
        return out

    l1 = {}
    for fn in ("phase_scan.json", "phase_scan_cross.json", "phase_scan_refine.json"):
        l1.update(cells(fn, ("primary", "secondary", "cross", "refine"), "L1"))
    l2 = {}
    for fn in ("phase_scan_fov.json", "phase_scan_fov_refine.json"):
        l2.update(cells(fn, ("primary", "cross", "refine"), "L2"))

    betas = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
    ss = [0.5, 0.75, 1.0, 1.5, 2.0]
    panels = (("frac_time_largest_ge_90__mean", "fraction of time largest comp. $\\geq 0.9N$", "magma_r", (0, 1)),
              ("mean_n_components__mean", "mean number of coherent components", "viridis", (1, 5)),
              ("mean_component_lifetime__mean", "mean component lineage lifetime (steps)", "cividis", (0, 70)))
    fig, axes = plt.subplots(2, 3, figsize=(10.2, 5.9))
    fig.subplots_adjust(hspace=0.42, wspace=0.42, top=0.80)
    for row, (name, grid) in enumerate((("L1\nfixed Moore graph", l1),
                                        ("L2\nheading-dependent FOV", l2))):
        for col, (key, label, cmap, vlim) in enumerate(panels):
            M = np.full((len(ss), len(betas)), np.nan)
            for a_, s_ in enumerate(ss):
                for b_, be in enumerate(betas):
                    if (be, s_) in grid:
                        M[a_, b_] = grid[(be, s_)][key]
            ax = axes[row, col]
            im = ax.imshow(M, origin="lower", aspect="auto", cmap=cmap,
                           vmin=vlim[0], vmax=vlim[1])
            ax.set_xticks(range(len(betas))); ax.set_xticklabels(betas, fontsize=7)
            ax.set_yticks(range(len(ss))); ax.set_yticklabels(ss, fontsize=7)
            if row == 1:
                ax.set_xlabel(r"$\beta$")
            if col == 0:
                ax.set_ylabel(f"{name}\n\nprecision scale $s$", fontsize=7.5)
            if row == 0:
                ax.set_title(label, fontsize=8)
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.03).ax.tick_params(labelsize=6)
    fig.suptitle("Fig. 6.8-1  Uncontrolled phase map (nn=100, 20 seeds, identical metrics at both rungs).\n"
                 "No cell of either predeclared grid satisfies all six frozen mesoscopic criteria at L1 or L2 — but the FOV rule\n"
                 "shifts the whole diagram towards coexisting domains: fewer globally-locked states, 1.2→4 components.",
                 y=0.99, fontsize=8.5)
    save(fig, "fig_6_8_1_phase_map")

    # companion: the finite-size scan that set the operating point
    d = load_json(DATA_DIR / "phase_scan_size.json")
    fig, axes = plt.subplots(1, 3, figsize=(9.5, 2.9))
    nns = sorted({c["nn"] for c in d["cells"]})
    for ax, key, lab in zip(axes,
                            ("mesoscopic_episode_fraction", "frac_time_largest_ge_90__mean",
                             "mean_component_lifetime__mean"),
                            ("mesoscopic-episode fraction", "frac. time largest ≥ 0.9N",
                             "mean component lifetime")):
        for beta in sorted({c["beta"] for c in d["cells"]}):
            ys = [next(c[key] for c in d["cells"] if c["nn"] == n and c["beta"] == beta) for n in nns]
            ax.plot(nns, ys, "o-", ms=3, lw=1.2, label=f"β={beta}")
        ax.set_xscale("log"); ax.set_xticks(nns); ax.set_xticklabels(nns)
        ax.set_xlabel("lattice size nn"); ax.set_ylabel(lab)
    axes[0].axvline(400, color="k", ls=":", lw=1)
    axes[0].annotate("operating point", (400, 0.15), textcoords="offset points",
                     xytext=(-60, 10), fontsize=7)
    axes[2].legend(frameon=False, ncol=2)
    fig.suptitle("Fig. 6.8-1b  Finite size was the confound: coexisting domains need a lattice "
                 "large enough to hold them (L2, identical criteria and seeds).", y=1.06, fontsize=8.5)
    save(fig, "fig_6_8_1b_size_scan")


# ---------------------------------------------------------------- Fig 6.8-2 --
def fig2():
    """One time series showing the TRUE FOV causal interface visibly changing
    as birds reorient."""
    d = load_json(DATA_DIR / "oracle_interface.json")
    runs = {(r["label"], r["seed"]): r for r in d["runs"]}
    seeds = sorted({r["seed"] for r in d["runs"]})
    seed = seeds[2] if len(seeds) > 2 else seeds[0]
    l2 = runs[("L2_fov", seed)]
    l0 = runs[("L0_fixed_graph", seed)]

    ts = sorted(int(t) for t in l2["size_series"])
    fig = plt.figure(figsize=(10.5, 4.6))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.15, 1], hspace=0.45, wspace=0.35)

    ax = fig.add_subplot(gs[0, :2])
    ax.plot(ts, [l0["size_series"][str(t)] for t in ts], color=C_ORACLE, lw=1.6,
            label=f"L0 fixed graph  (|B| ≡ {l0['mean_B_size']:.0f}, 1 distinct set)")
    ax.plot(ts, [l2["size_series"][str(t)] for t in ts], color=C_CAUS, lw=1.6,
            label=f"L2 FOV  ({l2['n_distinct_interfaces']} distinct sets in {l2['n_timepoints']} steps)")
    ax.set_xlabel("t"); ax.set_ylabel(r"$|B_t^D|$")
    ax.set_title(r"true causal interface size, fixed reference interior")
    ax.set_ylim(min(l2["size_series"].values()) - 2, l0["mean_B_size"] + 4)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, -0.02), fontsize=6.8)

    ax = fig.add_subplot(gs[0, 2:])
    sd = [l2["symdiff_series"].get(str(t), 0) for t in ts]
    ax.bar(ts, sd, color=C_CAUS, width=0.9)
    ax.set_xlabel("t"); ax.set_ylabel(r"$|B_{t}^D \, \triangle \, B_{t-1}^D|$")
    ax.set_title("per-step interface churn  (L0 ≡ 0 everywhere)")

    # snapshots of the interface itself
    P = lattice_positions(load_json(DATA_DIR / "oracle_interface.json")["operating_point"]["nn"])
    I = set(l2["interior"])
    picks = [ts[0], ts[len(ts) // 3], ts[2 * len(ts) // 3], ts[-1]]
    for k, t in enumerate(picks):
        ax = fig.add_subplot(gs[1, k])
        B = set(l2["B_series"][str(t)])
        B0 = set(l2["B_series"][str(picks[0])])
        rest = [i for i in range(len(P)) if i not in I and i not in B]
        ax.scatter(P[rest, 0], P[rest, 1], s=1.5, c="#dddddd")
        ax.scatter(P[sorted(I), 0], P[sorted(I), 1], s=9, c=C_INT)
        kept, new = sorted(B & B0), sorted(B - B0)
        gone = sorted(B0 - B)
        if gone:
            ax.scatter(P[gone, 0], P[gone, 1], s=30, facecolors="none", edgecolors="#bbbbbb",
                       marker="s", lw=1.0)
        ax.scatter(P[kept, 0], P[kept, 1], s=16, c=C_CAUS, marker="s")
        if new:
            ax.scatter(P[new, 0], P[new, 1], s=26, c="#2f7d32", marker="s")
        c = P[sorted(I)].mean(0)
        ax.set_xlim(c[0] - 6, c[0] + 6); ax.set_ylim(c[1] - 6, c[1] + 6)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(f"t={t},  |B|={len(B)}" + ("" if k == 0 else
                     f"   (+{len(new)} / -{len(gone)} vs t={picks[0]})"), fontsize=7.5)
    fig.legend(handles=[Line2D([], [], marker="o", ls="", color=C_INT, label="reference interior I"),
                        Line2D([], [], marker="s", ls="", color=C_CAUS, label=r"$B_t^D$, also in $B^D$ at the first snapshot"),
                        Line2D([], [], marker="s", ls="", color="#2f7d32", label=r"$B_t^D$, newly recruited"),
                        Line2D([], [], marker="s", ls="", mfc="none", mec="#bbbbbb", label="left the interface")],
               loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle(f"Fig. 6.8-2  The true FOV causal interface changes as birds reorient "
                 f"(seed {seed}). The interior is held fixed, so every change is the "
                 f"interface's own.", y=1.0, fontsize=8.5)
    save(fig, "fig_6_8_2_interface_changes")


# ---------------------------------------------------------------- Fig 6.8-3 --
def fig3(tag="snapshot"):
    """Detected candidate interior + inferred predictive + sampled causal +
    oracle causal boundary."""
    rev = load_json(DATA_DIR / f"oracle_reveal__{tag}.json")
    P = lattice_positions(rev["operating_point"]["nn"])
    runs = [r for r in rev["runs"] if r["method"] == "affinity_louvain"][:4]
    if not runs:
        runs = rev["runs"][:4]
    fig, axes = plt.subplots(1, len(runs), figsize=(3.0 * len(runs), 3.8))
    fig.subplots_adjust(top=0.74, wspace=0.12)
    axes = np.atleast_1d(axes)
    inf = load_json(DATA_DIR / f"boundary_inference__{tag}.json")
    I_by = {(x["seed"], x["method"], x["t"], x["I_size"]): set(x["I"]) for x in inf["runs"]}
    for ax, r in zip(axes, runs):
        Imembers = set()
        for k, v in I_by.items():
            if k[0] == r["seed"] and k[1] == r["method"] and k[2] == r["t"] and k[3] == r["I_size"]:
                Imembers = v
                break
        BD, Bs, Bp = set(r["B_D"]), set(r["B_causal_sampled"]), set(r["B_pred"])
        others = [i for i in range(len(P)) if i not in Imembers | BD | Bs | Bp]
        ax.scatter(P[others, 0], P[others, 1], s=1.2, c="#e4e4e4")
        if Imembers:
            ax.scatter(P[sorted(Imembers), 0], P[sorted(Imembers), 1], s=7, c=C_INT, alpha=.75)
        ax.scatter(P[sorted(BD), 0], P[sorted(BD), 1], s=52, facecolors="none",
                   edgecolors=C_ORACLE, lw=1.1)
        ax.scatter(P[sorted(Bs), 0], P[sorted(Bs), 1], s=20, c=C_CAUS, marker="s")
        ax.scatter(P[sorted(Bp), 0], P[sorted(Bp), 1], s=9, c=C_PRED, marker="^")
        focus = sorted(Imembers | BD | Bs | Bp)
        if focus:
            fp = P[focus]
            ax.set_xlim(fp[:, 0].min() - 2, fp[:, 0].max() + 2)
            ax.set_ylim(fp[:, 1].min() - 2, fp[:, 1].max() + 2)
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(f"seed {r['seed']}, t={r['t']}\n"
                     f"|I|={r['I_size']}  |B^D|={len(BD)}\n"
                     f"causal J={r['structural_agreement']['jaccard']:.2f}  "
                     f"pred J={r['predictive_vs_BD']['jaccard']:.2f}", fontsize=7.5)
    fig.legend(handles=[
        Line2D([], [], marker="o", ls="", color=C_INT, label="detected interior $I_t$ (blind)"),
        Line2D([], [], marker="o", ls="", mfc="none", mec=C_ORACLE, label=r"oracle $B_t^D$"),
        Line2D([], [], marker="s", ls="", color=C_CAUS, label=r"$\hat B_t^{causal}$ (finite probing)"),
        Line2D([], [], marker="^", ls="", color=C_PRED, label=r"$\hat B_t^{pred}$ (passive)")],
        loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.08))
    fig.suptitle("Fig. 6.8-3  Blind detection and both inferred interfaces against the oracle.\n"
                 "The interior was proposed online from positions and headings only; the true "
                 "interface is a directional arc, not a full shell,\nbecause FOV makes only the "
                 "sources in front of a peripheral member live.", y=1.10, fontsize=8.5)
    save(fig, "fig_6_8_3_interfaces")


# ---------------------------------------------------------------- Fig 6.8-4 --
def fig4(tag="series"):
    """Precision / recall / lag of predictive vs causal interface over time."""
    rev = load_json(DATA_DIR / f"oracle_reveal__{tag}.json")
    seeds = sorted({r["seed"] for r in rev["runs"]})
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 5.4))
    for si, seed in enumerate(seeds[:2]):
        rs = sorted([r for r in rev["runs"] if r["seed"] == seed], key=lambda x: x["t"])
        ts = [r["t"] for r in rs]
        ax = axes[si, 0]
        ax.plot(ts, [r["structural_agreement"]["precision"] for r in rs], "s-", ms=3,
                color=C_CAUS, label="causal precision")
        ax.plot(ts, [r["structural_agreement"]["recall"] for r in rs], "s--", ms=3,
                color=C_CAUS, alpha=.55, label="causal recall")
        ax.plot(ts, [r["predictive_vs_BD"]["precision"] for r in rs], "^-", ms=3,
                color=C_PRED, label="predictive precision")
        ax.plot(ts, [r["predictive_vs_BD"]["recall"] for r in rs], "^--", ms=3,
                color=C_PRED, alpha=.55, label="predictive recall")
        ax.set_ylim(-0.05, 1.05); ax.set_xlabel("t"); ax.set_ylabel("precision / recall")
        ax.set_title(f"seed {seed}: interface recovery over time")
        if si == 0:
            ax.legend(frameon=False, ncol=2, fontsize=6.5)

        ax = axes[si, 1]
        ax.plot(ts, [len(r["B_D"]) for r in rs], "-", color=C_ORACLE, label=r"$|B_t^D|$")
        ax.plot(ts, [len(r["B_causal_sampled"]) for r in rs], "s-", ms=3, color=C_CAUS,
                label=r"$|\hat B_t^{causal}|$")
        ax.plot(ts, [len(r["B_pred"]) for r in rs], "^-", ms=3, color=C_PRED,
                label=r"$|\hat B_t^{pred}|$")
        tb = [(r["t"], r.get("T_B_causal")) for r in rs if r.get("T_B_causal") is not None]
        if tb:
            ax2 = ax.twinx()
            ax2.plot([t for t, _ in tb], [v for _, v in tb], ":", color="#6a9b5e", lw=1.3)
            ax2.set_ylabel(r"$T_B(t)$ turnover similarity", color="#6a9b5e", fontsize=7)
            ax2.set_ylim(-0.05, 1.05); ax2.spines["right"].set_visible(True)
        ax.set_xlabel("t"); ax.set_ylabel("interface size")
        ax.set_title(f"seed {seed}: sizes and turnover similarity")
        if si == 0:
            ax.legend(frameon=False, fontsize=6.5)
    lag = rev.get("temporal_lag", [])
    txt = "; ".join(f"seed {l['seed']}: causal best lag {l['causal']['best_lag']}, "
                    f"predictive best lag {l['predictive']['best_lag']}" for l in lag[:3])
    fig.suptitle("Fig. 6.8-4  Predictive vs finite-probe causal interface, tracked step by step "
                 "against the changing oracle.\n" + txt, y=1.04, fontsize=8.5)
    save(fig, "fig_6_8_4_precision_recall_lag")


# ---------------------------------------------------------------- Fig 6.8-5 --
def fig5():
    d = load_json(DATA_DIR / "control.json")
    arms = d["arms"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))
    palette = {"no_control": "#c9c9c9", "random_matched": "#9a9a9a",
               "frozen_causal": "#8ab4d8", "adaptive_causal": C_CAUS,
               "adaptive_oracle": C_ORACLE, "predictive": C_PRED}
    colors = {a: palette.get(a, "#666666") for a in arms}
    ax = axes[0]
    for k, arm in enumerate(arms):
        for split, mark, alpha in (("dev", "o", .45), ("heldout", "D", .95)):
            v = [r["final_target_fraction"] for r in d["runs"]
                 if r["arm"] == arm and r["split"] == split]
            if v:
                ax.scatter([k] * len(v), v, marker=mark, s=22, alpha=alpha,
                           color=colors[arm], edgecolors="none")
                ax.plot([k - .25, k + .25], [np.mean(v)] * 2, color=colors[arm], lw=2)
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels([a.replace("_", "\n") for a in arms], fontsize=6.5)
    ax.set_ylabel("final fraction of interior on target heading")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title(f"task success ({d['T_CONTROL']} steps, K_act={d['K_ACT']} matched)"
                 + ("\nBELOW the feasibility threshold -- ordering only"
                    if d.get("below_feasibility_threshold") else ""))
    ax = axes[1]
    for arm in arms:
        rs = [r for r in d["runs"] if r["arm"] == arm]
        if not rs:
            continue
        n = min(len(r["records"]) for r in rs)
        M = np.array([[rr["target_fraction"] for rr in r["records"][:n]] for r in rs])
        ax.plot(range(n), M.mean(0), lw=1.6, color=colors[arm], label=arm.replace("_", " "))
    ax.set_xlabel("control step"); ax.set_ylabel("fraction on target heading")
    ax.set_title("trajectory, mean over episodes")
    ax.legend(frameon=False, fontsize=6.5)
    fig.legend(handles=[Line2D([], [], marker="o", ls="", color="k", alpha=.45, label="development seed"),
                        Line2D([], [], marker="D", ls="", color="k", label="held-out seed")],
               loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.10))
    note = ("The task is infeasible at this scale even for the oracle arm "
            "(data/control_feasibility.json), so only the ORDERING of the arms is "
            "interpreted; no absolute success is claimed."
            if d.get("below_feasibility_threshold") else "")
    fig.suptitle("Fig. 6.8-5  Adaptive vs frozen interface control. Actuators are chosen by "
                 "causal weighted multicover on the inferred influence.\n" + note,
                 y=1.14, fontsize=8.5)
    save(fig, "fig_6_8_5_adaptive_vs_frozen")


# ---------------------------------------------------------------- Fig 6.8-6 --
def fig6():
    """FOV model versus FOV + stochastic gating."""
    g = load_json(DATA_DIR / "gate_choice.json")
    base, grid = g["baseline_L2"], g["grid"]
    fig, axes = plt.subplots(1, 3, figsize=(10.0, 3.1))
    x = [r["gate_flip_rate"] for r in grid]
    for ax, key, lab, bl in zip(
            axes,
            ("mesoscopic_episode_fraction", "mean_largest_component", "mean_heading_entropy"),
            ("mesoscopic-episode fraction (G1)", "mean largest coherent component (G3)",
             "mean heading entropy (G3)"),
            (base["mesoscopic_episode_fraction"], base["mean_largest_component"],
             base["mean_heading_entropy"])):
        ax.axhline(bl, color=C_ORACLE, ls="--", lw=1.2, label="L2, no gating")
        ax.scatter(x, [r[key] for r in grid],
                   c=[("#2f7d32" if r["accepted"] else C_CAUS) for r in grid], s=26)
        ch = g.get("fallback_for_robustness_probe")
        if ch:
            ax.scatter([ch["gate_flip_rate"]], [ch[key]], s=110, facecolors="none",
                       edgecolors="k", lw=1.3)
        if key == "mesoscopic_episode_fraction":
            ax.axhspan(0.5 * bl, 2 * bl, color="#2f7d32", alpha=.10)
        ax.set_xlabel("gate flip rate per directed edge per step")
        ax.set_ylabel(lab, fontsize=7)
        ax.legend(frameon=False, fontsize=6.5)
    fig.suptitle("Fig. 6.8-6  L2 (FOV) vs L3 (FOV + persistent hidden edge gates). "
                 "No gate regime in the predeclared grid satisfies G1 (shaded band):\n"
                 "gating leaves flocking intact but measurably suppresses the mesoscopic "
                 "regime. Circled point = the labelled robustness-probe fallback.",
                 y=1.06, fontsize=8.5)
    save(fig, "fig_6_8_6_fov_vs_gated")


ALL = dict(fig1=fig1, fig2=fig2, fig3=fig3, fig4=fig4, fig5=fig5, fig6=fig6)

if __name__ == "__main__":
    which = sys.argv[1:] or list(ALL)
    for w in which:
        try:
            ALL[w]()
        except FileNotFoundError as e:
            print(f"skip {w}: missing {e.filename}")
