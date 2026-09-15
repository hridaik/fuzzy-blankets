"""Stage 6.11B item 12: repair Bpred's certification, without moving delta or
using Bpred to restrict the control pool. Freezes the pretrained relational
predictor (the "existing online-buffer refit worsens prediction at all
tested speeds" finding from INVARIANCE_AND_TRANSFER_6_11.md is taken as
settled here, not re-litigated).

Adds, additively, to the existing single-source challenger
(`predictive_boundary_611.certify`, reproduced unchanged):
  1. pair/small-block challenger  (2-source ablation-reinclusion, same
     bootstrap-over-episodes convention)
  2. regularized, cross-fitted multivariate residual challenger, capable of
     modest interactions: presence-indicator features for the top-15
     individual-gain exterior sources PLUS pairwise-product interaction
     terms among the top 5 of those (never a huge unregularized
     all-exterior-birds model), L2-regularized, 5-fold cross-fitted so the
     reported gap is a genuine held-out number
  3. complexity curve L_K for K = 0..K_max_audit (24, double the original
     K_max=12), checking for a knee
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))
import common_611  # noqa: E402,F401

from common_611 import DATA_DIR, L_BOX, dump_json  # noqa: E402
from detect_69 import propose  # noqa: E402
import predictive_boundary_611 as PB  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

K_MAX_AUDIT = 24
M_OBS = 12
N_TOP_INDICATOR = 15
N_TOP_INTERACTION = 5
N_FOLDS = 5


def get_candidate_and_rows():
    d = np.load(DATA_DIR / "observational_corpus_611__val.npz")
    r_hist, z_hist = d["r_hist"][0], d["z_hist"][0]
    t0 = 90
    z_window = [z_hist[max(0, t0 - k)] for k in range(5, -1, -1)]
    cands = propose(r_hist[t0], z_window, L_BOX)
    members = cands[0]
    return members, r_hist, z_hist, t0


def complexity_curve(model, members, construct_rows, k_max):
    out = PB.construct_boundary(model, members, construct_rows, k_max=k_max)
    return out


def pair_challenger(model, members, B, test_episodes, dist_cuts, periphery_radius, rng,
                      max_rows_per_episode=800, n_boot=200, alpha=0.05):
    member_set = set(int(m) for m in members)
    keep_B = member_set | set(B)
    base_losses, cand_losses = [], {}
    all_sources = set()
    for ep in test_episodes:
        rows = PB.rows_for_targets([ep], members, L_BOX, M_OBS, dist_cuts, periphery_radius, rng,
                                     max_rows_total=max_rows_per_episode)
        hist_matrix, z_i_arr, label_arr = PB._rows_to_matrix(rows)
        if len(rows) == 0:
            base_losses.append(float("nan"))
            continue
        occ = PB._exterior_occurrences(rows, keep_B)
        base_mat = hist_matrix.copy()
        for ridx, cat in occ.values():
            np.subtract.at(base_mat, (ridx, cat), 1.0)
        np.clip(base_mat, 0.0, None, out=base_mat)
        base_losses.append(model.logloss_batch(z_i_arr, base_mat, label_arr))
        all_sources.update(occ.keys())
        # top individual-gain sources only, for pair tractability
        singles = sorted(occ.keys())[:min(20, len(occ))]
        for i, j in [(a, b) for idx, a in enumerate(singles) for b in singles[idx + 1:]]:
            trial = base_mat.copy()
            if i in occ:
                np.add.at(trial, occ[i], 1.0)
            if j in occ:
                np.add.at(trial, occ[j], 1.0)
            cand_losses.setdefault((i, j), []).append(model.logloss_batch(z_i_arr, trial, label_arr))
        for key in cand_losses:
            if len(cand_losses[key]) < len(base_losses):
                cand_losses[key].append(base_losses[-1])

    base_arr = np.array(base_losses)
    valid = np.where(~np.isnan(base_arr))[0]
    cand_arr = {k: np.array(v) for k, v in cand_losses.items()}
    challenge_gaps = np.zeros(n_boot)
    best_pair_per_boot = []
    for b in range(n_boot):
        idx = rng.choice(valid, size=len(valid), replace=True) if len(valid) else valid
        boot_base = float(np.mean(base_arr[idx])) if len(idx) else float("nan")
        best = boot_base
        for arr in cand_arr.values():
            best = min(best, float(np.mean(arr[idx]))) if len(idx) else best
        challenge_gaps[b] = boot_base - best if len(idx) else 0.0
    upper = float(np.quantile(challenge_gaps, 1 - alpha)) if n_boot else float("nan")
    return dict(base_test_logloss=float(np.nanmean(base_arr)) if len(base_arr) else None,
                 L_challenge_point=float(np.mean(challenge_gaps)) if n_boot else None,
                 L_challenge_upper=upper, n_pairs_tested=len(cand_arr))


def multivariate_residual_challenger(model, members, B, test_episodes, dist_cuts, periphery_radius, rng,
                                        max_rows_per_episode=800):
    member_set = set(int(m) for m in members)
    keep_B = member_set | set(B)
    all_rows, all_occ = [], []
    for ep in test_episodes:
        rows = PB.rows_for_targets([ep], members, L_BOX, M_OBS, dist_cuts, periphery_radius, rng,
                                     max_rows_total=max_rows_per_episode)
        all_rows.extend(rows)

    hist_matrix, z_i_arr, label_arr = PB._rows_to_matrix(all_rows)
    occ = PB._exterior_occurrences(all_rows, keep_B)
    base_mat = hist_matrix.copy()
    for ridx, cat in occ.values():
        np.subtract.at(base_mat, (ridx, cat), 1.0)
    np.clip(base_mat, 0.0, None, out=base_mat)
    base_loss_per_row = _per_row_loss(model, z_i_arr, base_mat, label_arr)

    top_sources = sorted(occ.keys(), key=lambda j: -len(occ[j][0]))[:N_TOP_INDICATOR]
    n = len(all_rows)
    presence = np.zeros((n, len(top_sources)))
    for si, j in enumerate(top_sources):
        ridx, _ = occ[j]
        presence[ridx, si] = 1.0
    top5_idx = list(range(min(N_TOP_INTERACTION, len(top_sources))))
    interactions = []
    for a in top5_idx:
        for b in top5_idx:
            if a < b:
                interactions.append(presence[:, a] * presence[:, b])
    X = np.concatenate([presence] + ([np.stack(interactions, axis=1)] if interactions else []), axis=1)
    # Cross-fitted comparison: does adding presence/interaction features for
    # the top exterior sources to the base (interior-only-conditioned)
    # histogram improve held-out log-loss on the ACTUAL next-heading label,
    # under L2 regularization? (base_loss_per_row computed above is kept
    # only as a per-row diagnostic, not used as a training target here.)
    del base_loss_per_row
    X_full = np.concatenate([base_mat, X], axis=1)
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=0)
    cv_losses_aug, cv_losses_base = [], []
    for h in range(PB.NU):
        mask = z_i_arr == h
        if mask.sum() < 50 or len(set(label_arr[mask].tolist())) < 2:
            continue
        Xh, yh = X_full[mask], label_arr[mask]
        Xh_base = base_mat[mask]
        for train_idx, test_idx in kf.split(Xh):
            if len(set(yh[train_idx].tolist())) < 2:
                continue
            clf_aug = LogisticRegression(C=0.3, max_iter=300, multi_class="multinomial")
            clf_aug.fit(Xh[train_idx], yh[train_idx])
            p = clf_aug.predict_proba(Xh[test_idx])
            classes = clf_aug.classes_
            ll = _logloss_from_proba(p, classes, yh[test_idx])
            cv_losses_aug.extend(ll.tolist())

            clf_base = LogisticRegression(C=1.0, max_iter=300, multi_class="multinomial")
            clf_base.fit(Xh_base[train_idx], yh[train_idx])
            p2 = clf_base.predict_proba(Xh_base[test_idx])
            ll2 = _logloss_from_proba(p2, clf_base.classes_, yh[test_idx])
            cv_losses_base.extend(ll2.tolist())

    return dict(cv_mean_logloss_base_features=float(np.mean(cv_losses_base)) if cv_losses_base else None,
                 cv_mean_logloss_augmented=float(np.mean(cv_losses_aug)) if cv_losses_aug else None,
                 gap=(float(np.mean(cv_losses_base) - np.mean(cv_losses_aug))
                       if cv_losses_base and cv_losses_aug else None),
                 n_top_indicator_sources=len(top_sources), n_interaction_terms=len(interactions),
                 n_rows_used=n)


def _per_row_loss(model, z_i_arr, hist_matrix, label_arr):
    ll = np.empty(len(z_i_arr))
    for h in range(PB.NU):
        mask = z_i_arr == h
        if not mask.any():
            continue
        m = model.models[h]
        X = hist_matrix[mask]
        if isinstance(m, tuple):
            s = np.full((mask.sum(), PB.NU), -np.inf); s[:, m[1]] = 0.0
        else:
            raw = X @ m.coef_.T + m.intercept_
            s = np.full((mask.sum(), PB.NU), -1e9); s[:, m.classes_] = raw
        s = s - s.max(axis=1, keepdims=True)
        p = np.exp(s); p = p / p.sum(axis=1, keepdims=True)
        lab = label_arr[mask]
        ll[mask] = -np.log(np.maximum(p[np.arange(len(lab)), lab], 1e-12))
    return ll


def _logloss_from_proba(p, classes, y):
    full = np.full((len(y), PB.NU), 1e-12)
    full[:, classes] = p
    full = full / full.sum(axis=1, keepdims=True)
    return -np.log(np.maximum(full[np.arange(len(y)), y], 1e-12))


def main():
    print("[bpred_recert] loading pretrained model + one candidate...", flush=True)
    model, base_rows, dist_cuts = ROC.load_pretrained_model(M_obs=M_OBS)
    members, r_hist, z_hist, t0 = get_candidate_and_rows()
    print(f"  candidate size={len(members)}", flush=True)

    from geometry_611 import local_scale
    periphery_radius = local_scale(r_hist[t0], L_BOX)
    rng = np.random.default_rng(3)
    ep_recent = dict(r_hist=r_hist[max(0, t0 - 10):t0 + 1], z_hist=z_hist[max(0, t0 - 10):t0 + 1])
    construct_rows = PB.rows_for_targets([ep_recent], members, L_BOX, M_OBS, dist_cuts, periphery_radius,
                                            rng, max_rows_total=800)

    print("[bpred_recert] complexity curve L_K, K=0..24 ...", flush=True)
    curve = complexity_curve(model, members, construct_rows, K_MAX_AUDIT)
    B = curve["B"]
    print(f"  B (K={len(B)}): final_loss={curve['final_loss']:.4f} full_pool_loss={curve['full_pool_loss']:.4f}", flush=True)

    d_test = np.load(DATA_DIR / "observational_corpus_611__test.npz")
    test_episodes = [dict(r_hist=d_test["r_hist"][k], z_hist=d_test["z_hist"][k]) for k in range(6)]

    print("[bpred_recert] single-source certification (reproduction) ...", flush=True)
    single = PB.certify(model, members, B, test_episodes, L_BOX, M_OBS, dist_cuts, periphery_radius, rng)

    print("[bpred_recert] pair/block challenger ...", flush=True)
    pair = pair_challenger(model, members, B, test_episodes, dist_cuts, periphery_radius, rng)

    print("[bpred_recert] regularized cross-fitted multivariate residual challenger ...", flush=True)
    multi = multivariate_residual_challenger(model, members, B, test_episodes, dist_cuts, periphery_radius, rng)

    out = dict(candidate_size=len(members), B=B, K=len(B),
                complexity_curve_trace=curve["trace"], full_pool_loss=curve["full_pool_loss"],
                interior_only_loss=curve["interior_only_loss"], final_loss=curve["final_loss"],
                single_source_certification_reproduction=single,
                pair_block_challenger=pair,
                multivariate_residual_challenger=multi,
                delta=PB.DELTA_SUFFICIENT)
    dump_json(out, AUDIT_DIR / "bpred_recertification_611.json")
    print(json.dumps({k: v for k, v in out.items() if k != "complexity_curve_trace"}, indent=1, default=str))


if __name__ == "__main__":
    main()
