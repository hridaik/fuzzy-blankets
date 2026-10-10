"""Shapes the Stage 6.6 scientific outputs (data/seed*__*.json,
data/archetype_trajectories.json) into one compact bundle for the
interactive demo: interactive_demo/data/collective_landscape_bundle.json.

Size discipline: the full landscape (5000 candidates x 15 snapshots) is
scientifically important but too large to comfortably inline into a
single-file static HTML demo (the existing build/index.html convention has
no server, no runtime fetch -- see interactive_demo/README.md). Each
snapshot's embedded candidate set is therefore a deterministic subsample
(default cap 1200, always including every Pareto-nondominated candidate and
the seed's reference I0) -- documented explicitly in
STAGE6_6_VISUALIZATION_NOTES.md as a demo-only sampling decision. The full
5000-candidate set for every snapshot remains available as scientific data
in data/*.json and data/*.csv, untouched by this script.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = STAGE_DIR / "data"
DEMO_DATA_DIR = STAGE_DIR.parent / "interactive_demo" / "data"

EMBED_CAP = 1200
RNG_SEED = 12345


def _subsample_rows(rows: list[dict], cap: int) -> list[dict]:
    if len(rows) <= cap:
        return rows
    rng = np.random.default_rng(RNG_SEED)
    must_keep_idx = [i for i, r in enumerate(rows)
                      if r["is_pareto"] or r["candidate_source"] == "seed_reference_I0"]
    must_keep = set(must_keep_idx)
    remaining_slots = max(0, cap - len(must_keep))
    pool = [i for i in range(len(rows)) if i not in must_keep]
    chosen = list(must_keep)
    if remaining_slots > 0 and pool:
        extra = rng.choice(pool, size=min(remaining_slots, len(pool)), replace=False)
        chosen.extend(int(x) for x in extra)
    chosen.sort()
    return [rows[i] for i in chosen]


def _columnar(rows: list[dict]) -> dict:
    return dict(
        id=[r["candidate_id"] for r in rows],
        src=[r["candidate_source"] for r in rows],
        I=[r["node_ids"] for r in rows],
        B=[r["boundary_ids"] for r in rows],
        C=[round(r["C_internal"], 5) for r in rows],
        G=[round(r["G_internal"], 6) for r in rows],
        L=[round(r["L_blanket"], 6) for r in rows],
        D=[round(r["D_local"], 5) for r in rows],
        He=[round(r["external_entropy"], 5) for r in rows],
        Dc=[round(r["directional_contrast"], 5) for r in rows],
        Sh=[r["structural_shell_size"] for r in rows],
        Bs=[r["boundary_size"] for r in rows],
        Pa=[r["is_pareto"] for r in rows],
    )


def _compact_illustrative(r: dict) -> dict:
    """Full-trajectory playback entries (code/run_illustrative_trajectories.py):
    a curated, small (~9) set of (seed, condition, candidate) examples chosen
    to span the (C,G,L,D) surface and the five control scenarios -- NOT every
    combination. Keeps z_hist as a plain (T+1, 100) int array (small: ~41x100
    per entry) so the demo can play back real heading arrows, not just the
    four scalar traces the archetype_trajectories bundle already provides."""
    s = r["series"]
    return dict(
        seed=r["seed"], condition=r["condition"], label=r["label"],
        I=r["candidate_node_ids"],
        t0=r["t0"], h0=r["h0"], h_star=r["h_star"], h_opp=r["h_opp"],
        T_u=r["T_u"], T_r=r["T_r"],
        shell=r["shell"], near_exterior=r["near_exterior"], controlled_exterior=r["controlled_exterior"],
        z_hist=r["z_hist"],
        series=dict(
            t=s["t"],
            C=[round(x, 5) for x in s["C"]], G=[round(x, 6) for x in s["G"]],
            L=[round(x, 6) for x in s["L"]], D=[round(x, 5) for x in s["D"]],
            He=[round(x, 5) for x in s["He"]], Dc=[round(x, 5) for x in s["Dc"]],
            Hstar=[round(x, 4) for x in s["Hstar"]],
        ),
    )


def build_lattice_block(neighbors: dict) -> dict:
    L = 10
    positions = []
    for i in range(100):
        row = i % L
        col = i // L
        positions.append([row, col])
    return dict(L=L, nn=100, positions=positions,
                neighbors={str(i): neighbors[str(i)] for i in range(100)})


def main():
    snapshot_files = sorted(DATA_DIR.glob("seed*__*.json"))
    if not snapshot_files:
        raise SystemExit("no data/seed*__*.json found -- run run_all_snapshots.py first")

    bundle = dict(K_boundary_budget=12, k_interior=20, snapshots={}, lattice=None)
    for path in snapshot_files:
        result = json.loads(path.read_text())
        meta = result["meta"]
        rows = result["rows"]
        if bundle["lattice"] is None:
            bundle["lattice"] = build_lattice_block(result["lattice_neighbors"])
        embedded = _subsample_rows(rows, EMBED_CAP)
        key = f"seed{meta['seed']}_{meta['condition']}"
        bundle["snapshots"][key] = dict(
            seed=meta["seed"], condition=meta["condition"], f_E=meta["f_E"],
            t0=meta["t0"], h0=meta["h0"], h_star=meta["h_star"], h_opp=meta["h_opp"],
            t_snapshot=meta["t_snapshot"],
            I0=meta["I0"],
            # S(I) and E_near(I) are NOT embedded per-candidate (would multiply the
            # bundle size); the JS side derives them from lattice.neighbors + the
            # selected candidate's I via BFS, mirroring code/common_66.py's
            # structural_shell/near_exterior (see STAGE6_6_VISUALIZATION_NOTES.md).
            controlled_exterior=meta["controlled_exterior"],
            representative_z=result["representative_z"],
            n_candidates_embedded=len(embedded), n_candidates_full=meta["n_candidates_unique"],
            candidates=_columnar(embedded),
        )

    archetype_path = DATA_DIR / "archetype_trajectories.json"
    if archetype_path.exists():
        bundle["archetype_trajectories"] = json.loads(archetype_path.read_text())

    illustrative_path = DATA_DIR / "illustrative_trajectories.json"
    if illustrative_path.exists():
        raw = json.loads(illustrative_path.read_text())
        bundle["illustrative_trajectories"] = [_compact_illustrative(r) for r in raw]

    DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DEMO_DATA_DIR / "collective_landscape_bundle.json"
    out_path.write_text(json.dumps(bundle, separators=(",", ":")))
    size_mb = out_path.stat().st_size / 1e6
    print(f"wrote {out_path} ({size_mb:.2f} MB), {len(bundle['snapshots'])} snapshots")
    for k, v in bundle["snapshots"].items():
        print(f"  {k}: embedded {v['n_candidates_embedded']}/{v['n_candidates_full']}")


if __name__ == "__main__":
    main()
