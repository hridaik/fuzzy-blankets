"""Stage 6.10 figures. EVALUATION-SIDE: reads only frozen JSON in data/.

Nothing here recomputes a scientific quantity; if a panel needs a number, that
number is already in a data file written by the run that established it.
"""
from __future__ import annotations

import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common_610 import load_json, DATA_DIR, FIG_DIR

plt.rcParams.update({"figure.dpi": 130, "font.size": 8, "axes.titlesize": 9,
                     "axes.labelsize": 8, "legend.fontsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False})

C_BENCH, C_ADAPT, C_HEUR = "#3b6ea5", "#e08a2e", "#b3453b"
C_MUTE, C_OK, C_BAD = "#8a8a8a", "#3f7d3f", "#a83232"


def save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("wrote", FIG_DIR / f"{name}.png")


# ------------------------------------------------------------ Fig 6.10-1 ----
def fig1_audit():
    """Part A: why full information lost. Four panels, one hypothesis family
    each, kept separate rather than summed into a single 'explanation'."""
    d = load_json(DATA_DIR / "audit_hypotheses.json")
    fig, ax = plt.subplots(1, 4, figsize=(11.2, 2.5))

    # H1 -- spend vs outcome
    pa = d["H1_actuator_spend"]["per_arm"]
    names = ["adaptive_causal", "adaptive_oracle", "frozen_causal",
             "predictive", "random_matched", "no_control"]
    lbl = {"adaptive_oracle": "full-info\nheuristic", "adaptive_causal": "adaptive\ncausal",
           "frozen_causal": "frozen\ncausal", "predictive": "predictive",
           "random_matched": "random\nmatched", "no_control": "no\ncontrol"}
    x = [pa[n]["mean_actuators"] for n in names]
    y = [pa[n]["mean_final"] for n in names]
    for n, xi, yi in zip(names, x, y):
        c = C_HEUR if n == "adaptive_oracle" else (C_ADAPT if n == "adaptive_causal" else C_MUTE)
        ax[0].scatter(xi, yi, s=26, color=c, zorder=3)
        dy = -14 if n == "adaptive_causal" else 3
        ax[0].annotate(lbl[n], (xi, yi), fontsize=6, xytext=(4, dy),
                       textcoords="offset points", color=c)
    ax[0].set_ylim(-0.02, max(y) * 1.32)
    ax[0].set_xlim(-1.2, max(x) * 1.22)
    ax[0].set_xlabel("mean actuators spent"); ax[0].set_ylabel("final target fraction")
    ax[0].set_title("H1  spend does not buy the outcome")

    # H3 -- KL vs task authority, pooled
    kl, au = [], []
    for st in d["H3_kl_vs_authority"]["per_state"]:
        a = st["authority"].get("2")
        if a is None:
            continue
        kl += list(st["kl"]); au += list(a)
    kl, au = np.array(kl), np.array(au)
    ax[1].scatter(np.maximum(kl, 1e-6), au, s=8, alpha=0.45, color=C_HEUR, lw=0)
    ax[1].set_xscale("log")
    ax[1].axhline(0, color="k", lw=0.6)
    ax[1].set_xlabel(r"KL influence $C^{do}_{j\to I}$  (task-agnostic)")
    ax[1].set_ylabel(r"task authority $A_j^{h^*,\tau=2}$")
    ax[1].set_title(r"H3  $\bar\rho$ = %.3f" % d["H3_kl_vs_authority"].get(
        "mean_rho", np.nan) if "mean_rho" in d["H3_kl_vs_authority"] else "H3  KL is not authority")

    # H5 -- rank agreement decays with horizon
    h5 = d["H5_horizon"]
    vals = [h5["mean_rho_tau2_tau4"], h5["mean_rho_tau2_tau8"], h5["mean_rho_kl_tau8"]]
    ax[2].bar(range(3), vals, color=[C_ADAPT, C_ADAPT, C_HEUR], width=0.6)
    ax[2].set_xticks(range(3))
    ax[2].set_xticklabels([r"$\tau$2 vs $\tau$4", r"$\tau$2 vs $\tau$8", r"KL vs $\tau$8"],
                          fontsize=6.5)
    ax[2].set_ylabel("mean Spearman rank corr.")
    ax[2].set_ylim(0, 1); ax[2].set_title("H5  short-horizon scores decay")

    # H6 -- the ordering was never established
    h6 = d["H6_ordering_noise"]
    diffs = [e["diff"] for e in h6["per_episode"]]
    ax[3].axvline(0, color="k", lw=0.8)
    ax[3].scatter(diffs, np.arange(len(diffs)), s=18, color=C_MUTE, zorder=3)
    lo, hi = h6["boot_ci"]
    ax[3].plot([lo, hi], [-1.2, -1.2], color=C_ADAPT, lw=2.4, solid_capstyle="butt")
    ax[3].scatter([h6["mean_diff"]], [-1.2], s=26, color=C_ADAPT, zorder=4)
    ax[3].set_yticks([]); ax[3].set_ylim(-2.2, len(diffs))
    ax[3].set_xlabel("per-episode  adaptive_causal − full-info heuristic")
    ax[3].set_title("H6  95% CI spans zero")
    fig.tight_layout()
    save(fig, "fig_6_10_1_audit")


# ------------------------------------------------------------ Fig 6.10-2 ----
def fig2_regime():
    """Part G: the regime map from UNCONTROLLED data, with the selected cell,
    the runner-up, and the rejected most-responsive cell all marked."""
    d = load_json(DATA_DIR / "regime_scan__main.json")
    rows = d["cells"] if isinstance(d.get("cells"), list) else d.get("rows", [])
    if not rows:
        rows = [v | dict(beta=v.get("beta"), s=v.get("s")) for v in d.values()
                if isinstance(v, dict) and "beta" in v]
    betas = sorted({r["beta"] for r in rows}, reverse=True)
    ss = sorted({r["s"] for r in rows})
    def grid(key):
        M = np.full((len(betas), len(ss)), np.nan)
        for r in rows:
            M[betas.index(r["beta"]), ss.index(r["s"])] = r[key]
        return M

    fig, ax = plt.subplots(1, 3, figsize=(9.6, 2.9))
    for a, key, ttl, cm in zip(ax, ["frac_locked", "chi_max_mean", "mean_jaccard"],
                               ["policy-locked fraction", r"susceptibility $\chi$",
                                "lineage Jaccard"],
                               ["magma_r", "viridis", "cividis"]):
        M = grid(key)
        im = a.imshow(M, cmap=cm, aspect="auto")
        a.set_xticks(range(len(ss))); a.set_xticklabels(ss)
        a.set_yticks(range(len(betas))); a.set_yticklabels(betas)
        a.set_xlabel("precision scale s"); a.set_ylabel(r"temperature $\beta$")
        a.set_title(ttl)
        for i in range(len(betas)):
            for j in range(len(ss)):
                if not np.isnan(M[i, j]):
                    a.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                           fontsize=6, color="w" if M[i, j] > np.nanmean(M) else "k")
        fig.colorbar(im, ax=a, fraction=0.046)

    def mark(a, beta, s, style, lab):
        a.add_patch(plt.Rectangle((ss.index(s) - .5, betas.index(beta) - .5), 1, 1,
                                  fill=False, lw=1.8, ls=style, ec=lab))
    for a in ax:
        mark(a, 0.4, 0.75, "-", C_OK)      # selected
        mark(a, 0.5, 0.50, ":", C_ADAPT)   # runner-up
        mark(a, 0.4, 0.50, "--", C_BAD)    # rejected by R5
        mark(a, 1.0, 1.00, "-.", C_MUTE)   # Stage 6.8 operating point
    ax[0].legend(handles=[Line2D([], [], color=C_OK, ls="-", label="selected"),
                          Line2D([], [], color=C_ADAPT, ls=":", label="runner-up"),
                          Line2D([], [], color=C_BAD, ls="--", label="rejected (R5)"),
                          Line2D([], [], color=C_MUTE, ls="-.", label="Stage 6.8 point")],
                 loc="upper left", bbox_to_anchor=(0, -0.28), ncol=2, frameon=False)
    fig.tight_layout()
    save(fig, "fig_6_10_2_regime")


# ------------------------------------------------------------ Fig 6.10-3 ----
def fig3_thingness():
    """Part E/F: the thingness landscape and clumpness as SEPARATE axes.
    Snake-like candidates are drawn, not deleted."""
    d = load_json(DATA_DIR / "uncontrolled_reference__main.json")
    C = d["candidates"]
    q = np.array([c["q_clump"] for c in C])
    thr = d["clump_stratum_threshold"]
    fig, ax = plt.subplots(1, 4, figsize=(11.2, 2.5))
    for a, key, ttl in zip(ax[:3], ["C", "G", "D"],
                           ["C  heading coherence", "G  internal integration",
                            "D  exterior contrast"]):
        v = np.array([c[key] for c in C], float)
        m = ~np.isnan(v)
        a.scatter(q[m], v[m], s=14, alpha=0.6, lw=0,
                  color=np.where(q[m] >= thr, C_OK, C_MUTE))
        a.axvline(thr, color=C_OK, lw=0.9, ls="--")
        a.set_xlabel(r"$Q_{clump}$"); a.set_ylabel(key); a.set_title(ttl)
        if key == "G":
            a.axhline(0, color="k", lw=0.6)
    Lv = np.array([c["L"] for c in C], float)
    ax[3].hist(Lv[~np.isnan(Lv)], bins=24, color=C_MUTE)
    ax[3].set_xlabel("L  residual leakage"); ax[3].set_ylabel("candidates")
    ax[3].set_title("L is ~0 throughout\n(reported, not used to rank)")
    fig.tight_layout()
    save(fig, "fig_6_10_3_thingness")


# ------------------------------------------------------------ Fig 6.10-4 ----
def fig4_controllability():
    """Part H: can full-model control steer this collective at all, and at what
    resource cost? The frozen operating task is marked. This is the gate: no
    controller comparison runs on a task this panel says is not achievable."""
    d = load_json(DATA_DIR / "controllability__main.json")
    cells = d["cells"]
    fracs = sorted({c["frac"] for c in cells.values()})
    hors = sorted({c["horizon"] for c in cells.values()})
    def grid(key):
        M = np.full((len(fracs), len(hors)), np.nan)
        for c in cells.values():
            M[fracs.index(c["frac"]), hors.index(c["horizon"])] = c[key]
        return M
    lo, hi = d["success_band"]

    fig, ax = plt.subplots(1, 3, figsize=(9.8, 2.9))
    for a, key, ttl in zip(ax, ["mean_final", "frac_above_hi", "frac_below_lo"],
                           [r"mean final $H^*(I_t,t)$",
                            f"fraction reaching {hi:.2f}",
                            f"fraction stuck below {lo:.2f}"]):
        M = grid(key)
        im = a.imshow(M, cmap="viridis" if key != "frac_below_lo" else "magma_r",
                      aspect="auto", vmin=0, vmax=1)
        a.set_xticks(range(len(hors))); a.set_xticklabels(hors)
        a.set_yticks(range(len(fracs))); a.set_yticklabels(fracs)
        a.set_xlabel("control horizon T"); a.set_ylabel("actuator fraction of interface")
        a.set_title(ttl)
        for i in range(len(fracs)):
            for j in range(len(hors)):
                if not np.isnan(M[i, j]):
                    a.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                           fontsize=7, color="w" if M[i, j] < 0.6 else "k")
        fig.colorbar(im, ax=a, fraction=0.046)
    ft = d.get("frozen_task")
    ft = ft["frozen_cell"] if ft and "frozen_cell" in ft else ft
    if ft:
        for a in ax:
            a.add_patch(plt.Rectangle((hors.index(ft["horizon"]) - .5,
                                       fracs.index(ft["frac"]) - .5), 1, 1,
                                      fill=False, lw=2.0, ec=C_OK))
        ax[0].plot([], [], color=C_OK, lw=2, label="frozen operating task")
        ax[0].legend(loc="upper left", bbox_to_anchor=(0, -0.3), frameon=False)
    fig.tight_layout()
    save(fig, "fig_6_10_4_controllability")


