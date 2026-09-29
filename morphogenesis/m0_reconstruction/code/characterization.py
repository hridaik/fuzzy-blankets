"""Runs E1-E6 descriptive characterization on the Python port ONLY.

UNVALIDATED RE-DERIVATION: no MATLAB/Octave reference exists (README.md), so
every number this script produces describes the Python reconstruction's own
behaviour, not the published simulator's. All E2-E5 quantities that touch
internal expectations/free energy are HIDDEN-tier by definition (per Task D)
-- they characterize the *inference process*, not an observable phenotype.

Sample counts are reduced from the task prompt's request (50/20 seeds) to
keep this pass tractable; see the reduction table this script prints and
CHARACTERIZATION.md.
"""
import json
import time
import numpy as np
from scipy.optimize import linear_sum_assignment

from template import decode_template, T_L4
from synthetic_template import synthetic_template
from field import field_concentration
from generative import Mg
from solver import run as solver_run
from interventions import high_identity_expectation_v0

RESULTS = {}
REDUCTION_TABLE = []


def hungarian_distance(final_x: np.ndarray, template_x: np.ndarray) -> float:
    """Min-cost assignment of final cell positions to template positions
    (scipy linear_sum_assignment on pairwise Euclidean distance)."""
    n = final_x.shape[1]
    cost = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            cost[i, j] = np.linalg.norm(final_x[:, i] - template_x[:, j])
    ri, ci = linear_sum_assignment(cost)
    return float(cost[ri, ci].sum() / n)


def init_setup():
    P_x, P_s, n, m = decode_template()
    P_c = field_concentration(P_x, P_s)
    return P_x, P_s, P_c, n, m


def e1_determinism():
    P_x, P_s, P_c, n, m = init_setup()
    rng = np.random.default_rng(0)
    v0 = rng.standard_normal((n, n)) / 8.0
    gx, gs, _, _ = Mg(v0, P_x, P_s, P_c, t=1 / 32)
    tr1 = solver_run(v0, gx, gs, P_x, P_s, P_c, n_bins=32)
    tr2 = solver_run(v0, gx, gs, P_x, P_s, P_c, n_bins=32)
    bitwise = bool(np.array_equal(tr1["a_x"], tr2["a_x"]) and np.array_equal(tr1["v"], tr2["v"]))
    RESULTS["E1_determinism"] = {
        "engine": "python (no MATLAB/Octave available)",
        "bitwise_identical_repeat": bitwise,
        "note": "solver is a deterministic explicit-Euler gradient scheme with "
                "no RNG in the D-step; determinism here establishes only that "
                "the Python implementation itself is reproducible, not that it "
                "matches spm_ADEM's determinism properties.",
    }


def e2_noise_sensitivity(n_seeds=10):
    P_x, P_s, P_c, n, m = init_setup()
    rng0 = np.random.default_rng(0)
    v0 = rng0.standard_normal((n, n)) / 8.0
    gx0, gs0, _, _ = Mg(v0, P_x, P_s, P_c, t=1 / 32)
    dists = []
    for seed in range(n_seeds):
        tr = solver_run(v0, gx0, gs0, P_x, P_s, P_c, n_bins=32, noise_seed=1000 + seed)
        dists.append(hungarian_distance(tr["a_x"][-1], P_x))
    dists = np.array(dists)
    RESULTS["E2_process_noise_sensitivity"] = {
        "n_seeds": n_seeds,
        "requested_n_seeds": 20,
        "fixed_initial_v0_seed": 0,
        "hidden_tier_note": "distance-to-template after Hungarian assignment "
                             "is a HIDDEN-tier reproduction-quality metric here, "
                             "not a claimed morphology/identity metric.",
        "mean_hungarian_distance": float(dists.mean()),
        "std_hungarian_distance": float(dists.std()),
        "min": float(dists.min()), "max": float(dists.max()),
        "process_noise_std_used": float(1.0 / np.exp(8.0)),
    }


