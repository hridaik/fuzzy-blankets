"""Uncontrolled-phenomenology metrics for the Stage 6.8 phase scan.

EVALUATION-SIDE (imports the lattice). These are *descriptive statistics of
the raw dynamics*, computed before any inference or control code exists, and
are the only quantities allowed to influence the choice of operating point
(task brief section 2: "Use no boundary, causal-discovery or control metric
when choosing an operating regime").

A **coherent component** is a connected component of the *geometric* Moore
graph restricted to edges whose two endpoints share a heading. On a fixed
lattice this is the natural "spatially contiguous group of birds currently
doing the same thing"; it is a property of the trajectory, not of any
inferred object.
"""
from __future__ import annotations

import numpy as np

from common_68 import NU, jaccard

MIN_COMPONENT_SIZE = 3      # frozen: components smaller than this are not counted
                            # as "groups" (a lone bird or a pair is not a collective)


def coherent_components(z: np.ndarray, neighbor_ids: list[np.ndarray],
                        min_size: int = MIN_COMPONENT_SIZE) -> list[np.ndarray]:
    """Union-find over same-heading Moore edges. Returns components of size
    >= min_size, sorted by descending size."""
    nn = len(z)
    parent = np.arange(nn)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(nn):
        for j in neighbor_ids[i]:
            if j > i and z[i] == z[j]:
                ra, rb = find(i), find(int(j))
                if ra != rb:
                    parent[ra] = rb
    roots = {}
    for i in range(nn):
        roots.setdefault(find(i), []).append(i)
    comps = [np.array(sorted(v)) for v in roots.values() if len(v) >= min_size]
    comps.sort(key=len, reverse=True)
    return comps


def heading_entropy(z: np.ndarray, nu: int = NU) -> float:
    """Shannon entropy (nats) of the empirical heading histogram. 0 = all birds
    on one heading, log(nu) = uniform."""
    counts = np.bincount(z, minlength=nu).astype(float)
    p = counts / counts.sum()
    nz = p[p > 0]
    return float(-(nz * np.log(nz)).sum())


def track_components(comp_series: list[list[np.ndarray]], match_jaccard: float = 0.5):
    """Greedy one-step lineage over consecutive frames' component lists.

    Two components in consecutive frames continue the same lineage if their
    Jaccard overlap is the mutual best match and exceeds `match_jaccard`.
    Deliberately simple and task-neutral: no heading, no target, no boundary.
    Returns (lifetimes, turnovers) where `lifetimes` is a list of lineage
    lengths in steps and `turnovers` is a list of per-step
    |I_t \\ I_{t-1}| / |I_t| values pooled over all continued lineages.
    """
    lifetimes, turnovers = [], []
    active: dict[int, int] = {}      # component index in previous frame -> lineage length
    prev = comp_series[0] if comp_series else []
    active = {k: 1 for k in range(len(prev))}
    for t in range(1, len(comp_series)):
        cur = comp_series[t]
        Jm = np.zeros((len(prev), len(cur)))
        for a, ca in enumerate(prev):
            for b, cb in enumerate(cur):
                Jm[a, b] = jaccard(ca, cb)
        new_active: dict[int, int] = {}
        used_cur = set()
        if Jm.size:
            for a in range(len(prev)):
                b = int(np.argmax(Jm[a])) if Jm.shape[1] else -1
                if b < 0 or Jm[a, b] < match_jaccard:
                    continue
                if int(np.argmax(Jm[:, b])) != a or b in used_cur:
                    continue
                used_cur.add(b)
                new_active[b] = active.get(a, 1) + 1
                sa, sb = set(prev[a].tolist()), set(cur[b].tolist())
                turnovers.append(len(sb - sa) / max(1, len(sb)))
        # lineages with no continuation this frame have ended: record their length
        matched_prev = set()
        if Jm.size:
            for b in used_cur:
                a = int(np.argmax(Jm[:, b]))
                matched_prev.add(a)
        for a in range(len(prev)):
            if a not in matched_prev:
                lifetimes.append(active.get(a, 1))
        for b in range(len(cur)):
            if b not in new_active:
                new_active[b] = 1
        active, prev = new_active, cur
    for a in range(len(prev)):
        lifetimes.append(active.get(a, 1))
    return lifetimes, turnovers


def summarize_run(z_hist: np.ndarray, neighbor_ids: list[np.ndarray], burn_in: int,
                  polarization_fn) -> dict:
    """All phase-scan statistics for one uncontrolled trajectory."""
    nt = z_hist.shape[0]
    ts = range(burn_in, nt)
    pol, ent, largest, ncomp = [], [], [], []
    comp_series = []
    for t in ts:
        z = z_hist[t]
        comps = coherent_components(z, neighbor_ids)
        comp_series.append(comps)
        pol.append(polarization_fn(z))
        ent.append(heading_entropy(z))
        largest.append(len(comps[0]) if comps else 0)
        ncomp.append(len(comps))
    lifetimes, turnovers = track_components(comp_series)
    pol = np.asarray(pol)
    return dict(
        mean_polarization=float(pol.mean()),
        sd_polarization=float(pol.std()),
        frac_time_pol_above_0_9=float(np.mean(pol > 0.9)),
        mean_heading_entropy=float(np.mean(ent)),
        mean_largest_component=float(np.mean(largest)),
        max_largest_component=int(np.max(largest)) if largest else 0,
        frac_time_largest_ge_90=float(np.mean(np.asarray(largest) >= 90)),
        mean_n_components=float(np.mean(ncomp)),
        mean_component_lifetime=float(np.mean(lifetimes)) if lifetimes else 0.0,
        p90_component_lifetime=float(np.percentile(lifetimes, 90)) if lifetimes else 0.0,
        mean_membership_turnover=float(np.mean(turnovers)) if turnovers else float("nan"),
    )
