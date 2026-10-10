"""B7 (exploratory, per the task brief's own framing -- not a mandatory
model-selection project): relate inference quality to control outcome
across the discriminating flocks."""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr


def quality_vs_control(rows: list[dict]) -> dict:
    recall = np.array([r["recall_B_hat"] for r in rows])
    excess_loss = np.array([r["excess_loss_B_hat"] for r in rows])
    size = np.array([len(r["B_hat"]) for r in rows])
    budget = np.array([r["inferred"]["n_actuators"] for r in rows])
    p_success = np.array([r["inferred"]["p_success"] for r in rows])

    def _corr(x, y):
        if len(x) < 3 or np.all(x == x[0]) or np.all(y == y[0]):
            return dict(r=float("nan"), p=float("nan"), n=len(x))
        r, p = spearmanr(x, y)
        return dict(r=float(r), p=float(p), n=len(x))

    return dict(
        recall_vs_p_success=_corr(recall, p_success),
        excess_loss_vs_p_success=_corr(excess_loss, p_success),
        boundary_size_vs_p_success=_corr(size, p_success),
        actuator_budget_vs_p_success=_corr(budget, p_success),
        raw=dict(seed=[int(r["seed"]) for r in rows], recall=recall.tolist(),
                  excess_loss=excess_loss.tolist(), boundary_size=size.tolist(),
                  actuator_budget=budget.tolist(), p_success=p_success.tolist()),
    )
