"""Top-level simulation driver. All randomness flows through an explicit
numpy.random.Generator supplied by the caller (never global RNG state), per the
task brief's requirement.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .lattice import Lattice
from .model import ModelParams
from .active_inference import PrecomputedModel, build_model, step


@dataclass
class SimulationResult:
    z_hist: np.ndarray            # (nt+1, nn) heading at each timestep incl. initial
    natural_action_hist: np.ndarray   # (nt, nn)
    applied_action_hist: np.ndarray   # (nt, nn)
    overridden_hist: np.ndarray       # (nt, nn) bool
    params: ModelParams
    nn: int
    nt: int
    seed: int


def init_headings(nn: int, nu: int, rng: np.random.Generator, pu: np.ndarray | None = None) -> np.ndarray:
    if pu is None:
        pu = np.full(nu, 1.0 / nu)
    cdf = np.cumsum(pu)
    cdf[-1] = 1.0
    u = rng.random(nn)
    return (u[:, None] > cdf[None, :]).sum(axis=1).astype(int).clip(max=nu - 1)


def run_simulation(
    nn: int = 100,
    nt: int = 60,
    seed: int = 0,
    params: ModelParams | None = None,
    nh: int = 8,
    interventions: dict[int, dict[int, int]] | None = None,
    init_z: np.ndarray | None = None,
    pm: PrecomputedModel | None = None,
    lattice: Lattice | None = None,
) -> SimulationResult:
    """interventions: {timestep -> {bird_id -> forced_action}}. Timesteps are
    0-based, indexing which *transition* (z_hist[t] -> z_hist[t+1]) is forced."""
    params = params or ModelParams()
    lattice = lattice or Lattice(nn=nn, nh=nh)
    pm = pm or build_model(params)
    rng = np.random.default_rng(seed)

    z = init_z if init_z is not None else init_headings(nn, params.nu, rng)
    z_hist = np.zeros((nt + 1, nn), dtype=int)
    z_hist[0] = z
    nat_hist = np.zeros((nt, nn), dtype=int)
    app_hist = np.zeros((nt, nn), dtype=int)
    ovr_hist = np.zeros((nt, nn), dtype=bool)

    interventions = interventions or {}
    for t in range(nt):
        forced = interventions.get(t)
        out = step(pm, lattice, z, rng, forced_actions=forced)
        z = out["z_new"]
        z_hist[t + 1] = z
        nat_hist[t] = out["natural_action"]
        app_hist[t] = out["applied_action"]
        ovr_hist[t] = out["was_overridden"]

    return SimulationResult(
        z_hist=z_hist,
        natural_action_hist=nat_hist,
        applied_action_hist=app_hist,
        overridden_hist=ovr_hist,
        params=params,
        nn=nn,
        nt=nt,
        seed=seed,
    )
