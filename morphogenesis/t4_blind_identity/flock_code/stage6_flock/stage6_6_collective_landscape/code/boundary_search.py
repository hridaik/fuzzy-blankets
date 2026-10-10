"""Section 10 of the task brief: choose B*_K(I) subseteq S(I), |B|=min(K,|S(I)|),
minimizing held-out L_I, via greedy forward selection then one-swap local
refinement. B is chosen only from I's own structural shell S(I) -- using the
simulator's known shell as the candidate pool is an explicit, stated
simplification for this collective-*characterization* stage (task brief
section 10, "not observational boundary discovery")."""
from __future__ import annotations

import numpy as np

from common_66 import structural_shell
from predictive_cache import PredictiveCache, clamp_machine_eps


def _L_I_only(cache: PredictiveCache, I, B) -> float:
    vals = []
    for i in I:
        ell_IB = cache.get_loss(i, cache.mask_IB(i, I, B))
        ell_full = cache.get_loss(i, cache.mask_full(i))
        vals.append(clamp_machine_eps(ell_IB - ell_full))
    return float(np.mean(vals))


def select_boundary(cache: PredictiveCache, lattice, I: np.ndarray, K: int,
                     max_swap_passes: int = 2) -> dict:
    S = structural_shell(lattice, I)
    S_size = len(S)
    target_size = min(K, S_size)

    if S_size <= K:
        B = np.array(sorted(S), dtype=int)
        L_I = _L_I_only(cache, I, B)
        return dict(B=B, S=S, structural_shell_size=S_size, boundary_budget=K,
                    boundary_size=len(B), L_I=L_I, used_full_shell=True, trace=[])

    remaining = set(int(s) for s in S)
    B: list[int] = []
    trace = []
    for _step in range(target_size):
        best_node, best_L = None, None
        for cand in remaining:
            trial = B + [cand]
            L_val = _L_I_only(cache, I, trial)
            if best_L is None or L_val < best_L:
                best_node, best_L = cand, L_val
        B.append(best_node)
        remaining.discard(best_node)
        trace.append(dict(added=best_node, L_I=best_L))

    current_L = trace[-1]["L_I"] if trace else _L_I_only(cache, I, B)
    for _pass in range(max_swap_passes):
        improved = False
        for b in list(B):
            others = [x for x in S if x not in B]
            best_swap, best_L = None, current_L
            for s in others:
                trial = [x for x in B if x != b] + [s]
                L_val = _L_I_only(cache, I, trial)
                if L_val < best_L - 1e-12:
                    best_swap, best_L = s, L_val
            if best_swap is not None:
                B = [x for x in B if x != b] + [best_swap]
                current_L = best_L
                improved = True
                trace.append(dict(swapped_out=b, swapped_in=best_swap, L_I=best_L))
        if not improved:
            break

    B_arr = np.array(sorted(B), dtype=int)
    L_I = _L_I_only(cache, I, B_arr)
    return dict(B=B_arr, S=S, structural_shell_size=S_size, boundary_budget=K,
                boundary_size=len(B_arr), L_I=L_I, used_full_shell=False, trace=trace)