def e3_initial_condition_sensitivity(n_draws=10):
    P_x, P_s, P_c, n, m = init_setup()

    def run_batch(sigma, label, n_draws):
        finals = []
        for i in range(n_draws):
            rng = np.random.default_rng(2000 + i)
            v0 = rng.standard_normal((n, n)) * sigma
            gx, gs, _, _ = Mg(v0, P_x, P_s, P_c, t=1 / 32)
            tr = solver_run(v0, gx, gs, P_x, P_s, P_c, n_bins=32)
            finals.append(tr["a_x"][-1].copy())
        finals = np.array(finals)
        dists = np.array([hungarian_distance(f, P_x) for f in finals])
        # simple descriptive clustering: pairwise distance among final configs,
        # 2-means via numpy (deterministic init at the two extreme draws)
        flat = finals.reshape(len(finals), -1)
        pw = np.linalg.norm(flat[:, None, :] - flat[None, :, :], axis=-1)
        c0, c1 = flat[np.argmin(dists)], flat[np.argmax(dists)]
        for _ in range(20):
            d0 = np.linalg.norm(flat - c0, axis=1)
            d1 = np.linalg.norm(flat - c1, axis=1)
            assign = (d1 < d0).astype(int)
            if assign.sum() in (0, len(assign)):
                break
            c0 = flat[assign == 0].mean(axis=0)
            c1 = flat[assign == 1].mean(axis=0)
        return {
            "n_draws": n_draws, "sigma": sigma,
            "mean_hungarian_distance": float(dists.mean()),
            "std_hungarian_distance": float(dists.std()),
            "mean_pairwise_distance_between_final_configs": float(pw[np.triu_indices(len(finals), 1)].mean()),
            "two_cluster_split": [int((assign == 0).sum()), int((assign == 1).sum())],
        }

    # 2015-paper-matched: log precision -2 => variance = 1/exp(-2) = exp(2)
    sigma_paper = float(np.sqrt(np.exp(2.0)))
    # scale-matched to the hard-coded morphopsy base matrix (~ +/-0.1-0.35, treat as sigma=1/8 like canonical)
    sigma_hardcoded = 1.0 / 8.0

    RESULTS["E3_initial_condition_sensitivity"] = {
        "requested_n_draws_each": 50,
        "actual_n_draws_each": n_draws,
        "paper_matched_sigma": sigma_paper,
        "hardcoded_matched_sigma": sigma_hardcoded,
        "paper_matched": run_batch(sigma_paper, "paper", n_draws),
        "hardcoded_matched": run_batch(sigma_hardcoded, "hardcoded", n_draws),
    }


def stationarity_bin(a_x_series, a_s_series, threshold, window=32):
    dx = np.linalg.norm(np.diff(a_x_series, axis=0), axis=(1, 2))
    ds = np.linalg.norm(np.diff(a_s_series, axis=0), axis=(1, 2))
    below = (dx < threshold) & (ds < threshold)
    for i in range(len(below) - window + 1):
        if below[i:i + window].all():
            return i + 1  # bin index (1-indexed into diffs => bin i+1 of original series)
    return None


def e4_long_horizon(n_bins=512):
    P_x, P_s, P_c, n, m = init_setup()
    configs = {}

    rng = np.random.default_rng(0)
    v0 = rng.standard_normal((n, n)) / 8.0
    gx, gs, _, _ = Mg(v0, P_x, P_s, P_c, t=1 / n_bins)
    configs["vanilla8"] = (v0, gx, gs, None)

    v0k = high_identity_expectation_v0(n, k=4, seed=0)
    gxk, gsk, _, _ = Mg(v0k, P_x, P_s, P_c, t=1 / n_bins)
    configs["high_identity_k4"] = (v0k, gxk, gsk, None)

    results = {}
    for name, (v0c, gxc, gsc, noise_seed) in configs.items():
        t0 = time.time()
        tr = solver_run(v0c, gxc, gsc, P_x, P_s, P_c, n_bins=n_bins, noise_seed=noise_seed)
        elapsed = time.time() - t0
        row = {"runtime_s": elapsed, "final_hungarian_distance": hungarian_distance(tr["a_x"][-1], P_x)}
        for thr in (1e-3, 1e-4):
            b = stationarity_bin(tr["a_x"], tr["a_s"], thr)
            row[f"stationary_from_bin_thr{thr}"] = b
        row["still_drifting_at_512"] = row["stationary_from_bin_thr0.001"] is None
        results[name] = row
    RESULTS["E4_long_horizon"] = {
        "n_bins": n_bins, "stationarity_window": 32,
        "criterion": "max per-bin displacement (a_x) AND secretion change (a_s), "
                     "L2 norm over all cells, below threshold for 32 consecutive bins",
        "results": results,
    }


