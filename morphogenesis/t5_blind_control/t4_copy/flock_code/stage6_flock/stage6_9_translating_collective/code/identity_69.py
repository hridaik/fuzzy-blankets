"""Three identity notions for a translating collective (task brief sections
28-32).

INFERENCE-SIDE / OBSERVER-FACING. Everything here is computed from observed
positions and headings plus the detector's own membership sets. The
simulator's true centre trajectory is never used (task brief section 29).

    Material identity      R_M(t) = |I_t n I_{t0}| / |I_{t0}|
    Ordinary lineage       J(I_t, I_{t-1})
    Co-moving functional   R_F(t), from a density/orientation field compared
                           after removing the estimated bulk translation

The field representation, centred on the collective's own current frame:

    rho_t(x) = sum_{i in I_t} K(x - (r_i - c_t))
    m_t(x)   = sum_{i in I_t} d_i K(x - (r_i - c_t)) / (rho_t(x) + eps)
    phi_t    = (rho_t, m_t)

Translation is estimated by centroid displacement, then refined by local
cross-correlation of the fields over a small integer-pixel search
(`estimate_translation`). Deformation is what is left after removing the best
bulk translation, so bulk motion is never mistaken for destruction.
"""
from __future__ import annotations

import numpy as np

GRID_HALF = 8.0        # field half-width, in space units, around the centroid
GRID_STEP = 0.5        # field pixel size
KERNEL_SIGMA = 0.9     # smoothing kernel width
EPS = 1e-9
SEARCH_PIX = 6         # +/- pixels of cross-correlation refinement


def torus_delta(a, b, L):
    return (a - b + L / 2) % L - L / 2


def centroid(r_members: np.ndarray, L: float) -> np.ndarray:
    """Torus-safe centroid: take the first member as a reference and average the
    minimum-image offsets around it."""
    ref = r_members[0]
    rel = torus_delta(r_members, ref, L)
    return (ref + rel.mean(axis=0)) % L


def field(r_members: np.ndarray, d_members: np.ndarray, L: float, centre: np.ndarray,
          half: float = GRID_HALF, step: float = GRID_STEP,
          sigma: float = KERNEL_SIGMA):
    """(rho, m) on a fixed grid in the collective's own co-moving frame."""
    ax = np.arange(-half, half + step / 2, step)
    X, Y = np.meshgrid(ax, ax, indexing="ij")
    rel = torus_delta(r_members, centre, L)
    inside = (np.abs(rel[:, 0]) <= half + 3 * sigma) & (np.abs(rel[:, 1]) <= half + 3 * sigma)
    rel, dm = rel[inside], d_members[inside]
    rho = np.zeros_like(X)
    m = np.zeros(X.shape + (2,))
    for p, d in zip(rel, dm):
        w = np.exp(-((X - p[0]) ** 2 + (Y - p[1]) ** 2) / (2 * sigma ** 2))
        rho += w
        m += w[..., None] * d[None, None, :]
    m = m / (rho[..., None] + EPS)
    return rho, m, ax


def _shift(a: np.ndarray, dx: int, dy: int) -> np.ndarray:
    return np.roll(np.roll(a, dx, axis=0), dy, axis=1)


def field_distance(rho_a, m_a, rho_b, m_b) -> float:
    """Normalized L2 distance between two fields: density mismatch plus
    density-weighted orientation mismatch."""
    denom = np.sqrt((rho_a ** 2).sum()) + np.sqrt((rho_b ** 2).sum()) + EPS
    d_rho = np.sqrt(((rho_a - rho_b) ** 2).sum()) / denom
    w = np.minimum(rho_a, rho_b)
    d_m = np.sqrt((w * ((m_a - m_b) ** 2).sum(-1)).sum() / (w.sum() + EPS)) / 2.0
    return float(0.5 * d_rho + 0.5 * d_m)


def estimate_translation(rho_a, m_a, rho_b, m_b, c_a, c_b, step: float = GRID_STEP,
                         search: int = SEARCH_PIX):
    """Delta_hat = argmin_Delta d(T_Delta phi_t, phi_{t+1}).

    Initialized at the observed centroid displacement (which is already removed
    by centring each field on its own centroid), then refined by an integer-pixel
    cross-correlation search. The simulator's true centre trajectory is never
    consulted."""
    best, best_d = (0, 0), np.inf
    for dx in range(-search, search + 1):
        for dy in range(-search, search + 1):
            d = field_distance(_shift(rho_a, dx, dy), _shift(m_a, dx, dy), rho_b, m_b)
            if d < best_d:
                best, best_d = (dx, dy), d
    refine = np.array(best, dtype=float) * step
    return dict(centroid_delta=c_b - c_a, refine_delta=refine,
                total_delta=(c_b - c_a) + refine, distance=float(best_d),
                distance_centroid_only=float(field_distance(rho_a, m_a, rho_b, m_b)))


def similarity(distance: float, d_norm: float) -> float:
    """R_F(t) = 1 - d(T_Delta phi_t, phi_{t+1}) / d_norm, kept continuous."""
    return float(1.0 - distance / max(d_norm, EPS))


def shape_metrics(r_members: np.ndarray, L: float, centre: np.ndarray) -> dict:
    """Topology/shape record (task brief section 32), so a thin chain or a
    fragmented remnant cannot be labelled the same collective just because its
    centroid moves smoothly."""
    rel = torus_delta(r_members, centre, L)
    if len(rel) < 3:
        return dict(area=0.0, aspect_ratio=1.0, density=0.0, n_components=1,
                    radius_of_gyration=0.0)
    cov = np.cov(rel.T)
    ev = np.sort(np.linalg.eigvalsh(cov))[::-1]
    ext = rel.max(0) - rel.min(0) + 1e-9
    D = np.sqrt(((rel[:, None, :] - rel[None, :, :]) ** 2).sum(-1))
    adj = D <= 1.6
    seen = np.zeros(len(rel), bool); ncomp = 0
    for s in range(len(rel)):
        if seen[s]:
            continue
        ncomp += 1; stack = [s]; seen[s] = True
        while stack:
            a = stack.pop()
            for b in np.where(adj[a] & ~seen)[0]:
                seen[b] = True; stack.append(int(b))
    return dict(area=float(ext[0] * ext[1]),
                aspect_ratio=float(np.sqrt(max(ev[0], EPS) / max(ev[1], EPS))),
                density=float(len(rel) / (ext[0] * ext[1])),
                n_components=int(ncomp),
                radius_of_gyration=float(np.sqrt(np.trace(cov))))
