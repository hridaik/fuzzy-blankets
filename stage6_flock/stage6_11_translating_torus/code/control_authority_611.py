"""Stage 6.11 control interface B^C and actuator selection (task brief items
12-13).

INFERENCE-SIDE. B^C is kept DISTINCT from B^pred (predictive_boundary_611.py)
and B^causal (probing_611.py): B^pred comes from passive prediction,
B^causal from task-neutral one-step perturbational effects, B^C from SIGNED,
TARGET-DIRECTED authority over a REACHABLE horizon tau >= 2,

    A_j^{h*,tau} = E[H*_{t+tau} | do(u_j=h*)] - E[H*_{t+tau} | baseline].

Never ranks actuators using one-step KL/discrepancy influence -- that is
`probing_611.B_causal`, a different interface for a different purpose (task
brief item 12's "do not rank a 90-degree steering actuator using one-step KL
influence"). Consumes only a duck-typed probe object's `.authority(...)`
output (`intervention_api_611.MultiStepAuthorityProbe`) -- never imports
`MovingFlock611` or `intervention_api_611` itself.
"""
from __future__ import annotations

K_ACT_DEFAULT = 10


def rank_actuators(probe, I, candidates, h_star: int) -> list[dict]:
    return sorted((probe.authority(I, j, h_star) for j in candidates), key=lambda r: -r["A"])


def select_actuators(probe, I, candidates, h_star: int, k_act: int = K_ACT_DEFAULT) -> dict:
    """Fixed-budget selection: always returns exactly min(k_act,
    len(candidates)) actuators by descending signed authority, so arm
    comparisons are budget-matched rather than actuator-count effects
    (task brief item 13)."""
    scored = rank_actuators(probe, I, candidates, h_star)
    chosen = scored[:k_act]
    return dict(B_C=[s["j"] for s in chosen], scores=scored, h_star=h_star, tau=probe.tau,
                total_authority=float(sum(s["A"] for s in chosen)),
                k_act_requested=k_act, k_act_actual=len(chosen))
