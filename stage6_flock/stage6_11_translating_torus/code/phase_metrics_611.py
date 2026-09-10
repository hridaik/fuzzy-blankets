"""Stage 6.11 Section O -- uncontrolled-phenomenology / world-selection
diagnostics.

EVALUATION-SIDE / PRIVILEGED module, deliberately outside the observer
firewall. Task brief item 2: "This is a world-selection criterion, not
available to the online observer." These functions read true positions and
headings directly and are used ONLY to (a) screen (R, v, cohesion, density)
cells before any inference code exists, and (b) certify the selected regime
against the predeclared criteria in `logs/regime_selection_predeclared_611.txt`.
They are never imported by any module on the observer side (enforced by
`tests/test_no_topology_leakage_611.py` once the observer modules exist).
"""
from __future__ import annotations

import numpy as np


# --------------------------------------------------------------- kinematics
def polarization(z: np.ndarray, uv4: np.ndarray) -> float:
    """Global Vicsek order parameter |mean heading vector|, in [0, 1]."""
    m = uv4[z].mean(axis=0)
    return float(np.hypot(m[0], m[1]))


def torus_distance_matrix(r: np.ndarray, L: float) -> np.ndarray:
    d = (r[None, :, :] - r[:, None, :] + L / 2.0) % L - L / 2.0
    D = np.sqrt((d ** 2).sum(-1))
    np.fill_diagonal(D, np.inf)
    return D


# ------------------------------------------------------- coherent components
def coherent_components(r: np.ndarray, z: np.ndarray, L: float, radius: float,
                         heading_match: bool = True) -> list[np.ndarray]:
    """Union-find over bird pairs within `radius` (torus, minimum image) that
    also currently share a heading (if heading_match). A spatial+kinematic
    notion of "locally moving as one piece" -- the oracle proxy for "domain",
    used only for world selection. Not a claim about the causal interaction
    graph (which may use a different radius); see PARAMETER_DICTIONARY.md for
    how this diagnostic radius relates to the physics radius R.
    """
    N = len(z)
    D = torus_distance_matrix(r, L)
    adj = D <= radius
    if heading_match:
        adj = adj & (z[:, None] == z[None, :])
    parent = np.arange(N)

    def find(a: int) -> int:
        root = a
        while parent[root] != root:
            root = parent[root]
        while parent[a] != root:
            parent[a], a = root, parent[a]
        return root

    ii, jj = np.nonzero(np.triu(adj, k=1))
    for a, b in zip(ii.tolist(), jj.tolist()):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups: dict[int, list[int]] = {}
    for i in range(N):
        groups.setdefault(find(i), []).append(i)
    return [np.array(v, dtype=int) for v in groups.values()]


def largest_component_fraction(components: list[np.ndarray], N: int) -> float:
    if not components:
        return 0.0
    return max(len(c) for c in components) / N


def domain_size_fractions(components: list[np.ndarray], N: int, min_size: int = 3) -> list[float]:
    return sorted((len(c) / N for c in components if len(c) >= min_size), reverse=True)


# ------------------------------------------------------------- domain lineage
def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    sa, sb = set(a.tolist()), set(b.tolist())
    if not sa and not sb:
        return 1.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def track_domains(component_series: list[list[np.ndarray]], N: int,
                   min_size: int = 3, min_jaccard: float = 0.3) -> dict:
    """Greedy mutual-best-Jaccard frame-to-frame domain tracker (world-
    selection only -- NOT the blind lineage tracker used later on candidates).

    Returns lifetimes (in steps), per-step count of alive domains, and a
    per-transition material-turnover series (1 - retention) for matched
    domains, used for the Section O report's "material turnover" column.
    """
    lifetimes: list[int] = []
    turnover_series: list[float] = []
    n_alive_series: list[int] = []
    active: dict[int, np.ndarray] = {}
    next_id = 0
    age: dict[int, int] = {}

    for t, comps in enumerate(component_series):
        comps = [c for c in comps if len(c) >= min_size]
        n_alive_series.append(len(comps))
        if t == 0:
            for c in comps:
                active[next_id] = c
                age[next_id] = 1
                next_id += 1
            continue
        used_prev, used_cur = set(), set()
        pairs = []
        for pid, pmem in active.items():
            for ci, cmem in enumerate(comps):
                j = jaccard(pmem, cmem)
                if j >= min_jaccard:
                    pairs.append((j, pid, ci))
        pairs.sort(reverse=True)
        new_active: dict[int, np.ndarray] = {}
        for j, pid, ci in pairs:
            if pid in used_prev or ci in used_cur:
                continue
            used_prev.add(pid)
            used_cur.add(ci)
            new_active[pid] = comps[ci]
            age[pid] = age.get(pid, 0) + 1
            turnover_series.append(1.0 - j)
        for pid in active:
            if pid not in used_prev:
                lifetimes.append(age.get(pid, 1))
        for ci, cmem in enumerate(comps):
            if ci not in used_cur:
                new_active[next_id] = cmem
                age[next_id] = 1
                next_id += 1
        active = new_active

    lifetimes.extend(age[pid] for pid in active)
    return dict(lifetimes=lifetimes, n_alive_series=n_alive_series, turnover_series=turnover_series)


# ----------------------------------------------------------- global collapse
def global_collapse_runs(polarization_series: list[float], largest_frac_series: list[float],
                          pol_thresh: float, frac_thresh: float, min_run: int) -> list[tuple[int, int]]:
    """Predeclared operational diagnostic (task brief item 2): sustained
    near-global order for >= min_run consecutive steps, with BOTH global
    polarization > pol_thresh AND largest coherent fraction > frac_thresh.
    Returns the [start, end) index ranges of qualifying runs."""
    flag = [(p > pol_thresh and f > frac_thresh) for p, f in zip(polarization_series, largest_frac_series)]
    runs = []
    i = 0
    n = len(flag)
    while i < n:
        if flag[i]:
            j = i
            while j < n and flag[j]:
                j += 1
            if j - i >= min_run:
                runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def episode_collapsed(polarization_series, largest_frac_series, pol_thresh, frac_thresh, min_run) -> bool:
    return len(global_collapse_runs(polarization_series, largest_frac_series, pol_thresh, frac_thresh, min_run)) > 0


# --------------------------------------------------------------- saturation
def policy_saturation_fraction(u: np.ndarray, thresh: float = 0.999) -> float:
    """Fraction of birds whose policy posterior u_t is (near-)deterministic."""
    return float((u.max(axis=1) >= thresh).mean())