# ------------------------------------------------------------ Fig 6.10-5 ----
def fig5_arms():
    """Part I/J: the seven arms under BOTH budget conventions, side by side.

    Plotting only the matched-budget table would be actively misleading: there
    random_matched appears to beat every causal arm, but that is an artefact of
    unequal spend (multicover stops early on its own coverage criterion, while
    random and predictive spend the full realized schedule). Fixed-K removes
    that confound and the ordering inverts. Both are shown so neither reads as
    the whole story on its own.
    """
    dm = load_json(DATA_DIR / "closed_loop__main.json")
    dk = load_json(DATA_DIR / "closed_loop__fixedk.json")
    arms = dm["arms"]
    lbl = {"full_model_benchmark": "full-model\nbenchmark",
           "adaptive_causal": "adaptive\ncausal",
           "full_info_heuristic": "full-info\nheuristic",
           "frozen_causal": "frozen\ncausal",
           "predictive": "predictive",
           "random_matched": "random\nmatched",
           "no_control": "no control"}

    def agg(d, arm, f):
        return np.array([f(e["arms"][arm]) for e in d["episodes"]], float)

    cols = [C_BENCH if a == "full_model_benchmark" else
            (C_ADAPT if a == "adaptive_causal" else
             (C_HEUR if a == "full_info_heuristic" else C_MUTE)) for a in arms]
    x = np.arange(len(arms))

    fig, ax = plt.subplots(1, 4, figsize=(13.2, 2.8))

    for a_idx, (d, ttl, spend_ttl) in enumerate(
            [(dm, "matched budget\n(spend varies by arm)", "spend (matched)"),
             (dk, "fixed K\n(every arm spends the same)", "spend (fixed K)")]):
        mH = [agg(d, a, lambda r: r["final_H_current"]).mean() for a in arms]
        sH = [agg(d, a, lambda r: r["final_H_current"]).std() / max(1, len(d["episodes"])) ** 0.5
              for a in arms]
        ax[a_idx].bar(x, mH, yerr=sH, color=cols, width=0.66, capsize=2)
        ax[a_idx].axhline(d["h_threshold"], color="k", lw=0.7, ls="--")
        ax[a_idx].set_ylabel(r"final $H^*(I_t,t)$"); ax[a_idx].set_title(ttl, fontsize=8)
        ax[a_idx].set_ylim(0, 1.05)

    d = dk   # task-vs-identity and spend are shown for fixed-K, where spend is
             # controlled and the comparison is therefore not confounded by it
    tk = [agg(d, a, lambda r: r["score"]["task_met"]).mean() for a in arms]
    iv = [agg(d, a, lambda r: r["score"]["identity_valid"]).mean() for a in arms]
    sc = [agg(d, a, lambda r: r["score"]["success"]).mean() for a in arms]
    ax[2].bar(x - 0.22, tk, width=0.2, color=C_MUTE, label="task met")
    ax[2].bar(x, iv, width=0.2, color=C_OK, label="identity valid")
    ax[2].bar(x + 0.22, sc, width=0.2, color=C_BENCH, label="conjunctive")
    ax[2].set_ylabel("fraction of episodes"); ax[2].set_title("task vs identity\n(fixed K)", fontsize=8)
    ax[2].legend(frameon=False, fontsize=6)

    mAm = [agg(dm, a, lambda r: r["mean_actuators"]).mean() for a in arms]
    mAk = [agg(dk, a, lambda r: r["mean_actuators"]).mean() for a in arms]
    ax[3].bar(x - 0.18, mAm, width=0.32, color=cols, alpha=0.45, label="matched")
    ax[3].bar(x + 0.18, mAk, width=0.32, color=cols, label="fixed K")
    ax[3].set_ylabel("mean actuators"); ax[3].set_title("spend, both conventions", fontsize=8)
    ax[3].legend(frameon=False, fontsize=6)

    for a in ax:
        a.set_xticks(x)
        a.set_xticklabels([lbl[k] for k in arms], fontsize=6, rotation=45, ha="right")
    fig.tight_layout()
    save(fig, "fig_6_10_5_arms")


