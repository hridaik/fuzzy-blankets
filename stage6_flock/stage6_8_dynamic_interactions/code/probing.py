"""Finite active probing -- the PRIMARY Stage 6.8 causal estimator
(task brief section 16).

INFERENCE-SIDE MODULE. It receives a duck-typed probe object (an
`intervention_api_68.FiniteProbe`) and calls only `probe(I, j, z', z_t)`. It
never imports `fov_dynamics`, `common_68` or `oracle_68`, never learns which
birds are neighbours, and never sees the FOV rule or the gates.

Stage 6.7's causal estimator used the exact closed-form propagator, which made
structural recovery trivially perfect (300/300 candidates, precision = recall
= 1.0). That measured identifiability, not estimation. Here the estimator is
finite: real observed states are sampled, `Z_j` is intervened on, paired
common-random-number one-step rollouts are run, and

    Chat^do_{j->i}(t) = E_{z'_j} KL[ phat(X_{i,t+1} | do(Z_j = z'_j), X_t)
                                  || phat(X_{i,t+1} | X_t) ]

is estimated from rollout frequencies. Node-level interface strength is the
sum over i in I_t. Bootstrap confidence intervals are taken over the sampled
(state, z') pairs, and `Bhat^causal_t = { j : CI lower bound > tau }`.
"""
from __future__ import annotations

import numpy as np

N_STATES = 12             # observed states probed per candidate
N_BOOT_CI = 500
ALPHA = 0.05
TAU_CAUSAL = 0.0          # CI lower bound must exceed this to enter Bhat^causal
NU = 4


def probe_sources(probe, I, sources, states, alpha: float = ALPHA,
                  n_boot: int = N_BOOT_CI, tau: float = TAU_CAUSAL,
                  rng=None) -> dict:
    """Estimate Chat^do_{j->I} for every candidate source j.

    `states` is a list of OBSERVED current-heading vectors, drawn from the
    passive record -- never a simulator-internal privileged state.
    """
    rng = rng or np.random.default_rng(0)
    I = sorted(int(x) for x in I)
    out = {}
    for j in sources:
        j = int(j)
        samples, per_bird_acc = [], {i: [] for i in I}
        for z_t in states:
            z_t = np.asarray(z_t)
            others = [h for h in range(NU) if h != int(z_t[j])]
            for zp in others:
                r = probe.probe(I, j, zp, z_t)
                samples.append(r["D_do_joint"])
                for i in I:
                    per_bird_acc[i].append(r["per_bird_kl"][i])
        s = np.asarray(samples, dtype=float)
        if len(s) == 0:
            continue
        bs = np.array([rng.choice(s, size=len(s), replace=True).mean() for _ in range(n_boot)])
        out[j] = dict(
            C_do=float(s.mean()),
            ci_lo=float(np.quantile(bs, alpha / 2)),
            ci_hi=float(np.quantile(bs, 1 - alpha / 2)),
            n_samples=len(s),
            per_bird=dict((i, float(np.mean(v))) for i, v in per_bird_acc.items()),
        )
    B = sorted([j for j, v in out.items() if v["ci_lo"] > tau])
    return dict(C=out, B_causal=B, tau=tau, alpha=alpha, n_states=len(states))


def influence_matrix(result: dict, I) -> dict:
    """Chat^do_{j->i} as a nested dict, for the causal weighted multicover
    (task brief section 21)."""
    return {int(j): {int(i): float(c) for i, c in v["per_bird"].items()}
            for j, v in result["C"].items()}


def sample_states(z_hist_reps: np.ndarray, t: int, n_states: int = N_STATES,
                  rng=None) -> list:
    """Draw `n_states` OBSERVED states at time t from the replicate record."""
    rng = rng or np.random.default_rng(0)
    n_rep = z_hist_reps.shape[0]
    idx = rng.choice(n_rep, size=min(n_states, n_rep), replace=False)
    return [z_hist_reps[r, t] for r in idx]
