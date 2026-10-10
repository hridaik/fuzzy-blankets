"""Stage 6.12C confirmatory experiment: K=1 exhaustive primary, K=2
secondary, duration-safety sub-study. Single integrated script so that
no-control baselines (the dominant reusable cost) are computed once per
(state, physics stream) and shared across the K=1, K=2, and d=24 arms
that share the same physics seed.

Seed bases (all disjoint from Stage 6.12/6.12B/prior audits):
  SEARCH_PHYSICS_SEED_BASE      = 13_000_000  (4 SEARCH streams/state)
  CONFIRM_PHYSICS_SEED_BASE     = 14_000_000  (8 CONFIRMATORY streams/state,
                                                K=1 uses all 8, K=2 secondary
                                                uses the first 6, duration
                                                d=24 arm uses the first 6)
  K2_PAIR_DESIGN_SEED_BASE      = 16_000_000  (random-pair sampling only,
                                                never a physics stream)

Frozen predictor: intervention_612b.kinematic_contact_scores(R=mf.R) --
see PREDICTOR_FREEZE.md. NOT modified here. window=d=8 for the K=1
primary scores (matches the primary d=8 horizon).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612c as C  # noqa: E402

D_PRIMARY = 8
D_LONG = 24
R_RELEASE = 24
N_SEARCH_STREAMS = 4
N_CONFIRM_STREAMS = 8
N_K2_CONFIRM_STREAMS = 6
N_K2_RANDOM_PAIRS = 24

SEARCH_PHYSICS_SEED_BASE = 13_000_000
CONFIRM_PHYSICS_SEED_BASE = 14_000_000
K2_PAIR_DESIGN_SEED_BASE = 16_000_000

DURATION_SUBSTUDY_N_STATES = 5   # first N states by seed order


def torus_min_dist_to_target(r0, pool_arr, tgt_arr, L):
    delta = C.torus_delta(r0[pool_arr][:, None, :], r0[tgt_arr][None, :, :], L)
    return np.sqrt((delta ** 2).sum(-1)).min(axis=1)


def candidate_metadata(r0, z0, pool_arr, tgt_arr, h_star, L):
    """Relative bearing, candidate heading, target heading, predicted
    relative motion (dot of candidate unit-heading with direction-to-target
    bearing), pool rank by static distance."""
    uv = C.UV4
    dist0 = torus_min_dist_to_target(r0, pool_arr, tgt_arr, L)
    order = np.argsort(dist0)
    rank = {int(pool_arr[i]): int(np.where(order == i)[0][0]) for i in range(len(pool_arr))}
    tgt_centroid = C.bulk_centroid(r0, set(int(x) for x in tgt_arr), L)
    meta = {}
    for i, j in enumerate(pool_arr):
        cand_heading = int(z0[j])
        bearing_vec = C.torus_delta(tgt_centroid[None, :], r0[j][None, :], L)[0]
        bearing_norm = bearing_vec / (np.linalg.norm(bearing_vec) + 1e-12)
        cand_dir = uv[cand_heading]
        predicted_relative_motion = float(cand_dir @ bearing_norm)
        rel_bearing_cardinal = C.bearing_to_cardinal(bearing_vec)
        meta[int(j)] = dict(
            candidate_heading=cand_heading, target_heading=int(h_star),
            relative_bearing_cardinal=int(rel_bearing_cardinal),
            predicted_relative_motion=predicted_relative_motion,
            pool_rank_by_static_distance=rank[int(j)],
            static_t0_distance=float(dist0[i]),
        )
    return meta


def run_k1_for_state(mf, rule, state, state_idx, is_safety_state):
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(state["interior0"]); h_star = state["h_star"]
    pool = state["pool20"]
    z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]
    pool_arr = np.array(sorted(int(p) for p in pool))
    tgt_arr = np.array(sorted(int(m) for m in seed_members))

    # A. frozen kinematic score, window = D_PRIMARY, R = mf.R (physics-assisted)
    kin_scores = C.IB.kinematic_contact_scores(r0, z0, pool, seed_members, C.L_BOX, mf.v, D_PRIMARY, R=mf.R)
    # C/D. metadata (static distance, contact@t0, bearing/heading/rank)
    meta = candidate_metadata(r0, z0, pool_arr, tgt_arr, h_star, C.L_BOX)
    delta0 = C.torus_delta(r0[pool_arr][:, None, :], r0[tgt_arr][None, :, :], C.L_BOX)
    dist0_full = np.sqrt((delta0 ** 2).sum(-1))
    direct_contact_t0 = {int(pool_arr[i]): int((dist0_full[i] <= mf.R).any()) for i in range(len(pool_arr))}

    d_grid = (D_PRIMARY, D_LONG) if is_safety_state else (D_PRIMARY,)

    # no-control baselines, one per physics stream, shared across K1/K2/duration
    search_nc = {}
    for r in range(N_SEARCH_STREAMS):
        seed = SEARCH_PHYSICS_SEED_BASE + state_idx * 1000 + r
        nc, _, _, _ = C.IB.run_no_control_full_b(mf, r0, z0, z_context, seed_members, rule, h_star, seed, d_grid)
        search_nc[r] = nc
    confirm_nc = {}
    for r in range(N_CONFIRM_STREAMS):
        seed = CONFIRM_PHYSICS_SEED_BASE + state_idx * 1000 + r
        nc, _, _, _ = C.IB.run_no_control_full_b(mf, r0, z0, z_context, seed_members, rule, h_star, seed, d_grid)
        confirm_nc[r] = nc

    candidate_rows = []
    rollout_rows = []
    for j in pool_arr:
        j = int(j)
        row = dict(state_id=state["state_id"], candidate=j, kinematic_score=kin_scores[j],
                   direct_contact_t0=direct_contact_t0[j], **meta[j])
        search_da, search_dc, search_contact = [], [], []
        confirm_da, confirm_dc, confirm_contact = [], [], []
        for r in range(N_SEARCH_STREAMS):
            seed = SEARCH_PHYSICS_SEED_BASE + state_idx * 1000 + r
            out = C.IB.run_one_b(mf, r0, z0, z_context, seed_members, rule, h_star, [j], D_PRIMARY, seed)
            j0 = search_nc[r][D_PRIMARY]
            da = out["J_assoc"] - j0["J_assoc"]; dc = out["J_conservative"] - j0["J_conservative"]
            search_da.append(da); search_dc.append(dc)
            search_contact.append(out["mech_cumulative_contact_edges"])
            rollout_rows.append(dict(state_id=state["state_id"], candidate=j, K=1, d=D_PRIMARY,
                                      stream_role="search", stream_idx=r, physics_seed=seed,
                                      delta_assoc=da, delta_conservative=dc,
                                      J_assoc=out["J_assoc"], J_conservative=out["J_conservative"],
                                      A_release_late=out["A_release_late"], V=out["V"],
                                      V_conservative=out["V_conservative"], event=out["event"],
                                      event_corrected=out["event_corrected"],
                                      align_end_forcing=out["align_end_forcing"],
                                      end_of_release_alignment=out["end_of_release_alignment"],
                                      target_size_end=out["target_size_end"],
                                      mech_cumulative_contact_edges=out["mech_cumulative_contact_edges"],
                                      mech_direct_contacts_t0=out["mech_direct_contacts_t0"]))
        for r in range(N_CONFIRM_STREAMS):
            seed = CONFIRM_PHYSICS_SEED_BASE + state_idx * 1000 + r
            out = C.IB.run_one_b(mf, r0, z0, z_context, seed_members, rule, h_star, [j], D_PRIMARY, seed)
            j0 = confirm_nc[r][D_PRIMARY]
            da = out["J_assoc"] - j0["J_assoc"]; dc = out["J_conservative"] - j0["J_conservative"]
            confirm_da.append(da); confirm_dc.append(dc)
            confirm_contact.append(out["mech_cumulative_contact_edges"])
            rollout_rows.append(dict(state_id=state["state_id"], candidate=j, K=1, d=D_PRIMARY,
                                      stream_role="confirm", stream_idx=r, physics_seed=seed,
                                      delta_assoc=da, delta_conservative=dc,
                                      J_assoc=out["J_assoc"], J_conservative=out["J_conservative"],
                                      A_release_late=out["A_release_late"], V=out["V"],
                                      V_conservative=out["V_conservative"], event=out["event"],
                                      event_corrected=out["event_corrected"],
                                      align_end_forcing=out["align_end_forcing"],
                                      end_of_release_alignment=out["end_of_release_alignment"],
                                      target_size_end=out["target_size_end"],
                                      mech_cumulative_contact_edges=out["mech_cumulative_contact_edges"],
                                      mech_direct_contacts_t0=out["mech_direct_contacts_t0"]))
        row.update(
            mean_search_delta_assoc=float(np.mean(search_da)), mean_search_delta_conservative=float(np.mean(search_dc)),
            mean_confirm_delta_assoc=float(np.mean(confirm_da)), mean_confirm_delta_conservative=float(np.mean(confirm_dc)),
            mean_search_forced_contact=float(np.mean(search_contact)), mean_confirm_forced_contact=float(np.mean(confirm_contact)),
            search_delta_conservative_all=search_dc, confirm_delta_conservative_all=confirm_dc,
            search_delta_assoc_all=search_da, confirm_delta_assoc_all=confirm_da,
            confirm_forced_contact_all=confirm_contact,
        )
        candidate_rows.append(row)

    return candidate_rows, rollout_rows


def sample_k2_pairs(pool_arr, kin_scores, state_idx):
    pool = sorted(int(p) for p in pool_arr)
    top2 = [k for k, _ in sorted(kin_scores.items(), key=lambda kv: -kv[1])[:2]]
    bottom2 = [k for k, _ in sorted(kin_scores.items(), key=lambda kv: kv[1])[:2]]
    design_rng = np.random.default_rng(K2_PAIR_DESIGN_SEED_BASE + state_idx)
    all_pairs = [(a, b) for i, a in enumerate(pool) for b in pool[i + 1:]]
    exclude = {tuple(sorted(top2)), tuple(sorted(bottom2))}
    candidates = [p for p in all_pairs if p not in exclude]
    idx = design_rng.choice(len(candidates), size=min(N_K2_RANDOM_PAIRS, len(candidates)), replace=False)
    random_pairs = [candidates[i] for i in idx]
    return dict(top_predicted=sorted(top2), low_predicted=sorted(bottom2), random_pairs=[sorted(p) for p in random_pairs])


def run_k2_for_state(mf, rule, state, state_idx, kin_scores, pool_arr):
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(state["interior0"]); h_star = state["h_star"]
    z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]

    pairs_spec = sample_k2_pairs(pool_arr, kin_scores, state_idx)
    all_pairs = ([("top_predicted", pairs_spec["top_predicted"])] +
                 [("low_predicted", pairs_spec["low_predicted"])] +
                 [("random", p) for p in pairs_spec["random_pairs"]])

    confirm_nc = {}
    for r in range(N_K2_CONFIRM_STREAMS):
        seed = CONFIRM_PHYSICS_SEED_BASE + state_idx * 1000 + r
        nc, _, _, _ = C.IB.run_no_control_full_b(mf, r0, z0, z_context, seed_members, rule, h_star, seed, (D_PRIMARY,))
        confirm_nc[r] = nc

    pair_rows = []
    for role, S in all_pairs:
        da_list, dc_list = [], []
        for r in range(N_K2_CONFIRM_STREAMS):
            seed = CONFIRM_PHYSICS_SEED_BASE + state_idx * 1000 + r
            out = C.IB.run_one_b(mf, r0, z0, z_context, seed_members, rule, h_star, S, D_PRIMARY, seed)
            j0 = confirm_nc[r][D_PRIMARY]
            da_list.append(out["J_assoc"] - j0["J_assoc"]); dc_list.append(out["J_conservative"] - j0["J_conservative"])
        pair_rows.append(dict(state_id=state["state_id"], role=role, S=list(S),
                               pair_kin_score=float(kin_scores[S[0]] + kin_scores[S[1]]),
                               mean_delta_assoc=float(np.mean(da_list)), mean_delta_conservative=float(np.mean(dc_list)),
                               delta_conservative_all=dc_list, delta_assoc_all=da_list))
    return pair_rows


def run_duration_substudy_for_state(mf, rule, state, state_idx, k1_candidate_rows):
    """d=8 vs d=24, top-kinematic candidate and one matched random
    candidate, same 6 confirmatory streams (first 6 of the 8), reusing the
    already-computed d=8 K=1 primary results for those same streams."""
    r0 = np.array(state["r0"]); z0 = np.array(state["z0"], dtype=int)
    seed_members = frozenset(state["interior0"]); h_star = state["h_star"]
    z_context = [np.array(zc, dtype=int) for zc in state["z_context"]]

    top_row = max(k1_candidate_rows, key=lambda r: r["kinematic_score"])
    top_cand = top_row["candidate"]
    design_rng = np.random.default_rng(17_000_000 + state_idx)
    others = [r["candidate"] for r in k1_candidate_rows if r["candidate"] != top_cand]
    random_cand = int(design_rng.choice(others))

    confirm_nc = {}
    for r in range(N_K2_CONFIRM_STREAMS):
        seed = CONFIRM_PHYSICS_SEED_BASE + state_idx * 1000 + r
        nc, _, _, _ = C.IB.run_no_control_full_b(mf, r0, z0, z_context, seed_members, rule, h_star, seed, (D_PRIMARY, D_LONG))
        confirm_nc[r] = nc

    rows = []
    for label, cand in (("top_kinematic", top_cand), ("matched_random", random_cand)):
        d8_da = [k1_candidate_rows[[c["candidate"] for c in k1_candidate_rows].index(cand)]["confirm_delta_assoc_all"][r]
                 for r in range(N_K2_CONFIRM_STREAMS)]
        d8_dc = [k1_candidate_rows[[c["candidate"] for c in k1_candidate_rows].index(cand)]["confirm_delta_conservative_all"][r]
                 for r in range(N_K2_CONFIRM_STREAMS)]
        d8_lost = []
        d24_da, d24_dc, d24_lost, d24_vcons = [], [], [], []
        for r in range(N_K2_CONFIRM_STREAMS):
            seed = CONFIRM_PHYSICS_SEED_BASE + state_idx * 1000 + r
            out24 = C.IB.run_one_b(mf, r0, z0, z_context, seed_members, rule, h_star, [cand], D_LONG, seed)
            j0_24 = confirm_nc[r][D_LONG]
            d24_da.append(out24["J_assoc"] - j0_24["J_assoc"])
            d24_dc.append(out24["J_conservative"] - j0_24["J_conservative"])
            d24_lost.append(1 if out24["event"] in ("lost_dead",) else 0)
            d24_vcons.append(out24["V_conservative"])
        rows.append(dict(state_id=state["state_id"], candidate=int(cand), label=label,
                          d8_mean_delta_assoc=float(np.mean(d8_da)), d8_mean_delta_conservative=float(np.mean(d8_dc)),
                          d24_mean_delta_assoc=float(np.mean(d24_da)), d24_mean_delta_conservative=float(np.mean(d24_dc)),
                          d24_lost_dead_rate=float(np.mean(d24_lost)), d24_v_conservative_rate=float(np.mean(d24_vcons)),
                          d8_delta_conservative_all=d8_dc, d24_delta_conservative_all=d24_dc,
                          n_streams=N_K2_CONFIRM_STREAMS))
    return rows


def main():
    manifest = json.load(open(C.DATA_DIR / "state_manifest_612c.json"))
    states = manifest["states"]
    rule, _ = C.load_frozen_rule()
    mf = C.make_flock()

    all_candidate_rows, all_rollout_rows, all_pair_rows, all_duration_rows = [], [], [], []
    t_all = time.time()
    for state_idx, state in enumerate(states):
        is_safety = state_idx < DURATION_SUBSTUDY_N_STATES
        t0 = time.time()
        cand_rows, roll_rows = run_k1_for_state(mf, rule, state, state_idx, is_safety)
        dt1 = time.time() - t0
        all_candidate_rows.extend(cand_rows)
        all_rollout_rows.extend(roll_rows)

        pool_arr = np.array(sorted(int(p) for p in state["pool20"]))
        kin_scores = {r["candidate"]: r["kinematic_score"] for r in cand_rows}
        t1 = time.time()
        pair_rows = run_k2_for_state(mf, rule, state, state_idx, kin_scores, pool_arr)
        dt2 = time.time() - t1
        all_pair_rows.extend(pair_rows)

        dt3 = 0.0
        if is_safety:
            t2 = time.time()
            dur_rows = run_duration_substudy_for_state(mf, rule, state, state_idx, cand_rows)
            dt3 = time.time() - t2
            all_duration_rows.extend(dur_rows)

        print(f"[{state['state_id']}] K1={dt1:.0f}s K2={dt2:.0f}s dur={dt3:.0f}s total={dt1+dt2+dt3:.0f}s "
              f"(elapsed {time.time()-t_all:.0f}s)", flush=True)

        # checkpoint after every state
        json.dump(all_candidate_rows, open(C.DATA_DIR / "k1_candidates_612c.json", "w"), indent=1)
        json.dump(all_rollout_rows, open(C.DATA_DIR / "k1_rollouts_612c.json", "w"))
        json.dump(all_pair_rows, open(C.DATA_DIR / "k2_pairs_612c.json", "w"), indent=1)
        json.dump(all_duration_rows, open(C.DATA_DIR / "duration_substudy_612c.json", "w"), indent=1)

    total_dt = time.time() - t_all
    print(f"TOTAL wall time: {total_dt:.1f}s ({total_dt/3600:.2f}h)")
    with open(C.LOG_DIR / "run_confirmatory_612c_timing.txt", "a") as f:
        f.write(f"total_wall_time_s={total_dt:.1f} n_states={len(states)}\n")


if __name__ == "__main__":
    main()
