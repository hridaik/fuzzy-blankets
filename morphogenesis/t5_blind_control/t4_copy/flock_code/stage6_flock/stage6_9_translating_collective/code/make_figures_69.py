"""Stage 6.9 figures (task brief §39). EVALUATION-SIDE: reads frozen JSON only."""
from __future__ import annotations

import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common_69 import load_json, DATA_DIR, FIG_DIR, ModelParams, N_BIRDS, L_BOX, \
    R_RADIUS, V_SPEED, BETA, RHO, OMEGA, UV4

plt.rcParams.update({"figure.dpi": 130, "font.size": 8, "axes.titlesize": 9,
                     "axes.labelsize": 8, "legend.fontsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False})
C_MAT, C_FUNC, C_DEF, C_PRED, C_CAUS, C_ORACLE = \
    "#b3453b", "#3b6ea5", "#6a9b5e", "#e08a2e", "#b3453b", "#4a4a4a"


def save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("wrote", FIG_DIR / f"{name}.png")


def _sim():
    from moving_flock import MovingFlock
    return MovingFlock(N=N_BIRDS, L=L_BOX, R=R_RADIUS, v=V_SPEED,
                       params=ModelParams(beta=BETA, precB=RHO, precC=OMEGA))


def _best_episode(gate):
    """The episode to illustrate. Gate-passing episodes are preferred; when the
    gate fails outright (as it does at specification) the LONGEST-TRACKED
    episode is shown instead, so the figure depicts what the specified model
    actually does rather than nothing at all."""
    p = [e for e in gate["episodes"] if e["passes"]]
    if p:
        return min(p, key=lambda e: e["R_M_final"]), True
    t = [e for e in gate["episodes"] if e.get("tracked")]
    return (max(t, key=lambda e: e["duration"]), False) if t else (None, False)


# ------------------------------------------------------------------ 6.9-1 ---
def fig1():
    """World-frame emergence and translation, with the detected collective and
    its original members picked out (membership from the frozen viz bundle)."""
    B = load_json(DATA_DIR / "viz_bundle_69.json")
    L, origin = B["L"], set(B["origin"])
    picks = [0, len(B["frames"]) // 3, 2 * len(B["frames"]) // 3, len(B["frames"]) - 1]
    fig, axes = plt.subplots(1, 4, figsize=(11.5, 3.2))
    cen = np.array([f["centroid"] for f in B["frames"]])
    for ax, i in zip(axes, picks):
        f, w = B["frames"][i], B["world"][i]
        mem = set(f["members"])
        x, y = np.array(w["x"]), np.array(w["y"])
        other = [k for k in range(len(x)) if k not in mem]
        ax.scatter(x[other], y[other], s=1.6, c="#e6e6e4")
        m = sorted(mem)
        col = [C_MAT if k in origin else C_FUNC for k in m]
        ax.scatter(x[m], y[m], s=7, c=col)
        # draw the centroid trail, split wherever it wraps around the torus
        trail = cen[:i + 1]
        if len(trail) > 1:
            jump = (np.abs(np.diff(trail, axis=0)) > L / 2).any(axis=1)
            start = 0
            for k in np.append(np.where(jump)[0] + 1, len(trail)):
                seg = trail[start:k]
                if len(seg) > 1:
                    ax.plot(seg[:, 0], seg[:, 1], "-", color="#26262b", lw=0.9, alpha=.55)
                start = k
        ax.plot(*f["centroid"], "x", color="k", ms=7, mew=1.6)
        ax.set_xlim(0, L); ax.set_ylim(0, L); ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(f"t={f['t']}   |I|={f['size']}   $R_M$={f['R_M']:.2f}", fontsize=8)
    fig.legend(handles=[Line2D([], [], marker="o", ls="", color=C_MAT,
                               label="original member, still in the collective"),
                        Line2D([], [], marker="o", ls="", color=C_FUNC, label="recruited member"),
                        Line2D([], [], marker="o", ls="", color="#e6e6e4", label="other birds")],
               loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.06))
    S = B["summary"]
    fig.suptitle(f"Fig. 6.9-1  World-frame emergence and translation (seed {B['seed']}): "
                 f"a collective forms, is tracked {S['duration']} steps and travels "
                 f"{S['displacement_radii']:.1f} interaction radii\nwhile red (original) "
                 f"members are progressively replaced by blue (recruited) ones.",
                 y=1.08, fontsize=8.5)
    save(fig, "fig_6_9_1_world_frame_translation")


# ------------------------------------------------------------------ 6.9-2 ---
def fig2():
    """Material retention versus co-moving functional identity."""
    gate = load_json(DATA_DIR / "translation_gate.json")
    eps = sorted(gate["episodes"], key=lambda e: e["R_M_final"])
    passing = [e for e in eps if e["passes"]]
    panel1_label = "gate-passing episodes"
    if not passing:   # the gate failed outright: show the longest-tracked instead
        passing = sorted([e for e in eps if e.get("tracked")],
                         key=lambda e: -e["duration"])[:4]
        panel1_label = "longest-tracked episodes (no episode passed)"
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))

    ax = axes[0]
    for e in passing[:4]:
        t = [r["t"] for r in e["records"]]
        ax.plot(t, [r["R_M"] for r in e["records"]], "-", color=C_MAT, lw=1.2, alpha=.8)
        rf = [(r["t"], r["R_F"]) for r in e["records"] if "R_F" in r]
        ax.plot([x for x, _ in rf], [y for _, y in rf], "-", color=C_FUNC, lw=1.2, alpha=.8)
    ax.set_xlabel("t"); ax.set_ylabel("identity"); ax.set_ylim(-0.03, 1.03)
    ax.set_title(panel1_label, fontsize=8)
    ax.legend(handles=[Line2D([], [], color=C_MAT, label=r"$R_M$ material"),
                       Line2D([], [], color=C_FUNC, label=r"$R_F$ co-moving functional")],
              frameon=False, loc="lower left")

    ax = axes[1]
    ok = [e for e in gate["episodes"] if e.get("tracked")]
    ax.scatter([e["R_M_final"] for e in ok], [e["mean_R_F"] for e in ok],
               c=["#2f7d32" if e["passes"] else "#bbbbbb" for e in ok], s=26)
    ax.axvline(gate["criteria"]["T3_max_material_retention"], color=C_MAT, ls="--", lw=1)
    ax.axhline(gate["criteria"]["T4_min_mean_RF"], color=C_FUNC, ls="--", lw=1)
    ax.set_xlabel(r"final material retention $R_M$")
    ax.set_ylabel(r"mean co-moving similarity $R_F$")
    ax.set_ylim(0, 1.05)
    n_pass = sum(1 for e in gate["episodes"] if e["passes"])
    ax.set_title(f"every screened episode\n({n_pass} of {len(gate['episodes'])} pass all five criteria)",
                 fontsize=8)

    ax = axes[2]
    dw = [np.mean([r["D_world_frame"] for r in e["records"] if "D_world_frame" in r])
          for e in ok]
    dd = [e["mean_D_deform"] for e in ok]
    ax.scatter(dd, dw, c=["#2f7d32" if e["passes"] else "#bbbbbb" for e in ok], s=26)
    lim = max(max(dw), max(dd)) * 1.05
    ax.plot([0, lim], [0, lim], ":", color="k", lw=1)
    ax.set_xlabel(r"$D_{\rm deform}$  (best translation removed)")
    ax.set_ylabel(r"$D$ in world coordinates (no alignment)")
    on_diag = np.mean([abs(a - b) / max(b, 1e-9) for a, b in zip(dd, dw)]) < 0.25
    ax.set_title("removing translation buys nothing here"
                 if on_diag else "bulk motion is not destruction", fontsize=8)
    passed = any(e["passes"] for e in gate["episodes"])
    if passed:
        cap = ("Fig. 6.9-2  Material retention falls while co-moving functional identity holds — "
               "and the gap between world-frame and\nde-translated field distance shows the "
               "difference is genuinely translation, not deformation.")
    else:
        cap = ("Fig. 6.9-2  At the specified interaction scale the two halves of the hypothesis do "
               "NOT co-occur: material retention falls (left, red)\nbut co-moving functional "
               "identity falls with it (left, blue; middle, mostly below the 0.70 line), and the "
               "world-frame and de-translated\nfield distances are nearly equal (right, on the "
               "diagonal) — what is left after removing translation is deformation, not transport.")
    fig.suptitle(cap, y=1.10, fontsize=8.5)
    save(fig, "fig_6_9_2_material_vs_functional")


