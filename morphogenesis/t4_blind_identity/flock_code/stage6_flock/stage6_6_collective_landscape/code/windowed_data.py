"""Section 6 of the task brief: past-only local regime dataset for a
snapshot at time t, built from R=100 paired replicates branching from a
common ancestor state, pooling the trailing W=10-step window ending at t.

"Paired" mirrors v2_interface_control/code/common_v2.py:evaluate_arm's
common-random-number replicate scheme: every replicate shares the same
init_z (the branch state) and the same interventions profile (the
condition being visualized -- natural, or one of the archetypes), and
differs only in its RNG seed (seed_offset + r). Never uses future
observations relative to t (each replicate is only run out to at least t;
data are simply the trailing states of the same forward rollout used to
*reach* t, nothing beyond it is read).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from common_66 import run_simulation, R_REPLICATES, W_WINDOW

TRAIN_FRACTION = 0.7   # trajectory-level split of the R replicates; frozen here,
                        # restated in configs/protocol_6_6.yaml at freeze time.


@dataclass
class WindowDataset:
    train_prev: np.ndarray
    train_next: np.ndarray
    val_prev: np.ndarray
    val_next: np.ndarray
    n_replicates: int
    n_replicates_train: int
    n_replicates_val: int
    effective_window: int   # actual number of states used (<= W_WINDOW)
    t: int
    representative_z: np.ndarray   # z at time t, replicate 0 -- "one representative realization"


def run_condition_replicates(z_branch: np.ndarray, lattice, interventions: dict | None,
                              nt: int, n_rep: int = R_REPLICATES, seed_offset: int = 0) -> np.ndarray:
    """Returns z_hist_reps: (n_rep, nt+1, n_bird). Replicate r uses
    seed=seed_offset+r, all branching from the same init_z=z_branch and the
    same `interventions` dict (None for the uncontrolled/natural condition)."""
    nn = lattice.nn
    out = np.zeros((n_rep, nt + 1, nn), dtype=int)
    for r in range(n_rep):
        res = run_simulation(nn=nn, nt=nt, seed=seed_offset + r, init_z=z_branch,
                              interventions=interventions, lattice=lattice)
        out[r] = res.z_hist
    return out


def build_window_dataset(z_hist_reps: np.ndarray, t: int, W: int = W_WINDOW,
                          train_fraction: float = TRAIN_FRACTION, split_seed: int = 0) -> WindowDataset:
    """z_hist_reps: (R, nt+1, n_bird). t: absolute timestep index (0-based) into
    the replicate axis-1; the snapshot being visualized. Window = states
    [max(0, t-W+1), t] inclusive, per replicate -- never reads index > t."""
    n_rep, nt_plus1, n_bird = z_hist_reps.shape
    start = max(0, t - W + 1)
    effective_window = t - start + 1
    if effective_window < 2:
        raise ValueError(f"t={t} leaves fewer than 2 states of history (effective_window={effective_window}); "
                          "cannot form even one transition")

    rng = np.random.default_rng(split_seed)
    order = rng.permutation(n_rep)
    n_train = max(1, int(round(train_fraction * n_rep)))
    n_train = min(n_train, n_rep - 1) if n_rep > 1 else n_rep
    train_ids = order[:n_train]
    val_ids = order[n_train:]
    if len(val_ids) == 0:
        # degenerate (very small n_rep): fall back to reusing train as val,
        # documented rather than silently producing an empty val set.
        val_ids = train_ids

    def _flatten(ids):
        prev_list, next_list = [], []
        for r in ids:
            traj = z_hist_reps[r, start:t + 1]   # (effective_window, n_bird)
            prev_list.append(traj[:-1])
            next_list.append(traj[1:])
        if not prev_list:
            return np.zeros((0, n_bird), dtype=int), np.zeros((0, n_bird), dtype=int)
        return np.concatenate(prev_list, axis=0), np.concatenate(next_list, axis=0)

    train_prev, train_next = _flatten(train_ids)
    val_prev, val_next = _flatten(val_ids)

    return WindowDataset(
        train_prev=train_prev, train_next=train_next,
        val_prev=val_prev, val_next=val_next,
        n_replicates=n_rep, n_replicates_train=len(train_ids), n_replicates_val=len(val_ids),
        effective_window=effective_window, t=t,
        representative_z=z_hist_reps[0, t],
    )
