"""Builds synced-compare viewers (perturbed vs vanilla baseline) for every
Part C perturbation run, plus index.html, per the exemplar rule in
viz/VIEWER.md. Run after code/run_perturbation_batch.py completes.
"""
import glob
import json
import os
import sys
import numpy as np
import scipy.io as sio

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIZ_DIR = os.path.join(REPO_ROOT, "..", "viz")
sys.path.insert(0, VIZ_DIR)
from build_viewer import rollout_to_json_dict, build_html  # noqa: E402
from build_index import build_index, select_exemplars, hungarian_distance_type_constrained  # noqa: E402

PERT_DIR = os.path.join(REPO_ROOT, "data", "oracle_traces", "perturbations")
BASELINE_N32 = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "data",
                             "oracle_traces", "vanilla8_N32_seed0.mat")
BASELINE_N512 = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "data",
                              "oracle_traces", "vanilla8_N512_seed0.mat")

OUT_AUDIT = os.path.join(VIZ_DIR, "output", "audit")
OUT_OBS = os.path.join(VIZ_DIR, "output", "observable")


def load_rollout(path, n_cells=8):
    d = sio.loadmat(path)
    pos = d["positions"]
    sec = d["secretion"]
    N = pos.shape[1]
    a_x = pos.T.reshape(N, 2, n_cells, order="F")
    a_s = sec.T.reshape(N, 4, n_cells, order="F")
    target_x = d.get("target_x")
    return a_x, a_s, target_x, d


def main():
    os.makedirs(OUT_AUDIT, exist_ok=True)
    os.makedirs(OUT_OBS, exist_ok=True)

    files = sorted(glob.glob(os.path.join(PERT_DIR, "*.mat")))
    files = [f for f in files if not f.endswith("batch_results.json")]
    print(f"{len(files)} perturbation traces found")

    index_entries = []
    metrics = {}

    for fpath in files:
        name = os.path.basename(fpath).replace(".mat", "")
        n_bins = 512 if "N512" in name else 32
        baseline_path = BASELINE_N512 if n_bins == 512 else BASELINE_N32
        if not os.path.exists(baseline_path):
            continue
        try:
            a_x_p, a_s_p, target_x, d_p = load_rollout(fpath)
            a_x_b, a_s_b, _, _ = load_rollout(baseline_path)
        except Exception as e:
            print(f"  SKIP {name}: {e}")
            continue

        final_dist = hungarian_distance_type_constrained(
            a_x_p[-1], target_x, None, None) if target_x is not None else 0.0
        metrics[name] = final_dist

        rd_pert = rollout_to_json_dict(f"{name} (perturbed)", a_x_p, a_s_p, target_x=target_x)
        rd_base = rollout_to_json_dict("vanilla-8 baseline (unperturbed)", a_x_b, a_s_b, target_x=target_x)

        header = (f"config=vanilla8, perturbation={name}\n"
                  f"engine=fallback_octave_subprocess (SPM12 spm_ADEM via Octave 10.3.0)\n"
                  f"seed=0\nvalidation_status=validated (runs the real Octave oracle)\n"
                  f"N={n_bins} bins; final Hungarian distance to template={final_dist:.4f}")
        out_name = f"perturbation_{name}_audit.html"
        try:
            build_html([rd_pert, rd_base], f"Perturbation: {name}",
                       "VALIDATED: runs the Octave reference oracle directly",
                       "banner-validated", header, True,
                       os.path.join(OUT_AUDIT, out_name))
            index_entries.append({"name": name, "file": f"audit/{out_name}",
                                   "engine": "fallback_octave_subprocess",
                                   "validation": "validated", "tier": "audit",
                                   "notes": f"N={n_bins}, dist={final_dist:.3f}"})
        except Exception as e:
            print(f"  BUILD FAIL {name}: {e}")

    if metrics:
        sel = select_exemplars(metrics, seed=0)
        with open(os.path.join(VIZ_DIR, "output", "exemplar_selection.json"), "w") as f:
            json.dump(sel, f, indent=2)
        print("exemplar selection:", sel)

    rule_text = ("For each batch of same-kind runs: median, best, worst by "
                 "type-constrained Hungarian distance to template (hidden-tier "
                 "metric), plus 2 uniformly random picks (seed=0). See "
                 "viz/output/exemplar_selection.json for this batch's picks.")
    build_index(index_entries, os.path.join(VIZ_DIR, "index.html"), rule_text)
    print(f"index.html built with {len(index_entries)} entries")


if __name__ == "__main__":
    main()
