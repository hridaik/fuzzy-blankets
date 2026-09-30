"""Post-batch analysis: for each perturbation trace, report final Hungarian
distance to template, whether phenotype persists at N=512 (distance still
elevated vs baseline), and ramp-width sensitivity. Prints a markdown table
to fill into PERTURBATIONS_EXECUTED.md.
"""
import glob
import os
import sys
import numpy as np
import scipy.io as sio

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIZ_DIR = os.path.join(REPO_ROOT, "..", "viz")
sys.path.insert(0, VIZ_DIR)
from build_index import hungarian_distance_type_constrained  # noqa: E402

PERT_DIR = os.path.join(REPO_ROOT, "data", "oracle_traces", "perturbations")
BASELINE_N32 = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "data",
                             "oracle_traces", "vanilla8_N32_seed0.mat")
BASELINE_N512 = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "data",
                              "oracle_traces", "vanilla8_N512_seed0.mat")


def final_dist(path, n_cells=8):
    d = sio.loadmat(path)
    pos = d["positions"]
    N = pos.shape[1]
    a_x = pos.T.reshape(N, 2, n_cells, order="F")[-1]
    target_x = d["target_x"]
    return hungarian_distance_type_constrained(a_x, target_x, None, None)


def main():
    base32 = final_dist(BASELINE_N32) if os.path.exists(BASELINE_N32) else None
    base512 = final_dist(BASELINE_N512) if os.path.exists(BASELINE_N512) else None
    print(f"baseline N=32 dist={base32}, N=512 dist={base512}")

    files = sorted(glob.glob(os.path.join(PERT_DIR, "*.mat")))
    rows = []
    for fpath in files:
        name = os.path.basename(fpath).replace(".mat", "")
        try:
            d = final_dist(fpath)
        except Exception as e:
            print(f"SKIP {name}: {e}")
            continue
        rows.append((name, d))

    print("\n| perturbation | final Hungarian dist | vs baseline |")
    print("|---|---|---|")
    for name, d in rows:
        n_bins = 512 if "N512" in name else 32
        base = base512 if n_bins == 512 else base32
        rel = f"{d/base:.2f}x" if base else "n/a"
        print(f"| {name} | {d:.4f} | {rel} |")


if __name__ == "__main__":
    main()
