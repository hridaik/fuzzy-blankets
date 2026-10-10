"""Implements INTERIOR_ACTUATION_METHOD_NOTE.md's A_minus_j / J_minus_j
correction exactly as specified there (stage6_12C_kinematic_contact_
confirmation/stable_selectivity_analysis/INTERIOR_ACTUATION_METHOD_NOTE.md).

For an interior/boundary actuator j (a bird that is in `seed_members` at t0,
or that ever appears in the traced target's membership during forcing/
release), the ordinary A_release_late/J metrics trivially count j's own
forced-to-h_star heading once j is inside the traced membership set at the
evaluation frame -- see the method note for the exact mechanism. A_minus_j
recomputes the SAME alignment fraction over target_members(t) \\ {j} at every
frame, using the tracer's own already-computed per-frame membership sets
(genuine identity-aware exclusion, not (|target|-1)/|target| arithmetic).
"""
from __future__ import annotations

import numpy as np

import common_closure as C

R_RELEASE = 24  # matches intervention_612.R_RELEASE


def _frac_at_minus_j(members, z_row, h_star, j):
    if members is None:
        return None
    members2 = frozenset(m for m in members if int(m) != int(j))
    if not members2:
        return None
    return C.frac_at_heading(members2, z_row, h_star)


def compute_a_minus_j(hist, z_hist, h_star, j, d):
    """Reproduces intervention_612.outcome_metrics' release-window A_release_late
    computation exactly, substituting frac_at_minus_j for frac_at."""
    n = len(hist)

    def frac_at(idx):
        return _frac_at_minus_j(hist[idx].accepted_members, z_hist[idx], h_star, j)

    release_start = min(d, n - 1)
    release_end = min(d + R_RELEASE, n - 1)
    release_idxs = list(range(release_start, release_end + 1))
    release_vals_by_idx = {i: frac_at(i) for i in release_idxs}
    late_idxs = release_idxs[-8:] if len(release_idxs) >= 8 else release_idxs
    late_vals = [v for i in late_idxs if (v := release_vals_by_idx[i]) is not None]
    a_minus_j_release_late = float(np.mean(late_vals)) if late_vals else None
    return a_minus_j_release_late


def add_interior_correction(out: dict, hist, z_hist, h_star, d, j, is_interior: bool):
    """Mutates `out` (already produced by intervention_612b.add_conservative)
    in place, adding A_minus_j / J_assoc_minus_j / J_conservative_minus_j.
    For an exterior actuator this is a no-op copy (A_minus_j == A_release_late,
    per the method note: 'for exterior actuators all target members are
    unforced, so ordinary target scoring already is this quantity')."""
    if not is_interior:
        out["A_minus_j_release_late"] = out.get("A_release_late")
        out["J_assoc_minus_j"] = out.get("J_assoc")
        out["J_conservative_minus_j"] = out.get("J_conservative")
        out["interior_actuator_correction_applied"] = False
        return out
    a_mj = compute_a_minus_j(hist, z_hist, h_star, j, d)
    V = out["V"]
    Vc = out["V_conservative"]
    out["A_minus_j_release_late"] = a_mj
    out["J_assoc_minus_j"] = float(V * a_mj) if a_mj is not None else 0.0
    out["J_conservative_minus_j"] = float(Vc * a_mj) if a_mj is not None else 0.0
    out["interior_actuator_correction_applied"] = True
    return out
