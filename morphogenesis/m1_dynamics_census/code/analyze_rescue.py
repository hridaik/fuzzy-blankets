"""Part A analysis: which rescue version (R-text vs R-caption) reproduces
the published description, and whether a position switch occurs.
"""
import json
import os
import sys
import numpy as np
import scipy.io as sio

sys.path.insert(0, os.path.dirname(__file__))
from analysis import d_target, d_pair, P_X
from analyze_census import wilson_interval

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESCUE_DIR = os.path.join(REPO_ROOT, "data", "rescue")
CENSUS_DIR = os.path.join(REPO_ROOT, "data", "census")
ANOMALOUS_CELL_0BASED = 4  # 1-based cell 5 -> 0-based index 4


def load_final(mat_path, n_cells=8):
    d = sio.loadmat(mat_path)
    pos = d["positions"]; sec = d["secretion"]
    return (pos[:, -1].reshape(2, n_cells, order="F"),
            sec[:, -1].reshape(4, n_cells, order="F"))


def position_switch_check(unpert_x, unpert_s, rescued_x, rescued_s, anomalous_cell=ANOMALOUS_CELL_0BASED):
    """Checks whether the role the anomalous cell held in the UNPERTURBED
    twin is now held by a DIFFERENT cell in the rescued end-state (nearest-
    neighbour position correspondence)."""
    cost = np.linalg.norm(unpert_x[:, :, None] - rescued_x[:, None, :], axis=0)
    from scipy.optimize import linear_sum_assignment
    ri, ci = linear_sum_assignment(cost)
    # which rescued cell corresponds to the anomalous cell's UNPERTURBED slot?
    corresponding = ci[list(ri).index(anomalous_cell)]
    return corresponding != anomalous_cell, int(corresponding)


def run():
    manifest = json.load(open(os.path.join(RESCUE_DIR, "rescue_manifest.json")))
    rows = []
    for r in manifest["results"]:
        if r.get("status") != "ok" or not os.path.exists(r.get("out_mat", "")):
            continue
        ind = r["individual"]
        x, s = load_final(r["out_mat"])
        dist, role_map, ftype, n_mismatch = d_target(x, s)

        census_mat = os.path.join(CENSUS_DIR, f"primary_{ind:04d}_N512.mat")
        switched, corr = (None, None)
        if os.path.exists(census_mat):
            ux, us = load_final(census_mat)
            d_to_unpert = d_pair(x, s, ux, us)
            switched, corr = position_switch_check(ux, us, x, s)
        else:
            d_to_unpert = None

        rows.append({"tag": r["tag"], "individual": ind, "d_target": dist,
                     "n_type_mismatch": n_mismatch, "d_to_unperturbed_twin": d_to_unpert,
                     "position_switch": switched, "switch_partner_cell": corr})
    return rows


if __name__ == "__main__":
    rows = run()
    by_tag = {}
    for r in rows:
        by_tag.setdefault(r["tag"], []).append(r)

    print(f"{'tag':25s} {'n':>3s} {'mean d_target':>14s} {'mean d_to_unpert':>17s} {'switch rate':>12s}")
    summary = {}
    for tag, items in sorted(by_tag.items()):
        dts = [i["d_target"] for i in items]
        dus = [i["d_to_unperturbed_twin"] for i in items if i["d_to_unperturbed_twin"] is not None]
        switches = [i["position_switch"] for i in items if i["position_switch"] is not None]
        n_switch = sum(switches)
        p, lo, hi = wilson_interval(n_switch, len(switches)) if switches else (0, 0, 0)
        print(f"{tag:25s} {len(items):>3d} {np.mean(dts):>14.4f} "
              f"{np.mean(dus) if dus else float('nan'):>17.4f} "
              f"{n_switch}/{len(switches)} [{lo:.2f},{hi:.2f}]")
        summary[tag] = {"n": len(items), "mean_d_target": float(np.mean(dts)),
                         "mean_d_to_unperturbed": float(np.mean(dus)) if dus else None,
                         "switch_rate": [n_switch, len(switches), lo, hi]}

    with open(os.path.join(RESCUE_DIR, "rescue_analysis.json"), "w") as f:
        json.dump({"rows": rows, "summary": summary}, f, indent=2, default=str)
