"""Stage 6.12B S18/S19: validate PRE-INTERVENTION contact-persistence
predictors against the exhaustive K=1/K=2 search's realized paired effect.

Three predictor levels, all computed BEFORE any forced rollout (per-
candidate scores at t0, then aggregated over a set S by summation --
`C_hat_S(d) = sum_{j in S} C_hat_j(d)`, exactly the task brief's
definition):

  18.1 static distance    : -min distance from candidate to any t0 target
                             member (higher = closer = better).
  18.2 kinematic           : `intervention_612b.kinematic_contact_scores`,
                             physics-assisted (true R) and radius-free
                             variants -- deployable, current
                             positions/headings/known v only.
  18.3 oracle (audit-only) : `intervention_612b.oracle_future_contact_scores`,
                             computed from the SAME dev-stream no-control
                             trajectory that the exhaustive search's own
                             `delta_assoc`/`delta_conservative` were paired
                             against (physics_seed = DEV_PHYSICS_SEED_BASE +
                             state_idx*1000 + 0) -- a legitimate CRN pairing,
                             not leakage from the forced trajectory itself.

Validated with Spearman rank correlation only (no learned model, per S19/S31).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612b as C            # noqa: E402
import intervention_612 as I611    # noqa: E402
import intervention_612b as IB     # noqa: E402
from run_fixed_set_exhaustive_612b import DEV_PHYSICS_SEED_BASE  # noqa: E402

D_GRID = (4, 8)


def spearman(x, y):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def per_state_predictors(state, state_idx, rule):
    mf = C.make_flock()
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(state["interior0"]); pool = state["pool20"]
    z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]

    # static distance (pure t0 geometry, no window dependence)
    pool_arr = np.array(sorted(int(p) for p in pool))
    tgt_arr = np.array(sorted(int(m) for m in seed_members))
    delta0 = C.torus_delta(r0[pool_arr][:, None, :], r0[tgt_arr][None, :, :], C.L_BOX)
    dist0 = np.sqrt((delta0 ** 2).sum(-1)).min(axis=1)
    static_score = {int(pool_arr[i]): -float(dist0[i]) for i in range(len(pool_arr))}

    # dev-stream no-control trajectory (stream 0) -- needed for the oracle predictor
    physics_seed = DEV_PHYSICS_SEED_BASE + state_idx * 1000 + 0
    n_steps = max(D_GRID) + I611.R_RELEASE
    nc_r_hist, nc_z_hist = I611.simulate_branch(mf, r0, z0, physics_seed, None, 0, 0, n_steps)
    nc_tr = I611.trace_target(nc_r_hist, nc_z_hist, z_context, seed_members, rule)

    kinematic_by_d, oracle_by_d, kinematic_free_by_d = {}, {}, {}
    for d in D_GRID:
        kinematic_by_d[d] = IB.kinematic_contact_scores(r0, z0, pool, seed_members, C.L_BOX, mf.v, d, R=mf.R)
        kinematic_free_by_d[d] = IB.kinematic_contact_scores(r0, z0, pool, seed_members, C.L_BOX, mf.v, d, R=None)
        oracle_by_d[d] = IB.oracle_future_contact_scores(nc_r_hist, nc_z_hist, nc_tr, 0, d, pool, C.L_BOX, mf.R,
                                                          fallback_members=seed_members)
    return dict(static=static_score, kinematic=kinematic_by_d, kinematic_radius_free=kinematic_free_by_d,
                oracle=oracle_by_d)


def main():
    rule, _ = C.load_frozen_rule()
    manifest = json.load(open(C.DATA_DIR / "state_manifest_612b.json"))
    states = {s["state_id"]: (i, s) for i, s in enumerate(manifest["states"])}
    exhaustive = json.load(open(C.DATA_DIR / "fixed_set_exhaustive_612b.json"))

    rows = []
    for st in exhaustive:
        sid = st["state_id"]
        state_idx, state = states[sid]
        preds = per_state_predictors(state, state_idx, rule)
        for cell_key, cell in st["cells"].items():
            d = cell["d"]
            for r in cell["search_rows"]:
                S = r["S"]
                static_s = sum(preds["static"][j] for j in S)
                kin_s = sum(preds["kinematic"][d][j] for j in S)
                kin_free_s = sum(preds["kinematic_radius_free"][d][j] for j in S)
                orac_s = sum(preds["oracle"][d][j] for j in S)
                rows.append(dict(state_id=sid, cell=cell_key, K=cell["K"], d=d, S=S,
                                  static_score=static_s, kinematic_score=kin_s,
                                  kinematic_radius_free_score=kin_free_s, oracle_score=orac_s,
                                  delta_assoc=r["mean_delta_assoc"], delta_conservative=r["mean_delta_conservative"]))

    predictor_keys = ["static_score", "kinematic_score", "kinematic_radius_free_score", "oracle_score"]
    overall = {}
    for pk in predictor_keys:
        vals = [r[pk] for r in rows]
        da = [r["delta_assoc"] for r in rows]
        dc = [r["delta_conservative"] for r in rows]
        overall[pk] = dict(n=len(rows), spearman_vs_delta_assoc=spearman(vals, da),
                            spearman_vs_delta_conservative=spearman(vals, dc))

    by_state = {}
    for sid in states:
        srows = [r for r in rows if r["state_id"] == sid]
        if not srows:
            continue
        by_state[sid] = {pk: spearman([r[pk] for r in srows], [r["delta_assoc"] for r in srows]) for pk in predictor_keys}

    by_cell = {}
    for cell_key in sorted(set(r["cell"] for r in rows)):
        crows = [r for r in rows if r["cell"] == cell_key]
        by_cell[cell_key] = {pk: spearman([r[pk] for r in crows], [r["delta_assoc"] for r in crows]) for pk in predictor_keys}

    out = dict(n_rows=len(rows), overall=overall, by_state=by_state, by_cell=by_cell, rows=rows)
    json.dump(out, open(C.DATA_DIR / "contact_predictor_analysis_612b.json", "w"), indent=1, default=str)
    print(json.dumps(dict(overall=overall, by_state=by_state, by_cell=by_cell), indent=1))
    print("wrote", C.DATA_DIR / "contact_predictor_analysis_612b.json")


if __name__ == "__main__":
    main()
