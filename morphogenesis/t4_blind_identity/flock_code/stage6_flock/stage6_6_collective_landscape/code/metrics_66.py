"""Metric 1 (coherence) and Metric 4 (local inside/outside contrast) plus the
secondary diagnostics (external entropy, directional opposition). Metrics 2/3
(G_I, L_I) live in predictive_cache.py because they need the mask-cache
machinery. Pure functions of (z, node sets) only -- no simulator/lattice
mutation, easy to unit test in isolation (task brief section 33)."""
from __future__ import annotations

import numpy as np

from common_66 import heading_pmf, unit_heading_vectors, NU
from flock_sim.metrics import coherence as _coherence


def coherence_C(z: np.ndarray, I: np.ndarray) -> float:
    """C_I(t) = max_h (1/|I|) sum_{i in I} 1[z_i(t)=h]. Identical to the frozen
    flock_sim.metrics.coherence -- reused directly, not reimplemented, per the
    task brief's own observation that this is "deliberately simple"."""
    return _coherence(z, I)


def windowed_mean_coherence(z_window: np.ndarray, I: np.ndarray) -> float:
    """bar C_I: secondary diagnostic, mean of C_I(t) over a recent window of
    states. z_window: (n_steps, n_bird)."""
    if len(z_window) == 0:
        return float("nan")
    return float(np.mean([coherence_C(z_window[t], I) for t in range(len(z_window))]))


def jensen_shannon_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """Natural-log JSD, in [0, ln 2] for any two categorical distributions
    (independent of alphabet size). See D_local's own docstring for the
    normalization."""
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    m = 0.5 * (p + q)

    def _kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log(a[mask] / b[mask])))

    return 0.5 * _kl(p, m) + 0.5 * _kl(q, m)


def local_contrast_D(z: np.ndarray, I: np.ndarray, E_near: np.ndarray) -> float:
    """D_local(I) = JSD(p_I, p_E_near) / ln(2), in [0, 1].
    0: inside and near-outside have the same heading distribution.
    1: maximally different (disjoint supports)."""
    p_I = heading_pmf(z, I)
    p_E = heading_pmf(z, E_near)
    return float(jensen_shannon_divergence(p_I, p_E) / np.log(2.0))


def external_entropy_H(z: np.ndarray, E_near: np.ndarray, nu: int = NU) -> float:
    """H_E = -(1/ln nu) sum_h p_E(h) ln p_E(h), in [0,1]. Secondary diagnostic:
    distinguishes an opposite-but-coherent exterior (H_E near 0) from a
    disordered exterior (H_E near 1). Uses the SAME near-exterior set E_near(I)
    as D_local (task brief section 7 leaves p_E's referent implicit; this stage
    fixes it to the near-exterior ring, the only "the exterior" defined for a
    generic candidate -- documented explicitly here rather than left silent)."""
    p_E = heading_pmf(z, E_near, nu=nu)
    mask = p_E > 0
    if not mask.any():
        return 0.0
    ent = -float(np.sum(p_E[mask] * np.log(p_E[mask])))
    return ent / np.log(nu)


def directional_opposition(z: np.ndarray, I: np.ndarray, E_near: np.ndarray) -> dict:
    """Secondary directional-alignment/opposition diagnostic (task brief section
    7). Encodes cardinal headings as unit vectors (same UV4 map as
    flock_sim.model.UV4), takes the mean interior and mean near-exterior
    heading vectors, and reports both the raw cosine similarity (+1 = same
    direction, -1 = opposite) and a [0,1]-normalized "opposition"
    (0 = fully aligned, 1 = fully opposite). Does NOT replace JSD (task brief
    is explicit on this point) -- an opposite-coherent exterior and a
    disordered exterior are both JSD-distinct from the interior but differ in
    cosine similarity (near -1 vs near 0) and in external entropy (near 0 vs
    near 1), which is exactly why both diagnostics are kept."""
    UV4 = unit_heading_vectors()
    if len(I) == 0 or len(E_near) == 0:
        return dict(cosine_similarity=float("nan"), opposition=float("nan"),
                     interior_vector=[float("nan")] * 2, exterior_vector=[float("nan")] * 2)
    v_I = UV4[z[I]].mean(axis=0)
    v_E = UV4[z[E_near]].mean(axis=0)
    n_I, n_E = np.linalg.norm(v_I), np.linalg.norm(v_E)
    if n_I < 1e-12 or n_E < 1e-12:
        cos_sim = 0.0
    else:
        cos_sim = float(np.clip(np.dot(v_I, v_E) / (n_I * n_E), -1.0, 1.0))
    return dict(
        cosine_similarity=cos_sim,
        opposition=float((1.0 - cos_sim) / 2.0),
        interior_vector=v_I.tolist(),
        exterior_vector=v_E.tolist(),
    )
