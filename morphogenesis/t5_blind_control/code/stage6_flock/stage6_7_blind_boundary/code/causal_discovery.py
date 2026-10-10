"""INFERENCE-SIDE MODULE -- see blind_cache.py's header for the import
restriction (enforced by tests/test_no_topology_leakage.py). Notably: this
file takes an intervention "oracle" object as a plain parameter (duck-typed,
must expose `.do(I, j, z_prime, X_t) -> dict(D_do_joint, per_bird_kl)`) and
never imports `flock_sim`, `intervention_api`, or the lattice itself -- it
never inspects what the oracle used internally to answer (task brief section
12).

Sections 12-14 of the task brief: for candidate interior I, every exterior
bird j, sampled OBSERVED current states X_t (drawn from the passive
trajectory data, never simulator-privileged) x alternative headings z'_j,
call the injected oracle and aggregate:

  D_j^do = E_{X_t,z'_j} D_KL[p(X_{I,t+1}|do(Z_{j,t}=z'_j),X_t) || p(X_{I,t+1}|X_t)]
  C_{j->i}^do = the same, but the per-target-bird i breakdown (never
                collapsed to one scalar -- section 13).

Bhat^causal(I) = {j : bootstrap CI lower bound on D_j^do > 0} -- a bootstrap
criterion over the SAMPLED STATES actually tested, not a hand-picked
threshold (section 14).
"""
from __future__ import annotations

import numpy as np

NU = 4


def estimate_causal_effects(I, exterior_candidates: list[int], X_samples: np.ndarray, oracle) -> dict:
    """X_samples: (n_samples, n_bird) int heading arrays, drawn from observed
    trajectory data. Returns dict(D_j_do={j: float}, C_j_to_i={j: {i: float}},
    raw_D_samples={j: [floats]}, raw_C_samples={j: {i: [floats]}}) -- the raw
    per-(state, alt-heading) samples are kept so bootstrap_ci_causal can
    resample them without re-calling the (potentially expensive) oracle."""
    I_sorted = sorted(int(i) for i in I)
    raw_D = {j: [] for j in exterior_candidates}
    raw_C = {j: {i: [] for i in I_sorted} for j in exterior_candidates}

    for X_t in X_samples:
        for j in exterior_candidates:
            z_j = int(X_t[j])
            for z_prime in range(NU):
                if z_prime == z_j:
                    continue
                res = oracle.do(I_sorted, j, z_prime, X_t)
                raw_D[j].append(float(res["D_do_joint"]))
                for i_key, kl in res["per_bird_kl"].items():
                    raw_C[j][int(i_key)].append(float(kl))

    D_j_do = {j: (float(np.mean(v)) if v else 0.0) for j, v in raw_D.items()}
    C_j_to_i = {j: {i: (float(np.mean(v)) if v else 0.0) for i, v in raw_C[j].items()}
                for j in exterior_candidates}

    return dict(D_j_do=D_j_do, C_j_to_i=C_j_to_i, raw_D_samples=raw_D, raw_C_samples=raw_C,
                I=I_sorted, exterior_candidates=list(exterior_candidates))


def bootstrap_ci_causal(raw_D_samples: dict, n_boot: int = 1000, alpha: float = 0.05,
                         rng: np.random.Generator | None = None) -> dict:
    """Bootstraps the mean D_j^do over the ALREADY-COLLECTED per-(state,
    alt-heading) samples (cheap: no new oracle calls). Returns
    {j: dict(mean, lower, upper, n_samples)}."""
    rng = rng or np.random.default_rng(0)
    out = {}
    for j, vals in raw_D_samples.items():
        arr = np.asarray(vals, dtype=float)
        if len(arr) == 0:
            out[j] = dict(mean=0.0, lower=0.0, upper=0.0, n_samples=0)
            continue
        boot_means = np.empty(n_boot)
        for b in range(n_boot):
            idx = rng.integers(0, len(arr), size=len(arr))
            boot_means[b] = arr[idx].mean()
        lower, upper = np.percentile(boot_means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
        out[j] = dict(mean=float(arr.mean()), lower=float(lower), upper=float(upper), n_samples=len(arr))
    return out


def infer_causal_boundary(ci: dict) -> list[int]:
    """Bhat^causal(I) = {j : CI lower bound > 0} -- bootstrap criterion, not a
    hand-picked threshold (task brief section 14)."""
    return sorted(j for j, c in ci.items() if c["lower"] > 0)
