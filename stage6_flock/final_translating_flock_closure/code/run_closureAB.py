"""Closure A (organizational-role/membership privilege) + Closure B (true
FOV-gated directed causal interface) main campaign -- SAME simulations serve
both closures, as required by the task spec (Closure B section: 'Use the SAME
Closure-A simulations -- do not create a separate campaign').

K=1, d=8, release=24. Up to 3 actuators per class per state (core_member,
boundary_member, live_exterior_parent, near_exterior_non_parent), 4 paired
physics streams per actuator, CRN-paired against a per-stream no-control
baseline (same physics_seed).

RNG protocol (disjoint from all prior stages -- see RNG_PROTOCOL.md
precedent in stage6_12_control_readiness/stage6_12B_contact_persistence):
  physics_seed = PHYSICS_SEED_BASE(40_000_000) + state_idx*1000 + r   (r=0..3)
  design_seed  = DESIGN_SEED_BASE(41_000_000) + state_idx   (actuator
                 sampling ONLY -- a np.random.default_rng instance never
                 passed to mf.step)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_closure as C  # noqa: E402
import live_edge_utils as LE  # noqa: E402
import rollout_closure as RC  # noqa: E402

D_PRIMARY = 8
N_STREAMS = 4
MAX_PER_CLASS = 3
PHYSICS_SEED_BASE = 40_000_000
DESIGN_SEED_BASE = 41_000_000

CLASSES = ["core_member", "boundary_member", "live_exterior_parent", "near_exterior_non_parent"]


def sample_actuators(classes: dict, design_rng) -> dict:
    picked = {}
    for cls in CLASSES:
        cands = classes[cls]
        if not cands:
            picked[cls] = []
            continue
        cands_sorted = sorted(int(c) for c in cands)
        n = min(MAX_PER_CLASS, len(cands_sorted))
        idx = design_rng.choice(len(cands_sorted), size=n, replace=False)
        picked[cls] = sorted(int(cands_sorted[i]) for i in idx)
    return picked


def run_state(mf, rule, state, state_idx):
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(state["interior0"]); h_star = state["h_star"]
    z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]
    pool20 = state["pool20"]

    classes = LE.assign_classes(mf, r0, z0, seed_members, pool20)
    design_rng = np.random.default_rng(DESIGN_SEED_BASE + state_idx)
    picked = sample_actuators(classes, design_rng)

    # distance diagnostics for class C vs D residual-mismatch visibility
    dist_by_class = {}
    for cls in ("live_exterior_parent", "near_exterior_non_parent"):
        dist_by_class[cls] = {int(a): LE.geometric_distance(mf, r0, a, seed_members, C.L_BOX) for a in picked[cls]}

    # per-stream no-control baseline (shared across all actuators for this state)
    nc_by_stream = {}
    for r in range(N_STREAMS):
        seed = PHYSICS_SEED_BASE + state_idx * 1000 + r
        nc_by_stream[r] = RC.run_no_control_closure(mf, r0, z0, z_context, seed_members, rule, h_star, seed, D_PRIMARY)

    rollout_rows = []
    actuator_summary_rows = []
    for cls in CLASSES:
        for act in picked[cls]:
            deltas_c, deltas_a, deltas_c_mj, deltas_a_mj = [], [], [], []
            for r in range(N_STREAMS):
                seed = PHYSICS_SEED_BASE + state_idx * 1000 + r
                out = RC.run_one_closure(mf, r0, z0, z_context, seed_members, rule, h_star, act, D_PRIMARY, seed,
                                          target_set_t0=seed_members, onset_offset=0)
                nc = nc_by_stream[r]
                dj_c = out["J_conservative"] - nc["J_conservative"]
                dj_a = out["J_assoc"] - nc["J_assoc"]
                dj_c_mj = out["J_conservative_minus_j"] - nc["J_conservative_minus_j"]
                dj_a_mj = out["J_assoc_minus_j"] - nc["J_assoc_minus_j"]
                deltas_c.append(dj_c); deltas_a.append(dj_a)
                deltas_c_mj.append(dj_c_mj); deltas_a_mj.append(dj_a_mj)
                row = dict(state_id=state["state_id"], state_idx=state_idx, actuator_class=cls,
                           actuator=act, stream_idx=r, physics_seed=seed, d=D_PRIMARY,
                           delta_J_conservative=dj_c, delta_J_assoc=dj_a,
                           delta_J_conservative_minus_j=dj_c_mj, delta_J_assoc_minus_j=dj_a_mj,
                           is_interior_actuator=out["is_interior_actuator"],
                           V=out["V"], V_conservative=out["V_conservative"], event=out["event_corrected"],
                           target_size_end=out["target_size_end"],
                           mech_cumulative_contact_edges=out["mech_cumulative_contact_edges"],
                           mech_direct_contacts_t0=out["mech_direct_contacts_t0"],
                           live_cumulative_actuator_to_target_edges=out["live_cumulative_actuator_to_target_edges"],
                           live_cumulative_target_to_actuator_edges=out["live_cumulative_target_to_actuator_edges"],
                           live_n_unique_target_members_directly_influenced=out["live_n_unique_target_members_directly_influenced"],
                           live_duration_with_live_access=out["live_duration_with_live_access"],
                           live_fraction_forcing_steps_with_live_access=out["live_fraction_forcing_steps_with_live_access"],
                           reach_n_reached_le1=out["reach_n_reached_le1"], reach_n_reached_le2=out["reach_n_reached_le2"],
                           reach_n_reached_le3=out["reach_n_reached_le3"],
                           reach_frac_reached_le1=out["reach_frac_reached_le1"],
                           reach_frac_reached_le2=out["reach_frac_reached_le2"],
                           reach_frac_reached_le3=out["reach_frac_reached_le3"],
                           static_min_distance=dist_by_class.get(cls, {}).get(act))
                rollout_rows.append(row)
            actuator_summary_rows.append(dict(
                state_id=state["state_id"], state_idx=state_idx, actuator_class=cls, actuator=act,
                is_interior_actuator=picked_is_interior(act, seed_members),
                mean_delta_J_conservative=float(np.mean(deltas_c)), mean_delta_J_assoc=float(np.mean(deltas_a)),
                mean_delta_J_conservative_minus_j=float(np.mean(deltas_c_mj)),
                mean_delta_J_assoc_minus_j=float(np.mean(deltas_a_mj)),
                n_streams=N_STREAMS, static_min_distance=dist_by_class.get(cls, {}).get(act),
            ))

    class_availability = {cls: len(classes[cls]) for cls in CLASSES}
    class_sampled = {cls: picked[cls] for cls in CLASSES}
    return rollout_rows, actuator_summary_rows, class_availability, class_sampled, classes["diagnostics"]


def picked_is_interior(act, seed_members):
    return int(act) in seed_members


def main():
    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    C.LOG_DIR.mkdir(parents=True, exist_ok=True)

    manifest = json.load(open(C.DATA_DIR / "state_manifest_closure.json"))
    states = manifest["states"]
    rule, _ = C.load_frozen_rule()
    mf = C.make_flock()

    all_rollout_rows, all_actuator_rows = [], []
    class_availability_by_state = {}
    class_sampled_by_state = {}
    t_all = time.time()
    for state_idx, state in enumerate(states):
        t0 = time.time()
        rollout_rows, actuator_rows, avail, sampled, diag = run_state(mf, rule, state, state_idx)
        dt = time.time() - t0
        all_rollout_rows.extend(rollout_rows)
        all_actuator_rows.extend(actuator_rows)
        class_availability_by_state[state["state_id"]] = avail
        class_sampled_by_state[state["state_id"]] = sampled
        print(f"[{state['state_id']}] n_rollouts={len(rollout_rows)} avail={avail} dt={dt:.0f}s "
              f"(elapsed {time.time()-t_all:.0f}s)", flush=True)
        json.dump(all_rollout_rows, open(C.DATA_DIR / "closureAB_rollouts.json", "w"))
        json.dump(all_actuator_rows, open(C.DATA_DIR / "closureAB_actuator_summary.json", "w"), indent=1)
        json.dump(class_availability_by_state, open(C.DATA_DIR / "closureAB_class_availability.json", "w"), indent=1)
        json.dump(class_sampled_by_state, open(C.DATA_DIR / "closureAB_class_sampled.json", "w"), indent=1)

    total_dt = time.time() - t_all
    print(f"TOTAL wall time: {total_dt:.1f}s ({total_dt/60:.1f}min), n_rollouts={len(all_rollout_rows)}")
    with open(C.LOG_DIR / "run_closureAB_timing.txt", "a") as f:
        f.write(f"total_wall_time_s={total_dt:.1f} n_rollouts={len(all_rollout_rows)} n_states={len(states)}\n")


if __name__ == "__main__":
    main()
