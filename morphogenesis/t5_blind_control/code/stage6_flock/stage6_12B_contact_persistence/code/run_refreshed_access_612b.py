"""Stage 6.12B-B runner: fixed vs. refreshed actuator-set strategies at
matched total effort (K birds forced every one of T_control=24 steps),
across refresh cadence q in {24,8,4,2,1} and K in {2,4}.

Strategies: random (refreshed-random access maintenance only), nearest
(observation-based, non-learned), kinematic (deployable, physics-assisted
true-R predicted contact), kinematic_radius_free (deployable, no R),
oracle (AUDIT/UPPER-BOUND ONLY -- uses the paired no-control future
trajectory, never presented as deployable), fixed_reference (K=2 only,
static reference = Stage 6.12B-A's own held-out-confirmed S_star at
K=2,d=8, held for the WHOLE 24-step control period regardless of q --
included only for states covered by the exhaustive search).

DISCLOSED REDUCTION: N_STREAMS_B=3 CRN-paired physics streams per
(state,K,q,strategy) cell (measured cost ~6.72s/rollout, constant across
q since total simulated length is fixed at T_control+R_RELEASE=48 steps
regardless of cadence).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612b as C     # noqa: E402
import refresh_612b as RB   # noqa: E402

N_STREAMS_B = 3
PHYSICS_SEED_BASE = 20_000_000
DESIGN_SEED_BASE = 21_000_000

EXHAUSTIVE_DATA_PATH = C.DATA_DIR / "fixed_set_exhaustive_612b.json"


def load_fixed_reference(state_id):
    if not EXHAUSTIVE_DATA_PATH.exists():
        return None
    data = json.load(open(EXHAUSTIVE_DATA_PATH))
    for st in data:
        if st["state_id"] == state_id:
            cell = st["cells"].get("K2_d8")
            if cell:
                s_star_holdout = next((h for h in cell["holdout_evals"] if h["role"] == "S_star"), None)
                if s_star_holdout:
                    return s_star_holdout["S"]
    return None


def run_state(state, state_idx):
    rule, _ = C.load_frozen_rule()
    mf = C.make_flock()
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(state["interior0"]); h_star = state["h_star"]
    z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]
    fixed_ref_S = load_fixed_reference(state["state_id"])

    nc_by_stream = {}
    for r in range(N_STREAMS_B):
        physics_seed = PHYSICS_SEED_BASE + state_idx * 1000 + r
        out, nc_r_hist, nc_z_hist, nc_tr = RB.run_no_control_full(mf, r0, z0, z_context, seed_members, rule, h_star, physics_seed)
        nc_by_stream[r] = dict(out=out, r_hist=nc_r_hist, z_hist=nc_z_hist, tr=nc_tr)

    cells = {}
    for K in RB.K_GRID:
        for q in RB.Q_GRID:
            strategies = list(RB.STRATEGIES)
            if K != 2 or fixed_ref_S is None:
                strategies = [s for s in strategies if s != "fixed_reference"]
            for strat in strategies:
                t0 = time.time()
                rows = []
                for r in range(N_STREAMS_B):
                    physics_seed = PHYSICS_SEED_BASE + state_idx * 1000 + r
                    design_rng = np.random.default_rng(DESIGN_SEED_BASE + state_idx * 100000 + K * 1000 + q * 10 + r) \
                        if strat == "random" else None
                    nc_data = (nc_by_stream[r]["r_hist"], nc_by_stream[r]["z_hist"], nc_by_stream[r]["tr"]) \
                        if strat == "oracle" else None
                    out = RB.run_refresh_rollout(mf, r0, z0, z_context, seed_members, rule, h_star, K, q, strat,
                                                  physics_seed, design_rng=design_rng, nc_data=nc_data,
                                                  fixed_reference_S=fixed_ref_S if strat == "fixed_reference" else None)
                    j0 = nc_by_stream[r]["out"]
                    out["J0_assoc"] = j0["J_assoc"]; out["J0_conservative"] = j0["J_conservative"]
                    out["delta_assoc"] = out["J_assoc"] - j0["J_assoc"]
                    out["delta_conservative"] = out["J_conservative"] - j0["J_conservative"]
                    out["stream"] = r
                    rows.append(out)
                dt = time.time() - t0
                cell_key = f"K{K}_q{q}_{strat}"
                cells[cell_key] = dict(
                    K=K, q=q, strategy=strat, n_streams=N_STREAMS_B, rows=rows,
                    mean_delta_assoc=float(np.mean([r["delta_assoc"] for r in rows])),
                    mean_delta_conservative=float(np.mean([r["delta_conservative"] for r in rows])),
                    mean_J_assoc=float(np.mean([r["J_assoc"] for r in rows])),
                    identity_valid_fraction=float(np.mean([r["V"] for r in rows])),
                    mean_cumulative_contact_edges=float(np.mean([r["cumulative_contact_edges"] for r in rows])),
                    mean_fraction_actuator_steps_in_contact=float(np.mean(
                        [r["fraction_actuator_steps_in_contact"] for r in rows if r["fraction_actuator_steps_in_contact"] is not None]))
                    if any(r["fraction_actuator_steps_in_contact"] is not None for r in rows) else None,
                    mean_turnovers=float(np.mean([r["n_turnovers"] for r in rows])),
                    time_s=dt,
                )
                print(f"  {state['state_id']} {cell_key}: delta_assoc={cells[cell_key]['mean_delta_assoc']:.4f} "
                      f"({dt:.0f}s)", flush=True)

    no_control_summary = dict(
        mean_J_assoc=float(np.mean([nc_by_stream[r]["out"]["J_assoc"] for r in range(N_STREAMS_B)])),
        mean_J_conservative=float(np.mean([nc_by_stream[r]["out"]["J_conservative"] for r in range(N_STREAMS_B)])),
    )
    return dict(state_id=state["state_id"], role=state["role"], fixed_reference_S=fixed_ref_S,
                no_control=no_control_summary, cells=cells)


def main():
    manifest = json.load(open(C.DATA_DIR / "state_manifest_612b.json"))
    states = manifest["states"]
    out = []
    t_all = time.time()
    for i, s in enumerate(states):
        t0 = time.time()
        res = run_state(s, i)
        dt = time.time() - t0
        print(f"[{s['state_id']} / {s['role']}] done in {dt:.1f}s", flush=True)
        out.append(res)
        json.dump(out, open(C.DATA_DIR / "refreshed_access_612b.json", "w"), indent=1, default=str)
    print(f"Stage 6.12B-B total wall time: {time.time()-t_all:.1f}s")


if __name__ == "__main__":
    main()
