"""Part I: mechanism-audit figures."""
from __future__ import annotations

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import ROOT, AUDIT_DIR, load_canonical
from flock_sim.lattice import bird_to_rowcol

FIG_DIR = AUDIT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
L = 10


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def fig_A_three_interfaces():
    c = load_canonical()
    I0 = c["I0"]
    ds = json.load(open(AUDIT_DIR / "data" / "dynamical_shell.json"))
    B_D0, B_F0 = np.array(ds["B_D0"]), np.array(ds["B_F0"])
    other = np.setdiff1d(np.arange(100), np.union1d(I0, B_D0))

    fig, ax = plt.subplots(figsize=(7, 7))
    row_o, col_o = bird_to_rowcol(other, L)
    row_i, col_i = bird_to_rowcol(I0, L)
    row_d, col_d = bird_to_rowcol(B_D0, L)
    row_f, col_f = bird_to_rowcol(B_F0, L)
    ax.scatter(col_o, row_o, c="#dddddd", s=140, marker="s", label=f"other exterior E (n={len(other)})")
    ax.scatter(col_d, row_d, c="#4c72b0", s=180, marker="s", label=f"dynamical shell B^D_0 (n={len(B_D0)})")
    ax.scatter(col_i, row_i, c="#333333", s=220, marker="s", label=f"frozen core I0 (n={len(I0)})")
    ax.scatter(col_f, row_f, facecolors="none", edgecolors="#c44e52", s=380, linewidths=3,
               marker="o", label=f"Fiedler boundary B^F_0 (n={len(B_F0)})")
    ax.invert_yaxis()
    ax.set_xlim(-1, L); ax.set_ylim(L, -1)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Three interfaces on the canonical flock (seed 2, t0=41)\n"
                 "B^F_0 (red rings) is a small subset of B^D_0 (blue); most of B^D_0 is unmarked by spectral analysis")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    savefig(fig, "audit_figA_three_interfaces")


