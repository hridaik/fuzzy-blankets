"""INFERENCE-SIDE MODULE -- see blind_cache.py's header for the import
restriction (enforced by tests/test_no_topology_leakage.py).

Task brief section 5: trajectory(=replicate)-level bootstrap resampling of
the WHOLE graph_inference.py procedure, B_boot=30 times per snapshot. Per
directed edge (i<-j), records mean gain, median gain, selection frequency
(fraction of boots with Delta>0), and sign stability -- "an edge should not
be called stable merely because one fit gives a large coefficient."

The edge-stability rule itself (`stability_flags`) is a threshold on
(selection_frequency, sign_stability) that must be frozen from development
seeds 2/3 ONLY (task brief: "Seed 4 is held out for that tuning step. Do not
tune after oracle graph reveal.") -- the driver script that calls this module
is responsible for that freeze order; this module just implements the
statistic and a threshold-application function, so the SAME code path is
used whether developing the threshold or applying it.
"""
from __future__ import annotations

import multiprocessing as mp

import numpy as np

from nodewise_model import flatten_transitions
from directed_graph_inference import infer_directed_graph


def _one_boot(args):
    (z_train, val_prev, val_next, n_bird, shortlist_k, model_kwargs, seed) = args
    rng = np.random.default_rng(seed)
    n_traj = z_train.shape[0]
    idx = rng.integers(0, n_traj, size=n_traj)
    z_b = z_train[idx]
    train_prev, train_next = flatten_transitions(z_b)
    result = infer_directed_graph(train_prev, train_next, val_prev, val_next,
                                   n_bird=n_bird, shortlist_k=shortlist_k,
                                   model_kwargs=model_kwargs, n_jobs=1)
    return result["G"]


def bootstrap_graph(z_train: np.ndarray, z_val: np.ndarray, n_boot: int = 30,
                     shortlist_k: int = 25, model_kwargs: dict | None = None,
                     n_bird: int | None = None, rng: np.random.Generator | None = None,
                     n_jobs: int = 1) -> dict:
    """z_train: (n_traj, n_time, n_bird), resampled WITH REPLACEMENT along the
    trajectory(=replicate) axis only -- a resampled trajectory keeps all its
    own timesteps intact, so no transition is invented that never happened.
    z_val is held fixed (mirrors stage6_5/boundary_inference/code/bootstrap.py's
    convention) so validated loss is comparable boot-to-boot.

    Returns dict(edge_stats={i: {j: dict(mean_gain, median_gain,
    selection_frequency, sign_stability, n_boot_shortlisted)}}, n_boot=..)."""
    model_kwargs = model_kwargs or {}
    n_bird = n_bird or z_train.shape[-1]
    rng = rng or np.random.default_rng(0)
    val_prev, val_next = flatten_transitions(z_val)

    seeds = rng.integers(0, 2**31 - 1, size=n_boot)
    tasks = [(z_train, val_prev, val_next, n_bird, shortlist_k, model_kwargs, int(s)) for s in seeds]

    if n_jobs > 1:
        with mp.Pool(n_jobs) as pool:
            boot_graphs = pool.map(_one_boot, tasks)
    else:
        boot_graphs = [_one_boot(t) for t in tasks]

    edge_stats = {}
    for i in range(n_bird):
        edge_stats[i] = {}
        for j in range(n_bird):
            if j == i:
                continue
            gains = np.array([g[i][j] for g in boot_graphs])
            n_shortlisted = int(np.sum(gains != 0.0))
            selection_frequency = float(np.mean(gains > 0))
            n_pos = int(np.sum(gains > 0))
            n_neg = int(np.sum(gains < 0))
            sign_stability = float(max(n_pos, n_neg) / n_boot) if n_boot else float("nan")
            edge_stats[i][j] = dict(
                mean_gain=float(gains.mean()), median_gain=float(np.median(gains)),
                selection_frequency=selection_frequency, sign_stability=sign_stability,
                n_boot_shortlisted=n_shortlisted,
            )
    return dict(edge_stats=edge_stats, n_boot=n_boot, n_bird=n_bird, shortlist_k=shortlist_k)


def stability_flags(edge_stats: dict, tau_freq: float, tau_sign: float) -> dict:
    """Applies the frozen edge-stability rule:
    stable(i<-j) <=> selection_frequency >= tau_freq AND sign_stability >= tau_sign.
    Returns {i: {j: bool}}."""
    flags = {}
    for i, row in edge_stats.items():
        flags[i] = {}
        for j, s in row.items():
            flags[i][j] = bool(s["selection_frequency"] >= tau_freq and s["sign_stability"] >= tau_sign)
    return flags
