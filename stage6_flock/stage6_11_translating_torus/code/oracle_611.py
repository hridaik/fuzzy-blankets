"""Stage 6.11 oracle/reference reveal (task brief item 18).

EVALUATION-SIDE. Runs ONLY after inference decisions (detection, lineage,
thingness thresholds, B^pred, B^causal, B^C, actuator selection) are frozen
for a given snapshot/episode. Compares:

  * detected interior I_t vs the true live-neighbour graph's own boundary
    B_t^D (MovingFlock611.oracle_B_D, inherited from MovingFlock -- ORACLE);
  * B_pred / B_causal / B_C vs B_t^D (precision/recall/Jaccard);
  * the SAMPLED causal interface (probing_611, finite-rollout) vs the EXACT
    one-step effect, computed here in closed form (no sampling): given the
    model's own policy posterior u_i and transition matrix Bu, the marginal
    P(z_i(t+1)=h) = sum_u u_i(u) Bu[h,u] is analytic, so an "exact"
    do(Z_j=z') comparison needs zero rollouts and has zero estimation error
    -- this isolates ESTIMATION ERROR (sampled vs exact) from
    IDENTIFIABILITY (exact vs the true graph B^D), mirroring Stage 6.8's
    `oracle_68.py` / `ExactPropagator` split.

Oracle information computed here MUST NEVER feed back into fitting,
threshold selection, lineage decisions, or control -- there is no code path
in this file that writes back into any of those modules' state.
"""
from __future__ import annotations

import numpy as np

from moving_flock_611 import MovingFlock611


def oracle_B_D(mf: MovingFlock611, r_t: np.ndarray, z_t: np.ndarray, I: np.ndarray) -> np.ndarray:
    return mf.oracle_B_D(r_t, z_t, I)


def exact_policy_dist(mf: MovingFlock611, r_t: np.ndarray, z_t: np.ndarray) -> np.ndarray:
    """Analytic P(z_i(t+1)=h | z_t, r_t) for every bird i, (N,4). Uses the
    TRUE model (oracle-only): mf.policy() computes G from the true live
    edges, and Bu is the model's exact transition matrix."""
    u = mf.policy(r_t, z_t)          # (N,4) policy posterior over actions
    Bu = mf.pm.Bu                    # (4,4): Bu[h, u] = P(next=h | action=u)
    return u @ Bu.T                  # (N,4)


def exact_effect(mf: MovingFlock611, r_t: np.ndarray, z_t: np.ndarray, j: int, z_prime: int,
                  I: np.ndarray) -> dict:
    """Closed-form (zero-sampling-error) counterfactual effect of do(Z_j=z')
    on each interior bird's next-heading distribution, via forward KL."""
    p_base = exact_policy_dist(mf, r_t, z_t)
    z_do = z_t.copy()
    z_do[int(j)] = int(z_prime)
    p_do = exact_policy_dist(mf, r_t, z_do)
    eps = 1e-12
    kl = (p_do * (np.log(p_do + eps) - np.log(p_base + eps))).sum(axis=1)
    per_bird = {int(i): float(kl[i]) for i in I}
    return dict(D_do_joint=float(sum(per_bird.values())), per_bird=per_bird)


def compare_sets(B_hat, B_true) -> dict:
    a, b = set(int(x) for x in B_hat), set(int(x) for x in B_true)
    inter = len(a & b)
    union = len(a | b)
    precision = inter / len(a) if a else (1.0 if not b else 0.0)
    recall = inter / len(b) if b else (1.0 if not a else 0.0)
    jaccard = inter / union if union else 1.0
    return dict(precision=precision, recall=recall, jaccard=jaccard,
                size_hat=len(a), size_true=len(b), n_true_positive=inter)


def reveal_snapshot(mf: MovingFlock611, r_t: np.ndarray, z_t: np.ndarray, I: np.ndarray,
                     B_pred: list[int], B_causal_sampled: list[int], B_causal_sampled_result: dict,
                     B_C: list[int]) -> dict:
    """One-snapshot oracle reveal: structural agreement of each blind
    interface against B_t^D, plus estimation-error-vs-identifiability split
    for the sampled causal interface. Read-only: returns a report dict,
    never mutates any inference-side state."""
    B_D = oracle_B_D(mf, r_t, z_t, I)

    exact_effects = {}
    for j in set(int(x) for x in B_causal_sampled) | set(int(x) for x in B_D):
        z_j = int(z_t[j])
        per_alt = [exact_effect(mf, r_t, z_t, j, alt, I) for alt in range(4) if alt != z_j]
        exact_effects[j] = float(np.mean([e["D_do_joint"] for e in per_alt]))
    B_causal_exact = sorted(j for j, v in exact_effects.items() if v > 0.0)

    return dict(
        B_D_true=B_D.tolist(),
        vs_BD=dict(
            B_pred=compare_sets(B_pred, B_D),
            B_causal_sampled=compare_sets(B_causal_sampled, B_D),
            B_C=compare_sets(B_C, B_D),
        ),
        estimation_vs_identifiability=dict(
            B_causal_sampled_vs_exact=compare_sets(B_causal_sampled, B_causal_exact),
            B_causal_exact_vs_BD=compare_sets(B_causal_exact, B_D),
            B_causal_sampled_vs_BD=compare_sets(B_causal_sampled, B_D),
        ),
        exact_effect_per_candidate=exact_effects,
    )