def fig_B_overlap_ensemble():
    bc = json.load(open(AUDIT_DIR / "data" / "boundary_compare.json"))
    rows = bc["baseline_ensemble_overlap"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    sizes_F = [r["size_B_F0"] for r in rows]
    sizes_D = [r["size_B_D0"] for r in rows]
    jacc = [r["jaccard"] for r in rows]
    gap = [r["eigengap"] for r in rows]
    axes[0].scatter(sizes_D, sizes_F, s=60, c="#4c72b0")
    for r in rows:
        axes[0].annotate(f"s{r['seed']}", (r["size_B_D0"], r["size_B_F0"]), fontsize=7,
                          xytext=(3, 3), textcoords="offset points")
    axes[0].set_xlabel("|B^D_0| (dynamical shell size)")
    axes[0].set_ylabel("|B^F_0| (Fiedler boundary size)")
    axes[0].set_title("Boundary size: spectral vs. dynamical")
    axes[1].scatter(gap, jacc, s=60, c="#c44e52")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("eigengap (log scale)")
    axes[1].set_ylabel("Jaccard(B^F_0, B^D_0)")
    axes[1].set_title(f"Overlap vs. eigengap (n={len(rows)} qualifying flocks)")
    fig.suptitle("Spectral vs. dynamical boundary across independently emergent flocks")
    savefig(fig, "audit_figB_spectral_vs_dynamical_ensemble")


def fig_C_response_vs_distance():
    bc = json.load(open(AUDIT_DIR / "data" / "boundary_compare.json"))
    rows = bc["response_by_distance"]
    dist = np.array([r["dynamical_distance"] for r in rows])
    resp = np.array([r["mean_Hstar_end"] for r in rows])
    in_bf = np.array([r["in_B_F0"] for r in rows])
    in_bd = np.array([r["in_B_D0"] for r in rows])

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(dist[~in_bd], resp[~in_bd], c="#dddddd", s=50, label="other exterior")
    ax.scatter(dist[in_bd & ~in_bf], resp[in_bd & ~in_bf], c="#4c72b0", s=70, label="in B^D_0")
    ax.scatter(dist[in_bf], resp[in_bf], c="#c44e52", s=110, marker="*", label="in B^F_0 (spectral boundary)")
    ax.set_xlabel("graph distance to I0 (static lattice, hops)")
    ax.set_ylabel("single-actuator mean H*(t0+Tu)  (k=1 exhaustive, n=50/bird)")
    ax.set_title(f"Single-actuator control response vs. dynamical distance\n"
                 f"Spearman(response, distance) = {bc['spearman_response_vs_distance']:.2f}")
    ax.legend(fontsize=9)
    savefig(fig, "audit_figC_response_vs_distance")


def fig_D_feasibility_ladder():
    fl = json.load(open(AUDIT_DIR / "data" / "feasibility_ladder.json"))
    arms = fl["arms"]
    order = ["D0_baseline_empty", "D2_fiedler_boundary_BF0", "D3_D4_dynamical_shell_BD0", "D5_all_non_core", "D1_full_interior_I0"]
    labels = ["D0 baseline\n(0 birds)", "D2 Fiedler\nboundary (2)", "D3/D4 dynamical\nshell (12)",
              "D5 all\nnon-core (80)", "D1 full core\n(20, inadmissible)"]
    mean_end = [arms[a]["mean_Hstar_end"] for a in order]
    p_success = [arms[a]["p_success"] for a in order]
    p_both = [arms[a]["p_success_and_integrity"] for a in order]

    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(9, 5.2))
    w = 0.26
    ax.bar(x - w, mean_end, width=w, label="mean H*(t0+Tu)", color="#4c72b0")
    ax.bar(x, p_success, width=w, label="P(success)  H*>=0.8", color="#55a868")
    ax.bar(x + w, p_both, width=w, label="P(success & integrity)", color="#c44e52")
    ax.axhline(0.8, ls="--", c="gray", lw=1, label="success threshold")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylim(0, 1.05)
    ax.set_title("Part D: external feasibility ladder (canonical flock, n=50 replicates/arm)")
    ax.legend(fontsize=8, loc="upper left")
    savefig(fig, "audit_figD_feasibility_ladder")


def fig_E_pair_synergy():
    ps = json.load(open(AUDIT_DIR / "data" / "pair_synergy.json"))
    rows = ps["all_pairs"]
    R = np.array([r["R_ij"] for r in rows])
    S = np.array([r["S_ij"] for r in rows])
    both_bd = np.array([r["both_in_B_D0"] for r in rows])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    axes[0].hist(R, bins=40, color="#4c72b0")
    axes[0].axvline(0.8, ls="--", c="red", label="success threshold")
    axes[0].set_xlabel("R_ij = mean H*(t0+Tu)")
    axes[0].set_ylabel("count (of 3160 pairs)")
    axes[0].set_title(f"Distribution of all-pairs response (n={ps['n_replicates']} reps/pair)")
    axes[0].legend(fontsize=8)

    axes[1].scatter(R[~both_bd], S[~both_bd], s=10, alpha=0.4, c="#dddddd", label="not both in B^D_0")
    axes[1].scatter(R[both_bd], S[both_bd], s=16, alpha=0.7, c="#4c72b0", label="both in B^D_0")
    axes[1].set_xlabel("R_ij"); axes[1].set_ylabel("S_ij (control-response synergy)")
    axes[1].set_title("Pair response vs. synergy")
    axes[1].legend(fontsize=8)
    fig.suptitle("Part E: exhaustive pair-synergy audit (all C(80,2)=3160 non-core pairs)")
    savefig(fig, "audit_figE_pair_synergy")


