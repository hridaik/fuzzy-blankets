"""Part C: invariance (exact, numerical) and dynamical-transfer (frozen v=0.28
model evaluated at v in {0.14, 0.28, 0.42}) checks. Additive, read-only.
No control anywhere in this script.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import (DATA_DIR, L_BOX, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY,  # noqa: E402
                          SOCIAL_PRIMARY, BETA_610, S_610, resolved_params, N_BIRDS, dump_json)
from moving_flock_611 import MovingFlock611  # noqa: E402
from flock_sim.model import UV4  # noqa: E402
from detect_69 import propose  # noqa: E402
from geometry_611 import torus_delta  # noqa: E402
import predictive_boundary_611 as PB  # noqa: E402
from lineage_611 import dice, retention_purity  # noqa: E402
from identity_69 import centroid, field, field_distance, estimate_translation, similarity  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

RNG_SEED = 12345


# =====================================================================
# 1. Exact invariance checks (one real snapshot pair, no new simulation)
# =====================================================================
def load_one_snapshot():
    d = np.load(DATA_DIR / "observational_corpus_611__test.npz")
    r_hist, z_hist = d["r_hist"][0], d["z_hist"][0]
    return r_hist, z_hist


def invariance_checks():
    r_hist, z_hist = load_one_snapshot()
    t0 = 50
    r, z = r_hist[t0], z_hist[t0]
    z_window = [z_hist[t0 - k] for k in range(4, -1, -1)]

    model, base_rows, dist_cuts = ROC.load_pretrained_model(M_obs=12)
    L = L_BOX

    results = {}

    # ---- translation invariance ----
    rng = np.random.default_rng(RNG_SEED)
    delta = rng.random(2) * L
    r_t = (r + delta) % L
    z_window_t = z_window  # headings unaffected by translation

    i = 7  # arbitrary probe bird
    hist0, pool0, cat0 = PB.pool_and_histogram(r, z, i, L, dist_cuts, 12)
    hist1, pool1, cat1 = PB.pool_and_histogram(r_t, z, i, L, dist_cuts, 12)
    results["translation_histogram_identical"] = bool(np.array_equal(hist0, hist1))
    results["translation_pool_identical"] = bool(np.array_equal(np.sort(pool0), np.sort(pool1)))
    p0 = model.predict_proba(int(z[i]), hist0)
    p1 = model.predict_proba(int(z[i]), hist1)
    results["translation_predict_proba_max_abs_diff"] = float(np.max(np.abs(p0 - p1)))

    cands0 = propose(r, z_window, L)
    cands1 = propose(r_t, z_window_t, L)
    same_partition = (len(cands0) == len(cands1) and
                       all(set(int(x) for x in a) == set(int(x) for x in b) for a, b in zip(cands0, cands1)))
    results["translation_candidate_partition_identical"] = bool(same_partition)

    if cands0:
        members = cands0[0]
        c0 = centroid(r[members], L)
        rho0, m0, _ = field(r[members], UV4[z[members]], L, c0)
        c1 = centroid(r_t[members], L)
        rho1, m1, _ = field(r_t[members], UV4[z[members]], L, c1)
        results["translation_field_rho_max_abs_diff"] = float(np.max(np.abs(rho0 - rho1)))
        results["translation_field_m_max_abs_diff"] = float(np.max(np.abs(m0 - m1)))
        other = np.array(sorted(rng.choice(N_BIRDS, size=len(members), replace=False)))
        c0o = centroid(r[other], L); rho0o, m0o, _ = field(r[other], UV4[z[other]], L, c0o)
        c1o = centroid(r_t[other], L); rho1o, m1o, _ = field(r_t[other], UV4[z[other]], L, c1o)
        d_norm0 = max(field_distance(rho0, m0, rho0o, m0o), 1e-3)
        d_norm1 = max(field_distance(rho1, m1, rho1o, m1o), 1e-3)
        results["translation_d_norm_rel_diff"] = float(abs(d_norm0 - d_norm1) / d_norm0)

        periphery_radius = 3.0
        rows0 = PB.rows_for_targets([dict(r_hist=r_hist[t0 - 1:t0 + 1], z_hist=z_hist[t0 - 1:t0 + 1])],
                                     members, L, 12, dist_cuts, periphery_radius, rng, max_rows_total=300)
        r_hist_t = r_hist.copy(); r_hist_t[t0 - 1:t0 + 1] = (r_hist[t0 - 1:t0 + 1] + delta) % L
        rows1 = PB.rows_for_targets([dict(r_hist=r_hist_t[t0 - 1:t0 + 1], z_hist=z_hist[t0 - 1:t0 + 1])],
                                     members, L, 12, dist_cuts, periphery_radius, rng, max_rows_total=300)
        B0 = PB.construct_boundary(model, members, rows0)
        B1 = PB.construct_boundary(model, members, rows1)
        results["translation_boundary_B_identical"] = (B0["B"] == B1["B"])
        results["translation_boundary_loss_abs_diff"] = float(abs(B0["final_loss"] - B1["final_loss"]))

    # ---- permutation invariance ----
    rng2 = np.random.default_rng(RNG_SEED + 1)
    perm = rng2.permutation(N_BIRDS)          # new_index -> old_index (r_p[k] = r[perm[k]])
    inv_perm = np.argsort(perm)                # old_index -> new_index
    r_p, z_p = r[perm], z[perm]
    z_window_p = [zw[perm] for zw in z_window]

    old_i = 7
    new_i = int(inv_perm[old_i])
    hist_p, pool_p, cat_p = PB.pool_and_histogram(r_p, z_p, new_i, L, dist_cuts, 12)
    results["permutation_histogram_identical_for_same_physical_bird"] = bool(np.array_equal(hist0, hist_p))
    p_p = model.predict_proba(int(z_p[new_i]), hist_p)
    results["permutation_predict_proba_max_abs_diff"] = float(np.max(np.abs(p0 - p_p)))

    cands_p = propose(r_p, z_window_p, L)
    cands_p_as_old_ids = [set(int(perm[x]) for x in c) for c in cands_p]
    cands0_as_sets = [set(int(x) for x in c) for c in cands0]
    same_up_to_relabel = (len(cands0_as_sets) == len(cands_p_as_old_ids) and
                           all(a == b for a, b in zip(cands0_as_sets, cands_p_as_old_ids)))
    results["permutation_candidate_membership_identical_as_physical_ids"] = bool(same_up_to_relabel)

    if cands0:
        members_p = np.array(sorted(int(inv_perm[x]) for x in members))
        rows_p = PB.rows_for_targets([dict(r_hist=np.stack([r_p, r_p]), z_hist=np.stack([z_p, z_p]))],
                                      members_p, L, 12, dist_cuts, 3.0, rng2, max_rows_total=300)
        Bp = PB.construct_boundary(model, members_p, rows_p) if rows_p else None
        if Bp is not None:
            B0_as_old = set(B0["B"])
            Bp_as_old = set(int(perm[x]) for x in Bp["B"])
            results["permutation_boundary_B_identical_as_physical_ids"] = (B0_as_old == Bp_as_old)

    # ---- lineage continuation math: translation/permutation covariance ----
    if cands0 and len(cands0) > 1:
        h_members = cands0[0]
        c_members = cands0[1] if len(set(cands0[1]) & set(h_members)) < len(cands0[1]) else cands0[1]
        prev_set, cur_set = set(int(x) for x in h_members), set(int(x) for x in c_members)
        r_retain0, r_purity0 = retention_purity(prev_set, cur_set)
        dice0 = dice(prev_set, cur_set)
        # under translation: identical members -> identical dice/retention trivially; check R_F
        c_h0 = centroid(r[h_members], L); rho_h0, m_h0, _ = field(r[h_members], UV4[z[h_members]], L, c_h0)
        c_h1 = centroid(r_t[h_members], L); rho_h1, m_h1, _ = field(r_t[h_members], UV4[z[h_members]], L, c_h1)
        c_c0 = centroid(r[c_members], L); rho_c0, m_c0, _ = field(r[c_members], UV4[z[c_members]], L, c_c0)
        c_c1 = centroid(r_t[c_members], L); rho_c1, m_c1, _ = field(r_t[c_members], UV4[z[c_members]], L, c_c1)
        tr0 = estimate_translation(rho_h0, m_h0, rho_c0, m_c0, c_h0, c_c0)
        tr1 = estimate_translation(rho_h1, m_h1, rho_c1, m_c1, c_h1, c_c1)
        results["translation_lineage_R_F_input_distance_abs_diff"] = float(abs(tr0["distance"] - tr1["distance"]))
        results["translation_lineage_dice_retention_trivially_identical"] = True  # pure set ops, torus_delta-free

    # ---- 90-degree lattice-rotation check (narrower than general rotation) ----
    # UV4 = [up, down, left, right]; rotate positions by 90 CCW about the box
    # centre AND relabel headings by the matching 90 CCW permutation of UV4,
    # since headings live on the fixed 4-state lattice and only a rotation
    # that maps the lattice onto itself is even well-defined here.
    ROT90 = np.array([[0.0, -1.0], [1.0, 0.0]])   # CCW
    centre = np.array([L / 2, L / 2])
    r_rot = (ROT90 @ (r - centre).T).T + centre
    r_rot = r_rot % L
    # UV4 order: [0]=up(0,1) [1]=down(0,-1) [2]=left(-1,0) [3]=right(1,0)
    # 90 CCW maps up->left, left->down, down->right, right->up
    HEADING_ROT_MAP = np.array([2, 3, 1, 0])  # z_rot = HEADING_ROT_MAP[z]
    z_rot = HEADING_ROT_MAP[z]
    hist_rot, _, _ = PB.pool_and_histogram(r_rot, z_rot, i, L, dist_cuts, 12)
    # NOTE: category indexing bakes in absolute UV4 heading identity
    # (category_index uses z_j directly, 0..3), so a 90-rotated CONFIGURATION
    # does not in general produce the identical raw histogram under the
    # model's own fixed per-heading-id coefficients unless the model itself
    # is separately checked for equivariance under the SAME relabelling of
    # its 4 per-stratum coefficient sets -- report the raw comparison and do
    # NOT round it off to a same/different verdict without that caveat.
    results["rotation90_histogram_identical_no_relabel_of_model_strata"] = bool(np.array_equal(hist0, hist_rot))
    cands_rot = propose(r_rot, z_rot, [z_rot] * len(z_window), L) if False else propose(r_rot, [z_rot] * 5, L)
    results["rotation90_candidate_sizes"] = [len(c) for c in cands_rot]
    results["rotation90_note"] = ("Affinity/detection depends on torus distance (rotation-covariant) and "
                                    "per-step heading AGREEMENT (rotation-invariant under the consistent "
                                    "relabelling above), so candidate PARTITION structure is expected to be "
                                    "preserved; but the relational predictor's category index bakes in "
                                    "absolute heading identity (0..3), so raw category histograms/logits are "
                                    "NOT claimed invariant under 90-degree rotation without also relabelling "
                                    "the per-stratum coefficient sets. General continuous rotation is not "
                                    "claimed or testable: headings are constrained to the 4-state UV4 lattice.")

    return results


# =====================================================================
# 2. Dynamical transfer: frozen v=0.28 model at v in {0.14, 0.28, 0.42}
# =====================================================================
SPEEDS = (0.14, 0.28, 0.42)
N_EPISODES_PER_SPEED = 4
EPISODE_LEN = 150
TRANSFER_SEEDS = (300, 301, 302, 303)


def make_flock_at(v):
    pm = resolved_params(BETA_610, S_610)
    return MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=v, params=pm,
                           social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)


def generate_episode(v, seed, nt=EPISODE_LEN):
    mf = make_flock_at(v)
    rng = np.random.default_rng(seed)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)
    R_ = np.zeros((nt + 1, mf.N, 2)); R_[0] = r
    Z_ = np.zeros((nt + 1, mf.N), dtype=int); Z_[0] = z
    for t in range(nt):
        r, z, _ = mf.step(r, z, rng, forced_actions=None)
        R_[t + 1], Z_[t + 1] = r, z
    return R_, Z_


def walk_forward_eval(model, base_rows, dist_cuts, r_hist, z_hist, M_obs, adapt: bool):
    """Zero-adaptation (adapt=False) or online-buffer adaptation (adapt=True,
    mirrors run_online_control_611.step_world's buffer + refit cadence, but
    with NO control anywhere -- pure passive observation)."""
    from copy import deepcopy
    mdl = model if not adapt else deepcopy(model)
    online_buffer = []
    ONLINE_BUFFER_CAP = 3000
    losses = []
    T = z_hist.shape[0] - 1
    rng = np.random.default_rng(999)
    for t in range(T):
        idx = rng.choice(z_hist.shape[1], size=min(60, z_hist.shape[1]), replace=False)
        step_losses = []
        for i in idx:
            hist, pool_idx, cats = PB.pool_and_histogram(r_hist[t], z_hist[t], int(i), L_BOX, dist_cuts, M_obs)
            label = int(z_hist[t + 1, i])
            step_losses.append(mdl.logloss(int(z_hist[t, i]), hist, label))
            if adapt:
                online_buffer.append(PB.Row(t=t, i=int(i), z_i=int(z_hist[t, i]), hist=hist,
                                              label=label, pool_idx=pool_idx, pool_cat=cats))
        losses.append(float(np.mean(step_losses)))
        if adapt:
            if len(online_buffer) > ONLINE_BUFFER_CAP:
                del online_buffer[: len(online_buffer) - ONLINE_BUFFER_CAP]
            if t > 0 and t % ROC.REINFER_PRED_EVERY == 0:
                mdl.refit_with_buffer(base_rows, online_buffer)
    return dict(mean_logloss=float(np.mean(losses)), per_step_logloss=losses)


def candidate_stability(r_hist, z_hist, L, window=6):
    z_window = []
    prev_best = None
    jaccards = []
    for t in range(r_hist.shape[0]):
        z_window.append(z_hist[t])
        if len(z_window) > window:
            z_window.pop(0)
        if len(z_window) < 2:
            continue
        cands = propose(r_hist[t], z_window, L)
        if not cands:
            prev_best = None
            continue
        best = set(int(x) for x in cands[0])
        if prev_best is not None:
            j = len(best & prev_best) / max(1, len(best | prev_best))
            jaccards.append(j)
        prev_best = best
    return dict(mean_step_to_step_jaccard=float(np.mean(jaccards)) if jaccards else None,
                n_steps_evaluated=len(jaccards))


def bpred_quality_snapshot(model, r_hist, z_hist, L, M_obs, dist_cuts, rng):
    z_window = [z_hist[max(0, r_hist.shape[0] // 2 - k)] for k in range(4, -1, -1)]
    t0 = r_hist.shape[0] // 2
    cands = propose(r_hist[t0], z_window, L)
    if not cands:
        return None
    members = cands[0]
    ep = dict(r_hist=r_hist[max(0, t0 - 10):t0 + 1], z_hist=z_hist[max(0, t0 - 10):t0 + 1])
    rows = PB.rows_for_targets([ep], members, L, M_obs, dist_cuts, 3.0, rng, max_rows_total=600)
    if not rows:
        return None
    B = PB.construct_boundary(model, members, rows)
    return dict(candidate_size=len(members), B_size=len(B["B"]),
                interior_only_loss=B["interior_only_loss"], full_pool_loss=B["full_pool_loss"],
                final_loss=B["final_loss"])


def transfer_checks():
    model, base_rows, dist_cuts = ROC.load_pretrained_model(M_obs=12)
    out = {}
    for v in SPEEDS:
        print(f"[transfer] generating {N_EPISODES_PER_SPEED} episodes at v={v} ...", flush=True)
        episodes = []
        if v == V_PRIMARY:
            d = np.load(DATA_DIR / "observational_corpus_611__test.npz")
            for k in range(min(N_EPISODES_PER_SPEED, len(d["seeds"]))):
                episodes.append((d["r_hist"][k][:EPISODE_LEN + 1], d["z_hist"][k][:EPISODE_LEN + 1]))
        else:
            for seed in TRANSFER_SEEDS[:N_EPISODES_PER_SPEED]:
                episodes.append(generate_episode(v, seed))

        zero_losses, adapt_losses, stab, bpred = [], [], [], []
        for r_hist, z_hist in episodes:
            zero_losses.append(walk_forward_eval(model, base_rows, dist_cuts, r_hist, z_hist, 12, adapt=False))
            adapt_losses.append(walk_forward_eval(model, base_rows, dist_cuts, r_hist, z_hist, 12, adapt=True))
            stab.append(candidate_stability(r_hist, z_hist, L_BOX))
            rng = np.random.default_rng(42)
            bq = bpred_quality_snapshot(model, r_hist, z_hist, L_BOX, 12, dist_cuts, rng)
            if bq:
                bpred.append(bq)

        out[str(v)] = dict(
            n_episodes=len(episodes),
            zero_adapt_mean_logloss=float(np.mean([x["mean_logloss"] for x in zero_losses])),
            online_adapt_mean_logloss=float(np.mean([x["mean_logloss"] for x in adapt_losses])),
            candidate_stability_mean_jaccard=float(np.mean([s["mean_step_to_step_jaccard"] for s in stab
                                                              if s["mean_step_to_step_jaccard"] is not None])),
            bpred_mean_final_loss=float(np.mean([b["final_loss"] for b in bpred])) if bpred else None,
            bpred_mean_interior_only_loss=float(np.mean([b["interior_only_loss"] for b in bpred])) if bpred else None,
            bpred_mean_B_size=float(np.mean([b["B_size"] for b in bpred])) if bpred else None,
            zero_adapt_per_episode=[x["mean_logloss"] for x in zero_losses],
            online_adapt_per_episode=[x["mean_logloss"] for x in adapt_losses],
        )
        print(f"   v={v}: {json.dumps(out[str(v)], default=str)[:400]}", flush=True)
    return out


def main():
    print("=== Part C.1: exact invariance checks ===", flush=True)
    inv = invariance_checks()
    dump_json(inv, AUDIT_DIR / "invariance_checks_611.json")
    print(json.dumps(inv, indent=1, default=str))

    print("=== Part C.2: dynamical transfer across speeds ===", flush=True)
    tr = transfer_checks()
    dump_json(tr, AUDIT_DIR / "transfer_checks_611.json")


if __name__ == "__main__":
    main()
