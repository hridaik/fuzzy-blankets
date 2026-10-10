"""The Stage 6.8 observer / information firewall (task brief section 6).

INFERENCE-SIDE MODULE. `Observation` is the *only* channel through which any
inference module learns anything about the flock. It carries exactly what an
external observer of a physical flock would have:

    ALLOWED                          WITHHELD
    -------                          --------
    bird ids                         the FOV rule
    positions (r_i)                  the effective interaction edges
    headings (z_i)                   the latent stochastic edge gates
    past trajectories (up to t)      the oracle causal interface B_t^D
    interventions this code applied  the simulator's neighbour lists

Positions are newly permitted relative to Stage 6.7 and this is a real
weakening of the firewall on a fixed lattice: geometric adjacency IS
recoverable from positions. It is disclosed in PLAN.md and PROTOCOL_6_8.md
rather than hidden. What stays hidden -- and what Stage 6.8 actually asks
about -- is the heading-dependent *directed subset* of that adjacency which is
causally live at time t, which no function of positions can supply.

`Observation.window()` never returns an index greater than `t`, so no
inference module can see the future even by accident.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Observation:
    """Everything the observer knows at time `t`."""
    positions: np.ndarray                    # (nn, 2) float
    z_hist: np.ndarray                       # (T+1, nn) int -- may extend past t; see window()
    t: int
    interventions: dict = field(default_factory=dict)   # {t -> {bird: forced_action}}, self-applied only

    def __post_init__(self):
        self.positions = np.asarray(self.positions, dtype=float)
        self.z_hist = np.asarray(self.z_hist, dtype=int)
        self.nn = self.positions.shape[0]

    def window(self, W: int) -> np.ndarray:
        """(<=W, nn) the trailing window of headings ENDING at t, inclusive.
        Never indexes past t."""
        start = max(0, self.t - W + 1)
        return self.z_hist[start:self.t + 1]

    def current(self) -> np.ndarray:
        return self.z_hist[self.t]

    def at(self, t: int) -> np.ndarray:
        if t > self.t:
            raise ValueError(f"observer cannot see t={t} > current t={self.t}")
        return self.z_hist[t]

    def history_upto(self) -> np.ndarray:
        return self.z_hist[:self.t + 1]

    def advanced_to(self, t: int) -> "Observation":
        return Observation(self.positions, self.z_hist, t, self.interventions)


def pairwise_distance(positions: np.ndarray) -> np.ndarray:
    d = positions[:, None, :] - positions[None, :, :]
    return np.sqrt((d ** 2).sum(axis=-1))


def periodic_pairwise_distance(positions: np.ndarray, L: float) -> np.ndarray:
    """Torus distance -- used by Stage 6.9's moving-agent observer; on Stage
    6.8's free-boundary lattice `pairwise_distance` is the one in use."""
    d = np.abs(positions[:, None, :] - positions[None, :, :])
    d = np.minimum(d, L - d)
    return np.sqrt((d ** 2).sum(axis=-1))
