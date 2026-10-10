"""C1: separate detector jitter from physical change. D_X(t) = fraction of
ALL birds whose heading changed between t-1 and t (a lattice-wide physical
state-change measure); T_I(t) = |I_t triangle I_{t-1}| (the existing
identity_metrics.turnover). If T_I(t) is large while D_X(t) is small, that
is evidence of detector instability rather than genuine reorganization.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
COLLECTIVE_IDENTITY_CODE = ROOT / "stage6_5" / "collective_identity" / "code"
sys.path.insert(0, str(COLLECTIVE_IDENTITY_CODE))

from flock_sim.metrics import coherence, polarization  # noqa: E402
from identity_metrics import turnover  # noqa: E402


def physical_change_series(z_hist: np.ndarray) -> np.ndarray:
    """D_X(t) for t = 1..nt: fraction of all |V| birds whose heading changed
    from t-1 to t. D_X(0) is undefined (no t-1); index 0 of the returned
    array corresponds to t=1."""
    changed = (z_hist[1:] != z_hist[:-1])
    return changed.mean(axis=1)


def turnover_series(I_track: list[np.ndarray]) -> np.ndarray:
    """T_I(t) for t = 1..n-1 (T_I(0) = 0 by convention, matching
    identity_metrics.track_membership_metrics)."""
    return np.array([turnover(I_track[t - 1], I_track[t]) for t in range(1, len(I_track))])


def jitter_report(z_hist: np.ndarray, I_track: list[np.ndarray]) -> dict:
    """Aligns D_X(t) and T_I(t) (both indexed by transition t-1->t, t=1..n-1)
    and reports simple correlation plus explicit low-D_X/high-T_I flags --
    the direct evidence for 'detector instability, not reorganization'."""
    D_X = physical_change_series(z_hist)
    T_I = turnover_series(I_track)
    n = min(len(D_X), len(T_I))
    D_X, T_I = D_X[:n], T_I[:n]

    if n >= 3 and np.std(D_X) > 0 and np.std(T_I) > 0:
        corr = float(np.corrcoef(D_X, T_I)[0, 1])
    else:
        corr = float("nan")

    dx_median = float(np.median(D_X)) if n else float("nan")
    low_dx_mask = D_X <= dx_median
    ti_p90 = float(np.percentile(T_I, 90)) if n else float("nan")
    jitter_flag = low_dx_mask & (T_I > ti_p90) if n else np.array([], dtype=bool)

    return dict(
        n_steps=n, D_X=D_X.tolist(), T_I=T_I.tolist(),
        pearson_corr_DX_TI=corr,
        D_X_median=dx_median, T_I_p90=ti_p90,
        n_low_DX_high_TI=int(jitter_flag.sum()),
        frac_low_DX_high_TI=float(jitter_flag.mean()) if n else float("nan"),
        mean_T_I_when_low_DX=float(T_I[low_dx_mask].mean()) if low_dx_mask.any() else float("nan"),
        mean_T_I_when_high_DX=float(T_I[~low_dx_mask].mean()) if (~low_dx_mask).any() else float("nan"),
    )
