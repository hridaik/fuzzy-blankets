"""Stage 6.12B aggregate analysis: 6.12B-A fixed-set exhaustive summary
(rank stability dev->holdout, held-out best-vs-random), 6.12B-B refreshed-
access central comparisons (fixed vs refreshed random; predicted-contact
vs refreshed-random; oracle vs predicted vs random), state-clustered
uncertainty throughout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612b as C   # noqa: E402


def spearman(x, y):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    if len(x) < 2 or x.std() == 0 or y.std() == 0:
        return None
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def cluster_ci(vals, n_boot=3000, seed=3):
    vals = np.asarray([v for v in vals if v is not None], dtype=float)
    if len(vals) == 0:
        return (None, None)
    rng = np.random.default_rng(seed)
    means = [rng.choice(vals, size=len(vals), replace=True).mean() for _ in range(n_boot)]
    return float(np.percentile(means, 5)), float(np.percentile(means, 95))


def analyze_fixed_set():
    path = C.DATA_DIR / "fixed_set_exhaustive_612b.json"
    if not path.exists():
        return None
    data = json.load(open(path))
    per_cell = {}
    per_state_g_sel = {}
    for st in data:
        sid = st["state_id"]
        per_state_g_sel[sid] = {}
        for cell_key, cell in st["cells"].items():
            deltas = cell["dev_deltas_assoc"]
            finalists = cell["finalists"]
            holdout = cell["holdout_evals"]
            dev_rank = {f["set_idx"]: f["mean_delta_assoc"] for f in finalists}
            hold_rank = {h["set_idx"]: h["holdout_mean_delta_assoc"] for h in holdout}
            common_idx = sorted(set(dev_rank) & set(hold_rank))
            rank_stab = spearman([dev_rank[i] for i in common_idx], [hold_rank[i] for i in common_idx]) if len(common_idx) > 2 else None
            per_cell.setdefault(cell_key, []).append(dict(
                state_id=sid, K=cell["K"], d=cell["d"],
                dev_mean=float(np.mean(deltas)), dev_median=float(np.median(deltas)),
                dev_best=cell["best"]["mean_delta_assoc"], dev_worst=cell["worst"]["mean_delta_assoc"],
                dev_var=cell["between_set_var_dev"], G_sel=cell["G_sel"], rank_stability=rank_stab,
            ))
            per_state_g_sel[sid][cell_key] = cell["G_sel"]

    cell_summary = {}
    for ck, rows in per_cell.items():
        g_sels = [r["G_sel"] for r in rows if r["G_sel"] is not None]
        cell_summary[ck] = dict(n_states=len(rows), mean_dev_var=float(np.mean([r["dev_var"] for r in rows])),
                                 mean_G_sel=float(np.mean(g_sels)) if g_sels else None,
                                 g_sels_by_state=g_sels,
                                 mean_rank_stability=float(np.mean([r["rank_stability"] for r in rows if r["rank_stability"] is not None]))
                                 if any(r["rank_stability"] is not None for r in rows) else None,
                                 rows=rows)
    return dict(per_cell=cell_summary, per_state_g_sel=per_state_g_sel)


def analyze_refreshed_access():
    path = C.DATA_DIR / "refreshed_access_612b.json"
    if not path.exists():
        return None
    data = json.load(open(path))

    # central comparison 1: fixed random (q=24) vs refreshed random (q<24)
    comp1 = {}
    for K in (2, 4):
        fixed_vals, refreshed_vals = {}, {}
        for st in data:
            sid = st["state_id"]
            c24 = st["cells"].get(f"K{K}_q24_random")
            if c24:
                fixed_vals[sid] = c24["mean_delta_assoc"]
            rvals = []
            for q in (8, 4, 2, 1):
                c = st["cells"].get(f"K{K}_q{q}_random")
                if c:
                    rvals.append(c["mean_delta_assoc"])
            if rvals:
                refreshed_vals[sid] = float(np.mean(rvals))
        comp1[f"K{K}"] = dict(
            fixed_q24_by_state=fixed_vals, refreshed_mean_by_state=refreshed_vals,
            fixed_q24_mean=float(np.mean(list(fixed_vals.values()))) if fixed_vals else None,
            refreshed_mean=float(np.mean(list(refreshed_vals.values()))) if refreshed_vals else None,
            fixed_q24_ci90=cluster_ci(list(fixed_vals.values())),
            refreshed_ci90=cluster_ci(list(refreshed_vals.values())),
        )

    # central comparison 2: predicted-contact (kinematic, physics-assisted) vs refreshed-random, at each q
    comp2 = {}
    for K in (2, 4):
        for q in (8, 4, 2, 1):
            kin_vals, rand_vals = {}, {}
            for st in data:
                sid = st["state_id"]
                ck = st["cells"].get(f"K{K}_q{q}_kinematic")
                cr = st["cells"].get(f"K{K}_q{q}_random")
                if ck:
                    kin_vals[sid] = ck["mean_delta_assoc"]
                if cr:
                    rand_vals[sid] = cr["mean_delta_assoc"]
            comp2[f"K{K}_q{q}"] = dict(
                kinematic_mean=float(np.mean(list(kin_vals.values()))) if kin_vals else None,
                random_mean=float(np.mean(list(rand_vals.values()))) if rand_vals else None,
                kinematic_ci90=cluster_ci(list(kin_vals.values())),
                random_ci90=cluster_ci(list(rand_vals.values())),
            )

    # central comparison 3: oracle vs predicted vs random (room above deployable methods)
    comp3 = {}
    for K in (2, 4):
        for q in (8, 4, 2, 1):
            vals = {}
            for strat in ("random", "kinematic", "kinematic_radius_free", "nearest", "oracle"):
                sv = {}
                for st in data:
                    c = st["cells"].get(f"K{K}_q{q}_{strat}")
                    if c:
                        sv[st["state_id"]] = c["mean_delta_assoc"]
                vals[strat] = dict(mean=float(np.mean(list(sv.values()))) if sv else None,
                                    ci90=cluster_ci(list(sv.values())), by_state=sv)
            comp3[f"K{K}_q{q}"] = vals

    # dev vs holdout role split, per cell
    by_role = {}
    for st in data:
        role = st["role"]
        for ck, c in st["cells"].items():
            by_role.setdefault(ck, {"development": [], "holdout": []})[role].append(c["mean_delta_assoc"])

    return dict(fixed_vs_refreshed_random=comp1, predicted_vs_refreshed_random=comp2,
                oracle_vs_predicted_vs_random=comp3, by_role=by_role)


def main():
    fixed = analyze_fixed_set()
    refresh = analyze_refreshed_access()
    out = dict(fixed_set=fixed, refreshed_access=refresh)
    json.dump(out, open(C.DATA_DIR / "analysis_summary_612b.json", "w"), indent=1, default=str)
    print("wrote", C.DATA_DIR / "analysis_summary_612b.json")
    if refresh:
        print(json.dumps(refresh["fixed_vs_refreshed_random"], indent=1))


if __name__ == "__main__":
    main()
