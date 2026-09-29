"""Generative model Mg and generative process Gg.

Port of DEM_morphogenesis.m local functions Mg (lines 397-410) and Gg (lines
381-394). See MODEL_SPEC.md sections 2-3. ESTABLISHED transcription of the
mappings themselves; the *integration scheme* around them (spm_ADEM's D-step)
is a disclosed reduced reconstruction, not a byte-level port -- see
DISCREPANCIES.md section 9 and solver.py.
"""
import numpy as np
from field import field_concentration


def spm_softmax_cols(x: np.ndarray) -> np.ndarray:
    """Softmax over columns (spm_softmax.m, verified full-text read)."""
    x = x - x.max(axis=0, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=0, keepdims=True)


def sensitivity(t: float) -> float:
    """s = 1 - exp(-2t); t assigned as iY/nY in spm_ADEM.m line 444.
    See MODEL_SPEC.md section 3 for the code/paper discrepancy (paper: linear)."""
    return 1.0 - np.exp(-2.0 * t)


def Mg(v: np.ndarray, P_x: np.ndarray, P_s: np.ndarray, P_c: np.ndarray, t: float):
    """Generative model: hidden cause v (n_identity, n_cells) -> predicted
    sensations (position, intrinsic signal, extrinsic signal)."""
    s = sensitivity(t)
    p = spm_softmax_cols(v)          # (n_identity, n_cells)
    g_x = P_x @ p                     # (2, n_cells)
    g_s = P_s @ p                     # (m, n_cells)
    g_c = s * (P_c @ p)               # (m, n_cells)
    return g_x, g_s, g_c, p


def Gg(a_x: np.ndarray, a_s: np.ndarray, t: float):
    """Generative process: action (position, secretion) -> actual sensations.
    Position/intrinsic signal pass through unchanged (g.x=a.x, g.s=a.s);
    extrinsic signal is the field sampled at the cells' own positions."""
    s = sensitivity(t)
    g_x = a_x.copy()
    g_s = a_s.copy()
    g_c = s * field_concentration(a_x, a_s)
    return g_x, g_s, g_c
