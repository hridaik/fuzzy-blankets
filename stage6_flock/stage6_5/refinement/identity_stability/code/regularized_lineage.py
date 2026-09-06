"""C2: temporally regularized lineage tracking. Keeps definitions.py's
existing candidate-generation mechanism (core1_nodes/core2_nodes from a
trailing spectral window) unchanged; only regularizes SELECTION among
candidates (including explicitly keeping the previous collective as a
candidate) via

    S(C_t) = F(C_t) + lambda_J * J(C_t, I_{t-1}) - lambda_T * (|C_t triangle I_{t-1}| / |C_t union I_{t-1}|)

F(C_t) is the candidate's own self-coherence at the CURRENT frame
(flock_sim.metrics.coherence) -- a transparent, already-available "how
flock-like is this candidate right now" quality term, independent of
continuity with the past. Note |C triangle I_{t-1}| / |C union I_{t-1}| =
1 - J(C, I_{t-1}) exactly, so S(C) = F(C) + (lambda_J + lambda_T) J(C,
I_{t-1}) - lambda_T -- the two continuity terms in the boxed formula are a
single combined weight up to an additive constant that does not affect the
argmax; both are kept in the implementation below for fidelity to the
formula as given, but this simplification is why lambda_J is fixed
(PROTOCOL_6_5R.md) rather than swept jointly with lambda_T.

Explicitly including I_{t-1} itself as a third candidate (rather than a
separate "keep previous" fallback branch) gives a clean, transparent
hysteresis rule: keeping the previous collective always scores
F(I_{t-1}) + (lambda_J + lambda_T), the maximum possible continuity bonus,
so a genuinely different candidate is only chosen when its own coherence
gain outweighs that bonus -- exactly Part C2's "suppress large changes when
physical state changes little, permit them for genuine transitions"
requirement, tuned by a single scalar (lambda_T, since lambda_J is fixed).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
COLLECTIVE_IDENTITY_CODE = ROOT / "stage6_5" / "collective_identity" / "code"
sys.path.insert(0, str(COLLECTIVE_IDENTITY_CODE))

from flock_sim.spectral import analyze_window  # noqa: E402
from flock_sim.metrics import coherence  # noqa: E402
from definitions import jaccard, TW, _window  # noqa: E402

LAMBDA_J_FIXED = 0.3
# Chosen (before any calibration ran) so the "keep previous" continuity bonus
# does not structurally dominate every possible coherence gain: F(C) in
# [0,1] by construction (flock_sim.metrics.coherence), and S(I_{t-1}) always
# equals F(I_{t-1}) + lambda_J exactly (J(I_{t-1},I_{t-1})=1). A first attempt
# with lambda_J=1.0 was checked analytically (see
# tests/test_regularized_selection.py's derivation in the module docstring
# below) and found to make ANY alternative candidate mathematically unable
# to ever beat keeping the previous collective, regardless of overlap or
# coherence gap -- an unintended de facto permanent freeze, not the
# "suppress jitter, permit genuine transitions" behavior Part C2 asks for.
# lambda_J=0.3 leaves enough headroom for a genuinely large coherence gain
# (up to 1.0) at moderate overlap to still win; the actual suppression/
# permission balance is then tuned by lambda_T alone, calibrated in
# calibrate_lambda_T.py on baseline data only, per PROTOCOL_6_5R.md.


def score(C: np.ndarray, prev: np.ndarray, z_t: np.ndarray, lambda_J: float, lambda_T: float) -> float:
    F = coherence(z_t, C) if len(C) else 0.0
    J = jaccard(C, prev)
    turnover_frac = 1.0 - J  # = |C triangle prev| / |C union prev|
    return F + lambda_J * J - lambda_T * turnover_frac


def regularized_lineage_track(z_hist: np.ndarray, I0: np.ndarray, t_start: int, t_end: int,
                               lambda_T: float, lambda_J: float = LAMBDA_J_FIXED) -> list[np.ndarray]:
    """Same causal, trailing-window candidate generation as
    definitions.lineage_track; selection among {core1, core2, keep-previous}
    replaced by argmax S(C_t) above."""
    out = [np.array(sorted(int(i) for i in I0.tolist()))]
    prev = out[0]
    for t in range(t_start + 1, t_end + 1):
        window = _window(z_hist, t)
        if window.shape[0] < 2:
            out.append(prev)
            continue
        sr = analyze_window(window, refclust=prev)
        candidates = [sr.core1_nodes, sr.core2_nodes, prev]
        best = max(candidates, key=lambda C: score(C, prev, z_hist[t], lambda_J, lambda_T))
        cur = np.array(sorted(int(b) for b in best.tolist()))
        out.append(cur)
        prev = cur
    return out
