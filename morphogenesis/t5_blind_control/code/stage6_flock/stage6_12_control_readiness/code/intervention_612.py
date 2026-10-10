"""Stage 6.12 PRIMARY fixed-schedule intervention rollout + outcome metrics.

Semantics (frozen, task brief S4):
  1. actuator set S subset P_t (nearest-20 exterior pool) selected once at t0;
  2. force those physical bird IDs toward h_star;
  3. hold forcing for exactly d consecutive real steps (offsets 0..d-1);
  4. no replanning during those d steps;
  5. release all forcing;
  6. observe for a fixed R_RELEASE=24-step release period.

CRN: every branch (no-control / a given actuator set) for a given replicate
index r uses np.random.default_rng(PHYSICS_SEED_BASE + r) as its physics
stream, identically. Actuator-SET SAMPLING uses a completely separate design
RNG stream (np.random.default_rng(DESIGN_SEED_BASE + ...)), never the
physics stream -- see RNG_PROTOCOL.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612 as C  # noqa: E402

R_RELEASE = 24
D_GRID = (1, 2, 4, 8, 16, 24)
K_GRID = (1, 2, 4, 8)
D_MAX = max(D_GRID)


def simulate_branch(mf, r0, z0, physics_seed, S, h_star, d, n_steps):
    """Simulate n_steps from (r0,z0) forcing bird ids in S toward h_star for
    the first d steps, then releasing. S=None or d=0 means no forcing at all.
    Returns r_hist, z_hist arrays of length n_steps+1 (including t0)."""
    rng = np.random.default_rng(physics_seed)
    r, z = r0.copy(), z0.copy()
    r_hist = [r.copy()]
    z_hist = [z.copy()]
    forced_set = {int(b): int(h_star) for b in S} if (S is not None and d > 0) else {}
    for i in range(n_steps):
        forced = forced_set if (i < d and forced_set) else None
        r, z, _ = mf.step(r, z, rng, forced_actions=forced)
        r_hist.append(r.copy())
        z_hist.append(z.copy())
    return np.stack(r_hist), np.stack(z_hist)


def trace_target(r_hist, z_hist, z_context, seed_members, rule, L=None):
    """Runs detect_69.propose + ForwardMaterialTrace611 over a simulated
    trajectory, seeded from `seed_members` at t=0 (== t0)."""
    L = L or C.L_BOX
    z_window = list(z_context)
    z_window.append(z_hist[0])
    if len(z_window) > C.AFFINITY_WINDOW:
        z_window.pop(0)
    tr = C.ForwardMaterialTrace611(rule)
    tr.start(0, seed_members)
    for t in range(1, len(z_hist)):
        z_window.append(z_hist[t])
        if len(z_window) > C.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = C.detect_propose(r_hist[t], z_window, L) if len(z_window) >= 2 else []
        cands = [frozenset(int(x) for x in c) for c in cands]
        tr.step(t, cands)
    return tr


def outcome_metrics(tr, z_hist, h_star, d, r_hist=None, S=None, mf=None):
    """Computes the primary outcome bundle for one traced rollout, sliced at
    forcing duration d (rollout may be longer than d+R_RELEASE if a shared
    no-control rollout is being reused for multiple d values -- caller must
    pass an already-correctly-length-truncated tr/z_hist/r_hist for that d)."""
    hist = tr.history
    n = len(hist)

    def frac_at(idx):
        dec = hist[idx]
        if dec.accepted_members is None:
            return None
        return C.frac_at_heading(dec.accepted_members, z_hist[idx], h_star)

    # 9.1 immediate/control response
    idx_p4 = min(d + 4, n - 1)
    align_plus4 = frac_at(idx_p4)
    idx_end_forcing = min(d, n - 1)
    align_end_forcing = frac_at(idx_end_forcing)
    tail_idxs = [i for i in range(max(0, d - min(4, d)), min(d, n - 1) + 1)] if d > 0 else [0]
    tail_vals = [v for v in (frac_at(i) for i in tail_idxs) if v is not None]
    mean_forcing_tail = float(np.mean(tail_vals)) if tail_vals else None
    forcing_vals = [v for v in (frac_at(i) for i in range(0, min(d, n - 1) + 1)) if v is not None]
    peak_forcing = float(np.max(forcing_vals)) if forcing_vals else None

    # 9.2 release/persistence response
    release_start = min(d, n - 1)
    release_end = min(d + R_RELEASE, n - 1)
    release_idxs = list(range(release_start, release_end + 1))
    release_vals_by_idx = {i: frac_at(i) for i in release_idxs}
    late_idxs = release_idxs[-8:] if len(release_idxs) >= 8 else release_idxs
    late_vals = [v for i in late_idxs if (v := release_vals_by_idx[i]) is not None]
    A_release_late = float(np.mean(late_vals)) if late_vals else None
    end_release_val = release_vals_by_idx.get(release_end)
    release_traj = [release_vals_by_idx[i] for i in release_idxs]
    peak_release = float(np.max([v for v in release_traj if v is not None])) if any(v is not None for v in release_traj) else None

    # 9.3 strict identity validity through the release-evaluation window
    window_hist = [hist[i] for i in range(release_start, release_end + 1) if i < n]
    V = 1 if all(h.status == "continuing" for h in window_hist) and len(window_hist) == len(release_idxs) else 0
    # event classification
    event = "none"
    any_split = any(h.split_flag for h in hist[: release_end + 1])
    any_merge = any(h.merge_flag for h in hist[: release_end + 1])
    if V == 0:
        last = hist[min(release_end, n - 1)]
        if last.status == "dead":
            event = "lost_dead"
        elif last.status == "unresolved":
            event = "unresolved"
        else:
            event = "candidate_split_or_merge_interruption"
    if any_split:
        event = "confirmed_split" if event == "none" else event + "+split_flag"
    if any_merge:
        event = "confirmed_merge" if event == "none" else event + "+merge_flag"

    # 9.4 primary control utility
    J = float(V * A_release_late) if A_release_late is not None else 0.0

    out = dict(
        align_plus4=align_plus4, align_end_forcing=align_end_forcing,
        mean_forcing_tail=mean_forcing_tail, peak_forcing=peak_forcing,
        A_release_late=A_release_late, end_of_release_alignment=end_release_val,
        peak_release=peak_release, release_trajectory=release_traj,
        V=V, event=event, n_split_flags=int(sum(h.split_flag for h in hist)),
        n_merge_flags=int(sum(h.merge_flag for h in hist)),
        n_unresolved_steps=int(sum(h.status == "unresolved" for h in hist)),
        J=J,
        target_size_end=len(hist[min(release_end, n - 1)].accepted_members or []),
    )
    if r_hist is not None and S is not None and mf is not None:
        out.update(mechanism_diagnostics(hist, r_hist, z_hist, S, d, mf, h_star))
    return out


def mechanism_diagnostics(hist, r_hist, z_hist, S, d, mf, h_star):
    """AUDIT-ONLY oracle diagnostics (task brief S16): uses the true
    interaction radius R. Never used to choose actuator sets -- logged only.
    """
    if not S:
        return dict(mech_direct_contacts_t0=0, mech_cumulative_contact_edges=0,
                    mech_unique_target_coverage=0, mech_mean_actuator_target_dist=None,
                    mech_min_actuator_target_dist=None, mech_actuators_entered_target=0,
                    mech_actuators_lost_all_contact_step=None,
                    collateral_target_size_start=None, collateral_target_size_final=None,
                    collateral_frac_forced_heading_start=None, collateral_frac_forced_heading_final=None)
    S_arr = np.array(sorted(int(s) for s in S))
    cum_edges = 0
    covered = set()
    first_all_lost = None
    dists0 = None
    for i in range(0, min(d, len(r_hist) - 1) + 1):
        members = hist[i].accepted_members or frozenset()
        if not members:
            continue
        mem_arr = np.array(sorted(int(m) for m in members))
        delta = C.torus_delta(r_hist[i][S_arr][:, None, :], r_hist[i][mem_arr][None, :, :], mf.L)
        D = np.sqrt((delta ** 2).sum(-1))
        contact = D <= mf.R
        cum_edges += int(contact.sum())
        covered |= set(int(mem_arr[j]) for j in np.where(contact.any(axis=0))[0])
        any_contact_per_actuator = contact.any(axis=1)
        if i == 0:
            dists0 = D.min(axis=1)
        if not any_contact_per_actuator.any() and first_all_lost is None and i > 0:
            first_all_lost = i
    entered = sum(1 for s in S if int(s) in (hist[min(d, len(hist) - 1)].accepted_members or frozenset()))

    # S18 collateral diagnostics: heading-distribution change among birds
    # that are NEITHER the (current) target NOR an actuator, comparing t0 to
    # the final traced frame -- a coarse organizational-readout, not a new
    # multi-object identity system.
    final_idx = len(hist) - 1
    final_members = hist[final_idx].accepted_members or frozenset()
    start_members = hist[0].accepted_members or frozenset()
    S_set = set(int(s) for s in S)
    N = z_hist.shape[1]
    outside_final = np.array([i for i in range(N) if i not in final_members and i not in S_set])
    outside_start = np.array([i for i in range(N) if i not in start_members and i not in S_set])
    collateral_frac_start = float((z_hist[0][outside_start] == h_star).mean()) if len(outside_start) else None
    collateral_frac_final = float((z_hist[final_idx][outside_final] == h_star).mean()) if len(outside_final) else None

    return dict(
        collateral_target_size_start=len(start_members), collateral_target_size_final=len(final_members),
        collateral_frac_forced_heading_start=collateral_frac_start,
        collateral_frac_forced_heading_final=collateral_frac_final,
        mech_direct_contacts_t0=int((dists0 <= mf.R).sum()) if dists0 is not None else 0,
        mech_cumulative_contact_edges=cum_edges,
        mech_unique_target_coverage=len(covered),
        mech_mean_actuator_target_dist=float(dists0.mean()) if dists0 is not None else None,
        mech_min_actuator_target_dist=float(dists0.min()) if dists0 is not None else None,
        mech_actuators_entered_target=int(entered),
        mech_actuators_lost_all_contact_step=first_all_lost,
    )


def run_one(mf, r0, z0, z_context, seed_members, rule, h_star, S, d, physics_seed, with_mechanism=True):
    n_steps = d + R_RELEASE
    r_hist, z_hist = simulate_branch(mf, r0, z0, physics_seed, S, h_star, d, n_steps)
    tr = trace_target(r_hist, z_hist, z_context, seed_members, rule)
    return outcome_metrics(tr, z_hist, h_star, d, r_hist=r_hist if with_mechanism else None,
                            S=S if with_mechanism else None, mf=mf if with_mechanism else None)


def run_no_control_full(mf, r0, z0, z_context, seed_members, rule, h_star, physics_seed):
    """One no-forcing rollout of length D_MAX + R_RELEASE, traced once; slice
    at any d to get that budget's no-control outcome (valid since no forcing
    means the natural trajectory doesn't depend on d). Saves ~6x compute vs
    one no-control rollout per d value."""
    n_steps = D_MAX + R_RELEASE
    r_hist, z_hist = simulate_branch(mf, r0, z0, physics_seed, None, h_star, 0, n_steps)
    tr = trace_target(r_hist, z_hist, z_context, seed_members, rule)
    return {d: outcome_metrics(tr, z_hist, h_star, d) for d in D_GRID}
