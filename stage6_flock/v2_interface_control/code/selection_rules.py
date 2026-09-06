"""Part K1: the four predeclared, transparent actuator-selection rules,
operating on B^D_0(I0) for a given flock. See PROTOCOL_V2.md."""
from __future__ import annotations

import numpy as np

from common_v2 import T_U, evaluate_arm


def rule_A_degree(B_D0: np.ndarray, I0: np.ndarray, lattice, k: int) -> list[int]:
    I0_set = set(I0.tolist())
    deg = np.array([sum(1 for j in lattice.neighbor_ids[b].tolist() if j in I0_set) for b in B_D0])
    order = np.argsort(-deg, kind="stable")
    return B_D0[order][:k].tolist()


def rule_B_leverage(B_D0: np.ndarray, I0: np.ndarray, h_star: int, z_t0, lattice, k: int,
                     n_replicates: int = 20, seed_offset: int = 400_000) -> list[int]:
    resp = np.zeros(len(B_D0))
    for idx, b in enumerate(B_D0.tolist()):
        m = evaluate_arm([b], z_t0, I0, h_star, lattice, n_replicates=n_replicates, seed_offset=seed_offset)
        resp[idx] = m["mean_Hstar_end"]
    order = np.argsort(-resp, kind="stable")
    return B_D0[order][:k].tolist()


def rule_C_patch(B_D0: np.ndarray, I0: np.ndarray, lattice, k: int) -> list[int]:
    """Grow a single connected patch within B^D_0's own induced subgraph
    (edges = lattice adjacency restricted to B^D_0), BFS from the
    highest-I0-degree seed; if the graph is disconnected, continue with the
    next-largest unvisited component until k is reached."""
    B_set = set(B_D0.tolist())
    I0_set = set(I0.tolist())
    deg = {b: sum(1 for j in lattice.neighbor_ids[b].tolist() if j in I0_set) for b in B_D0.tolist()}
    remaining = set(B_D0.tolist())
    patch: list[int] = []
    while remaining and len(patch) < k:
        seed = max(remaining, key=lambda b: deg[b])
        comp_order = []
        visited = {seed}
        frontier = [seed]
        comp_order.append(seed)
        while frontier and len(comp_order) < len(remaining):
            nxt = []
            for b in frontier:
                for j in lattice.neighbor_ids[b].tolist():
                    if j in remaining and j not in visited:
                        visited.add(j)
                        comp_order.append(j)
                        nxt.append(j)
            frontier = nxt
        patch.extend(comp_order[: max(0, k - len(patch))])
        remaining -= set(comp_order)
    return patch[:k]


def rule_D_random(B_D0: np.ndarray, k: int, rng: np.random.Generator) -> list[int]:
    return rng.choice(B_D0, size=k, replace=False).tolist()
