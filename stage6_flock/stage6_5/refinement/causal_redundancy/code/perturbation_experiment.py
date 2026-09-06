"""A2/A3/A4: counterfactual perturbation experiment. For each of the three
exterior classes (included shell, omitted shell, non-shell), perturb every
member bird to each of its three alternative headings, on every held-out
checkpoint state, and record the exact D_j^do (see exact_intervention.py)
-- distributions, not only means (A4's explicit instruction).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from exact_intervention import default_precomputed_model, interior_do_kl  # noqa: E402

NU = 4


def run_class_perturbations(fl: dict, checkpoints: np.ndarray, bird_ids: list[int]) -> dict:
    """For every bird j in bird_ids, every checkpoint state, every alternative
    heading z'_j != z_j(state): compute D_j^do. Returns per-bird summaries
    plus the raw pooled sample so downstream code can look at the full
    distribution, not just summary statistics."""
    pm = default_precomputed_model()
    lattice, I0 = fl["lattice"], fl["I0"]

    per_bird = {}
    for j in bird_ids:
        joint_vals = []
        mean_vals = []
        for X_t in checkpoints:
            z_j = int(X_t[j])
            for z_prime in range(NU):
                if z_prime == z_j:
                    continue
                res = interior_do_kl(pm, lattice, X_t, I0, j, z_prime)
                joint_vals.append(res["D_do_joint"])
                mean_vals.append(res["D_do_mean_per_bird"])
        joint_vals = np.array(joint_vals)
        per_bird[j] = dict(
            D_do_joint_mean=float(joint_vals.mean()),
            D_do_joint_std=float(joint_vals.std()),
            D_do_joint_median=float(np.median(joint_vals)),
            D_do_joint_max=float(joint_vals.max()),
            D_do_joint_min=float(joint_vals.min()),
            D_do_joint_samples=[float(v) for v in joint_vals],
            n_samples=len(joint_vals),
        )
    return per_bird


def run_all_classes(fl: dict, checkpoints: np.ndarray, classes: dict) -> dict:
    return dict(
        included_shell=run_class_perturbations(fl, checkpoints, classes["included_shell"]),
        omitted_shell=run_class_perturbations(fl, checkpoints, classes["omitted_shell"]),
        non_shell_sample=run_class_perturbations(fl, checkpoints, classes["non_shell_sample"]),
    )


def pooled_class_distribution(class_result: dict) -> dict:
    """Pools every bird's D_do_joint samples in a class into one distribution
    (A4's "report distributions, not only means")."""
    pooled = []
    for bird_result in class_result.values():
        pooled.extend(bird_result["D_do_joint_samples"])
    pooled = np.array(pooled) if pooled else np.array([np.nan])
    return dict(
        n=len(pooled),
        mean=float(np.mean(pooled)),
        std=float(np.std(pooled)),
        median=float(np.median(pooled)),
        p10=float(np.percentile(pooled, 10)),
        p90=float(np.percentile(pooled, 90)),
        max=float(np.max(pooled)),
        min=float(np.min(pooled)),
    )
