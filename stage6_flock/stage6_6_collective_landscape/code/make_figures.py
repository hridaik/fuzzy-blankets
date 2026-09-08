"""Figures 6.6-1..4. Follows the existing Agg-backend, data-driven, PNG+PDF
convention (stage6_5/boundary_inference/code/make_figures_part1.py) -- reads
only from data/, never re-runs the simulator."""
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

L = 10
HEADING_COLORS = {0: "#4c72b0", 1: "#dd8452", 2: "#55a868", 3: "#c44e52"}  # up,down,left,right
HEADING_ARROWS = {0: (0, 1), 1: (0, -1), 2: (-1, 0), 3: (1, 0)}


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)


def load_snapshot(seed: int, condition: str) -> dict:
    matches = sorted(DATA_DIR.glob(f"seed{seed}__{condition}__*.json"))
    if not matches:
        raise FileNotFoundError(f"no data for seed={seed} condition={condition}")
    return json.loads(matches[-1].read_text())


def bird_rowcol(i: int) -> tuple[int, int]:
    return i % L, i // L


def draw_lattice(ax, z: np.ndarray, I=(), B=(), E_near=(), title: str = ""):
    I, B, E_near = set(int(x) for x in I), set(int(x) for x in B), set(int(x) for x in E_near)
    for i in range(100):
        r, c = bird_rowcol(i)
        color = HEADING_COLORS[int(z[i])]
        if i in I:
            face_alpha, edge, lw, size = 1.0, "black", 2.2, 260
        elif i in B:
            face_alpha, edge, lw, size = 0.9, "#7a5195", 1.6, 190
        elif i in E_near:
            face_alpha, edge, lw, size = 0.6, "#999999", 1.0, 150
        else:
            face_alpha, edge, lw, size = 0.25, "none", 0.0, 110
        ax.scatter([c], [r], s=size, c=[color], alpha=face_alpha, edgecolors=edge,
                   linewidths=lw, zorder=3)
        dx, dy = HEADING_ARROWS[int(z[i])]
        ax.annotate("", xy=(c + dx * 0.28, r + dy * 0.28), xytext=(c, r),
                    arrowprops=dict(arrowstyle="-|>", color="black", alpha=min(face_alpha + 0.2, 1.0), lw=0.8),
                    zorder=4)
    ax.set_xlim(-0.7, L - 0.3)
    ax.set_ylim(-0.7, L - 0.3)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=10)
    for spine in ax.spines.values():
        spine.set_visible(False)


def fig_6_6_1(seed=2, condition="no_control"):
    """Default 4D landscape scatter: x=L, y=G, color=D, size=C."""
    snap = load_snapshot(seed, condition)
    rows = snap["rows"]
    Lv = np.array([r["L_blanket"] for r in rows])
    Gv = np.array([r["G_internal"] for r in rows])
    Dv = np.array([r["D_local"] for r in rows])
    Cv = np.array([r["C_internal"] for r in rows])
    is_I0 = np.array([r["candidate_source"] == "seed_reference_I0" for r in rows])

    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    sc = ax.scatter(Lv, Gv, c=Dv, s=20 + 140 * Cv, cmap="viridis", alpha=0.55,
                     edgecolors="none")
    ax.scatter(Lv[is_I0], Gv[is_I0], s=260, facecolors="none", edgecolors="red",
               linewidths=2.0, label="reference $I_0$", zorder=5)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Local contrast $D$")
    ax.set_xlabel("Boundary leakage $L$ (nats/bird-step)")
    ax.set_ylabel("Internal predictive integration $G$ (nats/bird-step)")
    ax.set_title(f"Figure 6.6-1: Collective landscape, seed {seed}, {condition}\n"
                 f"({len(rows)} candidate k=20 interiors; size = coherence $C$)")
    ax.legend(loc="upper right", fontsize=8)
    suffix = "" if seed == 2 else f"_seed{seed}"
    savefig(fig, f"fig_6_6_1_landscape_scatter{suffix}")


def fig_6_6_2(seed=2):
    """Same coherence, different individuation: same_direction vs opposite vs
    disordered exterior, all at f_E=1.0, control-end."""
    conditions = ["same_direction", "opposite", "disordered"]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 5))
    for ax, condition in zip(axes, conditions):
        snap = load_snapshot(seed, condition)
        meta = snap["meta"]
        I0_row = next(r for r in snap["rows"] if r["candidate_source"] == "seed_reference_I0")
        z = np.array(snap["representative_z"])
        I, B = I0_row["node_ids"], I0_row["boundary_ids"]
        from common_66 import lattice_100, near_exterior
        lattice = lattice_100()
        E_near = near_exterior(lattice, np.array(I)).tolist()
        draw_lattice(ax, z, I=I, B=B, E_near=E_near,
                     title=(f"{condition}\nC={I0_row['C_internal']:.2f} G={I0_row['G_internal']:.3f} "
                            f"L={I0_row['L_blanket']:.3f}\nD={I0_row['D_local']:.2f} "
                            f"H_E={I0_row['external_entropy']:.2f}"))
    fig.suptitle(f"Figure 6.6-2: Same coherent interior, three exteriors (seed {seed}, $I_0$, $f_E$=1.0)", y=1.06)
    savefig(fig, "fig_6_6_2_same_coherence_different_individuation")