def fig_F_core_resistance():
    cr = json.load(open(AUDIT_DIR / "data" / "core_resistance.json"))
    rows = cr["rows"]
    k = [r["k"] for r in rows]
    by_deg = [r["mean_Hstar_end_by_degree"] for r in rows]
    rand = [r["mean_Hstar_end_random"] for r in rows]
    rand_std = [r["std_Hstar_end_random"] for r in rows]
    rel_deg = [r["mean_Hstar_release_by_degree"] for r in rows]

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.plot(k, by_deg, "o-", label="by internal degree (end of control)", color="#4c72b0")
    ax.errorbar(k, rand, yerr=rand_std, fmt="s--", label="random subset (end of control)", color="#55a868")
    ax.plot(k, rel_deg, "^:", label="by internal degree (post-release)", color="#c44e52")
    ax.set_xlabel("k = number of DIRECTLY forced interior (I0) birds")
    ax.set_ylabel("mean H*")
    ax.set_title("Part F: direct-core resistance curve (mechanistic diagnostic, NOT admissible control)")
    ax.legend(fontsize=8)
    savefig(fig, "audit_figF_core_resistance")


def fig_H_predictive_screening():
    ps = json.load(open(AUDIT_DIR / "data" / "predictive_screening.json"))
    fig, ax = plt.subplots(figsize=(6, 5))
    names = ["M_full\n(ground truth)", "M_BD\n(B^D_0, 12 birds)", "M_BF\n(B^F_0, 2 birds)"]
    vals = [ps["mean_logloss_full"], ps["mean_logloss_BD"], ps["mean_logloss_BF"]]
    colors = ["#333333", "#4c72b0", "#c44e52"]
    ax.bar(names, vals, color=colors)
    ax.set_ylabel("mean one-step-ahead log-loss (nats), core birds")
    ax.set_title("Part H: predictive screening -- does B^F screen I0's future\nstate as well as B^D?"
                 f"\n(n={ps['n_samples']} bird-samples; excess BF-full = {ps['excess_logloss_BF_minus_full']:.3f} nats)")
    for i, v in enumerate(vals):
        ax.text(i, v + 0.002, f"{v:.4f}", ha="center", fontsize=9)
    savefig(fig, "audit_figH_predictive_screening")


def fig_G_parameter_sensitivity():
    gp = json.load(open(AUDIT_DIR / "data" / "parameter_sensitivity.json"))
    regimes = list(gp.keys())
    qual = [gp[r]["from_scratch_baseline"]["qualification_rate"] for r in regimes]
    phi30 = [gp[r]["from_scratch_baseline"]["mean_phi_at_t30"] for r in regimes]
    bd_p = [gp[r]["ceteris_paribus_on_canonical"]["B_D0_p_success"] for r in regimes]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
    axes[0].bar(regimes, qual, color=["#4c72b0", "#c44e52"])
    axes[0].set_title("Flock-selection qualification rate\n(n=50 seeds)")
    axes[0].set_ylim(0, 1)
    axes[1].bar(regimes, phi30, color=["#4c72b0", "#c44e52"])
    axes[1].set_title("Mean polarization Phi at t=30")
    axes[1].set_ylim(0, 1)
    axes[2].bar(regimes, bd_p, color=["#4c72b0", "#c44e52"])
    axes[2].set_title("B^D_0 control P(success)\n(canonical IC, ceteris paribus)")
    axes[2].set_ylim(0, 1)
    for ax in axes:
        ax.tick_params(axis="x", labelsize=8, rotation=15)
    fig.suptitle("Part G: code_default (rho=15,omega=3) vs. manuscript_all_ones (rho=1,omega=1)")
    savefig(fig, "audit_figG_parameter_sensitivity")


def main():
    fig_A_three_interfaces()
    fig_B_overlap_ensemble()
    fig_C_response_vs_distance()
    fig_D_feasibility_ladder()
    fig_E_pair_synergy()
    fig_F_core_resistance()
    fig_G_parameter_sensitivity()
    fig_H_predictive_screening()
    print("All mechanism-audit figures written to", FIG_DIR)


if __name__ == "__main__":
    main()
