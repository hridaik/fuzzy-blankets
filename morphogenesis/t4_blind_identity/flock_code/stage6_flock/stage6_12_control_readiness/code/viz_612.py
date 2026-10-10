"""Stage 6.12 static visualizations (matplotlib, no interactivity needed for
the deliverable set): budget-map heatmaps (per state and aggregate),
actuator-set distribution view for the frozen primary search budget, and one
state-view scatter (target/pool/actuators/heading) for a representative
state. Colorblind-safe, explicit "unavailable" hatching, splits/losses never
smoothed over.
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
import common_612 as C            # noqa: E402
import intervention_612 as I      # noqa: E402

K_GRID = list(I.K_GRID)
D_GRID = list(I.D_GRID)


def grid_from_cells(cells, key):
    M = np.full((len(K_GRID), len(D_GRID)), np.nan)
    avail = np.zeros_like(M, dtype=bool)
    for ki, K in enumerate(K_GRID):
        for di, d in enumerate(D_GRID):
            c = cells.get(f"K{K}_d{d}")
            if c is None or c.get("unavailable"):
                continue
            v = c.get(key)
            if v is not None:
                M[ki, di] = v
                avail[ki, di] = True
    return M, avail


def heatmap(ax, M, avail, title, cmap="RdBu_r", vcenter=0.0, fmt="{:.2f}"):
    if vcenter is None:
        vmin = np.nanmin(M) if np.isfinite(M).any() else 0.0
        vmax = np.nanmax(M) if np.isfinite(M).any() else 1.0
        im = ax.imshow(M, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    else:
        vmax = np.nanmax(np.abs(M - vcenter)) if np.isfinite(M).any() else 1.0
        vmax = max(vmax, 1e-6)
        im = ax.imshow(M, cmap=cmap, vmin=vcenter - vmax, vmax=vcenter + vmax, aspect="auto")
    ax.set_xticks(range(len(D_GRID))); ax.set_xticklabels(D_GRID)
    ax.set_yticks(range(len(K_GRID))); ax.set_yticklabels(K_GRID)
    ax.set_xlabel("d (forcing steps)"); ax.set_ylabel("K (actuator count)")
    ax.set_title(title, fontsize=10)
    for ki in range(len(K_GRID)):
        for di in range(len(D_GRID)):
            if not avail[ki, di]:
                ax.add_patch(plt.Rectangle((di - 0.5, ki - 0.5), 1, 1, fill=False, hatch="////", edgecolor="grey"))
                ax.text(di, ki, "N/A", ha="center", va="center", fontsize=7, color="grey")
            elif np.isfinite(M[ki, di]):
                ax.text(di, ki, fmt.format(M[ki, di]), ha="center", va="center", fontsize=7)
    return im


def plot_state_budget_map(state_res, out_path):
    cells = state_res["cells"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    M, av = grid_from_cells(cells, "G_sus_mean")
    im = heatmap(axes[0, 0], M, av, "G_sus (mean paired delta)")
    fig.colorbar(im, ax=axes[0, 0], fraction=0.046)
    M, av = grid_from_cells(cells, "between_set_var")
    im = heatmap(axes[0, 1], M, av, "Between-set variance (selectivity signal)", cmap="viridis", vcenter=None)
    fig.colorbar(im, ax=axes[0, 1], fraction=0.046)
    M, av = grid_from_cells(cells, "identity_valid_fraction")
    im = heatmap(axes[1, 0], M, av, "Identity-valid fraction V", cmap="viridis", vcenter=None, fmt="{:.2f}")
    fig.colorbar(im, ax=axes[1, 0], fraction=0.046)
    M, av = grid_from_cells(cells, "identity_valid_fraction")
    Mloss = 1 - M
    im = heatmap(axes[1, 1], Mloss, av, "Split/loss/unresolved probability (1-V)", cmap="magma", vcenter=None)
    fig.colorbar(im, ax=axes[1, 1], fraction=0.046)
    fig.suptitle(f"Stage 6.12 budget map -- {state_res['state_id']} ({state_res['role']})")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def heatmap_fix(ax, M, avail, title, cmap, vcenter, fmt="{:.3f}"):
    if vcenter is None:
        vmin = np.nanmin(M) if np.isfinite(M).any() else 0.0
        vmax = np.nanmax(M) if np.isfinite(M).any() else 1.0
        im = ax.imshow(M, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    else:
        vmax = np.nanmax(np.abs(M - vcenter)) if np.isfinite(M).any() else 1.0
        vmax = max(vmax, 1e-6)
        im = ax.imshow(M, cmap=cmap, vmin=vcenter - vmax, vmax=vcenter + vmax, aspect="auto")
    ax.set_xticks(range(len(D_GRID))); ax.set_xticklabels(D_GRID)
    ax.set_yticks(range(len(K_GRID))); ax.set_yticklabels(K_GRID)
    ax.set_xlabel("d"); ax.set_ylabel("K")
    ax.set_title(title, fontsize=10)
    for ki in range(len(K_GRID)):
        for di in range(len(D_GRID)):
            if not avail[ki, di]:
                ax.add_patch(plt.Rectangle((di - 0.5, ki - 0.5), 1, 1, fill=False, hatch="////", edgecolor="grey"))
            elif np.isfinite(M[ki, di]):
                ax.text(di, ki, fmt.format(M[ki, di]), ha="center", va="center", fontsize=7)
    return im


def plot_aggregate_budget_map(phaseA, out_path):
    agg = {}
    for state_res in phaseA:
        for key, c in state_res["cells"].items():
            if c.get("unavailable"):
                continue
            agg.setdefault(key, {"g": [], "var": [], "ivf": []})
            agg[key]["g"].append(c["G_sus_mean"])
            agg[key]["var"].append(c["between_set_var"])
            agg[key]["ivf"].append(c["identity_valid_fraction"])
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, metric, title, cmap, vc in (
        (axes[0], "g", "Mean G_sus across states", "RdBu_r", 0.0),
        (axes[1], "var", "Mean between-set variance across states", "viridis", None),
        (axes[2], "ivf", "Mean identity-valid fraction across states", "viridis", None),
    ):
        M = np.full((len(K_GRID), len(D_GRID)), np.nan)
        avail = np.zeros_like(M, dtype=bool)
        for ki, K in enumerate(K_GRID):
            for di, d in enumerate(D_GRID):
                vals = agg.get(f"K{K}_d{d}", {}).get(metric)
                if vals:
                    M[ki, di] = float(np.mean(vals))
                    avail[ki, di] = True
        im = heatmap_fix(ax, M, avail, title, cmap, vc)
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle(f"Stage 6.12 aggregate readiness map ({len(phaseA)} states)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_selectivity_distribution(phaseBC, out_path):
    rows = [r for r in phaseBC if not r.get("unavailable")]
    if not rows:
        return
    fig, axes = plt.subplots(1, len(rows), figsize=(3.2 * len(rows), 4.2), sharey=True)
    if len(rows) == 1:
        axes = [axes]
    for ax, res in zip(axes, rows):
        random_means = [h["mean_J"] for h in res["holdout_random"]]
        j0 = res["holdout_no_control_mean_J"]
        j_star = res["holdout_S_star"]["mean_J"]
        ax.scatter(np.zeros(len(random_means)) + 0.1 * np.random.default_rng(0).standard_normal(len(random_means)),
                   random_means, color="grey", alpha=0.7, label="random sets (holdout)")
        ax.axhline(j0, color="black", linestyle=":", label="no control")
        ax.axhline(j_star, color="crimson", linewidth=2, label="S* (holdout)")
        ax.set_title(res["state_id"].replace("s612_", "").replace("development", "dev"), fontsize=8)
        ax.set_xticks([])
    axes[0].set_ylabel("J (release-late valid utility)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, fontsize=8)
    fig.suptitle(f"Stage 6.12 actuator-set distribution (frozen K={rows[0]['K']}, d={rows[0]['d']}, holdout streams)")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_state_view(state, out_path):
    r0 = np.array(state["r0"])
    interior = state["interior0"]
    pool = state["pool20"]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(r0[:, 0], r0[:, 1], s=8, color="lightgrey", label="all birds")
    ax.scatter(r0[pool, 0], r0[pool, 1], s=22, color="tab:orange", label="nearest-20 exterior pool")
    ax.scatter(r0[interior, 0], r0[interior, 1], s=22, color="tab:blue", label="material target")
    ax.set_title(f"Stage 6.12 state view -- {state['state_id']} ({state['role']})\n"
                 f"t0={state['t0']}, |target|={len(interior)}, h*={state['h_star']}")
    ax.set_xlim(0, C.L_BOX); ax.set_ylim(0, C.L_BOX)
    ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def main():
    manifest = json.load(open(C.DATA_DIR / "state_manifest_612.json"))
    phaseA = json.load(open(C.DATA_DIR / "phaseA_results_612.json"))
    C.FIG_DIR.mkdir(parents=True, exist_ok=True)

    for state_res in phaseA:
        plot_state_budget_map(state_res, C.FIG_DIR / f"budget_map_{state_res['state_id']}.png")
    plot_aggregate_budget_map(phaseA, C.FIG_DIR / "budget_map_aggregate.png")

    for state in manifest["states"][:3]:
        plot_state_view(state, C.FIG_DIR / f"state_view_{state['state_id']}.png")

    phaseBC_path = C.DATA_DIR / "phaseBC_results_612.json"
    if phaseBC_path.exists():
        phaseBC = json.load(open(phaseBC_path))
        plot_selectivity_distribution(phaseBC, C.FIG_DIR / "selectivity_distribution.png")

    print("wrote figures to", C.FIG_DIR)


if __name__ == "__main__":
    main()
