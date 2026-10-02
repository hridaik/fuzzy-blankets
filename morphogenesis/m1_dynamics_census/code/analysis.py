"""Shared hidden-tier analysis primitives for M1: permutation-invariant
outcome measures, cell-type assignment, classification. Imports m0b's
validated model.py (unmodified) for the template.
"""
import os
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                 "m0b_reference_port", "code"))
from model import decode_template  # noqa: E402

P_X, P_S, N_CELLS, M_SIG = decode_template()

# canonical type codes from the target template's own expression rows 1:4
# (row0 is the trivial "existence" channel, always 1 -- see MODEL_SPEC.md m0)
TARGET_TYPE_CODES = P_S[1:, :].T  # (n_cells, 3) binary codes, one per template slot
NN_SPACING = None


def nearest_neighbour_spacing():
    global NN_SPACING
    if NN_SPACING is None:
        d = np.linalg.norm(P_X[:, :, None] - P_X[:, None, :], axis=0)
        np.fill_diagonal(d, np.inf)
        NN_SPACING = d.min(axis=1)
    return NN_SPACING


TAU_POS_DEFAULT = 0.25 * nearest_neighbour_spacing().min()
TAU_PAIR_DEFAULT = TAU_POS_DEFAULT
TAU_BEL_DEFAULT = 0.9


def cell_type_from_expression(a_s_final: np.ndarray) -> np.ndarray:
    """a_s_final: (4, n) final secretion levels. Returns (n,) index into the
    UNIQUE type codes (_UNIQ_TYPES, defined below -- up to 4 distinct types
    in this template), nearest by L2 distance on the 3 informative channels.
    This is the OBSERVABLE-derivable type assignment. NOTE: must match
    against unique types, not all 8 (duplicated) per-slot codes, else
    same-type cells at different template slots get spuriously different
    'type' labels -- this was a real bug caught by testing (see tests/)."""
    codes = a_s_final[1:, :].T  # (n, 3)
    dists = np.linalg.norm(codes[:, None, :] - _UNIQ_TYPES[None, :, :], axis=-1)
    return np.argmin(dists, axis=1)


def cell_type_from_belief(v_final: np.ndarray) -> np.ndarray:
    """v_final: (n,n) identity-logit matrix (columns=cells). Returns (n,)
    argmax-believed template slot per cell (HIDDEN-tier)."""
    return np.argmax(v_final, axis=0)


def softmax_cols(v):
    e = np.exp(v - v.max(axis=0, keepdims=True))
    return e / e.sum(axis=0, keepdims=True)


def type_of_template_slot(slot_idx):
    """Maps a template slot (0..7) to its TYPE (one of the up-to-4 distinct
    expression codes), for type-CONSTRAINED matching."""
    codes = TARGET_TYPE_CODES
    uniq, inv = np.unique(codes, axis=0, return_inverse=True)
    return inv[slot_idx]


_UNIQ_TYPES, _SLOT_TYPE = np.unique(TARGET_TYPE_CODES, axis=0, return_inverse=True)


TYPE_MISMATCH_PENALTY = 3.0  # finite, declared: prefers same-type matches
# when feasible (Hungarian solver picks them first, since real geometric
# distances are typically << 3.0 units on this template) but degrades to a
# genuine (large but interpretable) distance instead of an uninterpretable
# blow-up when type-constrained assignment is infeasible (e.g. a perturbed
# cell's expression code no longer clearly matches any canonical type --
# this DOES happen under some Part C/D perturbations and is itself a real,
# reportable finding, tracked separately via the mismatch count below, not
# by making the distance metric meaningless).


