"""Sparse external-actuator intervention construction (Phase 3)."""
from __future__ import annotations

import numpy as np


def make_pulse(actuators: list[int] | np.ndarray, h_star: int, t0: int, t_u: int) -> dict[int, dict[int, int]]:
    """Force every bird in `actuators` toward action h_star for timesteps
    t0 <= t < t0 + t_u (0-based timestep = which transition z_hist[t]->z_hist[t+1]
    is forced)."""
    actuators = list(actuators)
    return {t: {int(b): int(h_star) for b in actuators} for t in range(t0, t0 + t_u)}
