"""Part 1A: structural quantities separating actuator cardinality from
interface coverage, computed on a flock's own (I0, B^D_0, lattice) for any
candidate actuator set A subset B^D_0. Pure graph computations -- no
simulation -- so they can be reported for every arm cheaply."""
from __future__ import annotations

import numpy as np


def core_coverage(A, I0, lattice) -> float:
    """Gamma(A) = fraction of I0 with >=1 neighbor in A."""
    if len(I0) == 0:
        return float("nan")
    A_set = set(int(a) for a in A)
    covered = sum(1 for i in I0.tolist() if A_set & set(lattice.neighbor_ids[i].tolist()))
    return covered / len(I0)


def multiplicities(A, I0, lattice) -> np.ndarray:
    """m_i(A) for every i in I0: count of A-members adjacent to i."""
    A_set = set(int(a) for a in A)
    return np.array([len(A_set & set(lattice.neighbor_ids[i].tolist())) for i in I0.tolist()])


def multiplicity_summary(A, I0, lattice) -> dict:
    m = multiplicities(A, I0, lattice)
    if len(m) == 0:
        return dict(mean_m=float("nan"), median_m=float("nan"), min_m=float("nan"),
                    frac_m_ge1=float("nan"), frac_m_ge2=float("nan"), frac_m_ge3=float("nan"))
    return dict(
        mean_m=float(m.mean()), median_m=float(np.median(m)), min_m=int(m.min()),
        frac_m_ge1=float(np.mean(m >= 1)), frac_m_ge2=float(np.mean(m >= 2)),
        frac_m_ge3=float(np.mean(m >= 3)),
    )


def _induced_components(nodes: list[int], lattice) -> list[list[int]]:
    """Connected components of `nodes` under the lattice's own adjacency,
    restricted to edges between members of `nodes` (matches rule_C_patch's
    notion of "connected within B^D_0's induced subgraph", generalized to any
    subset)."""
    node_set = set(nodes)
    visited = set()
    comps = []
    for start in nodes:
        if start in visited:
            continue
        comp = [start]
        visited.add(start)
        frontier = [start]
        while frontier:
            nxt = []
            for b in frontier:
                for j in lattice.neighbor_ids[b].tolist():
                    if j in node_set and j not in visited:
                        visited.add(j)
                        comp.append(j)
                        nxt.append(j)
            frontier = nxt
        comps.append(comp)
    return comps


def bfs_distances_from(source: int, lattice, nn: int) -> np.ndarray:
    dist = np.full(nn, -1, dtype=int)
    dist[source] = 0
    frontier = [source]
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


def _mean_pairwise_distance(nodes: list[int], lattice) -> float:
    if len(nodes) < 2:
        return 0.0
    total, count = 0.0, 0
    for s in nodes:
        d = bfs_distances_from(s, lattice, lattice.nn)
        for t in nodes:
            if t > s:
                total += d[t]
                count += 1
    return total / count if count else 0.0


def _sector_ids(B_D0, I0, lattice, n_sectors: int = 8) -> dict[int, int]:
    """Assign each B^D_0 member to one of n_sectors angular bins around the
    I0 centroid, in (row, col) lattice coordinates."""
    from flock_sim.lattice import bird_to_rowcol
    L = lattice.L
    i0_rows, i0_cols = bird_to_rowcol(I0, L)
    cr, cc = float(i0_rows.mean()), float(i0_cols.mean())
    rows, cols = bird_to_rowcol(B_D0, L)
    angles = np.arctan2(rows - cr, cols - cc)  # [-pi, pi]
    bin_width = 2 * np.pi / n_sectors
    bins = np.floor((angles + np.pi) / bin_width).astype(int).clip(max=n_sectors - 1)
    return {int(b): int(s) for b, s in zip(B_D0.tolist(), bins.tolist())}


def concentration_metrics(A, B_D0, I0, lattice, n_sectors: int = 8,
                           _cache: dict | None = None) -> dict:
    """Spatial/interface concentration of A within B^D_0. `_cache` may carry
    precomputed per-flock invariants (sector assignment, full-shell mean
    pairwise distance) to avoid recomputing them for every arm in a sweep."""
    A = list(int(a) for a in A)
    if len(A) == 0:
        return dict(n_components=0, max_component_fraction=float("nan"),
                    sector_entropy=float("nan"), mean_pairwise_graph_distance_norm=float("nan"))

    comps = _induced_components(A, lattice)
    n_components = len(comps)
    max_component_fraction = max(len(c) for c in comps) / len(A)

    if _cache is not None and "sector_ids" in _cache:
        sector_ids = _cache["sector_ids"]
    else:
        sector_ids = _sector_ids(B_D0, I0, lattice, n_sectors)
        if _cache is not None:
            _cache["sector_ids"] = sector_ids

    occupied_sectors = sorted(set(sector_ids.values()))
    n_occ = len(occupied_sectors)
    if n_occ <= 1:
        sector_entropy = 1.0  # degenerate: whole shell lives in <=1 sector, concentration is moot
    else:
        counts = np.array([sum(1 for a in A if sector_ids[a] == s) for s in occupied_sectors], dtype=float)
        p = counts / counts.sum()
        p_nz = p[p > 0]
        H = -np.sum(p_nz * np.log(p_nz))
        sector_entropy = float(H / np.log(n_occ))

    if _cache is not None and "full_shell_mean_dist" in _cache:
        full_shell_mean_dist = _cache["full_shell_mean_dist"]
    else:
        full_shell_mean_dist = _mean_pairwise_distance(B_D0.tolist(), lattice)
        if _cache is not None:
            _cache["full_shell_mean_dist"] = full_shell_mean_dist

    A_mean_dist = _mean_pairwise_distance(A, lattice)
    mean_pairwise_graph_distance_norm = (
        A_mean_dist / full_shell_mean_dist if full_shell_mean_dist > 0 else float("nan")
    )

    return dict(
        n_components=n_components,
        max_component_fraction=float(max_component_fraction),
        sector_entropy=sector_entropy,
        mean_pairwise_graph_distance_norm=float(mean_pairwise_graph_distance_norm),
    )


def structural_report(A, I0, B_D0, lattice, _cache: dict | None = None) -> dict:
    """All of Part 1A's structural quantities for one actuator set."""
    out = dict(n_actuators=len(A), f_A=len(A) / len(B_D0) if len(B_D0) else float("nan"),
               Gamma=core_coverage(A, I0, lattice))
    out.update(multiplicity_summary(A, I0, lattice))
    out.update(concentration_metrics(A, B_D0, I0, lattice, _cache=_cache))
    return out
