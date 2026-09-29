"""Field law: isotropic exponential-decay signal superposition.

Port of the local function `morphogenesis(x,s,y)` in DEM_morphogenesis.m
(lines 350-376). See MODEL_SPEC.md section 2. ESTABLISHED, k=1 hard-coded in
source, transcribed as such (not exposed as a free parameter).
"""
import numpy as np

K_DECAY = 1.0  # hard-coded in source; do not expose as a config knob


def field_concentration(x: np.ndarray, s: np.ndarray, y: np.ndarray = None) -> np.ndarray:
    """x: (2,n) source positions, s: (m,n) source signal levels,
    y: (2,k) sample positions [default: x]. Returns c: (m,k).
    """
    if y is None:
        y = x
    diff = y[:, :, None] - x[:, None, :]          # (2, k, n)
    d = np.sqrt(np.sum(diff ** 2, axis=0))          # (k, n)
    weight = np.exp(-K_DECAY * d)                   # (k, n)
    c = weight @ s.T                                 # (k, m)
    return c.T                                       # (m, k)
