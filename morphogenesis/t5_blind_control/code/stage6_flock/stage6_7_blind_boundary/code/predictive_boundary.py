"""INFERENCE-SIDE MODULE -- see blind_cache.py's header for the import
restriction (enforced by tests/test_no_topology_leakage.py).

Task brief section 6: given an arbitrary candidate interior I, the inferred
incoming predictive interface

    Shat^pred(I) = {j not in I : exists i in I with stable ghat_{i<-j} > 0}

is a pure lookup into the already-frozen directed graph Ghat (directed_graph_inference.py)
plus its bootstrap stability flags (graph_bootstrap.py) -- no geometry, no
lattice. A compact predictive boundary Bhat is then built by GREEDY
CONDITIONAL selection from this pool alone, reusing
stage6_5/boundary_inference/code/greedy_selection.py:greedy_forward_select
verbatim (same stopping rule: excess-over-full <= delta_tol, or best
remaining marginal gain <= min_gain, or |B|=K_max -- task brief section 6).
K_max=12 caps the search but Bhat is never padded/forced to that size.

Section 7's primary predictive criterion (Delta-ell(Bhat) on the untouched
TEST split) is also computed here, since it too is pure array arithmetic with
no topology involved.
"""
from __future__ import annotations

from greedy_selection import fit_eval, greedy_forward_select


def predictive_candidate_pool(I, G: dict, stab_flags: dict) -> list[int]:
    I_set = set(int(x) for x in I)
    pool = set()
    for i in I_set:
        row_G = G.get(i, {})
        row_flags = stab_flags.get(i, {})
        for j, delta in row_G.items():
            if j in I_set:
                continue
            if delta > 0 and row_flags.get(j, False):
                pool.add(int(j))
    return sorted(pool)


def infer_predictive_boundary(I, G: dict, stab_flags: dict,
                               train_prev, train_next, val_prev, val_next,
                               n_bird: int, delta_tol: float = 0.01, min_gain: float = 0.002,
                               max_size: int = 12, model_kwargs: dict | None = None) -> dict:
    model_kwargs = model_kwargs or {}
    I_sorted = sorted(int(x) for x in I)
    I_set = set(I_sorted)
    pool = predictive_candidate_pool(I_sorted, G, stab_flags)
    all_exterior = [j for j in range(n_bird) if j not in I_set]

    full_loss = fit_eval(I_sorted, all_exterior, train_prev, train_next, val_prev, val_next, **model_kwargs)
    interior_only_loss = fit_eval(I_sorted, [], train_prev, train_next, val_prev, val_next, **model_kwargs)

    B_hat, trace = greedy_forward_select(
        I_sorted, pool, train_prev, train_next, val_prev, val_next,
        full_loss=full_loss, delta_tol=delta_tol, min_gain=min_gain,
        max_size=max_size, **model_kwargs,
    )

    return dict(I=I_sorted, S_pred=pool, B_hat=B_hat, trace=trace,
                full_loss=full_loss, interior_only_loss=interior_only_loss,
                params=dict(delta_tol=delta_tol, min_gain=min_gain, max_size=max_size))


def test_excess_loss(I, B_hat, train_prev, train_next, test_prev, test_next,
                      n_bird: int, model_kwargs: dict | None = None) -> dict:
    """Section 7: Delta-ell(Bhat) = ell(M_{I,Bhat}) - ell(M_all) on the
    UNTOUCHED test trajectories. Continuous loss is reported regardless of
    pass/fail against delta_pred=0.01 nats/bird-step (the caller applies that
    threshold; this function only computes the numbers)."""
    model_kwargs = model_kwargs or {}
    I_sorted = sorted(int(x) for x in I)
    I_set = set(I_sorted)
    all_exterior = [j for j in range(n_bird) if j not in I_set]
    B_sorted = sorted(int(b) for b in B_hat)

    full_loss_test = fit_eval(I_sorted, all_exterior, train_prev, train_next, test_prev, test_next, **model_kwargs)
    B_loss_test = fit_eval(I_sorted, B_sorted, train_prev, train_next, test_prev, test_next, **model_kwargs)
    I_only_loss_test = fit_eval(I_sorted, [], train_prev, train_next, test_prev, test_next, **model_kwargs)

    return dict(full_loss_test=full_loss_test, B_loss_test=B_loss_test,
                I_only_loss_test=I_only_loss_test, excess_loss=B_loss_test - full_loss_test)
