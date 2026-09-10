"""Stage 6.11 causal-interface decision logic (task brief item 11).

INFERENCE-SIDE. Consumes only the numeric outputs of a black-box probe
object's `.probe_rollout_indicators(...)` method -- never imports
`MovingFlock611`, `intervention_api_611`, or any simulator internal. The
driver (evaluation-side) constructs one probe object per repeat (Stage 6.10
budget: 40 rollouts x 3 repeats, `intervention_api_611.PROBE_ROLLOUTS` /
`PROBE_REPEATS`) and passes the list in; this module treats each as an
opaque source of per-rollout binary disagreement indicators.

Uses FINITE-SAMPLE INTERVENTIONAL ESTIMATION (nonparametric bootstrap over
pooled rollouts) -- task brief item 11's explicit fallback: "if omitted [the
Dirichlet treatment], retain bootstrap/repeat uncertainty and describe the
method as finite-sample interventional estimation," adopted here because a
full per-bird 4-category Dirichlet-posterior treatment would materially
complicate this module without changing the B^causal decision rule (which
only needs a lower confidence bound on a scalar effect).
"""
from __future__ import annotations

import numpy as np

NU = 4
N_BOOT_CI = 500
ALPHA = 0.05
TAU_CAUSAL = 0.0


def probe_source(probes: list, I, j: int, z_t: np.ndarray, rng: np.random.Generator,
                  n_boot: int = N_BOOT_CI, alpha: float = ALPHA) -> dict:
    """Aggregate paired-discrepancy-rate influence of source j on interior I,
    across the (NU-1) alternative headings (uniform expectation, matching
    E_{z'}[...] in task brief item 11) and all provided repeat probes, pooled
    for a nonparametric bootstrap CI over individual rollouts."""
    z_j = int(z_t[j])
    alts = [h for h in range(NU) if h != z_j]
    pooled = {int(i): [] for i in I}
    for alt in alts:
        for probe in probes:
            ind = probe.probe_rollout_indicators(I, j, alt, z_t)
            for i in I:
                pooled[int(i)].append(ind[int(i)])
    for i in pooled:
        pooled[i] = np.concatenate(pooled[i]) if pooled[i] else np.array([])

    per_bird_mean = {i: float(v.mean()) if len(v) else 0.0 for i, v in pooled.items()}
    C_do_joint_point = float(sum(per_bird_mean.values()))

    # Vectorized bootstrap: for each bird, resample all n_boot replicates at
    # once (n_boot x n_samples index matrix) instead of looping n_boot times
    # per bird -- the same statistic, computed without the O(n_boot x birds)
    # Python-level loop that made this a bottleneck for interior sizes ~50-100.
    boot_sums = np.zeros(n_boot)
    for i, v in pooled.items():
        n = len(v)
        if n == 0:
            continue
        idx = rng.integers(0, n, size=(n_boot, n))
        boot_sums += v[idx].mean(axis=1)
    ci_lo, ci_hi = (float(x) for x in np.quantile(boot_sums, [alpha / 2, 1 - alpha / 2]))

    return dict(j=int(j), C_do_joint=C_do_joint_point, per_bird=per_bird_mean,
                ci_lo=ci_lo, ci_hi=ci_hi, n_samples=int(sum(len(v) for v in pooled.values())))


def probe_sources(probes: list, I, sources, z_t: np.ndarray, rng: np.random.Generator,
                   tau: float = TAU_CAUSAL, n_boot: int = N_BOOT_CI, alpha: float = ALPHA) -> dict:
    """B_causal = {j : bootstrap CI lower bound of C^do_j > tau}."""
    C = {}
    for j in sources:
        C[int(j)] = probe_source(probes, I, j, z_t, rng, n_boot, alpha)
    B_causal = sorted(j for j, res in C.items() if res["ci_lo"] > tau)
    return dict(C=C, B_causal=B_causal, tau=tau, alpha=alpha,
                method="finite-sample interventional estimation (bootstrap over pooled rollouts, "
                       "not a coefficient or Bayesian posterior)")


def influence_matrix(result: dict) -> dict:
    """{j: {i: C^do_{j->i}}} -- for actuator selection (item 13)."""
    return {j: {int(i): v for i, v in res["per_bird"].items()} for j, res in result["C"].items()}