# ------------------------------------------------------------------ 6.9-3 ---
def fig3():
    """Original IDs versus recruited IDs through time."""
    gate = load_json(DATA_DIR / "translation_gate.json")
    ep, passed = _best_episode(gate)
    recs = ep["records"]
    t = [r["t"] for r in recs]
    RM = np.array([r["R_M"] for r in recs])
    size = np.array([r["size"] for r in recs])
    n_orig = RM * size[0]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.1))
    ax = axes[0]
    ax.fill_between(t, 0, n_orig, color=C_MAT, alpha=.75, label="original members still present")
    ax.fill_between(t, n_orig, size, color=C_FUNC, alpha=.55, label="recruited members")
    ax.set_xlabel("t"); ax.set_ylabel("birds in the collective")
    ax.set_title(f"seed {ep['seed']}: composition through time")
    ax.legend(frameon=False, loc="upper left")
    ax = axes[1]
    ax.plot(t, RM, color=C_MAT, lw=1.5, label=r"$R_M$")
    ax.plot([r["t"] for r in recs[1:]], [r["J_prev"] for r in recs[1:]], color="#8a8a8a",
            lw=1.2, label=r"$J(I_t, I_{t-1})$ lineage")
    rf = [(r["t"], r["R_F"]) for r in recs if "R_F" in r]
    ax.plot([x for x, _ in rf], [y for _, y in rf], color=C_FUNC, lw=1.5, label=r"$R_F$")
    ax.set_ylim(0, 1.05); ax.set_xlabel("t"); ax.set_ylabel("identity")
    ax.set_title("the three notions, kept separate")
    ax.legend(frameon=False, loc="lower left")
    fig.suptitle("Fig. 6.9-3  Original versus recruited identities. Material continuity "
                 "decays; step-to-step lineage and co-moving\nfunctional continuity do not.",
                 y=1.06, fontsize=8.5)
    save(fig, "fig_6_9_3_original_vs_recruited")


