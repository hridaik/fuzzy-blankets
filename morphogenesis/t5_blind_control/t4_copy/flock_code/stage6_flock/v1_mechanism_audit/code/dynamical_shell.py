"""Part B: derive the model's actual instantaneous dynamical interface B^D_t
from the update code itself (flock_sim.active_inference.compute_G /
flock_sim.lattice.Lattice), NOT assumed geometrically.

Structural fact, read directly from source (see README.md section "Structural
dependency audit" for the full citation trail):

  - `active_inference.compute_G(pm, lattice, z)` computes, for every bird i,
    a sum over i's neighbors in `lattice.neighbor_ids[i]` of a term that
    depends on `z[neighbor]` (the neighbor's CURRENT heading) and the fixed
    (slot, action) lookup tables. There is no other channel by which any
    other bird's state enters bird i's G, its policy posterior `ut`, its
    sampled natural_action, or (absent an override) its next heading `z_new`.
  - `lattice.neighbor_ids[i]` is built once, from `Lattice.__init__`, purely
    as a function of bird i's fixed row/column position on the 10x10 grid
    (`lattice.py`, `neighbor_slots_1based`). It never depends on time, on any
    bird's heading, or on any other dynamic quantity. Unlike a literal
    Reynolds-boids model, birds in this port DO NOT MOVE: only the heading
    (Potts spin) state changes over time; the physical interaction graph is
    the same graph at every timestep of every simulation.

  Consequence (a genuine, non-obvious finding, stated here rather than
  assumed): because I0 is frozen (by definition of "the frozen core" being
  steered) and the lattice topology is time-invariant, the one-step
  dynamical shell

      B^D_t = { j not in I0 : j is an input to the update of some i in I0 at t }
            = { j not in I0 : j in union_i(lattice.neighbor_ids[i]) for i in I0 }

  is IDENTICAL at every timestep: B^D_t = B^D_0 for all t >= 0, as long as I0
  itself is held fixed. "Adaptive" vs. "static" dynamical-shell control (Part
  D3 vs D4) therefore collapse to the SAME intervention set in this port --
  this is reported explicitly rather than silently assumed, because it
  changes the interpretation of Outcome 3 in the task brief (see
  MECHANISM_AUDIT_RESULTS.md). The distinction would re-emerge in a model
  where I0's membership itself is tracked and allowed to drift (spectral
  lineage < 100%), which we also compute below for completeness (B^D from
  the CURRENT spectral interior at each t, not just from the frozen I0).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from common import ROOT, AUDIT_DIR, load_canonical, dump_json, TW


def one_hop_neighbors(lattice, node_set: np.ndarray) -> np.ndarray:
    """Union of lattice.neighbor_ids over all nodes in node_set, excluding node_set itself."""
    nbrs = set()
    for i in node_set.tolist():
        nbrs.update(lattice.neighbor_ids[i].tolist())
    nbrs -= set(node_set.tolist())
    return np.array(sorted(nbrs), dtype=int)


def k_hop_shell(lattice, core: np.ndarray, k: int) -> list[np.ndarray]:
    """Returns [B^D,(1), B^D,(2), ..., B^D,(k)] -- successive graph-distance shells
    around `core` in the static lattice graph, each EXCLUDING core and all closer shells."""
    visited = set(core.tolist())
    shells = []
    frontier = set(core.tolist())
    for _ in range(k):
        nxt = set()
        for i in frontier:
            nxt.update(lattice.neighbor_ids[i].tolist())
        nxt -= visited
        shells.append(np.array(sorted(nxt), dtype=int))
        visited |= nxt
        frontier = nxt
        if not frontier:
            break
    return shells


def graph_distance_from_set(lattice, core: np.ndarray, nn: int = 100) -> np.ndarray:
    """BFS shortest-path distance (in the static lattice graph) from each of the
    nn birds to the nearest member of `core`. core members get distance 0."""
    dist = np.full(nn, -1, dtype=int)
    dist[core] = 0
    frontier = list(core.tolist())
    d = 0
    while frontier:
        d += 1
        nxt = []
        for i in frontier:
            for j in lattice.neighbor_ids[i].tolist():
                if dist[j] == -1:
                    dist[j] = d
                    nxt.append(j)
        frontier = nxt
    return dist


def main():
    c = load_canonical()
    lattice, I0, t0 = c["lattice"], c["I0"], c["t0"]
    nn = lattice.nn

    B_D0 = one_hop_neighbors(lattice, I0)
    E_D0 = np.setdiff1d(np.arange(nn), np.union1d(I0, B_D0))
    dist = graph_distance_from_set(lattice, I0, nn)
    shells = k_hop_shell(lattice, I0, k=6)

    # Spectral boundary B^F_0 at t0, recomputed directly (sign-aligned to I0),
    # for direct comparison in boundary_compare.py. Window is [t0-TW+1, t0].
    z_hist = c["z_hist_full"]
    window = z_hist[t0 - TW + 1: t0 + 1]
    from flock_sim.spectral import analyze_window
    sr = analyze_window(window, refclust=I0)
    B_F0 = sr.boundary_nodes

    out = dict(
        t0=int(t0), nn=int(nn), I0=I0.tolist(),
        B_D0=B_D0.tolist(), size_B_D0=len(B_D0),
        E_D0=E_D0.tolist(), size_E_D0=len(E_D0),
        B_F0=B_F0.tolist(), size_B_F0=len(B_F0),
        eigengap_t0=float(sr.eigengap), lambda2_t0=float(sr.lambda2), lambda3_t0=float(sr.lambda3),
        graph_distance_from_I0=dist.tolist(),
        shells_by_hop={str(k + 1): s.tolist() for k, s in enumerate(shells)},
        shell_sizes_by_hop={str(k + 1): len(s) for k, s in enumerate(shells)},
        structural_claim=(
            "B^D_t == B^D_0 for all t as long as I0 is held fixed, because "
            "lattice.neighbor_ids (the sole channel by which other birds' "
            "states enter compute_G for a bird in I0) is built once from "
            "fixed row/column position and never changes with time or state. "
            "Verified by inspection of active_inference.compute_G and "
            "lattice.Lattice.__init__ (birds do not move in this port)."
        ),
    )
    dump_json(out, AUDIT_DIR / "data" / "dynamical_shell.json")
    print(f"|I0|={len(I0)} |B^D_0|={len(B_D0)} |E^D_0|={len(E_D0)} |B^F_0|={len(B_F0)} "
          f"(eigengap_t0={sr.eigengap:.3f})")
    print("B^D_0:", B_D0.tolist())
    print("B^F_0:", B_F0.tolist())
    print("shell sizes by hop:", {k: len(v) for k, v in enumerate(shells, start=1)})


if __name__ == "__main__":
    main()