def fig_6_6_3(seed=2):
    """Metric trajectories through the control/release episode, one panel
    per metric, all f_E=1.0 conditions overlaid."""
    traj = json.loads((DATA_DIR / "archetype_trajectories.json").read_text())
    seed_data = traj[str(seed)]["conditions"]
    colors = {"no_control": "#888888", "shell_only": "#4c72b0", "same_direction": "#55a868",
              "opposite": "#c44e52", "disordered": "#dd8452"}

    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5), sharex=True)
    metric_panels = [("C", "Coherence $C$"), ("G", "Integration $G$"),
                      ("L", "Leakage $L$"), ("D", "Contrast $D$")]
    for ax, (key, label) in zip(axes.flat, metric_panels):
        for condition, color in colors.items():
            s = seed_data[condition]["1.00"]["series"]
            ax.plot(s["t"], s[key], color=color, label=condition, lw=1.6)
        ax.axvline(20, color="black", ls="--", lw=0.8, alpha=0.6)
        ax.set_ylabel(label)
        ax.set_xlabel("t (steps from $t_0$)")
    axes.flat[0].legend(fontsize=7, loc="best")
    fig.suptitle(f"Figure 6.6-3: Metric trajectories under exterior-contrast control (seed {seed}, "
                 f"fixed $I=I_0$, dashed line = control-end $T_u$=20)")
    savefig(fig, "fig_6_6_3_metric_trajectories")


def fig_6_6_4(seed=2, condition="no_control"):
    """Candidate visual comparison: several candidates deliberately chosen
    from different regions of the (L,G,D,C) landscape. No claim any one is
    'best' -- face-validity inspection only (task brief section 32).

    Moore-connectivity permits diagonal-only "snake" chains (valid per the
    model's actual interaction graph -- lattice.neighbor_ids includes
    diagonal slots -- but visually scattered rather than blob-like). The
    naive top-(C+D) pick landed on exactly such a snake on a first pass
    (a spectral_resized candidate, avg internal Moore-degree ~2.1), which
    is itself a genuine "obvious visually bad candidate that nevertheless
    scores well" case (task brief section 33/36 asks whether these exist).
    Rather than discard that finding, the four main panels are chosen from
    reasonably compact candidates (avg_internal_degree above the
    landscape's own median) so the headline picks are legible, and that
    scattered/high-scoring-but-implausible example is kept as an explicit
    fifth panel."""
    from common_66 import lattice_100, near_exterior, avg_internal_degree

    snap = load_snapshot(seed, condition)
    rows = snap["rows"]
    z = np.array(snap["representative_z"])
    lattice = lattice_100()

    deg = np.array([avg_internal_degree(lattice, r["node_ids"]) for r in rows])
    compact = deg >= np.median(deg)

    def pick(cmp_key, top=True, mask=None):
        idxs = [i for i in range(len(rows)) if mask is None or mask[i]]
        return sorted(idxs, key=lambda i: rows[i][cmp_key], reverse=top)[0]

    idx_hiC_hiD = sorted([i for i in range(len(rows)) if compact[i]],
                          key=lambda i: rows[i]["C_internal"] + rows[i]["D_local"], reverse=True)[0]
    idx_hiG_loL = sorted([i for i in range(len(rows)) if compact[i]],
                          key=lambda i: rows[i]["G_internal"] - rows[i]["L_blanket"], reverse=True)[0]
    idx_loD = pick("D_local", top=False, mask=compact)
    idx_hiL = pick("L_blanket", top=True, mask=compact)
    idx_snake = int(np.argmin(deg))  # the scattered-but-formally-connected case, kept deliberately

    picks = [
        (idx_hiC_hiD, "high C + high D (compact)"),
        (idx_hiG_loL, "high G, low L (compact)"),
        (idx_loD, "low D (indistinct)"),
        (idx_hiL, "high L (leaky)"),
        (idx_snake, "Moore-connected but scattered\n(diagonal chain; visually implausible)"),
    ]
    fig, axes = plt.subplots(1, 5, figsize=(21, 5))
    for ax, (idx, label) in zip(axes, picks):
        r = rows[idx]
        E_near = near_exterior(lattice, np.array(r["node_ids"])).tolist()
        draw_lattice(ax, z, I=r["node_ids"], B=r["boundary_ids"], E_near=E_near,
                     title=(f"{label}\nsrc={r['candidate_source']} deg={deg[idx]:.1f}\n"
                            f"C={r['C_internal']:.2f} G={r['G_internal']:.3f} "
                            f"L={r['L_blanket']:.3f} D={r['D_local']:.2f}"))
    fig.suptitle(f"Figure 6.6-4: Candidate visual comparison (seed {seed}, {condition}) -- "
                 f"face-validity inspection, not a ranking", y=1.04)
    savefig(fig, "fig_6_6_4_candidate_comparison")


def main():
    import sys
    sys.path.insert(0, str(STAGE_DIR / "code"))
    for seed in (2, 3, 4):
        fig_6_6_1(seed=seed, condition="no_control")
    fig_6_6_2(seed=2)
    fig_6_6_3(seed=2)
    fig_6_6_4(seed=2, condition="no_control")
    print("figures written to", FIG_DIR)


if __name__ == "__main__":
    main()