def hungarian_distance_type_constrained(final_x, target_x=None, final_type=None,
                                          target_type=None):
    """Type-PREFERRING (not hard-constrained) Hungarian mean per-cell
    distance: real geometric distance when types match, a finite penalty
    (TYPE_MISMATCH_PENALTY) added when they don't, so the solver still
    prefers type-correct assignments but the reported number stays
    interpretable even when type-matching is infeasible. Returns
    (mean_distance, role_map, n_type_mismatches)."""
    if target_x is None:
        target_x = P_X
    n = final_x.shape[1]
    if target_type is None:
        target_type = _SLOT_TYPE
    cost = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            geom = np.linalg.norm(final_x[:, i] - target_x[:, j])
            if final_type is None or target_type is None or final_type[i] == target_type[j]:
                cost[i, j] = geom
            else:
                cost[i, j] = geom + TYPE_MISMATCH_PENALTY
    ri, ci = linear_sum_assignment(cost)
    n_mismatch = 0
    if final_type is not None and target_type is not None:
        n_mismatch = int(np.sum(final_type[ri] != target_type[ci]))
    raw_dist = float(np.linalg.norm(final_x[:, ri] - target_x[:, ci], axis=0).sum() / n)
    return raw_dist, ci, n_mismatch  # geometric distance (mismatch penalty excluded), role map, mismatch count


def d_target(final_x, a_s_final):
    """d_target: type-PREFERRING Hungarian mean geometric distance, plus a
    separately-reported expression-code mismatch count, per Part B spec."""
    final_type = cell_type_from_expression(a_s_final)
    dist, role_map, n_mismatch = hungarian_distance_type_constrained(final_x, P_X, final_type, _SLOT_TYPE)
    return dist, role_map, final_type, n_mismatch


def d_pair(x_a, s_a, x_b, s_b):
    """Type-preferring Hungarian distance between two END-STATES (not to
    template) -- role-swap invariant by construction (Hungarian assignment
    is over cell INDEX, not identity). Returns geometric distance only
    (mismatch count available via hungarian_distance_type_constrained if
    needed by a caller)."""
    type_a = cell_type_from_expression(s_a)
    type_b = cell_type_from_expression(s_b)
    n = x_a.shape[1]
    cost = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            geom = np.linalg.norm(x_a[:, i] - x_b[:, j])
            cost[i, j] = geom if type_a[i] == type_b[j] else geom + TYPE_MISMATCH_PENALTY
    ri, ci = linear_sum_assignment(cost)
    return float(np.linalg.norm(x_a[:, ri] - x_b[:, ci], axis=0).sum() / n)


def classify_individual(final_x, a_s_final, v_final, tau_pos=TAU_POS_DEFAULT,
                          tau_bel=TAU_BEL_DEFAULT, stationary=True):
    """TARGET-ASSEMBLED / DEFECT / NONCONVERGED, per Part B spec."""
    if not stationary:
        return "NONCONVERGED", None, None
    dist, role_map, final_type, n_mismatch = d_target(final_x, a_s_final)
    p = softmax_cols(v_final)
    max_bel = p.max(axis=0)
    # per-cell distance to its assigned target (role_map: cell i -> which target slot)
    per_cell_dist = np.array([np.linalg.norm(final_x[:, i] - P_X[:, role_map[i]])
                               for i in range(final_x.shape[1])])
    assembled = np.all(per_cell_dist < tau_pos) and np.all(max_bel > tau_bel)
    label = "TARGET-ASSEMBLED" if assembled else "DEFECT"
    return label, dist, role_map


def identity_events(v_final, final_x, extrusion_dist=3.0):
    """duplicated roles, vacant roles, extruded cells, dedifferentiated
    cells -- HIDDEN-tier identity events at the end-state."""
    argmax_slot = cell_type_from_belief(v_final)
    n = v_final.shape[1]
    p = softmax_cols(v_final)
    max_bel = p.max(axis=0)
    counts = np.bincount(argmax_slot, minlength=n)
    duplicated = int((counts > 1).sum())
    vacant = int((counts == 0).sum())
    # extrusion: farther than `extrusion_dist` x mean-nn-spacing from ALL others
    d = np.linalg.norm(final_x[:, :, None] - final_x[:, None, :], axis=0)
    np.fill_diagonal(d, np.inf)
    min_dist_to_others = d.min(axis=1)
    extruded = int((min_dist_to_others > extrusion_dist * nearest_neighbour_spacing().mean()).sum())
    dedifferentiated = int((max_bel < 0.5).sum())
    return {"duplicated_roles": duplicated, "vacant_roles": vacant,
            "extruded_cells": extruded, "dedifferentiated_cells": dedifferentiated}
