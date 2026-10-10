"""Part 5: V3 figures. Follows the existing Agg-backend, data-driven,
PNG+PDF convention from v1_mechanism_audit/code/make_figures.py and
v2_interface_control/code/make_v2_figures.py -- reads only from data/,
never re-runs the simulator (fig R3/R6 reproduce ONE illustrative trajectory
directly from the frozen actuator set, matching the existing project's own
precedent in python/figures/fig5_8_steering.py)."""
from __future__ import annotations

import json

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow

from common_v3 import V3_DIR, load_dev_flocks, dynamical_shell, run_simulation, make_pulse, T_U, T_R
from flock_sim.lattice import bird_to_rowcol
from flock_sim.model import UV4
from selection_rules_v3 import min_actuators_for_multicover, q_coverage_fraction

FIG_DIR = V3_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
FROZEN_Q, FROZEN_GAMMA = 2, 0.5


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def fig_r1(sweep):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    rule_colors = {"R_random": "#8172b2", "DEG_degree": "#4c72b0", "LEV_leverage": "#55a868",
                   "COVER_greedy": "#dd8452", "PATCH_patch": "#c44e52"}
    for ax, xkey, xlabel in zip(axes, ["f_A", "Gamma", "mean_m"],
                                 [r"$f_A = |A|/|B^D_0|$", r"$\Gamma(A)$ (core coverage)",
                                  r"mean multiplicity $\bar{m}$"]):
        for fl in sweep["flocks"]:
            for c in fl["conditions"]:
                ax.scatter(c[xkey], c["p_success"], s=14, alpha=0.35, color=rule_colors[c["rule"]])
        ax.set_xlabel(xlabel)
        ax.set_ylabel("P(success)" if xkey == "f_A" else "")
        ax.set_ylim(-0.03, 1.05)
        ax.axhline(0.8, ls="--", c="gray", lw=0.8)
    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=8, label=r)
               for r, c in rule_colors.items()]
    axes[1].legend(handles=handles, fontsize=8, loc="lower right", ncol=1)
    fig.suptitle("R1 — success vs. actuator fraction, core coverage, and mean multiplicity\n"
                 r"(10 dev flocks x 5 rules x 10 fractions x 20 reps; $\bar m$ is the strongest single predictor, "
                 r"$\Gamma$ the weakest — see RESULTS_V3.md)")
    savefig(fig, "R1_coverage_predicts_control")


def fig_r2(sweep):
    """Same budget, different spatial distribution: COVER/DEG/R (distributed)
    vs PATCH (connected), at the fraction closest to the frozen V3 budget."""
    target_f = 0.5
    fig, ax = plt.subplots(figsize=(8, 5.5))
    rule_order = ["PATCH_patch", "R_random", "DEG_degree", "LEV_leverage", "COVER_greedy"]
    colors = {"PATCH_patch": "#c44e52", "R_random": "#8172b2", "DEG_degree": "#4c72b0",
              "LEV_leverage": "#55a868", "COVER_greedy": "#dd8452"}
    data_by_rule = {r: [] for r in rule_order}
    for fl in sweep["flocks"]:
        by_f = {c["f_A_target"]: c for c in fl["conditions"]}
        c = by_f.get(target_f)
        if c is None:
            continue
    for fl in sweep["flocks"]:
        conds = [c for c in fl["conditions"] if c["f_A_target"] == target_f]
        for c in conds:
            data_by_rule[c["rule"]].append(c["p_success"])
    for i, r in enumerate(rule_order):
        vals = data_by_rule[r]
        ax.scatter([i] * len(vals), vals, color=colors[r], alpha=0.7, zorder=3, s=40)
        ax.scatter([i], [np.mean(vals)], color="black", marker="_", s=500, zorder=4)
    ax.set_xticks(range(len(rule_order)))
    ax.set_xticklabels(rule_order, rotation=15)
    ax.set_ylabel("P(success) per flock (dots), mean (black bar)")
    ax.set_title(f"R2 — same actuator budget (f_A={target_f}), different spatial distribution\n"
                 "connected patch (red) is the weakest and most variable; distributed rules cluster higher")
    ax.set_ylim(-0.03, 1.05)
    savefig(fig, "R2_distributed_vs_patch")


