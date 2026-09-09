"""Online candidate-collective proposal (task brief sections 7-8, 10).

INFERENCE-SIDE MODULE. Sees only an `Observation`. Never uses the control
target, oracle edges, the oracle boundary, or any future observation.

Primary proposal -- affinity + community
----------------------------------------
    W_ij(t) = K_sigma(||r_i - r_j||) * (1/W) sum_{tau=t-W+1}^{t} 1[z_i(tau) = z_j(tau)]

`K_sigma` is a smooth Gaussian spatial kernel, deliberately NOT the FOV
predicate and not the Moore adjacency indicator: it encodes only "nearby birds
with persistent behavioural agreement plausibly belong to the same collective".
Communities are extracted from `W` by the deterministic weighted Louvain in
`louvain.py`, which returns MULTIPLE communities; no winner is forced.

This affinity graph is NOT a Markov blanket and is never interpreted as one.

Comparator proposal -- spectral/coherence
-----------------------------------------
`spectral_proposal.py` runs the paper's Fiedler-style split on the same
observed coherence data. It is called a *spectral/coherence proposal*
throughout, never a Markov blanket. Neither method is privileged a priori.

Validity filtering
------------------
Candidates are filtered ONLY by predeclared basic validity constraints --
minimum size, maximum size, minimum persistence across consecutive windows,
and spatial connectedness/compactness. G, L, D, causal recovery and control
performance are neither computed nor importable here.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from observer import Observation, pairwise_distance
from louvain import louvain


# ---- frozen detector constants (PROTOCOL_6_8.md section 5) -----------------
W_AFFINITY = 8            # affinity averaging window (steps)
SIGMA = 1.75              # Gaussian spatial kernel width, in lattice units
KERNEL_CUTOFF = 4.0       # hard cutoff (kernel set to 0 beyond), lattice units
LOUVAIN_RESOLUTION = 1.0
MIN_SIZE_FRAC = 0.02      # candidate must hold >= 2% of the flock
MAX_SIZE_FRAC = 0.55      # ... and <= 55% (a near-global blob is not a candidate)
MIN_COMPACTNESS = 0.25    # size / (bounding-box area), see `compactness`
CONNECT_RADIUS = 1.75     # spatial-connectedness link radius, lattice units


def gaussian_kernel(D: np.ndarray, sigma: float = SIGMA, cutoff: float = KERNEL_CUTOFF) -> np.ndarray:
    K = np.exp(-(D ** 2) / (2.0 * sigma ** 2))
    K = np.where(D > cutoff, 0.0, K)
    np.fill_diagonal(K, 0.0)
    return K


def coherence_affinity(obs: Observation, W: int = W_AFFINITY, sigma: float = SIGMA) -> np.ndarray:
    """W_ij(t) of task brief section 8."""
    zw = obs.window(W)                                   # (<=W, nn)
    agree = np.zeros((obs.nn, obs.nn))
    for z in zw:
        agree += (z[:, None] == z[None, :]).astype(float)
    agree /= len(zw)
    K = gaussian_kernel(pairwise_distance(obs.positions), sigma)
    A = K * agree
    np.fill_diagonal(A, 0.0)
    return A


# ------------------------------------------------------------ shape metrics -
def compactness(positions: np.ndarray, members: np.ndarray) -> float:
    """|I| / area(axis-aligned bounding box). 1.0 = a solid filled rectangle."""
    if len(members) < 2:
        return 1.0
    p = positions[members]
    ext = p.max(axis=0) - p.min(axis=0) + 1.0
    return float(len(members) / float(ext[0] * ext[1]))


def aspect_ratio(positions: np.ndarray, members: np.ndarray) -> float:
    if len(members) < 2:
        return 1.0
    p = positions[members]
    ext = p.max(axis=0) - p.min(axis=0) + 1.0
    return float(max(ext) / max(1e-9, min(ext)))


def spatially_connected(positions: np.ndarray, members: np.ndarray,
                        radius: float = CONNECT_RADIUS) -> tuple[bool, int]:
    """Connectedness of the members under a plain distance threshold on the
    OBSERVED positions. This is a geometric property of a proposed set, not a
    use of the simulator's interaction graph."""
    m = np.asarray(members)
    if len(m) <= 1:
        return True, len(m)
    p = positions[m]
    D = np.sqrt(((p[:, None, :] - p[None, :, :]) ** 2).sum(-1))
    adj = D <= radius
    seen = np.zeros(len(m), bool)
    ncomp = 0
    for s in range(len(m)):
        if seen[s]:
            continue
        ncomp += 1
        stack = [s]
        seen[s] = True
        while stack:
            a = stack.pop()
            for b in np.where(adj[a] & ~seen)[0]:
                seen[b] = True
                stack.append(int(b))
    return ncomp == 1, ncomp


def internal_coherence(obs: Observation, members: np.ndarray, W: int = W_AFFINITY) -> float:
    """Fraction of members sharing the modal heading, averaged over the window."""
    zw = obs.window(W)
    vals = []
    for z in zw:
        zz = z[members]
        if len(zz) == 0:
            continue
        vals.append(np.bincount(zz, minlength=4).max() / len(zz))
    return float(np.mean(vals)) if vals else float("nan")


# ------------------------------------------------------------------ proposal
@dataclass
class Candidate:
    members: np.ndarray
    method: str
    t: int
    size: int
    coherence: float
    compactness: float
    aspect_ratio: float
    n_spatial_components: int
    centroid: tuple
    modal_heading: int

    def key(self) -> frozenset:
        return frozenset(int(x) for x in self.members)


def describe(obs: Observation, members: np.ndarray, method: str) -> Candidate:
    members = np.array(sorted(int(x) for x in members), dtype=int)
    _, ncomp = spatially_connected(obs.positions, members)
    z = obs.current()[members]
    c = obs.positions[members].mean(axis=0) if len(members) else (np.nan, np.nan)
    return Candidate(
        members=members, method=method, t=obs.t, size=len(members),
        coherence=internal_coherence(obs, members),
        compactness=compactness(obs.positions, members),
        aspect_ratio=aspect_ratio(obs.positions, members),
        n_spatial_components=ncomp,
        centroid=(float(c[0]), float(c[1])),
        modal_heading=int(np.bincount(z, minlength=4).argmax()) if len(z) else -1,
    )


def valid(cand: Candidate, nn: int) -> tuple[bool, str]:
    """Predeclared basic validity constraints ONLY."""
    if cand.size < max(3, int(MIN_SIZE_FRAC * nn)):
        return False, "too_small"
    if cand.size > int(MAX_SIZE_FRAC * nn):
        return False, "too_large"
    if cand.n_spatial_components != 1:
        return False, "not_spatially_connected"
    if cand.compactness < MIN_COMPACTNESS:
        return False, "not_compact"
    return True, "ok"


def propose(obs: Observation, W: int = W_AFFINITY, sigma: float = SIGMA,
            resolution: float = LOUVAIN_RESOLUTION) -> tuple[list[Candidate], list[Candidate]]:
    """Returns (valid_candidates, all_candidates) at time `obs.t`. Multiple
    communities are returned; no single winner is forced."""
    A = coherence_affinity(obs, W=W, sigma=sigma)
    labels = louvain(A, resolution=resolution)
    allc, ok = [], []
    for c in np.unique(labels):
        members = np.where(labels == c)[0]
        cand = describe(obs, members, method="affinity_louvain")
        allc.append(cand)
        if valid(cand, obs.nn)[0]:
            ok.append(cand)
    ok.sort(key=lambda c: -c.size)
    return ok, allc
