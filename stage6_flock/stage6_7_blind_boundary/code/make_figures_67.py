"""Figures 6.7-1..5. Follows the existing Agg-backend, data-driven, PNG+PDF
convention (stage6_6_collective_landscape/code/make_figures.py) -- reads only
from data/, never re-runs the simulator or any inference step."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = STAGE_DIR / "data"
FIG_DIR = STAGE_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
STAGE66_DATA_DIR = STAGE_DIR.parent / "stage6_6_collective_landscape" / "data"

_Z_CACHE = {}


def representative_z_for(seed: int, condition: str) -> np.ndarray:
    key = (seed, condition)
    if key not in _Z_CACHE:
        path = STAGE66_DATA_DIR / f"seed{seed}__{condition}__fE1.00__t20.json"
        _Z_CACHE[key] = np.array(json.loads(path.read_text())["representative_z"])
    return _Z_CACHE[key]

L = 10
HEADING_COLORS = {0: "#4c72b0", 1: "#dd8452", 2: "#55a868", 3: "#c44e52"}
HEADING_ARROWS = {0: (0, 1), 1: (0, -1), 2: (-1, 0), 3: (1, 0)}
OUTCOME_COLOR = {"A_identifiable": "#2a9d8f", "B_reduced_interface": "#4c72b0",
                 "C_estimator_inadequate": "#e9c46a", "D_failed": "#c44e52"}
OUTCOME_LABEL = {"A_identifiable": "A: high pred. + high struct.", "B_reduced_interface": "B: high pred. + low struct.",
                  "C_estimator_inadequate": "C: low pred. + high struct.", "D_failed": "D: low pred. + low struct."}


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def load(name):
    return json.loads((DATA_DIR / name).read_text())


def bird_rowcol(i: int):
    return i % L, i // L


def draw_lattice_67(ax, z, I=(), B_pred=(), B_D=(), title=""):
    I, B_pred, B_D = set(int(x) for x in I), set(int(x) for x in B_pred), set(int(x) for x in B_D)
    for i in range(100):
        r, c = bird_rowcol(i)
        color = HEADING_COLORS[int(z[i])]
        if i in I:
            face_alpha, edge, lw, size = 1.0, "black", 2.2, 260
        elif i in B_pred and i in B_D:
            face_alpha, edge, lw, size = 0.9, "#2a9d8f", 2.0, 200
        elif i in B_pred:
            face_alpha, edge, lw, size = 0.85, "#4c72b0", 1.8, 190
        elif i in B_D:
            face_alpha, edge, lw, size = 0.5, "#8172b2", 1.4, 160
        else:
            face_alpha, edge, lw, size = 0.2, "none", 0.0, 100
        ax.scatter([c], [r], s=size, c=[color], alpha=face_alpha, edgecolors=edge, linewidths=lw, zorder=3)
        dx, dy = HEADING_ARROWS[int(z[i])]
        ax.annotate("", xy=(c + dx * 0.28, r + dy * 0.28), xytext=(c, r),
                    arrowprops=dict(arrowstyle="-|>", color="black", alpha=min(face_alpha + 0.2, 1.0), lw=0.8),
                    zorder=4)
    ax.set_xlim(-1, L); ax.set_ylim(-1, L); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=10)


def fig_67_1(rows):
    fig, ax = plt.subplots(figsize=(6, 5))
    for outcome, color in OUTCOME_COLOR.items():
        pts = [r for r in rows if r["outcome"] == outcome]
        if not pts:
            continue
        ax.scatter([p["predictive_jaccard"] for p in pts], [p["excess_loss_test"] for p in pts],
                   s=18, alpha=0.7, color=color, label=OUTCOME_LABEL[outcome])
    ax.axhline(0.01, color="gray", linestyle="--", linewidth=1, label="delta_pred = 0.01 nats")
    ax.set_xlabel("Structural recovery J(Bhat^pred, B^D)")
    ax.set_ylabel("Predictive excess loss Delta-ell(Bhat^pred)  [nats/bird-step]")
    ax.set_title("Fig. 6.7-1: predictive sufficiency vs structural recovery (n=300)")
    ax.legend(fontsize=7, loc="upper right")
    savefig(fig, "fig_6_7_1_predictive_vs_structural")


def fig_67_2(rows):
    by_outcome = {}
    for r in rows:
        by_outcome.setdefault(r["outcome"], []).append(r)

    picks = []
    for key in ("A_identifiable", "B_reduced_interface", "D_failed"):
        cands = by_outcome.get(key) or by_outcome.get("C_estimator_inadequate", [])
        if cands:
            picks.append((key, cands[0]))
    if not picks:
        return

    fig, axes = plt.subplots(1, len(picks), figsize=(5 * len(picks), 5))
    if len(picks) == 1:
        axes = [axes]
    for ax, (key, row) in zip(axes, picks):
        z = representative_z_for(row["seed"], row["condition"])
        draw_lattice_67(ax, z, I=row["I"], B_pred=row["B_hat_pred"], B_D=row["B_D"],
                         title=f"{OUTCOME_LABEL[key]}\nseed{row['seed']} {row['condition']} J={row['predictive_jaccard']:.2f}")
    savefig(fig, "fig_6_7_2_representative_cases")


def fig_67_3(rows):
    both = sum(len(r["overlap"]["both"]) for r in rows if r.get("overlap"))
    pred_only = sum(len(r["overlap"]["predictive_only"]) for r in rows if r.get("overlap"))
    causal_only = sum(len(r["overlap"]["causal_only"]) for r in rows if r.get("overlap"))
    missed = sum(len(r["overlap"]["true_missed_by_both"]) for r in rows if r.get("overlap"))

    fig, ax = plt.subplots(figsize=(5, 4))
    cats = ["Predictive only", "Causal only", "Both", "True shell,\nmissed by both"]
    vals = [pred_only, causal_only, both, missed]
    colors = ["#4c72b0", "#c44e52", "#2a9d8f", "#999999"]
    ax.bar(cats, vals, color=colors)
    ax.set_ylabel("Total edges across 300 candidates")
    ax.set_title("Fig. 6.7-3: predictive vs causal interface overlap")
    for tick in ax.get_xticklabels():
        tick.set_fontsize(8)
    savefig(fig, "fig_6_7_3_predictive_vs_causal_overlap")


def fig_67_4(se_rows):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    r_grid = sorted(set(r["R"] for r in se_rows))
    for seed in sorted(set(r["seed"] for r in se_rows)):
        rows_s = [r for r in se_rows if r["seed"] == seed]
        loss_by_r = [np.mean([r["excess_loss_test"] for r in rows_s if r["R"] == R]) for R in r_grid]
        jac_by_r = [np.mean([r["jaccard"] for r in rows_s if r["R"] == R]) for R in r_grid]
        axes[0].plot(r_grid, loss_by_r, marker="o", label=f"seed {seed}")
        axes[1].plot(r_grid, jac_by_r, marker="o", label=f"seed {seed}")
    axes[0].axhline(0.01, color="gray", linestyle="--", linewidth=1)
    axes[0].set_xscale("log"); axes[0].set_xlabel("R (replicates)")
    axes[0].set_ylabel("Predictive excess loss [nats/bird-step]")
    axes[0].set_title("Predictive sufficiency vs sample size")
    axes[1].set_xscale("log"); axes[1].set_xlabel("R (replicates)")
    axes[1].set_ylabel("Structural Jaccard J(Bhat^pred, B^D)")
    axes[1].set_title("Structural recovery vs sample size")
    axes[0].legend(fontsize=8); axes[1].legend(fontsize=8)
    fig.suptitle("Fig. 6.7-4: sample-efficiency sweep")
    savefig(fig, "fig_6_7_4_sample_efficiency")


def fig_67_5(bl_rows):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    G_o = np.array([r["G_oracle"] for r in bl_rows]); G_b = np.array([r["G_blind"] for r in bl_rows])
    L_o = np.array([r["L_oracle"] for r in bl_rows]); L_b = np.array([r["L_blind"] for r in bl_rows])
    for ax, (o, b, name) in zip(axes, ((G_o, G_b, "G (internal integration)"), (L_o, L_b, "L (boundary leakage)"))):
        ax.scatter(o, b, s=14, alpha=0.5, color="#4c72b0")
        lo, hi = min(o.min(), b.min()), max(o.max(), b.max())
        ax.plot([lo, hi], [lo, hi], color="gray", linestyle="--", linewidth=1)
        ax.set_xlabel(f"{name}, oracle boundary")
        ax.set_ylabel(f"{name}, blind Bhat^pred")
        ax.set_title(name)
    fig.suptitle("Fig. 6.7-5: oracle- vs blind-boundary landscape coordinates (n=300)")
    savefig(fig, "fig_6_7_5_oracle_vs_blind_landscape")


def main():
    ov = load("oracle_validation_panel.json")["rows"]
    fig_67_1(ov)
    fig_67_2(ov)
    fig_67_3(ov)

    se = load("sample_efficiency.json")["rows"]
    fig_67_4(se)

    bl = load("blind_landscape_panel.json")["rows"]
    fig_67_5(bl)

    print(f"wrote figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