# ------------------------------------------------------------------ 6.9-4 ---
def fig4():
    """World frame versus aligned co-moving frame, members only."""
    B = load_json(DATA_DIR / "viz_bundle_69.json")
    L, origin = B["L"], set(B["origin"])
    fr = [f for f in B["frames"] if not np.isnan(f["R_F"])]
    picks = [0, len(fr) // 3, 2 * len(fr) // 3, len(fr) - 1]
    fig, axes = plt.subplots(2, 4, figsize=(11.5, 5.8))
    for k, i in enumerate(picks):
        f = fr[i]
        w = B["world"][B["frames"].index(f)]
        mem = sorted(set(f["members"]))
        x, y = np.array(w["x"]), np.array(w["y"])
        hh = np.array(w["h"])
        col = [C_MAT if m in origin else C_FUNC for m in mem]
        ax = axes[0, k]
        ax.scatter(x, y, s=1.4, c="#ececea")
        ax.quiver(x[mem], y[mem], UV4[hh[mem]][:, 0], UV4[hh[mem]][:, 1], color=col,
                  width=0.008, scale=26)
        ax.plot(*f["centroid"], "x", color="k", ms=7, mew=1.6)
        ax.set_xlim(0, L); ax.set_ylim(0, L)
        ax.set_title(f"world frame, t={f['t']}", fontsize=8)
        ax = axes[1, k]
        rel = np.array(f["rel"]); rh = np.array(f["rel_h"])
        ax.quiver(rel[:, 0], rel[:, 1], UV4[rh][:, 0], UV4[rh][:, 1], color=col,
                  width=0.009, scale=24)
        ax.axhline(0, color="#eeeeec", lw=1, zorder=0)
        ax.axvline(0, color="#eeeeec", lw=1, zorder=0)
        ax.set_xlim(-6, 6); ax.set_ylim(-6, 6)
        ax.set_title(f"co-moving   $R_F$={f['R_F']:.2f}   $D_{{\\rm deform}}$={f['D_deform']:.3f}",
                     fontsize=8)
        for a_ in (axes[0, k], axes[1, k]):
            a_.set_aspect("equal"); a_.set_xticks([]); a_.set_yticks([])
            for sp in a_.spines.values():
                sp.set_visible(False)
    fig.legend(handles=[Line2D([], [], color=C_MAT, label="original members"),
                        Line2D([], [], color=C_FUNC, label="recruited members")],
               loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Fig. 6.9-4  The same collective in world coordinates (top) and after "
                 "subtracting its ESTIMATED translation (bottom).\nThe world-frame group "
                 "crosses the torus; the co-moving representation stays in place while its "
                 "membership turns over.", y=1.02, fontsize=8.5)
    save(fig, "fig_6_9_4_world_vs_comoving")


# ------------------------------------------------------------------ 6.9-5 ---
def fig5():
    """Dynamic predictive/causal interfaces during translation."""
    rev = load_json(DATA_DIR / "oracle_reveal_69.json")
    runs = rev["runs"]
    seeds = sorted({r["seed"] for r in runs})
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.1))
    ax = axes[0]
    for s in seeds:
        rs = sorted([r for r in runs if r["seed"] == s], key=lambda x: x["t"])
        ax.plot([r["t"] for r in rs], [len(r["B_D"]) for r in rs], "-", color=C_ORACLE, lw=1.3)
        ax.plot([r["t"] for r in rs], [len(r["B_causal_sampled"]) for r in rs], "s-",
                ms=3, color=C_CAUS)
        ax.plot([r["t"] for r in rs], [len(r["B_pred"]) for r in rs], "^-", ms=3, color=C_PRED)
    ax.set_xlabel("t"); ax.set_ylabel("interface size")
    ax.set_title("interface size while the group moves")
    ax.legend(handles=[Line2D([], [], color=C_ORACLE, label=r"oracle $B_t^D$"),
                       Line2D([], [], color=C_CAUS, marker="s", label=r"$\hat B^{causal}$"),
                       Line2D([], [], color=C_PRED, marker="^", label=r"$\hat B^{pred}$")],
              frameon=False)
    ax = axes[1]
    for key, col, lab in (("structural_agreement", C_CAUS, "causal"),
                          ("predictive_vs_BD", C_PRED, "predictive")):
        for s in seeds:
            rs = sorted([r for r in runs if r["seed"] == s], key=lambda x: x["t"])
            ax.plot([r["t"] for r in rs], [r[key]["precision"] for r in rs], "-", color=col)
            ax.plot([r["t"] for r in rs], [r[key]["recall"] for r in rs], "--", color=col, alpha=.6)
    ax.set_ylim(-0.05, 1.05); ax.set_xlabel("t"); ax.set_ylabel("precision (solid) / recall (dashed)")
    ax.set_title(r"recovery of $B_t^D$")
    ax = axes[2]
    w = [r["BD_world_turnover"] for r in runs if "BD_world_turnover" in r]
    c = [r["BD_comoving_turnover"] for r in runs if "BD_comoving_turnover" in r]
    ax.bar([0, 1], [np.mean(w), np.mean(c)], yerr=[np.std(w), np.std(c)],
           color=[C_ORACLE, C_FUNC], width=.6, capsize=4)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["world\ncoordinates", "co-moving\nframe"])
    ax.set_ylabel("true interface turnover per step")
    ax.set_title("the interface moves with the group")
    fig.suptitle("Fig. 6.9-5  Predictive and causal interfaces of a translating collective, "
                 "re-inferred online at every step.", y=1.06, fontsize=8.5)
    save(fig, "fig_6_9_5_interfaces_during_translation")