def draw_lattice(ax, lattice, I0, B_D0, actuators, title, z=None, h_star=None):
    L = lattice.L
    all_ids = np.arange(lattice.nn)
    rows, cols = bird_to_rowcol(all_ids, L)
    role_color = np.full(lattice.nn, "#d9d9d9", dtype=object)
    role_color[B_D0] = "#f4b183"
    role_color[I0] = "#8fb9e8"
    A_set = set(int(a) for a in actuators)
    for a in A_set:
        role_color[a] = "#c44e52"
    ax.scatter(cols, rows, c=list(role_color), s=180, edgecolors="black", linewidths=0.4, zorder=2)
    if z is not None:
        vecs = UV4[z]
        ax.quiver(cols, rows, vecs[:, 0], vecs[:, 1], angles="xy", scale_units="xy", scale=2.2,
                  width=0.006, zorder=3, color="black")
    ax.set_xlim(-1, L)
    ax.set_ylim(-1, L)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])


def fig_r3(dev_flocks_by_seed, seed=2):
    fl = dev_flocks_by_seed[seed]
    lattice, I0, z_t0 = fl["lattice"], fl["I0"], fl["z_t0"]
    B_D0 = dynamical_shell(lattice, I0)
    A = min_actuators_for_multicover(B_D0, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA)
    gamma_ach = q_coverage_fraction(A, I0, lattice, FROZEN_Q)

    fig, ax = plt.subplots(figsize=(7, 7))
    draw_lattice(ax, lattice, I0, B_D0, A,
                 f"R3 — minimal sufficient interface (seed {seed})\n"
                 f"|I0|={len(I0)} |B^D_0|={len(B_D0)}  |A|={len(A)} (f_A={len(A)/len(B_D0):.2f})  "
                 f"double-coverage achieved={gamma_ach:.2f}", z=z_t0)
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#8fb9e8", markersize=12, label="core I0"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#f4b183", markersize=12, label="shell B^D_0 (unselected)"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#c44e52", markersize=12, label="selected actuator (in A)"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#d9d9d9", markersize=12, label="ordinary exterior"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2, fontsize=8)
    savefig(fig, "R3_minimal_sufficient_interface")


def fig_r4(staged, seed=3):
    fl = next(f for f in staged["flocks"] if f["seed"] == seed)
    fig, axes = plt.subplots(1, 1, figsize=(8, 5.5))
    colors = {"pulse": "#333333", "ramp_up": "#4c72b0", "sequential_sectors": "#55a868", "ramp_down": "#c44e52"}
    for kind, m in fl["schedules"].items():
        coh = m["coh_traj_mean_over_reps"]
        axes.plot(range(len(coh)), coh, label=f"{kind} (p_succ={m['p_success']:.2f}, effort={m['mean_control_effort']:.0f})",
                  color=colors[kind], lw=2)
    axes.axhline(0.8, ls="--", c="gray", lw=0.8, label="c_recover = 0.8")
    axes.set_xlabel("timestep (control window)")
    axes.set_ylabel(r"mean $C_{I_0}(t)$ across replicates")
    axes.set_title(f"R4 — transition-aware integrity: schedule comparison (seed {seed})\n"
                   "mean-min-coherence is essentially schedule-invariant; success tracks total control effort")
    axes.legend(fontsize=8, loc="lower right")
    axes.set_ylim(0.4, 1.05)
    savefig(fig, "R4_transition_aware_integrity")


def fig_r6(dev_flocks_by_seed, seed=3):
    fl = dev_flocks_by_seed[seed]
    lattice, I0, z_t0, h_star = fl["lattice"], fl["I0"], fl["z_t0"], fl["h_star"]
    B_D0 = dynamical_shell(lattice, I0)
    A = min_actuators_for_multicover(B_D0, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA)
    interventions = make_pulse(A, h_star, t0=0, t_u=T_U)
    res = run_simulation(nn=lattice.nn, nt=T_U + T_R, seed=999_111, init_z=z_t0,
                          interventions=interventions, lattice=lattice)

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    snaps = [(0, "before (t=0, control starts)"), (T_U, f"during->end of control (t={T_U})"),
             (T_U + T_R, f"after release (t={T_U + T_R})")]
    for ax, (t, label) in zip(axes, snaps):
        draw_lattice(ax, lattice, I0, B_D0, A if t <= T_U else [], label, z=res.z_hist[t])
    fig.suptitle(f"R6 — final control story (seed {seed}, frozen V3 controller, q=2/gamma=0.5)")
    savefig(fig, "R6_final_control_story")


