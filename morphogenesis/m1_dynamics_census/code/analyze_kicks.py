"""Part C analysis: classify each kick outcome against the individual's OWN
pre-kick end-state (RETURNED-SAME-ROLES / RETURNED-RELABELLED / NEW-FORM /
NONCONVERGED), report relaxation timescales.
"""
import json
import os
import sys
import numpy as np
import scipy.io as sio

sys.path.insert(0, os.path.dirname(__file__))
from analysis import d_pair, cell_type_from_expression, TAU_PAIR_DEFAULT

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS_DIR = os.path.join(REPO_ROOT, "data", "census")
KICK_DIR = os.path.join(REPO_ROOT, "data", "kicks")


def load_final(mat_path, n_cells=8):
    d = sio.loadmat(mat_path)
    pos = d["positions"]; sec = d["secretion"]
    return (pos[:, -1].reshape(2, n_cells, order="F"),
            sec[:, -1].reshape(4, n_cells, order="F"))


def role_map_from_expression(a_x, a_s):
    """Cheap role identity: which cell (by type+nearest position) plays each
    role, for RETURNED-SAME-ROLES vs RETURNED-RELABELLED discrimination."""
    return cell_type_from_expression(a_s)


def classify_kick_outcome(pre_x, pre_s, post_x, post_s, tau_pair=TAU_PAIR_DEFAULT,
                            stationary=True):
    if not stationary:
        return "NONCONVERGED", None
    d = d_pair(pre_x, pre_s, post_x, post_s)
    if d >= tau_pair:
        return "NEW-FORM", d
    # within tau_pair of pre-kick state -- check if roles (which physical
    # cell-position-slot pairing) are the same or permuted among same-type cells
    pre_type = cell_type_from_expression(pre_s)
    post_type = cell_type_from_expression(post_s)
    # nearest-cell correspondence (by position) to check role continuity
    cost = np.linalg.norm(pre_x[:, :, None] - post_x[:, None, :], axis=0)
    from scipy.optimize import linear_sum_assignment
    ri, ci = linear_sum_assignment(cost)
    same_roles = np.all(pre_type[ri] == post_type[ci]) and np.all(ri == ci)
    label = "RETURNED-SAME-ROLES" if same_roles else "RETURNED-RELABELLED"
    return label, d


def relaxation_fit(free_energy_J):
    """Fit a simple exponential relaxation to |J - J_inf| after a kick;
    returns the fitted timescale (bins) or None if fit fails."""
    j = np.asarray(free_energy_J).ravel()
    if len(j) < 10:
        return None
    j_inf = j[-min(20, len(j)):].mean()
    resid = np.abs(j - j_inf)
    resid = resid[resid > 1e-8]
    if len(resid) < 5:
        return None
    t = np.arange(len(resid))
    log_resid = np.log(resid + 1e-12)
    # simple linear fit of log(resid) vs t -> slope = -1/tau
    A = np.vstack([t, np.ones_like(t)]).T
    try:
        slope, intercept = np.linalg.lstsq(A, log_resid, rcond=None)[0]
    except Exception:
        return None
    if slope >= 0:
        return None
    return float(-1.0 / slope)


def run():
    manifest = json.load(open(os.path.join(KICK_DIR, "kicks_manifest.json")))
    results = []
    for r in manifest["results"]:
        if r["status"] != "ok":
            results.append({**r, "outcome": "ERROR"})
            continue
        census_mat = os.path.join(CENSUS_DIR, f"primary_{r['individual_idx']:04d}_N512.mat")
        pre_x, pre_s = load_final(census_mat)
        post_x, post_s = load_final(r["out_mat"])
        label, d = classify_kick_outcome(pre_x, pre_s, post_x, post_s,
                                           stationary=r["stationary"])
        mat = sio.loadmat(r["out_mat"])
        tau = relaxation_fit(mat["free_energy_J"])
        results.append({**r, "outcome": label, "d_pair_to_pre_kick": d,
                         "relaxation_tau_bins": tau})
    return results


if __name__ == "__main__":
    results = run()
    counts = {}
    for r in results:
        key = (r["kick"], r["outcome"])
        counts[key] = counts.get(key, 0) + 1
    for k, v in sorted(counts.items()):
        print(k, v)
    with open(os.path.join(KICK_DIR, "kicks_analysis.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
