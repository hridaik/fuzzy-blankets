"""Fiedler-vector Markov-blanket identification, ported from
getMarkovBlanketOfFlock.m. See METHODS_AUDIT.md section 10 for the itemized
audit of every design choice here (fixed 0.05 absolute threshold vs. the
manuscript's stated adaptive-percentile rule; the "normalized Laplacian" comment
being wrong in the original; inert self-loops; non-partition classification;
arbitrary eigenvector sign).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SpectralResult:
    A: np.ndarray            # (nn,nn) weighted adjacency (with inert diagonal = TW)
    L: np.ndarray            # (nn,nn) combinatorial Laplacian D - A
    eigvals: np.ndarray       # ascending
    fiedler_raw: np.ndarray   # unit-norm eigenvector for the 2nd-smallest eigenvalue (arbitrary sign)
    fiedler_norm: np.ndarray  # max-abs normalized to [-1, 1] (upstream convention)
    lambda1: float
    lambda2: float
    lambda3: float
    eigengap: float
    n_components: int        # count of eigenvalues ~ 0 (connectivity diagnostic)
    core1_nodes: np.ndarray
    core2_nodes: np.ndarray
    boundary_nodes: np.ndarray
    active_nodes: np.ndarray   # subset of boundary_nodes, closer to core1
    sensory_nodes: np.ndarray  # subset of boundary_nodes, closer to core2
    labels: np.ndarray         # (nn,) in {0:internal(core1 default),1:external(core2),2:active,3:sensory}


def build_adjacency(z_window: np.ndarray) -> np.ndarray:
    """z_window: (TW, nn) heading history over the trailing window.
    A[i,j] = number of timesteps in the window where z_i(t) == z_j(t), for all
    i,j including i==j (upstream literally loops j=i:nn, so self-loops with
    A[i,i] = TW are present by construction — verified numerically inert for L,
    see METHODS_AUDIT.md section 10)."""
    TW, nn = z_window.shape
    A = np.zeros((nn, nn))
    for t in range(TW):
        z = z_window[t]
        A += (z[:, None] == z[None, :]).astype(float)
    return A


ZERO_EIG_TOL = 1e-8


def compute_fiedler(A: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float, float, int]:
    D = np.diag(A.sum(axis=1))
    L = D - A
    # symmetric eigensolver: equivalent to MATLAB's eig(full(L)) + ascending sort
    # for a real symmetric matrix, EXCEPT that eigenvector sign is solver-
    # dependent (LAPACK convention), hence never comparable across time/solvers
    # without explicit sign alignment (align_to_reference below).
    eigvals, eigvecs = np.linalg.eigh(L)
    fiedler_raw = eigvecs[:, 1]
    denom = np.max(np.abs(fiedler_raw))
    fiedler_norm = fiedler_raw / denom if denom > 0 else fiedler_raw.copy()
    lambda1, lambda2, lambda3 = eigvals[0], eigvals[1], eigvals[2]
    eigengap = lambda3 - lambda2
    n_components = int(np.sum(eigvals < ZERO_EIG_TOL))
    return L, eigvals, fiedler_raw, fiedler_norm, lambda1, lambda2, lambda3, eigengap, n_components


def classify(
    A: np.ndarray,
    fiedler_norm: np.ndarray,
    boundary_rule: str = "fixed",
    fixed_threshold: float = 0.05,
    adaptive_pctl: tuple[float, float] = (10.0, 20.0),
    core_pctl: tuple[float, float] = (80.0, 20.0),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Literal port of information_flow_interpretation. boundary_rule='fixed'
    reproduces the released code exactly (|y2| < 0.05, absolute, on the
    max-abs-normalized vector). boundary_rule='adaptive' implements the
    manuscript's stated-but-unimplemented 10th-20th percentile of |y2| rule as an
    explicit, separate, opt-in alternative (see METHODS_AUDIT.md section 10,
    discrepancy #2) — never silently substituted for 'fixed'."""
    y2 = fiedler_norm
    nn = len(y2)
    hi, lo = core_pctl
    core1_nodes = np.where(y2 > np.percentile(y2, hi))[0]
    core2_nodes = np.where(y2 < np.percentile(y2, lo))[0]

    if boundary_rule == "fixed":
        boundary_nodes = np.where(np.abs(y2) < fixed_threshold)[0]
    elif boundary_rule == "adaptive":
        lo_p, hi_p = adaptive_pctl
        absy = np.abs(y2)
        lo_val = np.percentile(absy, lo_p)
        hi_val = np.percentile(absy, hi_p)
        boundary_nodes = np.where((absy >= lo_val) & (absy <= hi_val))[0]
    else:
        raise ValueError(f"unknown boundary_rule {boundary_rule!r}")

    conn1 = A[np.ix_(boundary_nodes, core1_nodes)].sum(axis=1) if len(core1_nodes) else np.zeros(len(boundary_nodes))
    conn2 = A[np.ix_(boundary_nodes, core2_nodes)].sum(axis=1) if len(core2_nodes) else np.zeros(len(boundary_nodes))

    active_mask = conn1 >= conn2
    active_nodes = boundary_nodes[active_mask]
    sensory_nodes = boundary_nodes[~active_mask]

    # Reproduce the exact (non-partitioning) labeling logic in
    # getMarkovBlanketOfFlock.m: default label 0 ("internal"/core1) for
    # everything, then overwrite core2 -> 1, boundary(active) -> 2, boundary
    # (sensory) -> 3. Any node that is neither core1, core2, nor boundary is
    # left at the default label 0, i.e. lumped in with "internal" even though it
    # was never actually placed in core1_nodes. See METHODS_AUDIT.md section 10.
    labels = np.zeros(nn, dtype=int)
    labels[core2_nodes] = 1
    labels[active_nodes] = 2
    labels[sensory_nodes] = 3

    return core1_nodes, core2_nodes, boundary_nodes, active_nodes, sensory_nodes, labels


