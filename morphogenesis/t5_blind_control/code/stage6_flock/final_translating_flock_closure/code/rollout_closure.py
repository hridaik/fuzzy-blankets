"""One fixed-schedule K=1 rollout (fixed onset), with:
  - ordinary J_assoc/J_conservative (intervention_612b semantics, reused),
  - interior-actuation A_minus_j/J_minus_j correction (interior_correction.py),
  - live-edge diagnostics over the forcing window (live_edge_utils.py),
  - minimal temporal reachability diagnostic (live_edge_utils.py),
  - the old geometric mech_cumulative_contact_edges diagnostic (reused,
    unmodified, for explicit geometric-vs-directed comparison).
"""
from __future__ import annotations

import numpy as np

import common_closure as C
import intervention_612 as I611
import intervention_612b as IB
import interior_correction as IC
import live_edge_utils as LE

R_RELEASE = 24


def run_one_closure(mf, r0, z0, z_context, seed_members, rule, h_star, actuator, d,
                     physics_seed, target_set_t0=None, onset_offset=0):
    """actuator: single bird id (K=1). target_set_t0: the class-assignment
    target set at t0 (used to decide is_interior + live-edge diagnostics
    against; if None, use seed_members)."""
    S = [int(actuator)]
    n_steps = d + R_RELEASE
    r_hist, z_hist = I611.simulate_branch(mf, r0, z0, physics_seed, S, h_star, d, n_steps)
    tr = I611.trace_target(r_hist, z_hist, z_context, seed_members, rule)
    out = I611.outcome_metrics(tr, z_hist, h_star, d, r_hist=r_hist, S=S, mf=mf)
    out = IB.add_conservative(out)

    tgt0 = target_set_t0 if target_set_t0 is not None else seed_members
    is_interior = int(actuator) in tgt0
    out = IC.add_interior_correction(out, tr.history, z_hist, h_star, d, int(actuator), is_interior)

    live_diag = LE.per_step_live_diagnostics(mf, r_hist, z_hist, int(actuator), tgt0, d)
    reach_diag = LE.temporal_reachability(mf, r_hist, z_hist, int(actuator), tgt0, max_hops=3)
    out.update({f"live_{k}": v for k, v in live_diag.items()})
    out.update({f"reach_{k}": v for k, v in reach_diag.items()})
    out["is_interior_actuator"] = is_interior
    out["onset_offset"] = onset_offset
    out["actuator"] = int(actuator)
    out["d"] = d
    out["physics_seed"] = int(physics_seed)
    return out


def run_no_control_closure(mf, r0, z0, z_context, seed_members, rule, h_star, physics_seed, d):
    n_steps = d + R_RELEASE
    r_hist, z_hist = I611.simulate_branch(mf, r0, z0, physics_seed, None, h_star, 0, n_steps)
    tr = I611.trace_target(r_hist, z_hist, z_context, seed_members, rule)
    out = I611.outcome_metrics(tr, z_hist, h_star, d)
    out = IB.add_conservative(out)
    out["A_minus_j_release_late"] = out.get("A_release_late")
    out["J_assoc_minus_j"] = out.get("J_assoc")
    out["J_conservative_minus_j"] = out.get("J_conservative")
    out["physics_seed"] = int(physics_seed)
    out["d"] = d
    return out