def e5_timescales(n_bins=512):
    P_x, P_s, P_c, n, m = init_setup()
    rng = np.random.default_rng(0)
    v0 = rng.standard_normal((n, n)) / 8.0
    gx, gs, _, _ = Mg(v0, P_x, P_s, P_c, t=1 / n_bins)
    tr = solver_run(v0, gx, gs, P_x, P_s, P_c, n_bins=n_bins)

    dx = np.linalg.norm(np.diff(tr["a_x"], axis=0), axis=(1, 2))
    ds = np.linalg.norm(np.diff(tr["a_s"], axis=0), axis=(1, 2))
    combined = dx + ds
    peak = int(np.argmax(combined))
    tail = combined[peak:]
    if tail[0] > 0:
        target = tail[0] / np.e
        efold_offset = next((i for i, v in enumerate(tail) if v <= target), None)
    else:
        efold_offset = None

    p = tr["p"]  # (n_bins, n, n)
    max_p = p.max(axis=1)  # (n_bins, n_cells)
    per_cell_time = []
    for c in range(n):
        idx = np.argmax(max_p[:, c] > 0.9) if (max_p[:, c] > 0.9).any() else None
        per_cell_time.append(int(idx) if idx is not None else None)

    RESULTS["E5_timescales"] = {
        "n_bins": n_bins,
        "peak_change_bin": peak,
        "e_folding_offset_bins_after_peak": efold_offset,
        "per_cell_bin_to_concentrated_expectation_gt_0.9": per_cell_time,
        "hidden_tier": True,
    }


def e6_scaling():
    rows = []
    configs = [("n8_real_template", None, 8), ("L4_larger_template", T_L4, None),
               ("synthetic_n24", "synthetic", 24), ("synthetic_n32", "synthetic", 32)]
    for name, T, n_target in configs:
        try:
            if isinstance(T, str) and T == "synthetic":
                T = synthetic_template(n_target)
                P_x, P_s, n, m = decode_template(T)
            elif T is not None:
                P_x, P_s, n, m = decode_template(T)
            else:
                P_x, P_s, n, m = decode_template()
            P_c = field_concentration(P_x, P_s)
            rng = np.random.default_rng(0)
            v0 = rng.standard_normal((n, n)) / 8.0
            gx, gs, _, _ = Mg(v0, P_x, P_s, P_c, t=1 / 32)
            t0 = time.time()
            tr = solver_run(v0, gx, gs, P_x, P_s, P_c, n_bins=32)
            elapsed = time.time() - t0
            ok = not (np.isnan(tr["a_x"]).any() or np.isinf(tr["a_x"]).any())
            rows.append({"config": name, "n_cells": n, "assembly_success": bool(ok),
                         "runtime_s_total_32bins": elapsed, "runtime_s_per_bin": elapsed / 32})
        except Exception as e:
            rows.append({"config": name, "assembly_success": False, "error": str(e)})
    RESULTS["E6_scaling"] = rows


if __name__ == "__main__":
    REDUCTION_TABLE.extend([
        {"task": "E2", "requested": "20 noise seeds", "actual": "10 noise seeds",
         "reason": "compute/time budget for this pass"},
        {"task": "E3", "requested": "50+50 initial-condition draws", "actual": "10+10 draws",
         "reason": "compute/time budget for this pass; E6 not reduced further, E4 horizon not shortened"},
        {"task": "E4", "requested": "every reproduced config + all E3 runs to >=512 bins",
         "actual": "2 configs (vanilla8, high_identity_k4) to 512 bins",
         "reason": "compute/time budget; horizon length itself (512) was NOT reduced"},
    ])
    e1_determinism()
    e2_noise_sensitivity()
    e3_initial_condition_sensitivity()
    e4_long_horizon()
    e5_timescales()
    e6_scaling()
    RESULTS["_reduction_table"] = REDUCTION_TABLE
    with open("../data/characterization_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print(json.dumps(RESULTS, indent=2, default=str)[:3000])