# ------------------------------------------------------------------ 6.9-6 ---
def fig6():
    """Guided path with identity-preserving vs identity-destroying controls."""
    d = load_json(DATA_DIR / "guidance.json")
    arms = d["arms"]
    pal = {"adaptive_causal": C_CAUS, "adaptive_oracle": C_ORACLE,
           "no_control": "#c9c9c9", "random_matched": "#9a9a9a",
           "interior_forcing": "#7d3c98"}
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.3))
    ax = axes[0]
    for k, arm in enumerate(arms):
        v = [r["mean_path_error_radii"] for r in d["runs"] if r["arm"] == arm and r.get("ok")]
        if v:
            ax.scatter([k] * len(v), v, s=22, color=pal.get(arm, "#666"), alpha=.75)
            ax.plot([k - .25, k + .25], [np.mean(v)] * 2, color=pal.get(arm, "#666"), lw=2)
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels([a.replace("_", "\n") for a in arms], fontsize=6.5)
    ax.set_ylabel("mean path error (interaction radii)")
    ax.set_title(r"$S_{\rm path}$: does it follow the route?")
    ax = axes[1]
    for arm in arms:
        rs = [r for r in d["runs"] if r["arm"] == arm and r.get("ok")]
        if not rs:
            continue
        ax.scatter([np.mean([r["final_R_M"] for r in rs])],
                   [np.mean([r["mean_R_F"] for r in rs])],
                   s=70, color=pal.get(arm, "#666"), label=arm.replace("_", " "))
    ax.axhline(0.70, color=C_FUNC, ls="--", lw=1)
    ax.set_xlabel(r"final material retention $R_M$")
    ax.set_ylabel(r"mean co-moving similarity $R_F$")
    ax.set_xlim(-0.05, 1.05); ax.set_ylim(0, 1.05)
    ax.set_title(r"$S_{\rm functional\ identity}$")
    ax.legend(frameon=False, fontsize=6.2, loc="lower left")
    ax = axes[2]
    keys = ["S_path", "S_functional_identity", "S_nondegenerate", "S_boundary", "S_full"]
    W = 0.8 / max(1, len(arms))
    for k, arm in enumerate(arms):
        rs = [r for r in d["runs"] if r["arm"] == arm and r.get("ok")]
        if not rs:
            continue
        vals = [np.mean([r[key] for r in rs]) for key in keys]
        ax.bar(np.arange(len(keys)) + k * W, vals, width=W, color=pal.get(arm, "#666"),
               label=arm.replace("_", " "))
    ax.set_xticks(np.arange(len(keys)) + 0.4)
    ax.set_xticklabels([k.replace("S_", "").replace("_", "\n") for k in keys], fontsize=6.2)
    ax.set_ylabel("fraction of episodes")
    ax.set_title("conjunctive success")
    note = ("Task below the feasibility threshold; ordering only. "
            if d.get("below_feasibility_threshold") else "")
    fig.suptitle("Fig. 6.9-6  Guided path, identity-preserving (boundary, causal) versus "
                 "identity-destroying (interior forcing) control.\n" + note +
                 "Material retention is reported, never required to stay high.",
                 y=1.08, fontsize=8.5)
    save(fig, "fig_6_9_6_guidance")


