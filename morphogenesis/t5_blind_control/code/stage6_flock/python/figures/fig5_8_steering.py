"""Figures 5-8: before/during/after snapshots, steering trajectory, sparse-
control requirement (k sweep), and release comparison. Given the Phase 5
result is negative (sparse control did not succeed), these figures honestly
depict the failure mode rather than a successful steering trajectory."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flock_sim.lattice import Lattice, bird_to_rowcol
from flock_sim.simulation import run_simulation
from flock_sim.interventions import make_pulse
from flock_sim.metrics import target_heading_fraction, coherence

T_U = 20
T_R = 20
N_REPLICATES = 50
BASE_SEED_OFFSET = 100_000
UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])


def load():
    d = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    rm = json.load(open(d / "phase4_5_response_map.json"))
    greedy = json.load(open(d / "phase5_greedy_k.json"))
    k2 = json.load(open(d / "phase5_k2_search.json"))
    meta = json.load(open(d / "canonical_snapshot_meta.json"))
    data = np.load(d / "canonical_snapshot.npz")
    return rm, greedy, k2, meta, data


def main():
    rm, greedy, k2, meta, data = load()
    I0 = np.array(rm["I0"])
    h_star = rm["h_star"]
    t0 = meta["t0"]
    z_t0 = data["z_hist_full"][t0]
    lattice = Lattice(nn=100, nh=8)
    L = 10
    fig_dir = Path(__file__).resolve().parents[2] / "figures"

    best_actuators = greedy["history"][-1]["actuators"]  # best-found sparse set (k=6)
    seed_demo = BASE_SEED_OFFSET  # single representative replicate for the snapshot figure

    # Run one representative trajectory: sparse-control arm and no-control arm
    interventions = make_pulse(best_actuators, h_star, t0=0, t_u=T_U)
    res_ctrl = run_simulation(nn=100, nt=T_U + T_R, seed=seed_demo, init_z=z_t0,
                               interventions=interventions, lattice=lattice)
    res_base = run_simulation(nn=100, nt=T_U + T_R, seed=seed_demo, init_z=z_t0,
                               interventions=None, lattice=lattice)
    res_pos = run_simulation(nn=100, nt=T_U + T_R, seed=seed_demo, init_z=z_t0,
                              interventions=make_pulse(I0.tolist(), h_star, 0, T_U), lattice=lattice)

    row, col = bird_to_rowcol(np.arange(100), L)

    # ---------------- Figure 5: before/during/after (sparse best-found arm) ----------------
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    snaps = [(0, "pre-control (t0)"), (5, "early control (t0+5)"),
             (T_U, "end of control (t0+Tu)"), (T_U + T_R, "after release (t0+Tu+Tr)")]
    for ax, (t, title) in zip(axes, snaps):
        z = res_ctrl.z_hist[t]
        vecs = UV4[z]
        colors = np.where(np.isin(np.arange(100), I0), "#1f77b4",
                           np.where(np.isin(np.arange(100), best_actuators), "#d62728", "#cccccc"))
        ax.quiver(col, row, vecs[:, 0], vecs[:, 1], color=colors, scale=18, width=0.01)
        ax.invert_yaxis(); ax.set_xlim(-1, L); ax.set_ylim(L, -1); ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title, fontsize=10)
    fig.suptitle(f"Best-found sparse steering attempt (k={len(best_actuators)} actuators, red); "
                 f"frozen core I0 outlined blue -- FAILED to reach H*>=0.8 (see Fig. 6)")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig05_before_during_after.png", dpi=150)
    fig.savefig(fig_dir / "fig05_before_during_after.pdf")
    plt.close(fig)

    # ---------------- Figure 6: steering trajectory ----------------
    ts = np.arange(T_U + T_R + 1)
    Hstar_ctrl = [target_heading_fraction(res_ctrl.z_hist[t], I0, h_star) for t in ts]
    Hstar_base = [target_heading_fraction(res_base.z_hist[t], I0, h_star) for t in ts]
    Hstar_pos = [target_heading_fraction(res_pos.z_hist[t], I0, h_star) for t in ts]
    Coh_ctrl = [coherence(res_ctrl.z_hist[t], I0) for t in ts]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ts, Hstar_pos, label="positive control (force entire I0, k=20)", color="#2ca02c")
    ax.plot(ts, Hstar_ctrl, label=f"best-found sparse (k={len(best_actuators)})", color="#d62728")
    ax.plot(ts, Hstar_base, label="no control", color="#7f7f7f")
    ax.plot(ts, Coh_ctrl, label="core coherence C_I0(t) [sparse arm]", color="#1f77b4", linestyle="--")
    ax.axvline(0, color='k', linestyle=':', linewidth=1)
    ax.axvline(T_U, color='k', linestyle=':', linewidth=1)
    ax.axhline(0.8, color='gray', linestyle='-.', linewidth=1, label="success threshold 0.8")
    ax.set_xlabel("timestep relative to t0"); ax.set_ylabel("fraction / coherence")
    ax.set_title("Steering trajectory (single representative replicate, seed=100000)\n"
                 "control window: [0, Tu]; dotted vertical lines mark control on/off")
    ax.legend(fontsize=8, loc="center right")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig06_steering_trajectory.png", dpi=150)
    fig.savefig(fig_dir / "fig06_steering_trajectory.pdf")
    plt.close(fig)

    # ---------------- Figure 7: sparse-control requirement (k sweep) ----------------
    k_hist = greedy["history"]
    ks = [1] + [h["k"] for h in k_hist]
    best_k1 = max(v["mean_Hstar_end"] for v in rm["results"].values())
    means = [best_k1] + [h["mean_Hstar_end"] for h in k_hist]
    psucc = [max(v["p_success"] for v in rm["results"].values())] + [h["p_success"] for h in k_hist]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(ks, means, marker='o', color="#d62728", label="mean H*(t0+Tu) [best found at each k]")
    ax.plot(ks, psucc, marker='s', color="#1f77b4", label="P(success) [best found at each k]")
    ax.axhline(0.8, color='gray', linestyle='-.', label="success threshold")
    ax.set_xlabel("number of actuators (k), greedy/exhaustive-best-found")
    ax.set_ylabel("value")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Sparse-control requirement: best-found response vs. actuator budget\n"
                 "(never reaches the success threshold within the tested range)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig07_sparse_requirement.png", dpi=150)
    fig.savefig(fig_dir / "fig07_sparse_requirement.pdf")
    plt.close(fig)

    # ---------------- Figure 8: release comparison (positive control, many replicates) ----------------
    from flock_sim.simulation import run_simulation as _rs
    Hstar_pos_all = np.zeros((N_REPLICATES, T_U + T_R + 1))
    Hstar_base_all = np.zeros((N_REPLICATES, T_U + T_R + 1))
    for r in range(N_REPLICATES):
        seed = BASE_SEED_OFFSET + r
        rp = _rs(nn=100, nt=T_U + T_R, seed=seed, init_z=z_t0,
                 interventions=make_pulse(I0.tolist(), h_star, 0, T_U), lattice=lattice)
        rb = _rs(nn=100, nt=T_U + T_R, seed=seed, init_z=z_t0, interventions=None, lattice=lattice)
        for t in ts:
            Hstar_pos_all[r, t] = target_heading_fraction(rp.z_hist[t], I0, h_star)
            Hstar_base_all[r, t] = target_heading_fraction(rb.z_hist[t], I0, h_star)

    fig, ax = plt.subplots(figsize=(8, 5))
    for r in range(N_REPLICATES):
        ax.plot(ts, Hstar_pos_all[r], color="#2ca02c", alpha=0.06, linewidth=0.8)
        ax.plot(ts, Hstar_base_all[r], color="#7f7f7f", alpha=0.06, linewidth=0.8)
    ax.plot(ts, Hstar_pos_all.mean(axis=0), color="#2ca02c", linewidth=2.5, label="positive control mean")
    ax.plot(ts, Hstar_base_all.mean(axis=0), color="#7f7f7f", linewidth=2.5, label="no-control mean")
    ax.fill_between(ts, np.percentile(Hstar_pos_all, 25, axis=0), np.percentile(Hstar_pos_all, 75, axis=0),
                     color="#2ca02c", alpha=0.2)
    ax.axvline(T_U, color='k', linestyle=':', linewidth=1, label="release")
    ax.set_xlabel("timestep relative to t0"); ax.set_ylabel("H*(t) (target-heading fraction of I0)")
    ax.set_title(f"Release test: positive control vs. no control (n={N_REPLICATES} replicates)\n"
                 f"mean H* at release (t0+Tu+Tr) = {Hstar_pos_all[:, -1].mean():.3f}")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig08_release_comparison.png", dpi=150)
    fig.savefig(fig_dir / "fig08_release_comparison.pdf")
    plt.close(fig)

    print("Figures 5-8 written to", fig_dir)


if __name__ == "__main__":
    main()
