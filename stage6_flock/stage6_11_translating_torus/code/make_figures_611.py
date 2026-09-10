"""Stage 6.11 figures. EVALUATION-SIDE: reads only frozen JSON/npz in data/.

Nothing here recomputes a scientific quantity; if a panel needs a number,
that number is already in a data file written by the run that established it.
"""
from __future__ import annotations

import json

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from common_611 import DATA_DIR, FIG_DIR, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, R_SECONDARY, V_SECONDARY, COHESION_SECONDARY

plt.rcParams.update({"figure.dpi": 130, "font.size": 8, "axes.titlesize": 9,
                     "axes.labelsize": 8, "legend.fontsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False})

C_MESO, C_GLOBAL, C_DISORDER = "#3f7d3f", "#a83232", "#8a8a8a"
C_PRIMARY, C_SECONDARY = "#1a1a1a", "#3b6ea5"


def load_json(path):
    return json.loads(path.read_text())


def save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("wrote", FIG_DIR / f"{name}.png")


# ------------------------------------------------------------ Fig 6.11-1 ----
def fig1_phase_map():
    """Section O coarse dev screen: mesoscopic-episode fraction over (R, v),
    one panel per cohesion value, with the selected primary/secondary
    regimes marked. Global-collapse probability was 0.00 in every cell (see
    logs/regime_selection_predeclared_611.txt addendum); disorder is read
    off mean_policy_saturation ~ 0 with meso_frac ~ 0 (e.g. cohesion=0 at
    small R -- fragmentation, not global order)."""
    d = load_json(DATA_DIR / "phase_scan_611__stage_a.json")
    cells = d["cells"]
    Rs = sorted(set(c["R"] for c in cells))
    vs = sorted(set(c["v"] for c in cells))
    cohesions = sorted(set(c["cohesion"] for c in cells))

    fig, axes = plt.subplots(1, len(cohesions), figsize=(3.6 * len(cohesions), 3.0), sharey=True)
    for ax, coh in zip(axes, cohesions):
        grid = np.full((len(vs), len(Rs)), np.nan)
        for c in cells:
            if c["cohesion"] != coh:
                continue
            i, j = vs.index(c["v"]), Rs.index(c["R"])
            grid[i, j] = c["mesoscopic_episode_fraction"]
        im = ax.imshow(grid, origin="lower", vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
        ax.set_xticks(range(len(Rs))); ax.set_xticklabels(Rs)
        ax.set_yticks(range(len(vs))); ax.set_yticklabels(vs)
        ax.set_xlabel("R (interaction radius)")
        if ax is axes[0]:
            ax.set_ylabel("v (speed)")
        ax.set_title(f"cohesion={coh}")
        if coh == COHESION_PRIMARY and R_PRIMARY in Rs and V_PRIMARY in vs:
            ax.add_patch(Circle((Rs.index(R_PRIMARY), vs.index(V_PRIMARY)), 0.32,
                                 fill=False, edgecolor=C_PRIMARY, linewidth=2))
            ax.annotate("primary", (Rs.index(R_PRIMARY), vs.index(V_PRIMARY)), color=C_PRIMARY,
                        fontsize=6, xytext=(6, 6), textcoords="offset points", weight="bold")
        if coh == COHESION_SECONDARY and R_SECONDARY in Rs and V_SECONDARY in vs:
            ax.add_patch(Circle((Rs.index(R_SECONDARY), vs.index(V_SECONDARY)), 0.32,
                                 fill=False, edgecolor=C_SECONDARY, linewidth=2, linestyle="--"))
            ax.annotate("secondary", (Rs.index(R_SECONDARY), vs.index(V_SECONDARY)), color=C_SECONDARY,
                        fontsize=6, xytext=(6, -12), textcoords="offset points", weight="bold")
    fig.colorbar(im, ax=axes, shrink=0.85, label="mesoscopic episode fraction (dev screen)")
    fig.suptitle("Fig 6.11-1  Phase map: disorder / mesoscopic / global-collapse regimes "
                 "(global-collapse probability = 0.00 in every cell)", fontsize=8.5, y=1.04)
    save(fig, "fig_6_11_1_phase_map")


# ------------------------------------------------------------ Fig 6.11-2 ----
def fig2_emergence_and_lineage():
    """Item 20's emergence-and-lineage figure: one uncontrolled episode's
    tracked-domain size and translation-aligned functional similarity over
    time, from the world-selection held-out confirmation data."""
    path = DATA_DIR / f"phase_scan_611__stage_b_R{R_PRIMARY}_v{V_PRIMARY}_c{COHESION_PRIMARY}.json"
    if not path.exists():
        print("  fig2: held-out confirmation data not found, skipping")
        return
    d = load_json(path)
    ep = d["cell"]["episodes"][0]
    qualifying = [r for r in ep["domain_records"] if r["qualifies"]]
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.6))
    durations = [r["duration"] for r in ep["domain_records"] if r["duration"] >= 3]
    ax[0].hist(durations, bins=20, color=C_MESO, alpha=0.8)
    ax[0].axvline(30, color=C_DISORDER, linestyle="--", linewidth=1, label="qualifying threshold")
    ax[0].set_xlabel("tracked domain duration (steps)")
    ax[0].set_ylabel("count")
    ax[0].set_title("domain lifetimes, one held-out episode")
    ax[0].legend()

    disp = [r["displacement_in_R"] for r in ep["domain_records"] if r["duration"] >= 3]
    dur2 = [r["duration"] for r in ep["domain_records"] if r["duration"] >= 3]
    colors = [C_MESO if r["qualifies"] else C_DISORDER for r in ep["domain_records"] if r["duration"] >= 3]
    ax[1].scatter(dur2, disp, c=colors, s=14, alpha=0.7)
    ax[1].axhline(3.0, color=C_GLOBAL, linestyle=":", linewidth=1, label="3R (several interaction lengths)")
    ax[1].set_xlabel("duration (steps)")
    ax[1].set_ylabel("net displacement / R")
    ax[1].set_title("translation vs persistence (green = qualifying)")
    ax[1].legend(fontsize=6)
    fig.suptitle("Fig 6.11-2  Spontaneous emergence: domain persistence and translation "
                 "(primary regime, held-out episode)", fontsize=8.5, y=1.05)
    save(fig, "fig_6_11_2_emergence_and_lineage")


# ------------------------------------------------------------ Fig 6.11-3 ----
def fig3_predictive_vs_causal():
    """Item 12: B^pred vs B^causal vs B^C are different sets. Shows the
    certified predictive boundary's construction trace and, where available,
    the causal budget-sensitivity result, side by side."""
    pb_path = DATA_DIR / "predictive_boundary_611.json"
    if not pb_path.exists():
        print("  fig3: predictive_boundary_611.json not found, skipping")
        return
    pb = load_json(pb_path)
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.8))

    for key, color, label in (("M_obs_12", "#3b6ea5", "M_obs=12"), ("M_obs_20", "#e08a2e", "M_obs=20")):
        if key not in pb or "boundary" not in pb[key]:
            continue
        trace = pb[key]["boundary"]["trace"]
        steps = [t["step"] for t in trace]
        losses = [t["mean_logloss"] for t in trace]
        ax[0].plot(steps, losses, "-o", color=color, markersize=3, label=label)
        ax[0].axhline(pb[key]["boundary"]["full_pool_loss"], color=color, linestyle=":", linewidth=1)
    ax[0].set_xlabel("greedy construction step")
    ax[0].set_ylabel("mean held-out log-loss")
    ax[0].set_title("B^pred construction (dotted = full-pool oracle)")
    ax[0].legend()

    cb_path = DATA_DIR / "causal_budget_sensitivity_611.json"
    if cb_path.exists():
        cb = load_json(cb_path)
        keys = list(cb.keys())
        sizes = [cb[k]["n_B_causal"] for k in keys]
        widths = [cb[k]["mean_ci_width"] for k in keys]
        x = range(len(keys))
        ax2 = ax[1]
        ax2.bar(x, sizes, color="#3b6ea5", alpha=0.7, label="|B_causal|")
        ax2.set_xticks(x); ax2.set_xticklabels([cb[k]["rollouts"] for k in keys])
        ax2.set_xlabel("probe rollouts per repeat (x3 repeats)")
        ax2.set_ylabel("|B_causal|")
        ax2b = ax2.twinx()
        ax2b.plot(x, widths, "o-", color="#a83232", label="mean CI width")
        ax2b.set_ylabel("mean bootstrap CI width", color="#a83232")
        ax2.set_title("B^causal budget sensitivity")
    else:
        ax[1].text(0.5, 0.5, "budget sensitivity\nnot yet run", ha="center", va="center",
                   transform=ax[1].transAxes, color=C_DISORDER)
    fig.suptitle("Fig 6.11-3  Predictive interface (B^pred) vs causal interface (B^causal): "
                 "distinct constructions", fontsize=8.5, y=1.05)
    save(fig, "fig_6_11_3_predictive_vs_causal")


