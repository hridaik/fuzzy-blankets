"""Stage 6.12B visualizations (static matplotlib PNGs, same convention as
Stage 6.12's `viz_612.py`): K=2 fixed-set heatmap (190 pairs), candidate
ranking (predicted vs. actual DeltaJ), q-vs-strategy outcome matrix,
cumulative-contact trajectory sketch, state views.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612b as C           # noqa: E402


def plot_k2_pair_heatmap(state_res, cell_key, out_path):
    cell = state_res["cells"].get(cell_key)
    if not cell or cell["K"] != 2:
        return
    pool = sorted(set(b for r in cell["search_rows"] for b in r["S"]))
    idx = {b: i for i, b in enumerate(pool)}
    M = np.full((len(pool), len(pool)), np.nan)
    for r in cell["search_rows"]:
        a, b = r["S"]
        M[idx[a], idx[b]] = r["mean_delta_assoc"]
        M[idx[b], idx[a]] = r["mean_delta_assoc"]
    fig, ax = plt.subplots(figsize=(7, 6))
    vmax = np.nanmax(np.abs(M))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(pool))); ax.set_xticklabels(pool, fontsize=6, rotation=90)
    ax.set_yticks(range(len(pool))); ax.set_yticklabels(pool, fontsize=6)
    ax.set_title(f"K=2 exhaustive pair landscape -- {state_res['state_id']} {cell_key}\n(mean dev Δ(J_assoc), 190 unique pairs)")
    fig.colorbar(im, ax=ax, fraction=0.046, label="mean dev Δ(J_assoc)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_predictor_ranking(predictor_data, out_path):
    rows = predictor_data["rows"]
    if not rows:
        return
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, pk, title in zip(axes, ("static_score", "kinematic_score", "oracle_score"),
                              ("Static t0 distance (deployable)", "Kinematic predicted contact (deployable)",
                               "Oracle no-control future contact (AUDIT ONLY)")):
        x = [r[pk] for r in rows]; y = [r["delta_assoc"] for r in rows]
        ax.scatter(x, y, s=6, alpha=0.35, color="tab:blue")
        ax.set_xlabel(title, fontsize=9); ax.set_ylabel("paired Δ(J_assoc)")
        rho = predictor_data["overall"][pk]["spearman_vs_delta_assoc"]
        ax.set_title(f"Spearman ρ={rho:.3f}" if rho is not None else "n/a", fontsize=9)
        ax.axhline(0, color="grey", linewidth=0.5)
    fig.suptitle("Stage 6.12B-A: pre-intervention contact predictors vs. realized paired effect\n"
                 "(all exhaustive K=1/K=2 sets, both durations, all searched states)")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_q_strategy_matrix(refresh_data, K, out_path):
    strategies = ["random", "nearest", "kinematic", "kinematic_radius_free", "oracle"]
    qs = [24, 8, 4, 2, 1]
    comp3 = refresh_data["oracle_vs_predicted_vs_random"]
    M = np.full((len(strategies), len(qs)), np.nan)
    for qi, q in enumerate(qs):
        cell = comp3.get(f"K{K}_q{q}", {})
        for si, strat in enumerate(strategies):
            v = cell.get(strat, {}).get("mean")
            if v is not None:
                M[si, qi] = v
    fig, ax = plt.subplots(figsize=(7, 5))
    vmax = np.nanmax(np.abs(M)) if np.isfinite(M).any() else 1.0
    im = ax.imshow(M, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(qs))); ax.set_xticklabels(qs)
    ax.set_yticks(range(len(strategies))); ax.set_yticklabels(strategies)
    ax.set_xlabel("refresh cadence q"); ax.set_title(f"Stage 6.12B-B: strategy x cadence outcome matrix (K={K})\nmean Δ(J_assoc) across all 5 states")
    for si in range(len(strategies)):
        for qi in range(len(qs)):
            if np.isfinite(M[si, qi]):
                ax.text(qi, si, f"{M[si,qi]:.3f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_state_view(state, out_path):
    r0 = np.array(state["r0"])
    interior = state["interior0"]; pool = state["pool20"]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(r0[:, 0], r0[:, 1], s=8, color="lightgrey", label="all birds")
    ax.scatter(r0[pool, 0], r0[pool, 1], s=22, color="tab:orange", label="nearest-20 exterior pool")
    ax.scatter(r0[interior, 0], r0[interior, 1], s=22, color="tab:blue", label="material target")
    ax.set_title(f"Stage 6.12B state view -- {state['state_id']} ({state['role']})\n"
                 f"t0={state['t0']}, |target|={len(interior)}, h*={state['h_star']}")
    ax.set_xlim(0, C.L_BOX); ax.set_ylim(0, C.L_BOX); ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def main():
    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.load(open(C.DATA_DIR / "state_manifest_612b.json"))
    for state in manifest["states"]:
        plot_state_view(state, C.FIG_DIR / f"state_view_{state['state_id']}.png")

    fx_path = C.DATA_DIR / "fixed_set_exhaustive_612b.json"
    if fx_path.exists():
        fx = json.load(open(fx_path))
        for st in fx:
            for ck in ("K2_d4", "K2_d8"):
                plot_k2_pair_heatmap(st, ck, C.FIG_DIR / f"k2_pair_heatmap_{st['state_id']}_{ck}.png")

    pred_path = C.DATA_DIR / "contact_predictor_analysis_612b.json"
    if pred_path.exists():
        pred = json.load(open(pred_path))
        plot_predictor_ranking(pred, C.FIG_DIR / "predictor_ranking.png")

    an_path = C.DATA_DIR / "analysis_summary_612b.json"
    if an_path.exists():
        an = json.load(open(an_path))
        if an.get("refreshed_access"):
            for K in (2, 4):
                plot_q_strategy_matrix(an["refreshed_access"], K, C.FIG_DIR / f"q_strategy_matrix_K{K}.png")

    print("wrote figures to", C.FIG_DIR)


if __name__ == "__main__":
    main()
