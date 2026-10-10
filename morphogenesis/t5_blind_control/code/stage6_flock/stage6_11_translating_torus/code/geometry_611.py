"""Stage 6.11 shared OBSERVER-SIDE geometry helpers.

INFERENCE-SIDE. Deliberately duplicates a few primitives that also exist in
the privileged `phase_metrics_611.py` (torus distance, union-find components)
rather than importing them -- `phase_metrics_611` is explicitly declared
world-selection-only/privileged, and re-implementing a few lines of torus
arithmetic here is the price of keeping that boundary real rather than
notional. Nothing in this file ever receives the true interaction radius R,
the true live-edge graph, or the FOV rule; every scale used below (spacing,
periphery shell, compactness radius) is estimated from observed positions.
"""
from __future__ import annotations

import numpy as np

# Fixed a priori (task brief item 8's "coarse, predeclared" spirit), not
# tuned on any detection/thingness/control outcome. A single multiplier used
# everywhere a "local neighbourhood scale" is needed, so the observer commits
# to one rule for "how far is local" rather than picking a different number
# per use.
SPACING_MULTIPLIER = 2.5


def torus_delta(a: np.ndarray, b: np.ndarray, L: float) -> np.ndarray:
    return (a - b + L / 2.0) % L - L / 2.0


def torus_distance_matrix(r: np.ndarray, L: float) -> np.ndarray:
    d = torus_delta(r[None, :, :], r[:, None, :], L)
    D = np.sqrt((d ** 2).sum(-1))
    np.fill_diagonal(D, np.inf)
    return D


def typical_spacing(r: np.ndarray, L: float) -> float:
    """Median nearest-neighbour distance over ALL observed birds -- an
    observable density scale, standing in for the (withheld) true R."""
    D = torus_distance_matrix(r, L)
    return float(np.median(D.min(axis=1)))


def local_scale(r: np.ndarray, L: float) -> float:
    """The one length scale this stage's observer code is allowed to derive
    and reuse: SPACING_MULTIPLIER x typical nearest-neighbour spacing."""
    return SPACING_MULTIPLIER * typical_spacing(r, L)


def bearing_octant(delta: np.ndarray, ref_heading: np.ndarray) -> np.ndarray:
    """Coarse relative bearing of `delta` (displacement TO a neighbour) as an
    octant index (0..7) measured relative to `ref_heading` (a unit vector per
    row), i.e. 0 = straight ahead, 4 = straight behind. Coarse/predeclared,
    per task brief item 6."""
    ang_delta = np.arctan2(delta[..., 1], delta[..., 0])
    ang_ref = np.arctan2(ref_heading[..., 1], ref_heading[..., 0])
    rel = (ang_delta - ang_ref) % (2 * np.pi)
    return np.round(rel / (np.pi / 4)).astype(int) % 8


def distance_bin_edges(distances: np.ndarray, n_bins: int = 3) -> np.ndarray:
    """Equal-frequency (quantile) bin edges over an observed distance sample.
    Never a function of the true interaction radius -- only of what the
    observer has actually measured (task brief item 6)."""
    qs = np.linspace(0, 1, n_bins + 1)[1:-1]
    return np.quantile(distances, qs)


def digitize_distance(d: np.ndarray, cut_points: np.ndarray) -> np.ndarray:
    return np.digitize(d, cut_points)


def connected_components(members: np.ndarray, r: np.ndarray, L: float, radius: float) -> int:
    """Number of spatially connected components within `members`, at `radius`."""
    if len(members) <= 1:
        return 1 if len(members) else 0
    sub = r[members]
    D = torus_distance_matrix(sub, L)
    adj = D <= radius
    n = len(members)
    seen = np.zeros(n, dtype=bool)
    ncomp = 0
    for s in range(n):
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
    return ncomp


def compactness(members: np.ndarray, r: np.ndarray, L: float, centre: np.ndarray) -> float:
    """Q: fraction-of-max-possible-density shape compactness, in (0, 1].
    1.0 for a perfectly disc-packed cluster, falling for elongated/sparse
    shapes. Uses only member positions and the observer's own local_scale."""
    rel = torus_delta(r[members], centre, L)
    if len(rel) < 3:
        return 1.0
    ext = rel.max(0) - rel.min(0) + 1e-9
    area = float(ext[0] * ext[1])
    return float(min(1.0, len(members) / max(area, 1e-9) / (1.0 / (np.pi * 0.5 ** 2))))


def modal_heading(z_members: np.ndarray, nu: int = 4) -> int:
    counts = np.bincount(z_members, minlength=nu)
    return int(np.argmax(counts))


def local_exterior_contrast(members: np.ndarray, r: np.ndarray, z: np.ndarray, L: float,
                             periphery_radius: float, nu: int = 4) -> float:
    """D: local exterior contrast. 1 - (fraction of the candidate's spatial
    periphery -- non-members within periphery_radius of ANY member -- that share
    the candidate's own modal heading). D near 1: periphery looks behaviourally
    distinct (candidate stands out). D near 0: periphery blends in (approaching
    population-wide alignment -- the "losing individuation" signature, task
    brief item 9)."""
    N = len(z)
    member_set = set(int(m) for m in members)
    non_members = np.array([i for i in range(N) if i not in member_set])
    if len(non_members) == 0 or len(members) == 0:
        return 1.0
    d = torus_delta(r[non_members][:, None, :], r[members][None, :, :], L)
    D = np.sqrt((d ** 2).sum(-1))
    near_any = (D <= periphery_radius).any(axis=1)
    periphery = non_members[near_any]
    if len(periphery) == 0:
        return 1.0
    mod = modal_heading(z[members], nu)
    agree = float((z[periphery] == mod).mean())
    return float(1.0 - agree)