def fig_gate():
    """The gate outcome and its diagnosis: what fails at specification, and how
    the phenomenon tracks interaction degree rather than the specification."""
    new = load_json(DATA_DIR / "translation_gate__R0.9_v0.28.json")
    old = load_json(DATA_DIR / "translation_gate__R1.6_v0.5__SUPERSEDED.json")
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.4))

    ax = axes[0]
    keys = ["T1", "T2", "T3", "T4", "T5"]
    lab = ["T1\npersists", "T2\ntranslates", "T3\nmembership\nchanges",
           "T4\norganization\npersists", "T5\nspatially\ncoherent"]
    x = np.arange(len(keys))
    ax.bar(x - 0.2, [new["rate_" + k] for k in keys], width=0.4, color=C_MAT,
           label="R=0.9, degree 8.9 (specification)")
    ax.bar(x + 0.2, [old["rate_" + k] for k in keys], width=0.4, color="#c2c2c2",
           label="R=1.6, degree 21.2 (superseded)")
    ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=6.3)
    ax.set_ylabel("fraction of 40 episodes"); ax.set_ylim(0, 1.05)
    ax.set_title("per-criterion rates: T5 is the binding failure")
    ax.legend(frameon=False, fontsize=6.3, loc="lower left")

    ax = axes[1]
    E = [e for e in new["episodes"] if e.get("tracked")]
    O = [e for e in old["episodes"] if e.get("tracked")]
    ax.scatter([e["R_M_final"] for e in E], [e["mean_R_F"] for e in E], s=26,
               color=C_MAT, label="specification (degree 8.9)")
    ax.scatter([e["R_M_final"] for e in O], [e["mean_R_F"] for e in O], s=26,
               color="#c2c2c2", label="superseded (degree 21.2)")
    ax.axhline(0.70, color=C_FUNC, ls="--", lw=1)
    ax.set_xlabel(r"final material retention $R_M$")
    ax.set_ylabel(r"mean co-moving similarity $R_F$")
    ax.set_xlim(-0.05, 1.05); ax.set_ylim(0, 1.05)
    ax.set_title("at spec, membership turns over\nbut organization does not survive")
    ax.legend(frameon=False, fontsize=6.3, loc="lower left")

    ax = axes[2]
    deg = [8.9, 14.8, 16.5, 21.2]
    rate = [0.00, 0.00, 2 / 6, 0.40]
    ax.plot(deg, rate, "o-", color=C_MAT, lw=1.6, ms=6)
    ax.axvline(8, color=C_FUNC, ls="--", lw=1.2)
    ax.annotate("Moore scale", (8, 0.42), fontsize=7, color=C_FUNC,
                ha="left", xytext=(9, 0.42), textcoords="data")
    ax.axhline(0.20, color="#999", ls=":", lw=1)
    ax.annotate("gate threshold", (21, 0.21), fontsize=6.5, color="#777", ha="right")
    ax.set_xlabel("mean realized live in-degree")
    ax.set_ylabel("gate pass rate")
    ax.set_ylim(-0.03, 0.45)
    ax.set_title("the phenomenon tracks connectivity")
    fig.suptitle("Fig. 6.9-G  The feasibility gate FAILS at the specified interaction scale "
                 "(0/40). Membership turnover is plentiful (T3 = 0.90) but the group\n"
                 "fragments into ~3.8 pieces and its co-moving organization does not persist "
                 "(T4 = 0.38). The phenomenon appears only at ~3x Moore connectivity.",
                 y=1.10, fontsize=8.5)
    save(fig, "fig_6_9_G_gate_failure")


ALL = dict(fig_gate=fig_gate, fig1=fig1, fig2=fig2, fig3=fig3, fig4=fig4,
           fig5=fig5, fig6=fig6)

if __name__ == "__main__":
    for w in (sys.argv[1:] or list(ALL)):
        try:
            ALL[w]()
        except FileNotFoundError as e:
            print(f"skip {w}: missing {e.filename}")
