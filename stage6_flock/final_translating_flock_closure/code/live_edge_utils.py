"""Closure A/B: live_edges-based organizational class assignment, live-edge
diagnostic persistence, and the minimal temporal-reachability diagnostic.

`live_edges(r, z)` (stage6_9_translating_collective/code/moving_flock.py,
inherited unmodified by MovingFlock611) returns `(recv, src, dvec)`: a
DIRECTED edge src->recv means bird `src` is a live source of influence into
bird `recv`'s next-heading computation (within R AND in recv's own FOV
half-plane, `(r_src-r_recv).heading_recv >= 0`). Edges are asymmetric.

Classes (assigned at intervention onset t0, from `target_set` = the traced
material target's current members and `pool20` = the nearest-20 exterior
pool):
  A. core_member      -- in target_set, no live edge crossing the boundary
                          (neither incoming-external nor outgoing-external).
  B. boundary_member   -- in target_set, participates in >=1 live edge
                          crossing the target/non-target boundary (either
                          direction). incoming/outgoing/reciprocal recorded
                          separately as diagnostics.
  C. live_exterior_parent -- NOT in target_set, has >=1 directed live edge
                          exterior_bird -> some target_member (actual
                          influence into the target, not distance alone).
  D. near_exterior_non_parent -- NOT in target_set, in pool20, with ZERO
                          live directed edge into target_set at t0.
"""
from __future__ import annotations

import numpy as np


def live_edge_sets(mf, r, z, target_set):
    """Returns dict of boundary/core/live-parent bookkeeping computed from
    one live_edges() call, restricted to edges touching target_set."""
    recv, src, dvec = mf.live_edges(r, z)
    N = mf.N
    is_t = np.zeros(N, dtype=bool)
    if target_set:
        is_t[np.array(sorted(int(m) for m in target_set))] = True
    recv_in_t = is_t[recv]
    src_in_t = is_t[src]

    ext_to_t_mask = recv_in_t & (~src_in_t)      # exterior -> target
    t_to_ext_mask = (~recv_in_t) & src_in_t       # target -> exterior
    intra_t_mask = recv_in_t & src_in_t            # target -> target (irrelevant to class)

    incoming_recv = set(int(x) for x in recv[ext_to_t_mask])   # target members WITH incoming external edge
    outgoing_src = set(int(x) for x in src[t_to_ext_mask])      # target members WITH outgoing external edge
    boundary_members = incoming_recv | outgoing_src
    core_members = (target_set - boundary_members)

    live_parents = set(int(x) for x in src[ext_to_t_mask])       # exterior birds with >=1 live edge INTO target
    # per-parent: which target members does it directly influence, and how many edges
    parent_to_targets: dict[int, set[int]] = {}
    for s, rv in zip(src[ext_to_t_mask].tolist(), recv[ext_to_t_mask].tolist()):
        parent_to_targets.setdefault(int(s), set()).add(int(rv))

    reciprocal_members = incoming_recv & outgoing_src

    return dict(
        boundary_members=boundary_members, core_members=core_members,
        incoming_only_members=incoming_recv - outgoing_src,
        outgoing_only_members=outgoing_src - incoming_recv,
        reciprocal_members=reciprocal_members,
        live_parents=live_parents, parent_to_targets=parent_to_targets,
        n_ext_to_target_edges=int(ext_to_t_mask.sum()), n_target_to_ext_edges=int(t_to_ext_mask.sum()),
        n_intra_target_edges=int(intra_t_mask.sum()),
    )


def assign_classes(mf, r0, z0, target_set, pool20):
    """Assign the 4 organizational classes at t0. Returns dict with class ->
    sorted candidate-id list, plus the raw live_edge_sets() bookkeeping."""
    les = live_edge_sets(mf, r0, z0, target_set)
    pool_set = set(int(p) for p in pool20)
    class_c = sorted(les["live_parents"] & pool_set)   # distance-comparable to D
    class_c_outside_pool = sorted(les["live_parents"] - pool_set)  # diagnostic only
    class_d = sorted(pool_set - les["live_parents"])
    return dict(
        core_member=sorted(les["core_members"]),
        boundary_member=sorted(les["boundary_members"]),
        live_exterior_parent=class_c,
        live_exterior_parent_outside_pool=class_c_outside_pool,
        near_exterior_non_parent=class_d,
        diagnostics=les,
    )


