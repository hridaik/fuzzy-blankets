"""Ties metrics_66 + predictive_cache + boundary_search together into one
per-candidate profile Phi(I) = (C, G, L, D) plus the section-16 bookkeeping
fields, and assembles a full snapshot's candidate landscape."""
from __future__ import annotations

import numpy as np

from common_66 import near_exterior, distant_exterior, K_BOUNDARY_BUDGET
from metrics_66 import coherence_C, local_contrast_D, external_entropy_H, directional_opposition
from predictive_cache import PredictiveCache, G_and_L
from boundary_search import select_boundary
from pareto import pareto_nondominated


def evaluate_candidate(cache: PredictiveCache, lattice, z: np.ndarray, I: np.ndarray,
                        K: int = K_BOUNDARY_BUDGET, include_per_bird: bool = False) -> dict:
    I = np.asarray(sorted(int(i) for i in I), dtype=int)
    bsel = select_boundary(cache, lattice, I, K)
    B = bsel["B"]
    gl = G_and_L(cache, I, B)
    E_near = near_exterior(lattice, I, nn=lattice.nn)
    C = coherence_C(z, I)
    D = local_contrast_D(z, I, E_near)
    H_E = external_entropy_H(z, E_near)
    dirinfo = directional_opposition(z, I, E_near)

    row = dict(
        node_ids=I.tolist(),
        boundary_ids=B.tolist(),
        C_internal=C, G_internal=gl["G_I"], L_blanket=gl["L_I"], D_local=D,
        external_entropy=H_E, directional_contrast=dirinfo["opposition"],
        cosine_similarity=dirinfo["cosine_similarity"],
        structural_shell_size=bsel["structural_shell_size"],
        boundary_budget=K, boundary_size=bsel["boundary_size"],
        used_full_shell=bsel["used_full_shell"],
        n_negative_G_i=gl["n_negative_G_i"], n_negative_L_i=gl["n_negative_L_i"],
    )
    if include_per_bird:
        row["per_bird"] = gl["per_bird"]
    return row


def assemble_landscape(cache: PredictiveCache, lattice, z: np.ndarray, candidates: list,
                        snapshot_id: str, K: int = K_BOUNDARY_BUDGET) -> list[dict]:
    """candidates: list of candidates.Candidate. Returns a list of row dicts
    (section 16 schema, minus is_pareto which is filled in by the caller once
    all rows for the snapshot are known)."""
    rows = []
    for idx, cand in enumerate(candidates):
        row = evaluate_candidate(cache, lattice, z, cand.nodes, K=K)
        row.update(candidate_id=f"{snapshot_id}__c{idx:05d}", snapshot_id=snapshot_id,
                   candidate_source=cand.source)
        rows.append(row)
    return rows


def attach_pareto(rows: list[dict]) -> list[dict]:
    C = np.array([r["C_internal"] for r in rows])
    G = np.array([r["G_internal"] for r in rows])
    L = np.array([r["L_blanket"] for r in rows])
    D = np.array([r["D_local"] for r in rows])
    flags = pareto_nondominated(C, G, L, D)
    for r, f in zip(rows, flags):
        r["is_pareto"] = bool(f)
    return rows
