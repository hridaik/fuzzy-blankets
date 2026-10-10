"""Stage 6.12B-B core: refreshing-actuator-set rollout. Interleaves
simulation and material tracing step-by-step (unlike Stage 6.12's
post-hoc-trace-the-whole-trajectory approach) because the deployable
strategies ('nearest', 'kinematic') and the exterior pool itself must be
recomputed from the CURRENT (already-simulated) state at every refresh
boundary -- never from future information.

Total intervention effort is matched across cadences: exactly K birds are
forced at every one of the T_control=24 control steps, for every q.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612b as C            # noqa: E402
import intervention_612 as I611    # noqa: E402
import intervention_612b as IB     # noqa: E402

T_CONTROL = 24
R_RELEASE = 24
POOL_M = 20
STRATEGIES = ("random", "nearest", "kinematic", "kinematic_radius_free", "oracle", "fixed_reference")
Q_GRID = (24, 8, 4, 2, 1)
K_GRID = (2, 4)


def _current_pool(members, r, L, M=POOL_M):
    if not members:
        return []
    return C.nearest_M_pool(np.array(sorted(int(m) for m in members)), r, L, M)


def _nearest_select(pool, r, members, L, K):
    if not pool:
        return []
    mem_arr = np.array(sorted(int(m) for m in members))
    pool_arr = np.array(sorted(int(p) for p in pool))
    d = C.torus_delta(r[pool_arr][:, None, :], r[mem_arr][None, :, :], L)
    dist = np.sqrt((d ** 2).sum(-1)).min(axis=1)
    order = np.argsort(dist)[:K]
    return [int(pool_arr[i]) for i in order]


def run_refresh_rollout(mf, r0, z0, z_context, seed_members, rule, h_star, K, q, strategy, physics_seed,
                         design_rng=None, nc_data=None, fixed_reference_S=None):
    """nc_data: (nc_r_hist, nc_z_hist, nc_trace) from a PAIRED no-control
    rollout at the SAME physics_seed -- required for strategy='oracle'
    only. fixed_reference_S: required for strategy='fixed_reference'."""
    rng = np.random.default_rng(physics_seed)
    r, z = r0.copy(), z0.copy()
    r_hist = [r.copy()]; z_hist = [z.copy()]
    z_window = list(z_context) + [z0.copy()]
    if len(z_window) > C.AFFINITY_WINDOW:
        z_window = z_window[-C.AFFINITY_WINDOW:]
    tr = C.ForwardMaterialTrace611(rule)
    tr.start(0, seed_members)
    n_steps = T_CONTROL + R_RELEASE
    current_actuators: list[int] = []
    actuator_log = []
    entered_target_events = 0
    turnover_count = 0

    for i in range(n_steps):
        if i < T_CONTROL and i % q == 0:
            members_now = tr.accepted or frozenset(seed_members)
            pool = _current_pool(members_now, r, C.L_BOX)
            window = min(q, T_CONTROL - i)
            if strategy == "random":
                chosen = [int(x) for x in design_rng.choice(pool, size=min(K, len(pool)), replace=False)] if pool else []
            elif strategy == "nearest":
                chosen = _nearest_select(pool, r, members_now, C.L_BOX, K)
            elif strategy == "kinematic":
                scores = IB.kinematic_contact_scores(r, z, pool, members_now, C.L_BOX, mf.v, window, R=mf.R)
                chosen = IB.top_k_by_score(scores, K)
            elif strategy == "kinematic_radius_free":
                scores = IB.kinematic_contact_scores(r, z, pool, members_now, C.L_BOX, mf.v, window, R=None)
                chosen = IB.top_k_by_score(scores, K)
            elif strategy == "oracle":
                nc_r_hist, nc_z_hist, nc_tr = nc_data
                scores = IB.oracle_future_contact_scores(nc_r_hist, nc_z_hist, nc_tr, i, window, pool,
                                                          C.L_BOX, mf.R, fallback_members=members_now)
                chosen = IB.top_k_by_score(scores, K)
            elif strategy == "fixed_reference":
                chosen = list(fixed_reference_S) if i == 0 else current_actuators
            else:
                raise ValueError(strategy)
            if current_actuators and set(chosen) != set(current_actuators):
                turnover_count += 1
            current_actuators = chosen
            actuator_log.append(dict(step_offset=i, actuators=[int(a) for a in chosen], pool_size=len(pool)))

        forced = {int(b): int(h_star) for b in current_actuators} if (i < T_CONTROL and current_actuators) else None
        r, z, _ = mf.step(r, z, rng, forced_actions=forced)
        r_hist.append(r.copy()); z_hist.append(z.copy())
        z_window.append(z.copy())
        if len(z_window) > C.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = C.detect_propose(r, z_window, C.L_BOX) if len(z_window) >= 2 else []
        cands = [frozenset(int(x) for x in c) for c in cands]
        d = tr.step(i + 1, cands)
        if current_actuators and d.accepted_members and any(int(a) in d.accepted_members for a in current_actuators):
            entered_target_events += 1

    r_hist = np.stack(r_hist); z_hist = np.stack(z_hist)
    out = I611.outcome_metrics(tr, z_hist, h_star, T_CONTROL)
    out = IB.add_conservative(out)

    # mechanism/collateral, computed over the WHOLE actuator history (not a
    # fixed S -- reimplemented here rather than reusing
    # intervention_612.mechanism_diagnostics, which assumes one fixed S)
    all_actuators_ever = sorted(set(a for e in actuator_log for a in e["actuators"]))
    cum_edges, covered = 0, set()
    zero_contact_steps = 0
    contact_actuator_steps = 0
    total_actuator_steps = 0
    for i in range(T_CONTROL):
        acts = next((e["actuators"] for e in reversed(actuator_log) if e["step_offset"] <= i), [])
        if not acts:
            continue
        total_actuator_steps += len(acts)
        members = tr.history[i].accepted_members or frozenset()
        if not members:
            zero_contact_steps += 1
            continue
        a_arr = np.array(sorted(int(a) for a in acts))
        m_arr = np.array(sorted(int(m) for m in members))
        delta = C.torus_delta(r_hist[i][a_arr][:, None, :], r_hist[i][m_arr][None, :, :], mf.L)
        dist = np.sqrt((delta ** 2).sum(-1))
        contact = dist <= mf.R
        cum_edges += int(contact.sum())
        covered |= set(int(m_arr[j]) for j in np.where(contact.any(axis=0))[0])
        n_contact_actuators = int(contact.any(axis=1).sum())
        contact_actuator_steps += n_contact_actuators
        if n_contact_actuators == 0:
            zero_contact_steps += 1

    out.update(dict(
        actuator_log=actuator_log, all_actuators_ever=all_actuators_ever,
        n_turnovers=turnover_count, n_refreshes=len(actuator_log),
        cumulative_contact_edges=cum_edges, unique_target_coverage=len(covered),
        zero_contact_steps=zero_contact_steps,
        fraction_actuator_steps_in_contact=(contact_actuator_steps / total_actuator_steps) if total_actuator_steps else None,
        entered_target_step_events=entered_target_events,
    ))
    return out


def run_no_control_full(mf, r0, z0, z_context, seed_members, rule, h_star, physics_seed):
    n_steps = T_CONTROL + R_RELEASE
    r_hist, z_hist = I611.simulate_branch(mf, r0, z0, physics_seed, None, h_star, 0, n_steps)
    tr = I611.trace_target(r_hist, z_hist, z_context, seed_members, rule)
    out = IB.add_conservative(I611.outcome_metrics(tr, z_hist, h_star, T_CONTROL))
    return out, r_hist, z_hist, tr
