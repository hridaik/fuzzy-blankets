"""Closure C: minimal timing-susceptibility check. Deliberately small.

Uses the FIRST 4 states of the predeclared 8-state manifest (not chosen from
Closure-A results). At onset offsets {0,4,8,12} real steps along the
UNFORCED trajectory: recompute material target, live edges, and actuator
classes at that new onset. Two class policies: live_exterior_parent and
boundary_member (uniformly sampled, up to 2 actuators each), K=1, d=8,
release=24, 3 physics streams per actuator.

RNG (disjoint from Closure A/B and all prior stages):
  physics_seed = PHYSICS_SEED_BASE(42_000_000) + state_idx*10000 + onset*100 + r
  design_seed  = DESIGN_SEED_BASE(43_000_000) + state_idx*10 + onset_idx
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
import intervention_612 as I611  # noqa: E402

D_PRIMARY = 8
N_STREAMS = 3
MAX_PER_CLASS = 2
ONSET_OFFSETS = (0, 4, 8, 12)
N_TIMING_STATES = 4
PHYSICS_SEED_BASE = 42_000_000
DESIGN_SEED_BASE = 43_000_000
TIMING_CLASSES = ["live_exterior_parent", "boundary_member"]


def advance_unforced(mf, r0, z0, z_context, seed_members, rule, h_star, offset, physics_seed):
    """Advance `offset` real steps with NO forcing (uses a dedicated physics
    stream, distinct from the evaluation streams below, purely to produce the
    onset-offset state -- deterministic given physics_seed)."""
    if offset == 0:
        tr0 = I611.trace_target(np.array(r0)[None], np.array(z0, dtype=int)[None], z_context, seed_members, rule)
        return r0.copy(), z0.copy(), z_context, tr0.accepted, tr0.history[-1].status == "continuing"
    r_hist, z_hist = I611.simulate_branch(mf, r0, z0, physics_seed, None, h_star, 0, offset)
    tr = I611.trace_target(r_hist, z_hist, z_context, seed_members, rule)
    ok = all(h.status == "continuing" and not h.split_flag and not h.merge_flag for h in tr.history)
    new_target = tr.accepted
    z_window = list(z_context)
    for zt in z_hist:
        z_window.append(zt)
    z_window = z_window[-C.AFFINITY_WINDOW:]
    new_context = z_window[:-1] if len(z_window) > 1 else []
    return r_hist[-1], z_hist[-1], new_context, new_target, ok


def run_state_timing(mf, rule, state, state_idx):
    r0_0 = np.array(state["r0"]); z0_0 = np.array(state["z0"], dtype=int)
    seed_members_0 = frozenset(state["interior0"]); h_star = state["h_star"]
    z_context_0 = [np.array(zc, dtype=int) for zc in state["z_context"]]

    rows = []
    onset_summary = []
    for onset_idx, offset in enumerate(ONSET_OFFSETS):
        adv_seed = PHYSICS_SEED_BASE + state_idx * 10000 + offset * 100 + 999  # dedicated advance stream
        r_off, z_off, z_ctx_off, target_off, ok = advance_unforced(
            mf, r0_0, z0_0, z_context_0, seed_members_0, rule, h_star, offset, adv_seed)
        if not ok or not target_off or len(target_off) < 5:
            onset_summary.append(dict(state_id=state["state_id"], onset_offset=offset,
                                       status="target_unavailable", n_target=len(target_off) if target_off else 0))
            continue
        pool_off = C.nearest_M_pool(np.array(sorted(int(m) for m in target_off)), r_off, C.L_BOX, 20)
        classes = LE.assign_classes(mf, r_off, z_off, target_off, pool_off)

        design_rng = np.random.default_rng(DESIGN_SEED_BASE + state_idx * 10 + onset_idx)
        picked = {}
        for cls in TIMING_CLASSES:
            cands = sorted(int(c) for c in classes[cls])
            n = min(MAX_PER_CLASS, len(cands))
            if n == 0:
                picked[cls] = []
                continue
            idx = design_rng.choice(len(cands), size=n, replace=False)
            picked[cls] = sorted(int(cands[i]) for i in idx)

        nc_by_stream = {}
        for r in range(N_STREAMS):
            seed = PHYSICS_SEED_BASE + state_idx * 10000 + offset * 100 + r
            nc_by_stream[r] = RC.run_no_control_closure(mf, r_off, z_off, z_ctx_off, target_off, rule, h_star, seed, D_PRIMARY)

        onset_summary.append(dict(state_id=state["state_id"], onset_offset=offset,
                                   status="ok", n_target=len(target_off),
                                   class_availability={cls: len(classes[cls]) for cls in TIMING_CLASSES},
                                   class_sampled=picked))

        for cls in TIMING_CLASSES:
            for act in picked[cls]:
                for r in range(N_STREAMS):
                    seed = PHYSICS_SEED_BASE + state_idx * 10000 + offset * 100 + r
                    out = RC.run_one_closure(mf, r_off, z_off, z_ctx_off, target_off, rule, h_star, act, D_PRIMARY,
                                              seed, target_set_t0=target_off, onset_offset=offset)
                    nc = nc_by_stream[r]
                    dj_c = out["J_conservative"] - nc["J_conservative"]
                    dj_a = out["J_assoc"] - nc["J_assoc"]
                    rows.append(dict(state_id=state["state_id"], state_idx=state_idx, onset_offset=offset,
                                      actuator_class=cls, actuator=act, stream_idx=r, physics_seed=seed,
                                      delta_J_conservative=dj_c, delta_J_assoc=dj_a,
                                      V=out["V"], V_conservative=out["V_conservative"],
                                      event=out["event_corrected"], n_target_at_onset=len(target_off)))
    return rows, onset_summary


def main():
    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    C.LOG_DIR.mkdir(parents=True, exist_ok=True)

    manifest = json.load(open(C.DATA_DIR / "state_manifest_closure.json"))
    states = manifest["states"][:N_TIMING_STATES]
    rule, _ = C.load_frozen_rule()
    mf = C.make_flock()

    all_rows, all_summary = [], []
    t_all = time.time()
    for state_idx, state in enumerate(states):
        t0 = time.time()
        rows, summary = run_state_timing(mf, rule, state, state_idx)
        dt = time.time() - t0
        all_rows.extend(rows)
        all_summary.extend(summary)
        print(f"[{state['state_id']}] n_rollouts={len(rows)} dt={dt:.0f}s (elapsed {time.time()-t_all:.0f}s)", flush=True)
        json.dump(all_rows, open(C.DATA_DIR / "closureC_timing_rollouts.json", "w"))
        json.dump(all_summary, open(C.DATA_DIR / "closureC_timing_onset_summary.json", "w"), indent=1)

    total_dt = time.time() - t_all
    print(f"TOTAL wall time: {total_dt:.1f}s ({total_dt/60:.1f}min), n_rollouts={len(all_rows)}")
    with open(C.LOG_DIR / "run_closureC_timing.txt", "a") as f:
        f.write(f"total_wall_time_s={total_dt:.1f} n_rollouts={len(all_rows)} n_states={len(states)}\n")


if __name__ == "__main__":
    main()
