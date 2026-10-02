"""Part B analysis: classification, clustering, identity events, threshold
sensitivity. Run after code/run_census.py's manifest is complete.
"""
import json
import os
import sys
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.stats import norm

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from analysis import (d_target, d_pair, classify_individual, identity_events,
                       cell_type_from_expression, cell_type_from_belief,
                       softmax_cols, TAU_POS_DEFAULT, TAU_BEL_DEFAULT)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS_DIR = os.path.join(REPO_ROOT, "data", "census")


def wilson_interval(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))) / denom
    return (p, max(0, center - half), min(1, center + half))


def load_final_state(mat_path, n_cells=8):
    import scipy.io as sio
    d = sio.loadmat(mat_path)
    pos = d["positions"]; sec = d["secretion"]
    a_x = pos[:, -1].reshape(2, n_cells, order="F")
    a_s = sec[:, -1].reshape(4, n_cells, order="F")
    v = d["v_expect"][:, -1].reshape(n_cells, n_cells, order="F")
    return a_x, a_s, v


def run_analysis(tau_pos=TAU_POS_DEFAULT, tau_bel=TAU_BEL_DEFAULT):
    manifest = json.load(open(os.path.join(CENSUS_DIR, "census_manifest.json")))
    records = []
    for r in manifest["results"]:
        mat_path = r["out_mat"]
        a_x, a_s, v = load_final_state(mat_path)
        label, dist, role_map = classify_individual(a_x, a_s, v, tau_pos=tau_pos,
                                                       tau_bel=tau_bel, stationary=r["stationary"])
        ev = identity_events(v, a_x)
        obs_type = cell_type_from_expression(a_s)
        hid_type = cell_type_from_belief(v)
        agreement = float(np.mean(obs_type == hid_type))
        records.append({
            "individual_id": r["individual_id"], "kind": r["kind"], "idx": r["idx"],
            "label": label, "d_target": dist, "stationary_at_bin": r["stationary_at_bin"],
            "n_bins_used": r["n_bins_used"], "identity_events": ev,
            "type_agreement": agreement, "a_x": a_x, "a_s": a_s, "v": v,
        })
    return records


def cluster_defects(records, tau_pair=TAU_POS_DEFAULT):
    defects = [r for r in records if r["label"] == "DEFECT"]
    n = len(defects)
    if n < 2:
        return defects, np.zeros(n, dtype=int)
    dmat = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = d_pair(defects[i]["a_x"], defects[i]["a_s"], defects[j]["a_x"], defects[j]["a_s"])
            dmat[i, j] = dmat[j, i] = d
    from scipy.spatial.distance import squareform
    condensed = squareform(dmat, checks=False)
    Z = linkage(condensed, method="single")
    clusters = fcluster(Z, t=tau_pair, criterion="distance")
    return defects, clusters


def summarize(records, tau_pair=TAU_POS_DEFAULT, label_suffix=""):
    out = {}
    for kind in ("primary", "secondary", "all"):
        subset = records if kind == "all" else [r for r in records if r["kind"] == kind]
        n = len(subset)
        if n == 0:
            continue
        counts = {}
        for r in subset:
            counts[r["label"]] = counts.get(r["label"], 0) + 1
        wilson = {lab: wilson_interval(c, n) for lab, c in counts.items()}
        out[kind] = {"n": n, "counts": counts, "wilson_95": wilson}
    defects, clusters = cluster_defects(records, tau_pair)
    n_defect_classes = len(set(clusters)) if len(defects) else 0
    out["n_defect_classes"] = n_defect_classes
    out["defect_cluster_sizes"] = {int(c): int((clusters == c).sum()) for c in set(clusters)} if len(defects) else {}
    return out


if __name__ == "__main__":
    records = run_analysis()
    summary = summarize(records)
    print(json.dumps(summary, indent=2, default=str))

    # threshold sensitivity: x0.5, x2
    for mult in (0.5, 2.0):
        recs2 = run_analysis(tau_pos=TAU_POS_DEFAULT * mult, tau_bel=TAU_BEL_DEFAULT)
        s2 = summarize(recs2, tau_pair=TAU_POS_DEFAULT * mult)
        print(f"\n--- tau_pos x{mult} ---")
        print(json.dumps({k: v for k, v in s2.items() if k != "defect_cluster_sizes"}, indent=2, default=str))

    with open(os.path.join(CENSUS_DIR, "census_analysis.json"), "w") as f:
        json.dump({"records_summary": [
            {k: v for k, v in r.items() if k not in ("a_x", "a_s", "v")} for r in records
        ], "summary": summary}, f, indent=2, default=str)