# ------------------------------------------------------------ Fig 6.10-6 ----
def fig6_release():
    """Part K: control off. Held heading, or snap-back?"""
    d = load_json(DATA_DIR / "release__fixedk.json")
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.8))
    ret = {}
    for ep in d["episodes"]:
        for arm, r in ep["arms"].items():
            ax[0].plot(range(len(r["H_trace"])), r["H_trace"], lw=0.8, alpha=0.55,
                       color=C_ADAPT if arm == "adaptive_causal" else C_MUTE)
            ret.setdefault(arm, []).append(r["retention"])
    ax[0].set_xlabel("free steps after control off")
    ax[0].set_ylabel(r"$H^*(I_t,t)$"); ax[0].set_title("Part K  release")
    ax[0].axhline(0.25, color="k", lw=0.6, ls=":")
    if ret:
        names = list(ret)
        ax[1].bar(range(len(names)), [np.mean(ret[a]) for a in names],
                  color=[C_ADAPT if a == "adaptive_causal" else C_MUTE for a in names],
                  width=0.6)
        ax[1].set_xticks(range(len(names)))
        ax[1].set_xticklabels(names, fontsize=6, rotation=45, ha="right")
        ax[1].axhline(1.0, color="k", lw=0.6, ls="--")
        ax[1].set_ylabel("retention  $H_{end}/H_{release}$")
        ax[1].set_title("held, or snapped back?")
    fig.tight_layout()
    save(fig, "fig_6_10_6_release")


FIGS = dict(audit=fig1_audit, regime=fig2_regime, thingness=fig3_thingness,
            controllability=fig4_controllability, arms=fig5_arms,
            release=fig6_release)

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    for k in want:
        FIGS[k]()
