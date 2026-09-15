"""Fits lineage_v2's p_continue = sigmoid(a*score + b) from UNCONTROLLED
development data only (train split of observational_corpus_611), never from
control outcome, per PLAN.md Section V rule 6's spirit extended to lineage_v2.

Labelled pairs, built from real (never control) trajectories:
  GOOD  = (candidate at t, its natural best-Jaccard-match candidate at t+1),
          restricted to Jaccard >= 0.5 -- an uncontested, ordinary one-step
          continuation.
  BAD   = (candidate at t, a candidate detected at an INDEPENDENTLY sampled,
          unrelated (episode, t') snapshot) -- an unrelated pair by
          construction (different episode, shuffled).

score = 0.6*dice + 0.4*R_F (lineage_v2_611's own formula, imported not
reimplemented). Fits a 1-D logistic regression score -> label (sklearn),
reports a held-out reliability curve and Brier score so this audit does NOT
claim "calibrated Bayesian posterior" without checking.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import DATA_DIR, L_BOX, dump_json  # noqa: E402
from flock_sim.model import UV4  # noqa: E402
from detect_69 import propose  # noqa: E402
from lineage_v2_611 import dice, component_sizes  # noqa: E402
from identity_69 import centroid, field, field_distance, estimate_translation, similarity  # noqa: E402
from geometry_611 import local_scale  # noqa: E402

AFFINITY_WINDOW = 6
N_EPISODES = 10


def score_transition(members_a, members_b, r_a, z_a, r_b, z_b, L, d_norm=None, rng=None):
    prev_set, cand_set = set(int(x) for x in members_a), set(int(x) for x in members_b)
    dc = dice(prev_set, cand_set)
    c_a = centroid(r_a[members_a], L); rho_a, m_a, _ = field(r_a[members_a], UV4[z_a[members_a]], L, c_a)
    c_b = centroid(r_b[members_b], L); rho_b, m_b, _ = field(r_b[members_b], UV4[z_b[members_b]], L, c_b)
    if d_norm is None:
        rng = rng or np.random.default_rng(0)
        other = np.array(sorted(rng.choice(len(z_a), size=len(members_a), replace=False)))
        c_o = centroid(r_a[other], L); rho_o, m_o, _ = field(r_a[other], UV4[z_a[other]], L, c_o)
        d_norm = max(field_distance(rho_a, m_a, rho_o, m_o), 1e-3)
    tr = estimate_translation(rho_a, m_a, rho_b, m_b, c_a, c_b)
    R_F = similarity(tr["distance"], d_norm)
    return 0.6 * dc + 0.4 * R_F


def collect_pairs():
    d = np.load(DATA_DIR / "observational_corpus_611__train.npz")
    episodes = [dict(r_hist=d["r_hist"][k], z_hist=d["z_hist"][k]) for k in range(min(N_EPISODES, len(d["seeds"])))]
    rng = np.random.default_rng(2024)

    all_cands = []   # (ep_idx, t, members, r, z)
    for ei, ep in enumerate(episodes):
        r_hist, z_hist = ep["r_hist"], ep["z_hist"]
        z_window = []
        for t in range(0, r_hist.shape[0] - 1, 3):   # subsample every 3rd step, tractability
            z_window.append(z_hist[t])
            if len(z_window) > AFFINITY_WINDOW:
                z_window.pop(0)
            if len(z_window) < 2:
                continue
            cands = propose(r_hist[t], z_window, L_BOX)
            for c in cands[:3]:   # largest few per step, tractability
                all_cands.append((ei, t, c, r_hist[t], z_hist[t]))

    good_scores, bad_scores = [], []
    for ei, t, members, r_a, z_a in all_cands:
        r_hist, z_hist = episodes[ei]["r_hist"], episodes[ei]["z_hist"]
        t1 = t + 1
        if t1 >= r_hist.shape[0]:
            continue
        z_window1 = [z_hist[max(0, t1 - k)] for k in range(AFFINITY_WINDOW - 1, -1, -1)]
        cands1 = propose(r_hist[t1], z_window1, L_BOX)
        if not cands1:
            continue
        prev_set = set(int(x) for x in members)
        best = max(cands1, key=lambda c: len(prev_set & set(int(x) for x in c)) / max(1, len(prev_set | set(int(x) for x in c))))
        j = len(prev_set & set(int(x) for x in best)) / max(1, len(prev_set | set(int(x) for x in best)))
        if j >= 0.5:
            s = score_transition(members, best, r_a, z_a, r_hist[t1], z_hist[t1], L_BOX, rng=rng)
            good_scores.append(s)

    # bad pairs: candidate from one (ep, t) vs a candidate from an unrelated (ep', t')
    for k in range(len(all_cands)):
        ei, t, members, r_a, z_a = all_cands[k]
        j2 = rng.integers(0, len(all_cands))
        ei2, t2, members2, r_b, z_b = all_cands[j2]
        if ei2 == ei and abs(t2 - t) < 20:
            continue   # ensure genuinely unrelated in time too
        s = score_transition(members, members2, r_a, z_a, r_b, z_b, L_BOX, rng=rng)
        bad_scores.append(s)
        if len(bad_scores) >= len(good_scores) * 1.2:
            break

    return np.array(good_scores), np.array(bad_scores)


def main():
    print("[calibrate_lineage_v2] collecting labelled good/bad continuation pairs...", flush=True)
    good, bad = collect_pairs()
    print(f"  n_good={len(good)} n_bad={len(bad)}", flush=True)
    X = np.concatenate([good, bad]).reshape(-1, 1)
    y = np.concatenate([np.ones(len(good)), np.zeros(len(bad))])

    rng = np.random.default_rng(7)
    idx = rng.permutation(len(X))
    n_train = int(0.7 * len(X))
    train_idx, test_idx = idx[:n_train], idx[n_train:]

    clf = LogisticRegression()
    clf.fit(X[train_idx], y[train_idx])
    a, b = float(clf.coef_[0, 0]), float(clf.intercept_[0])
    print(f"  fitted: p_continue = sigmoid({a:.4f} * score + {b:.4f})", flush=True)

    # held-out reliability check
    p_test = clf.predict_proba(X[test_idx])[:, 1]
    y_test = y[test_idx]
    brier = float(np.mean((p_test - y_test) ** 2))
    bins = np.linspace(0, 1, 11)
    bin_idx = np.digitize(p_test, bins) - 1
    reliability = []
    for bi in range(10):
        mask = bin_idx == bi
        if mask.sum() == 0:
            continue
        reliability.append(dict(bin=bi, mean_predicted=float(p_test[mask].mean()),
                                  empirical_frac_good=float(y_test[mask].mean()), n=int(mask.sum())))

    out = dict(a=a, b=b, n_good=len(good), n_bad=len(bad), n_train=len(train_idx), n_test=len(test_idx),
                held_out_brier_score=brier, reliability_curve=reliability,
                good_score_percentiles=dict(p5=float(np.percentile(good, 5)), p50=float(np.percentile(good, 50)),
                                               p95=float(np.percentile(good, 95))),
                bad_score_percentiles=dict(p5=float(np.percentile(bad, 5)), p50=float(np.percentile(bad, 50)),
                                              p95=float(np.percentile(bad, 95))))
    dump_json(out, AUDIT_DIR / "lineage_v2_calibration_611.json")
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
