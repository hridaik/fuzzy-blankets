"""Deterministic weighted Louvain community detection.

INFERENCE-SIDE MODULE. Must never import `flock_sim`, `common_68`,
`fov_dynamics`, `oracle_68`, or anything else carrying the simulator's
interaction structure. Takes a dense symmetric non-negative weight matrix and
returns a partition; it has no notion of "neighbour", "lattice", or "visible".

Why re-implemented rather than imported: `networkx` is not in this project's
environment (`environment.yml`), and the reference Louvain implementation is
randomized (random node order per pass). Stage 6.8 needs a *deterministic,
documented* community procedure so that a candidate collective proposed at
time t is reproducible bit-for-bit. The two departures from the reference
algorithm are therefore both determinizations, not heuristic changes:

  1. nodes are visited in ascending index order, not a shuffled order;
  2. ties in modularity gain are broken toward the lowest community index,
     and a node only moves on a STRICTLY positive gain.

Everything else is standard Blondel et al. (2008) two-phase modularity
optimization: local moving to convergence, then aggregation into a
community-level weighted graph, repeated until modularity stops improving.
"""
from __future__ import annotations

import numpy as np


def modularity(W: np.ndarray, labels: np.ndarray) -> float:
    m2 = W.sum()
    if m2 <= 0:
        return 0.0
    k = W.sum(axis=1)
    q = 0.0
    for c in np.unique(labels):
        idx = np.where(labels == c)[0]
        q += W[np.ix_(idx, idx)].sum() / m2 - (k[idx].sum() / m2) ** 2
    return float(q)


def _local_move(W: np.ndarray, resolution: float, max_passes: int = 50) -> np.ndarray:
    n = W.shape[0]
    m2 = W.sum()
    if m2 <= 0:
        return np.arange(n)
    k = W.sum(axis=1)
    labels = np.arange(n)
    sigma_tot = k.copy()                    # total degree per community
    self_w = np.diag(W).copy()

    for _ in range(max_passes):
        moved = False
        for i in range(n):                   # deterministic ascending order
            ci = labels[i]
            sigma_tot[ci] -= k[i]
            # weight from i into each community (excluding i's own self-loop)
            w_to = np.zeros(n)
            row = W[i].copy()
            row[i] = 0.0
            np.add.at(w_to, labels, row)
            gain = w_to / m2 - resolution * sigma_tot * k[i] / (m2 ** 2)
            # candidate communities: i's own, plus those it actually connects to
            cand = np.where(w_to > 0)[0]
            cand = np.union1d(cand, [ci])
            best = cand[0]
            best_gain = gain[cand[0]]
            for c in cand[1:]:               # ties -> lowest community index
                if gain[c] > best_gain + 1e-15:
                    best, best_gain = c, gain[c]
            if best != ci and best_gain > gain[ci] + 1e-15:
                labels[i] = best
                moved = True
            sigma_tot[labels[i]] += k[i]
        if not moved:
            break
    return labels


def _relabel(labels: np.ndarray) -> np.ndarray:
    uniq = np.unique(labels)
    remap = {int(u): i for i, u in enumerate(uniq)}
    return np.array([remap[int(x)] for x in labels], dtype=int)


def louvain(W: np.ndarray, resolution: float = 1.0, max_levels: int = 10) -> np.ndarray:
    """Return an (n,) integer partition of the nodes of the symmetric
    non-negative weight matrix `W`. Deterministic given `W`."""
    W = np.asarray(W, dtype=float)
    W = 0.5 * (W + W.T)
    n = W.shape[0]
    if n == 0:
        return np.zeros(0, dtype=int)
    if W.sum() <= 0:
        return np.arange(n)

    node_labels = np.arange(n)
    cur = W
    cur_map = np.arange(n)          # node -> index in `cur`
    best_q = modularity(W, node_labels)

    for _ in range(max_levels):
        part = _relabel(_local_move(cur, resolution))
        new_labels = part[cur_map]
        q = modularity(W, new_labels)
        if q <= best_q + 1e-12 or len(np.unique(part)) == cur.shape[0]:
            break
        best_q, node_labels, cur_map = q, new_labels, new_labels
        nc = len(np.unique(part))
        agg = np.zeros((nc, nc))
        for a in range(cur.shape[0]):
            for b in range(cur.shape[0]):
                agg[part[a], part[b]] += cur[a, b]
        cur = agg
    return _relabel(node_labels)
