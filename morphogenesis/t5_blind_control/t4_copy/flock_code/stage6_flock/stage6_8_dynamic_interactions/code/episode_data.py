"""Episode / observation-record construction (EVALUATION-SIDE).

Builds the data the observer is given. Two distinct protocols, kept explicit:

* **Detection and tracking** run truly online on the SINGLE real trajectory --
  `Observation(positions, z_hist, t)` with `t` advancing one step at a time.
  No replicates, no future.

* **Predictive model fitting** needs more transitions than one W-step window
  contains (a window of 10 steps gives 9 transitions; the models have hundreds
  of parameters). Stage 6.6/6.7 solved this with R repeated observations of the
  same flock condition, and Stage 6.8 carries that protocol over UNCHANGED:
  `R` replicates are branched from the episode's own state at `t - W + 1` and
  rolled forward `W - 1` steps under independent noise. This is a disclosed
  repeated-observation assumption, not a claim that one passive trajectory
  suffices.

The 60/20/20 split is at the REPLICATE level with a fixed `split_seed`, so
every transition from a replicate stays in one split and nothing leaks across
the boundary -- the same convention as `stage6_7.../common_67.WindowDataset3`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from common_68 import ModelParams, Lattice, lattice_positions, RHO, OMEGA
from fov_dynamics import FovSimulator, GateParams

W_WINDOW = 10
R_REPLICATES = 100
SPLIT_SEED = 0
TRAIN_FRAC, VAL_FRAC = 0.6, 0.2
REPLICATE_SEED_OFFSET = 880_000     # disjoint from every earlier stage's offsets


@dataclass
class Splits:
    tr_prev: np.ndarray; tr_next: np.ndarray
    va_prev: np.ndarray; va_next: np.ndarray
    te_prev: np.ndarray; te_next: np.ndarray
    te_traj: np.ndarray                 # test-row -> replicate id, for the trajectory bootstrap
    z_reps: np.ndarray                  # (R, W, nn) the replicate window itself
    t: int
    n_train: int; n_val: int; n_test: int


def make_simulator(nn: int, beta: float, s: float) -> FovSimulator:
    return FovSimulator(ModelParams(beta=beta, precB=s * RHO, precC=s * OMEGA),
                        Lattice(nn=nn, nh=8))


def run_episode(sim: FovSimulator, seed: int, nt: int, gate_params=None, record_oracle=True):
    return sim.run(nt=nt, seed=seed, gate_params=gate_params, record_oracle=record_oracle)


def replicate_window(sim: FovSimulator, z_start: np.ndarray, n_steps: int,
                     n_rep: int = R_REPLICATES, seed_offset: int = REPLICATE_SEED_OFFSET,
                     gate_params=None) -> np.ndarray:
    """(n_rep, n_steps+1, nn) replicate rollouts from a common start state."""
    out = np.zeros((n_rep, n_steps + 1, sim.nn), dtype=int)
    for r in range(n_rep):
        res = sim.run(nt=n_steps, seed=seed_offset + r, init_z=z_start,
                      gate_params=gate_params, record_oracle=False)
        out[r] = res.z_hist
    return out


def build_splits(z_reps: np.ndarray, t: int, split_seed: int = SPLIT_SEED) -> Splits:
    n_rep, n_time, nn = z_reps.shape
    rng = np.random.default_rng(split_seed)
    order = rng.permutation(n_rep)
    n_tr = max(1, int(round(TRAIN_FRAC * n_rep)))
    n_va = max(1, int(round(VAL_FRAC * n_rep)))
    tr_ids, va_ids, te_ids = order[:n_tr], order[n_tr:n_tr + n_va], order[n_tr + n_va:]
    if len(te_ids) == 0:
        te_ids = va_ids

    def flat(ids):
        p, n, tid = [], [], []
        for r in ids:
            traj = z_reps[r]
            p.append(traj[:-1]); n.append(traj[1:])
            tid.append(np.full(traj.shape[0] - 1, r))
        return (np.concatenate(p), np.concatenate(n), np.concatenate(tid))

    trp, trn, _ = flat(tr_ids)
    vap, van, _ = flat(va_ids)
    tep, ten, tet = flat(te_ids)
    return Splits(trp, trn, vap, van, tep, ten, tet, z_reps, t,
                  len(tr_ids), len(va_ids), len(te_ids))


def observation_record(sim: FovSimulator, z_hist: np.ndarray, t: int, interventions=None):
    """The inference-side view. Deliberately constructed HERE (evaluation-side)
    and handed over as a plain data object."""
    from observer import Observation
    return Observation(lattice_positions(sim.nn), z_hist, t, interventions or {})
