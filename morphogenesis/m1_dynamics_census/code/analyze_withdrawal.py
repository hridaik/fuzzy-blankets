"""Part D/E analysis: classify each withdrawal/sham run against its two
twins (UNPERTURBED from Part B, SUSTAINED from Part D), using d_pair.
"""
import json
import os
import sys
import numpy as np
import scipy.io as sio

sys.path.insert(0, os.path.dirname(__file__))
from analysis import d_pair, TAU_PAIR_DEFAULT

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS_DIR = os.path.join(REPO_ROOT, "data", "census")
WD_DIR = os.path.join(REPO_ROOT, "data", "withdrawal")
SHAM_DIR = os.path.join(REPO_ROOT, "data", "sham")


def load_final(mat_path, n_cells=8):
    d = sio.loadmat(mat_path)
    pos = d["positions"]; sec = d["secretion"]
    return (pos[:, -1].reshape(2, n_cells, order="F"),
            sec[:, -1].reshape(4, n_cells, order="F"))


def classify_withdrawal(run_x, run_s, unpert_x, unpert_s, sustained_x, sustained_s,
                          tau_pair=TAU_PAIR_DEFAULT, stationary=True):
    if not stationary:
        return "NONCONVERGED", None, None
    d_un = d_pair(run_x, run_s, unpert_x, unpert_s)
    d_sus = d_pair(run_x, run_s, sustained_x, sustained_s)
    close_un = d_un < tau_pair
    close_sus = d_sus < tau_pair
    if close_un and close_sus:
        label = "AMBIGUOUS-BOTH"  # perturbation had no durable effect to begin with
    elif close_un:
        label = "REVERTED"
    elif close_sus:
        label = "PERSISTED"
    else:
        label = "NOVEL"
    return label, d_un, d_sus


def run_for_dir(data_dir, manifest_names, is_sham=False):
    """manifest_names: str or list of manifest filenames to merge (BUGFIX:
    run_withdrawal.py's orchestrated invocation writes separate
    'withdrawal_manifest_sustained.json' / '_withdrawal.json' files, not a
    single '_all.json' -- this merges them)."""
    if isinstance(manifest_names, str):
        manifest_names = [manifest_names]
    all_results = []
    for name in manifest_names:
        manifest_path = os.path.join(data_dir, name)
        if os.path.exists(manifest_path):
            all_results.extend(json.load(open(manifest_path))["results"])
    if not all_results:
        return []
    results = []
    for r in all_results:
        if r.get("status") != "ok":
            results.append({**r, "outcome": "ERROR"})
            continue
        ind = r["individual_idx"]
        timing = r["timing"]
        if timing == "SUSTAINED":
            continue  # twins, not classified against themselves
        kind = r.get("kind", "DH" if is_sham else None)
        census_mat = os.path.join(CENSUS_DIR, f"primary_{ind:04d}_N512.mat")
        if not os.path.exists(census_mat):
            census_mat = os.path.join(CENSUS_DIR, f"primary_{ind:04d}_N2048.mat")
        if not os.path.exists(census_mat):
            results.append({**r, "outcome": "MISSING-UNPERTURBED-TWIN"})
            continue
        sustained_kind = kind if kind in ("DH", "DT", "AN") else "DH"
        sustained_mat = os.path.join(WD_DIR, f"primary_{ind:04d}_{sustained_kind}_SUSTAINED_N1024.mat")
        if not os.path.exists(sustained_mat):
            results.append({**r, "outcome": "MISSING-SUSTAINED-TWIN"})
            continue
        run_x, run_s = load_final(r["out_mat"])
        un_x, un_s = load_final(census_mat)
        sus_x, sus_s = load_final(sustained_mat)
        label, d_un, d_sus = classify_withdrawal(run_x, run_s, un_x, un_s, sus_x, sus_s,
                                                    stationary=r.get("stationary", True))
        results.append({**r, "outcome": label, "d_to_unperturbed": d_un, "d_to_sustained": d_sus})
    return results


if __name__ == "__main__":
    wd_results = run_for_dir(WD_DIR, ["withdrawal_manifest_sustained.json",
                                       "withdrawal_manifest_withdrawal.json",
                                       "withdrawal_manifest_all.json"])
    sham_results = run_for_dir(SHAM_DIR, "sham_manifest.json", is_sham=True)

    from collections import Counter
    wd_counts = Counter((r.get("kind"), r.get("timing"), r["outcome"]) for r in wd_results)
    sham_counts = Counter((r.get("timing"), r["outcome"]) for r in sham_results)
    print("Withdrawal outcomes:")
    for k, v in sorted(wd_counts.items(), key=lambda x: str(x[0])):
        print(" ", k, v)
    print("Sham outcomes:")
    for k, v in sorted(sham_counts.items(), key=lambda x: str(x[0])):
        print(" ", k, v)

    with open(os.path.join(WD_DIR, "withdrawal_analysis.json"), "w") as f:
        json.dump(wd_results, f, indent=2, default=str)
    with open(os.path.join(SHAM_DIR, "sham_analysis.json"), "w") as f:
        json.dump(sham_results, f, indent=2, default=str)