def geometric_distance(mf, r0, actuator, target_set, L):
    """Static min torus distance from actuator to nearest target member, for
    the distance-match diagnostic between class C and class D (spec: 'don't
    do complicated propensity matching -- just record distance distributions
    so residual mismatch is visible')."""
    from common_closure import torus_delta
    tgt_arr = np.array(sorted(int(m) for m in target_set))
    delta = torus_delta(r0[tgt_arr], r0[int(actuator)][None, :], L)
    return float(np.sqrt((delta ** 2).sum(-1)).min())


def temporal_reachability(mf, r_hist, z_hist, actuator_id, target_set, max_hops=3):
    """Minimal time-unfolded reachability diagnostic (Closure B). Starting at
    `actuator_id` at forcing onset (frame 0 of r_hist/z_hist, i.e. t0), using
    the REALIZED forced trajectory's actual directed live_edges at each of
    the first `max_hops` forcing steps, one hop is allowed per real
    simulator step (information takes >=1 physical step per relay). Returns
    reachable-target-member counts/fractions within <=1, <=2, <=3 hops.
    Not used to select actuators -- diagnostic/persisted only.
    """
    target_arr = sorted(int(m) for m in target_set)
    n_target = len(target_arr) if target_arr else 1
    reached = {int(actuator_id): 0}
    hop_reached_counts = {}
    n_steps = min(max_hops, len(r_hist) - 1)
    for t in range(n_steps):
        recv, src, _ = mf.live_edges(r_hist[t], z_hist[t])
        newly = {}
        for s_i, r_i in zip(src.tolist(), recv.tolist()):
            if s_i in reached and r_i not in reached and r_i not in newly:
                newly[r_i] = reached[s_i] + 1
        reached.update(newly)
        hop = t + 1
        reached_targets = set(target_arr) & set(reached.keys())
        hop_reached_counts[hop] = dict(
            n_reached_targets=len(reached_targets),
            frac_reached_targets=float(len(reached_targets) / n_target),
        )
    out = {}
    for h in (1, 2, 3):
        if h in hop_reached_counts:
            out[f"n_reached_le{h}"] = hop_reached_counts[h]["n_reached_targets"]
            out[f"frac_reached_le{h}"] = hop_reached_counts[h]["frac_reached_targets"]
        else:
            last = max(hop_reached_counts.keys()) if hop_reached_counts else None
            out[f"n_reached_le{h}"] = hop_reached_counts[last]["n_reached_targets"] if last else 0
            out[f"frac_reached_le{h}"] = hop_reached_counts[last]["frac_reached_targets"] if last else 0.0
    return out


def per_step_live_diagnostics(mf, r_hist, z_hist, actuator_id, target_set, d):
    """Persist actuator->target / target->actuator live-edge diagnostics for
    each of the d forcing steps (Closure B persistence requirement)."""
    target_arr = np.array(sorted(int(m) for m in target_set)) if target_set else np.array([], dtype=int)
    out_deg_per_step, rev_deg_per_step, reciprocal_per_step = [], [], []
    unique_covered = set()
    steps_with_access = 0
    for t in range(min(d, len(r_hist))):
        recv, src, _ = mf.live_edges(r_hist[t], z_hist[t])
        a2t = (src == int(actuator_id)) & np.isin(recv, target_arr)
        t2a = (recv == int(actuator_id)) & np.isin(src, target_arr)
        out_deg = int(a2t.sum())
        rev_deg = int(t2a.sum())
        out_deg_per_step.append(out_deg)
        rev_deg_per_step.append(rev_deg)
        reciprocal_per_step.append(int(out_deg > 0 and rev_deg > 0))
        if out_deg > 0:
            steps_with_access += 1
            unique_covered |= set(int(x) for x in recv[a2t])
    d_eff = max(1, min(d, len(r_hist)))
    return dict(
        actuator_to_target_out_degree_per_step=out_deg_per_step,
        target_to_actuator_reverse_degree_per_step=rev_deg_per_step,
        reciprocity_per_step=reciprocal_per_step,
        cumulative_actuator_to_target_edges=int(sum(out_deg_per_step)),
        cumulative_target_to_actuator_edges=int(sum(rev_deg_per_step)),
        n_unique_target_members_directly_influenced=len(unique_covered),
        duration_with_live_access=steps_with_access,
        fraction_forcing_steps_with_live_access=float(steps_with_access / d_eff),
    )
