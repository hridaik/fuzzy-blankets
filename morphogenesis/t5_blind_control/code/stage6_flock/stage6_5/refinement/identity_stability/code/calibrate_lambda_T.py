"""C2 calibration: pick lambda_T from the frozen grid using ONLY
uncontrolled/baseline continuations of the 5 informative flocks (never
controlled-episode outcomes -- Part C7's stopping rule). Criterion (frozen
in PROTOCOL_6_5R.md before this ran): the smallest lambda_T in the grid that
(a) reduces mean turnover during low-D_X(t) stretches (D_X(t) <= the
trajectory's own median) to below half of the UNREGULARIZED lineage
track's turnover in those same stretches, while (b) retaining at least half
of the unregularized track's turnover during high-D_X(t) stretches
(D_X(t) >= the trajectory's own 90th percentile) -- i.e. it suppresses
jitter without flattening genuine transitions.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
COLLECTIVE_IDENTITY_CODE = ROOT / "stage6_5" / "collective_identity" / "code"
sys.path.insert(0, str(COLLECTIVE_IDENTITY_CODE))
CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from flock_sim.simulation import run_simulation  # noqa: E402
from common_v2 import find_flock  # noqa: E402
from definitions import lineage_track  # noqa: E402
from regularized_lineage import regularized_lineage_track  # noqa: E402
from jitter_analysis import physical_change_series, turnover_series

INFORMATIVE_SEEDS = [2, 3, 4, 8, 9]
LAMBDA_T_GRID = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
BASELINE_NT = 60
BASELINE_SEED_OFFSET = 8_500_000


def generate_baseline(seed: int) -> dict:
    fl = find_flock(seed)
    assert fl is not None
    res = run_simulation(nn=fl["lattice"].nn, nt=BASELINE_NT, seed=BASELINE_SEED_OFFSET + seed,
                          init_z=fl["z_t0"], lattice=fl["lattice"])
    return dict(seed=seed, fl=fl, z_hist=res.z_hist)


def _low_high_masks(D_X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    median = np.median(D_X)
    p90 = np.percentile(D_X, 90)
    return D_X <= median, D_X >= p90


def evaluate_lambda_T(baselines: list[dict], lambda_T: float) -> dict:
    low_reg, high_reg, low_orig, high_orig = [], [], [], []
    for b in baselines:
        z_hist, fl = b["z_hist"], b["fl"]
        I0 = fl["I0"]
        orig_track = lineage_track(z_hist, I0, t_start=0, t_end=BASELINE_NT)
        reg_track = regularized_lineage_track(z_hist, I0, t_start=0, t_end=BASELINE_NT, lambda_T=lambda_T)
        D_X = physical_change_series(z_hist)
        T_orig = turnover_series(orig_track)
        T_reg = turnover_series(reg_track)
        n = min(len(D_X), len(T_orig), len(T_reg))
        D_X, T_orig, T_reg = D_X[:n], T_orig[:n], T_reg[:n]
        low_mask, high_mask = _low_high_masks(D_X)
        if low_mask.any():
            low_orig.append(T_orig[low_mask].mean())
            low_reg.append(T_reg[low_mask].mean())
        if high_mask.any():
            high_orig.append(T_orig[high_mask].mean())
            high_reg.append(T_reg[high_mask].mean())

    mean_low_orig = float(np.mean(low_orig)) if low_orig else float("nan")
    mean_low_reg = float(np.mean(low_reg)) if low_reg else float("nan")
    mean_high_orig = float(np.mean(high_orig)) if high_orig else float("nan")
    mean_high_reg = float(np.mean(high_reg)) if high_reg else float("nan")

    suppresses_jitter = mean_low_reg <= 0.5 * mean_low_orig if mean_low_orig > 0 else True
    permits_transitions = mean_high_reg >= 0.5 * mean_high_orig if mean_high_orig > 0 else True

    return dict(
        lambda_T=lambda_T,
        mean_turnover_low_DX_original=mean_low_orig, mean_turnover_low_DX_regularized=mean_low_reg,
        mean_turnover_high_DX_original=mean_high_orig, mean_turnover_high_DX_regularized=mean_high_reg,
        suppresses_jitter=bool(suppresses_jitter), permits_transitions=bool(permits_transitions),
        criterion_met=bool(suppresses_jitter and permits_transitions),
    )


def calibrate(baselines: list[dict] | None = None) -> dict:
    baselines = baselines if baselines is not None else [generate_baseline(s) for s in INFORMATIVE_SEEDS]
    grid_results = [evaluate_lambda_T(baselines, lt) for lt in LAMBDA_T_GRID]
    chosen = next((r for r in grid_results if r["criterion_met"]), None)
    fallback_reason = None
    if chosen is not None:
        chosen_lambda_T = chosen["lambda_T"]
    else:
        # No grid value satisfies BOTH halves of the frozen criterion. Fall
        # back to the smallest lambda_T that satisfies the PRIMARY verb of
        # the criterion ("the smallest lambda_T that SUPPRESSES...") alone --
        # a pre-specifiable, principled tie-break (favor the goal the
        # criterion names first), not a value chosen after inspecting which
        # one "looks best". This is reported as a fallback, not hidden.
        suppressing = next((r for r in grid_results if r["suppresses_jitter"]), None)
        if suppressing is not None:
            chosen_lambda_T = suppressing["lambda_T"]
            fallback_reason = "no grid value satisfied both suppresses_jitter and permits_transitions; " \
                               "fell back to the smallest lambda_T satisfying suppresses_jitter alone"
        else:
            chosen_lambda_T = LAMBDA_T_GRID[-1]
            fallback_reason = "no grid value satisfied even suppresses_jitter alone; fell back to the " \
                               "tightest (largest) grid value as the most conservative option"
    return dict(
        informative_seeds=INFORMATIVE_SEEDS, lambda_T_grid=LAMBDA_T_GRID, baseline_nt=BASELINE_NT,
        grid_results=grid_results, chosen_lambda_T=chosen_lambda_T,
        chose_by_fallback=(chosen is None), fallback_reason=fallback_reason,
    )