def align_to_reference(
    core1_nodes: np.ndarray, core2_nodes: np.ndarray, conn1: np.ndarray, conn2: np.ndarray, refclust: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Literal port of the refclust swap logic at the top of
    getMarkovBlanketOfFlock.m: if core2 overlaps the reference set more than
    core1 does (by raw membership count, not Jaccard), swap the two labels so
    that "core1"/internal continues to denote the side tracking the reference."""
    overlap1 = np.isin(core1_nodes, refclust).sum()
    overlap2 = np.isin(core2_nodes, refclust).sum()
    if overlap1 < overlap2:
        return core2_nodes, core1_nodes
    return core1_nodes, core2_nodes


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    sa, sb = set(a.tolist()), set(b.tolist())
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def analyze_window(
    z_window: np.ndarray,
    refclust: np.ndarray | None = None,
    boundary_rule: str = "fixed",
) -> SpectralResult:
    A = build_adjacency(z_window)
    L, eigvals, fiedler_raw, fiedler_norm, l1, l2, l3, gap, ncomp = compute_fiedler(A)
    core1, core2, boundary, active, sensory, labels = classify(A, fiedler_norm, boundary_rule=boundary_rule)

    if refclust is not None and len(refclust) > 0:
        core1, core2 = align_to_reference(core1, core2, None, None, refclust)
        # relabel boundary active/sensory & full label array consistent with the swap
        conn1 = A[np.ix_(boundary, core1)].sum(axis=1) if len(core1) else np.zeros(len(boundary))
        conn2 = A[np.ix_(boundary, core2)].sum(axis=1) if len(core2) else np.zeros(len(boundary))
        active_mask = conn1 >= conn2
        active = boundary[active_mask]
        sensory = boundary[~active_mask]
        labels = np.zeros(len(fiedler_norm), dtype=int)
        labels[core2] = 1
        labels[active] = 2
        labels[sensory] = 3

    return SpectralResult(
        A=A, L=L, eigvals=eigvals, fiedler_raw=fiedler_raw, fiedler_norm=fiedler_norm,
        lambda1=l1, lambda2=l2, lambda3=l3, eigengap=gap, n_components=ncomp,
        core1_nodes=core1, core2_nodes=core2, boundary_nodes=boundary,
        active_nodes=active, sensory_nodes=sensory, labels=labels,
    )
