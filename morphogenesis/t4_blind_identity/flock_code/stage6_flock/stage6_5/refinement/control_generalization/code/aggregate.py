"""B6: flock-level aggregation. Does NOT treat replicates as independent
evidence for generalization -- bootstrap resamples FLOCKS, not replicates.
"""
from __future__ import annotations

import numpy as np


def per_flock_deltas(rows: list[dict]) -> dict:
    """Delta_s^(f) = P_Bhat^(f)(success) - P_random^(f)(success), per flock."""
    return {
        int(r["seed"]): r["inferred"]["p_success"] - r["random_matched"]["p_success"]
        for r in rows
    }


def bootstrap_ci_over_flocks(deltas: dict[int, float], n_boot: int = 10_000,
                              rng: np.random.Generator | None = None,
                              alpha: float = 0.05) -> dict:
    """Bootstrap CI for the mean Delta_s across flocks, resampling FLOCK
    INDICES with replacement (B6's explicit instruction), not replicates."""
    rng = rng or np.random.default_rng(0)
    vals = np.array(list(deltas.values()))
    n = len(vals)
    if n == 0:
        return dict(mean=float("nan"), ci_lo=float("nan"), ci_hi=float("nan"), n_flocks=0)
    boot_means = np.array([vals[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    return dict(
        mean=float(vals.mean()),
        ci_lo=float(np.percentile(boot_means, 100 * alpha / 2)),
        ci_hi=float(np.percentile(boot_means, 100 * (1 - alpha / 2))),
        n_flocks=n, n_boot=n_boot,
    )


def summarize(rows: list[dict]) -> dict:
    deltas = per_flock_deltas(rows)
    ci = bootstrap_ci_over_flocks(deltas)
    n_beats_random = sum(1 for v in deltas.values() if v > 0)
    p_inferred = {int(r["seed"]): r["inferred"]["p_success"] for r in rows}
    p_random = {int(r["seed"]): r["random_matched"]["p_success"] for r in rows}
    p_oracle = {int(r["seed"]): r["oracle"]["p_success"] for r in rows}
    p_fiedler = {int(r["seed"]): r["fiedler"]["p_success"] for r in rows}
    return dict(
        per_flock_delta=deltas, bootstrap=ci,
        n_flocks=len(rows), n_inferred_beats_random=n_beats_random,
        mean_p_success=dict(
            oracle=float(np.mean(list(p_oracle.values()))) if p_oracle else float("nan"),
            inferred=float(np.mean(list(p_inferred.values()))) if p_inferred else float("nan"),
            fiedler=float(np.mean(list(p_fiedler.values()))) if p_fiedler else float("nan"),
            random_matched=float(np.mean(list(p_random.values()))) if p_random else float("nan"),
        ),
        mean_actuator_cost=dict(
            oracle=float(np.mean([r["oracle"]["n_actuators"] for r in rows])) if rows else float("nan"),
            inferred=float(np.mean([r["inferred"]["n_actuators"] for r in rows])) if rows else float("nan"),
            fiedler=float(np.mean([r["fiedler"]["n_actuators"] for r in rows])) if rows else float("nan"),
            random_matched=float(np.mean([r["random_matched"]["n_actuators"] for r in rows])) if rows else float("nan"),
        ),
    )