# ------------------------------------------------------------ Fig 6.11-4 ----
def fig4_turn_and_release(seed=501):
    """Item 20: adaptive-turn-and-release figure, from run_online_control_611.py's
    output. seed=501 is a SUCCESS case (3/5 online seeds turned and persisted
    through release, see RESULTS_6_11.md for the full 5-seed table -- this
    figure illustrates the phenomenon, not "the" typical outcome)."""
    path = DATA_DIR / f"online_control_611__seed{seed}.json"
    if not path.exists():
        print(f"  fig4: online_control_611__seed{seed}.json not found, skipping")
        return
    d = load_json(path)
    log = d["log"]
    control = [e for e in log if e["event"] == "control_step"]
    release = [e for e in log if e["event"] == "release_step"]
    if not control:
        print("  fig4: no control phase reached, skipping")
        return

    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.8))
    t_c = [e["t"] for e in control]
    f_c = [e["frac_interior_at_target"] for e in control]
    t_r = [e["t"] for e in release]
    f_r = [e["frac_interior_at_target"] for e in release]
    ax[0].plot(t_c, f_c, "-o", color="#3b6ea5", markersize=3, label="control (forced)")
    if t_r:
        ax[0].plot(t_r, f_r, "-o", color="#e08a2e", markersize=3, label="release (unforced)")
        ax[0].axvline(t_r[0], color=C_DISORDER, linestyle="--", linewidth=1)
    ax[0].axhline(0.25, color=C_DISORDER, linestyle=":", linewidth=1, label="chance (4 headings)")
    ax[0].set_xlabel("t"); ax[0].set_ylabel("fraction of interior at target heading")
    ax[0].set_title("turn (forced) then release (unforced)")
    ax[0].legend(fontsize=6)

    sizes_c = [e["interior_size"] for e in control]
    sizes_r = [e["interior_size"] for e in release]
    ax[1].plot(t_c, sizes_c, "-o", color="#3b6ea5", markersize=3, label="control")
    if t_r:
        ax[1].plot(t_r, sizes_r, "-o", color="#e08a2e", markersize=3, label="release")
        ax[1].axvline(t_r[0], color=C_DISORDER, linestyle="--", linewidth=1)
    ax[1].set_xlabel("t"); ax[1].set_ylabel("interior (dominant hypothesis) size")
    ax[1].set_title("identity persistence through release")
    ax[1].legend(fontsize=6)
    fig.suptitle("Fig 6.11-4  Adaptive turn and release", fontsize=8.5, y=1.05)
    save(fig, "fig_6_11_4_turn_and_release")


if __name__ == "__main__":
    fig1_phase_map()
    fig2_emergence_and_lineage()
    fig3_predictive_vs_causal()
    fig4_turn_and_release()