def fig_r5(pp):
    taus = list(range(1, pp["tau_max"] + 1))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    colors = plt.cm.tab10(np.linspace(0, 1, len(pp["flocks"])))
    for fl, col in zip(pp["flocks"], colors):
        bd = [fl["predictive_permeability_B_D0"][str(t)]["excess_logloss"] for t in taus]
        bf = [fl["predictive_permeability_B_F0"][str(t)]["excess_logloss"] for t in taus]
        ax.plot(taus, bd, color=col, ls="-", marker="o", ms=4, label=f"seed {fl['seed']}: B^D")
        ax.plot(taus, bf, color=col, ls="--", marker="s", ms=4, label=f"seed {fl['seed']}: B^F")
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel(r"horizon $\tau$")
    ax.set_ylabel("excess log-loss (nats/bird-step)")
    ax.set_title("per-flock predictive leakage vs. horizon\n(solid=B^D, dashed=B^F)")
    ax.legend(fontsize=6.5, ncol=2, loc="upper left")
    ax.set_ylim(-0.03, 0.22)
    ax.annotate("seed 13 B^F, tau=1 = 0.353\n(off-scale; tiny |B^F|=3 shell)", xy=(1.05, 0.10), xytext=(3.3, 0.205),
                fontsize=8, color="#0b6e75", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#0b6e75", lw=1.3))

    ax = axes[1]
    pooled_bd, pooled_bf = [], []
    for t in taus:
        bd_num = sum(fl["predictive_permeability_B_D0"][str(t)]["excess_logloss"] * fl["predictive_permeability_B_D0"][str(t)]["n_samples"] for fl in pp["flocks"])
        bd_den = sum(fl["predictive_permeability_B_D0"][str(t)]["n_samples"] for fl in pp["flocks"])
        bf_num = sum(fl["predictive_permeability_B_F0"][str(t)]["excess_logloss"] * fl["predictive_permeability_B_F0"][str(t)]["n_samples"] for fl in pp["flocks"])
        bf_den = sum(fl["predictive_permeability_B_F0"][str(t)]["n_samples"] for fl in pp["flocks"])
        pooled_bd.append(bd_num / bd_den)
        pooled_bf.append(bf_num / bf_den)
    ax.plot(taus, pooled_bd, color="#dd8452", marker="o", lw=2.5, label=r"$B^D$ (dynamical shell)")
    ax.plot(taus, pooled_bf, color="#d4a72c", marker="s", lw=2.5, label=r"$B^F$ (Fiedler boundary)")
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel(r"horizon $\tau$")
    ax.set_ylabel("pooled excess log-loss (nats/bird-step)")
    ax.set_title(r"$B^D$: exact at $\tau$=1, grows with horizon (E→B→I propagation)."
                 "\n" r"$B^F$ leaks MORE at every horizon tested.")
    ax.legend(fontsize=9)

    fig.suptitle("R5 — predictive permeability vs. horizon (4 dev flocks: seeds 2, 3, 8, 13)")
    savefig(fig, "R5_predictive_permeability")


def main():
    sweep = json.load(open(V3_DIR / "data" / "coverage_sweep.json"))
    staged = json.load(open(V3_DIR / "data" / "staged_actuation.json"))
    dev_flocks_by_seed = {fl["seed"]: fl for fl in load_dev_flocks()}

    fig_r1(sweep)
    fig_r2(sweep)
    fig_r3(dev_flocks_by_seed, seed=13)
    fig_r4(staged, seed=3)
    fig_r6(dev_flocks_by_seed, seed=3)

    pp_path = V3_DIR / "data" / "predictive_permeability.json"
    if pp_path.exists():
        fig_r5(json.load(open(pp_path)))
        print("Wrote R1, R2, R3, R4, R5, R6 to", FIG_DIR)
    else:
        print("Wrote R1, R2, R3, R4, R6 to", FIG_DIR, "(R5 skipped -- predictive_permeability.json not found)")


if __name__ == "__main__":
    main()
