"""Audit-only instrumented replay of seed 500's first real online control
step (t=61, the exact step already reported in
`data/online_control_611__seed500.json`'s first `control_step` log entry).

Not a new experiment: reproduces `run_online_control_611.run_episode`'s loop
BIT-FOR-BIT (same RNG draw order, same functions, same constants, imported
not re-implemented) up to and including the decision made at t=61, but
records every intermediate quantity the production loop computes and then
discards, for METHODS_AUDIT_6_11.md's worked numerical example. Read-only:
never fed back into any run_online_control_611 output or RESULTS_6_11.md
number.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AUDIT_DIR.parent / "code"))

from common_611 import DATA_DIR, dump_json, L_BOX  # noqa: E402
from moving_flock_611 import MovingFlock611  # noqa: E402
from flock_sim.model import UV4, ROT_CW, ROT_CCW  # noqa: E402
from detect_69 import propose  # noqa: E402
from lineage_611 import LineageTracker611  # noqa: E402
from geometry_611 import local_scale  # noqa: E402
import predictive_boundary_611 as PB  # noqa: E402
import probing_611 as PR  # noqa: E402
from intervention_api_611 import FiniteProbeMoving611, MultiStepAuthorityProbe, near_exterior  # noqa: E402
import control_authority_611 as CA  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

SEED = 500
STOP_AT_T = 61   # the control_step=1 event's t, from the seed-500 log


def main():
    model, base_rows, dist_cuts = ROC.load_pretrained_model(M_obs=12)
    mf = ROC.make_flock()
    rng = np.random.default_rng(SEED)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)

    tracker = None
    z_window = []
    online_buffer = []
    ONLINE_BUFFER_CAP = 3000
    r_snap_window, z_snap_window = [], []
    SNAP_WINDOW = 20
    M_obs = 12

    def step_world():
        nonlocal r, z
        r_prev, z_prev = r.copy(), z.copy()
        r, z, _ = mf.step(r, z, rng, forced_actions=None)
        idx = rng.choice(mf.N, size=min(20, mf.N), replace=False)
        for i in idx:
            hist, pool_idx, cats = PB.pool_and_histogram(r_prev, z_prev, int(i), L_BOX, dist_cuts, M_obs)
            online_buffer.append(PB.Row(t=-1, i=int(i), z_i=int(z_prev[i]), hist=hist,
                                          label=int(z[i]), pool_idx=pool_idx, pool_cat=cats))
        if len(online_buffer) > ONLINE_BUFFER_CAP:
            del online_buffer[: len(online_buffer) - ONLINE_BUFFER_CAP]
        r_snap_window.append(r_prev)
        z_snap_window.append(z_prev)
        if len(r_snap_window) > SNAP_WINDOW + 1:
            r_snap_window.pop(0)
            z_snap_window.pop(0)

    t = 0
    record = None
    while t <= STOP_AT_T:
        z_window.append(z.copy())
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r, z_window, L_BOX) if len(z_window) >= 2 else []

        if tracker is None and cands:
            tracker = LineageTracker611(L=L_BOX, uv4=UV4)
            tracker.start(cands[0], r, z, t)
        elif tracker is not None:
            tracker.update(cands, r, z, t)
            if not tracker.hypotheses and cands:
                tracker = LineageTracker611(L=L_BOX, uv4=UV4)
                tracker.start(cands[0], r, z, t)

        interior = ROC.dominant_interior(tracker) if tracker is not None else None

        if t == STOP_AT_T:
            # ---- full instrumentation of the decision made at this step ----
            assert interior is not None
            top_h = max(tracker.hypotheses, key=lambda h: h.prob)
            hyp_detail = [dict(hid=h.hid, prob=h.prob, size=len(h.members), age=h.age,
                                status=h.status, last_record=h.records[-1] if h.records else None)
                          for h in sorted(tracker.hypotheses, key=lambda h: -h.prob)]

            periphery_radius = local_scale(r, L_BOX)
            ep_recent = dict(r_hist=np.stack(r_snap_window + [r]), z_hist=np.stack(z_snap_window + [z]))
            construct_rows = PB.rows_for_targets([ep_recent], interior, L_BOX, M_obs, dist_cuts,
                                                   periphery_radius, rng, max_rows_total=600)
            B_pred = PB.construct_boundary(model, interior, construct_rows) if construct_rows else None

            exterior_pool = near_exterior(mf, r, interior, radius_factor=3.0)
            # reference-only: true live-neighbour boundary, for the audit ONLY
            # (never consumed by any inference-side decision in this script)
            B_D_true = mf.oracle_B_D(r, z, interior).tolist()

            probes = [FiniteProbeMoving611(mf, r, n_rollouts=ROC.PROBE_ROLLOUTS_ONLINE, seed=1000 + t + rep)
                      for rep in range(ROC.PROBE_REPEATS_ONLINE)]
            B_causal = PR.probe_sources(probes, interior, exterior_pool, z, rng, n_boot=100)

            auth_probe = MultiStepAuthorityProbe(mf, r, z, tau=ROC.TAU_CONTROL,
                                                   n_rollouts=ROC.AUTHORITY_ROLLOUTS_ONLINE, seed=2000 + t)
            target_heading = 1  # from the seed-500 log's qualified_and_target_set event at this same t
            B_C = CA.select_actuators(auth_probe, interior, exterior_pool, target_heading, k_act=ROC.K_ACT)

            forced = {j: target_heading for j in B_C["B_C"]}
            r_next, z_next, _ = mf.step(r.copy(), z.copy(),
                                          np.random.default_rng(999_000 + t),
                                          forced_actions=forced)

            record = dict(
                t=t, seed=SEED,
                n_candidates_raw=len(cands), candidate_sizes=[len(c) for c in cands],
                interior_size=len(interior), interior_ids_first10=sorted(int(x) for x in interior)[:10],
                lineage_n_hypotheses=len(tracker.hypotheses),
                lineage_top_hypothesis=dict(hid=top_h.hid, prob=top_h.prob, size=len(top_h.members),
                                             age=top_h.age, status=top_h.status),
                lineage_all_hypotheses=hyp_detail,
                B_pred=dict(B=B_pred["B"], full_pool_loss=B_pred["full_pool_loss"],
                             interior_only_loss=B_pred["interior_only_loss"],
                             final_loss=B_pred["final_loss"]) if B_pred else None,
                exterior_pool_size=len(exterior_pool),
                exterior_pool_first10=exterior_pool[:10],
                n_true_causal_parents_in_pool=len(set(exterior_pool) & set(B_D_true)),
                n_true_causal_parents_total=len(B_D_true),
                B_causal_selected=B_causal["B_causal"],
                B_causal_per_source_ci={str(j): dict(C_do_joint=res["C_do_joint"], ci_lo=res["ci_lo"],
                                                       ci_hi=res["ci_hi"])
                                          for j, res in list(B_causal["C"].items())[:10]},
                target_heading=target_heading,
                B_C_selected=B_C["B_C"],
                B_C_top_scores=[dict(j=s["j"], A=s["A"], H_do_mean=s["H_do_mean"], H_base_mean=s["H_base_mean"])
                                 for s in B_C["scores"][:10]],
                frac_interior_at_target_before=float((z[interior] == target_heading).mean()),
                frac_interior_at_target_after_this_step=float((z_next[interior] == target_heading).mean()),
                B_D_true_reference_only=B_D_true,
            )
            break

        step_world()
        t += 1

    out_path = AUDIT_DIR / "worked_example_seed500_t61.json"
    dump_json(record, out_path)
    print(f"wrote {out_path}")
    print(json.dumps({k: v for k, v in record.items() if k not in
                       ("lineage_all_hypotheses", "B_D_true_reference_only")}, indent=1, default=str))


if __name__ == "__main__":
    main()
