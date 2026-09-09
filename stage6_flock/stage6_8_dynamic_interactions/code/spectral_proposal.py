"""Spectral/coherence candidate proposal -- the Stage 6.8 COMPARATOR
(task brief section 10).

INFERENCE-SIDE MODULE.

This is the paper's / Stage 6's Fiedler-style detector, recomputed on the
observed coherence adjacency. Terminology, deliberately and consistently:
this produces a **spectral/coherence proposal**. It is NOT a Markov blanket,
and nothing in Stage 6.8 calls it one. The upstream implementation
(`python/flock_sim/spectral.py`, ported from `getMarkovBlanketOfFlock.m`) is
left untouched; it is reimplemented here rather than imported because that
module is evaluation-side and importing it would breach the firewall, and
because the upstream `classify` step needs no lattice at all -- it operates
purely on the co-heading count matrix, which the observer can see.

Algorithmic equivalence to `python/flock_sim/spectral.py`, asserted in
tests/test_spectral_proposal_matches_upstream.py:
  * `build_adjacency` -- number of window timesteps where z_i == z_j, self
    loops included, exactly as upstream (verified numerically inert for L);
  * combinatorial Laplacian L = D - A, `numpy.linalg.eigh`, second-smallest
    eigenvector, max-abs normalization;
  * `core_pctl=(80, 20)` split into the two cores.
The one Stage 6.8 addition is that the interior side is chosen by a
task-neutral rule (larger co-heading mass) instead of upstream's `refclust`
alignment, because Stage 6.8 has no supplied reference set to align to --
using one would be exactly the "start from a supplied I0" that section 7
forbids.
"""
from __future__ import annotations

import numpy as np

from observer import Observation
from candidate_detection import Candidate, describe, valid, W_AFFINITY


def coheading_adjacency(obs: Observation, W: int = W_AFFINITY) -> np.ndarray:
    zw = obs.window(W)
    A = np.zeros((obs.nn, obs.nn))
    for z in zw:
        A += (z[:, None] == z[None, :]).astype(float)
    return A


def fiedler_split(A: np.ndarray, core_pctl: tuple = (80.0, 20.0)):
    D = np.diag(A.sum(axis=1))
    L = D - A
    eigvals, eigvecs = np.linalg.eigh(L)
    y = eigvecs[:, 1]
    denom = np.max(np.abs(y))
    y = y / denom if denom > 0 else y
    hi, lo = core_pctl
    core1 = np.where(y > np.percentile(y, hi))[0]
    core2 = np.where(y < np.percentile(y, lo))[0]
    return core1, core2, y, eigvals


def propose(obs: Observation, W: int = W_AFFINITY) -> tuple[list[Candidate], list[Candidate]]:
    """Returns (valid, all) spectral/coherence candidates. Both Fiedler cores
    are returned as candidates -- the method does not know which side is 'the'
    collective, and Stage 6.8 does not tell it."""
    A = coheading_adjacency(obs, W)
    core1, core2, y, _ = fiedler_split(A)
    allc, ok = [], []
    for members in (core1, core2):
        if len(members) == 0:
            continue
        cand = describe(obs, members, method="spectral_coherence")
        allc.append(cand)
        if valid(cand, obs.nn)[0]:
            ok.append(cand)
    ok.sort(key=lambda c: -c.size)
    return ok, allc
