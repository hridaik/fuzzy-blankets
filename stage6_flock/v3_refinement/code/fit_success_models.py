"""Part 1C: does P(success) collapse more cleanly against core interface
coverage (Gamma) than against raw actuator fraction (f_A)? Fit on
development-flock data only; report leave-one-dev-flock-out held-out
log-loss (not in-sample fit, which trivially favors the richer model).
"""
from __future__ import annotations

import json

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

from common_v3 import V3_DIR, dump_json


def build_replicate_table(data):
    """One row per (flock, rule, fraction, replicate): f_A, Gamma, mean_m, success."""
    rows = []
    for fl in data["flocks"]:
        for c in fl["conditions"]:
            for s in c["success_per_rep"]:
                rows.append(dict(seed=fl["seed"], rule=c["rule"], f_A=c["f_A"], Gamma=c["Gamma"],
                                  mean_m=c["mean_m"], n_components=c["n_components"],
                                  max_component_fraction=c["max_component_fraction"],
                                  sector_entropy=c["sector_entropy"],
                                  frac_m_ge1=c["frac_m_ge1"], frac_m_ge2=c["frac_m_ge2"],
                                  frac_m_ge3=c["frac_m_ge3"], success=s))
    return rows


def loo_logloss(rows, feature_cols, seeds):
    """Leave-one-dev-flock-out logistic regression log-loss."""
    y = np.array([r["success"] for r in rows])
    X = np.array([[r[c] for c in feature_cols] for r in rows], dtype=float)
    seed_arr = np.array([r["seed"] for r in rows])
    losses = []
    for held in seeds:
        train = seed_arr != held
        test = seed_arr == held
        if train.sum() == 0 or test.sum() == 0:
            continue
        y_train = y[train]
        if len(np.unique(y_train)) < 2:
            continue  # degenerate fold, skip
        clf = LogisticRegression(max_iter=2000)
        clf.fit(X[train], y_train)
        p = clf.predict_proba(X[test])[:, 1]
        eps = 1e-9
        p = np.clip(p, eps, 1 - eps)
        losses.append(log_loss(y[test], p, labels=[0, 1]))
    return float(np.mean(losses)), len(losses)


def in_sample_mcfadden_r2(rows, feature_cols):
    y = np.array([r["success"] for r in rows])
    X = np.array([[r[c] for c in feature_cols] for r in rows], dtype=float)
    clf = LogisticRegression(max_iter=2000).fit(X, y)
    p = np.clip(clf.predict_proba(X)[:, 1], 1e-9, 1 - 1e-9)
    ll_model = np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
    p0 = y.mean()
    ll_null = np.sum(y * np.log(p0) + (1 - y) * np.log(1 - p0))
    return float(1 - ll_model / ll_null), clf.coef_.ravel().tolist(), float(clf.intercept_[0])


def main():
    data = json.load(open(V3_DIR / "data" / "coverage_sweep.json"))
    rows = build_replicate_table(data)
    seeds = sorted(set(r["seed"] for r in rows))
    print(f"{len(rows)} replicate-level rows across {len(seeds)} dev flocks")

    models = {
        "f_A_only": ["f_A"],
        "Gamma_only": ["Gamma"],
        "Gamma_plus_mean_m": ["Gamma", "mean_m"],
        "f_A_plus_concentration": ["f_A", "max_component_fraction", "sector_entropy"],
        "frac_m_ge1_only": ["frac_m_ge1"],
        "frac_m_ge2_only": ["frac_m_ge2"],
        "frac_m_ge2_plus_mean_m": ["frac_m_ge2", "mean_m"],
        "mean_m_only": ["mean_m"],
    }

    out = dict(n_rows=len(rows), n_dev_flocks=len(seeds), models={})
    for name, cols in models.items():
        r2, coef, intercept = in_sample_mcfadden_r2(rows, cols)
        ll, n_folds = loo_logloss(rows, cols, seeds)
        out["models"][name] = dict(features=cols, in_sample_mcfadden_r2=r2, coef=coef,
                                    intercept=intercept, loo_holdout_logloss=ll, n_loo_folds=n_folds)
        print(f"{name:24s} features={cols}  in-sample McFadden R2={r2:.4f}  "
              f"LOO-holdout logloss={ll:.4f} (n_folds={n_folds})")

    dump_json(out, V3_DIR / "data" / "success_model_fits.json")
    print("\nWrote data/success_model_fits.json")


if __name__ == "__main__":
    main()
