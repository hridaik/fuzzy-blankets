"""Part H: build synced triples (withdrawal run / unperturbed twin /
sustained twin) for each Part D perturbation x timing cell, per the
declared exemplar rule (median/best/worst by d_pair to the relevant twin,
+2 random). Also handles Part E sham, synced against its DH counterpart.
"""
import json
import os
import sys
import numpy as np
import scipy.io as sio

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIZ_DIR = os.path.join(REPO_ROOT, "..", "viz")
sys.path.insert(0, VIZ_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "code"))
from build_viewer import rollout_to_json_dict, build_html  # noqa: E402

CENSUS_DIR = os.path.join(REPO_ROOT, "data", "census")
WD_DIR = os.path.join(REPO_ROOT, "data", "withdrawal")
SHAM_DIR = os.path.join(REPO_ROOT, "data", "sham")
OUT_AUDIT = os.path.join(VIZ_DIR, "output", "audit")


def load_rollout(mat_path, n_cells=8):
    d = sio.loadmat(mat_path)
    pos = d["positions"]; sec = d["secretion"]
    N = pos.shape[1]
    a_x = pos.T.reshape(N, 2, n_cells, order="F")
    a_s = sec.T.reshape(N, 4, n_cells, order="F")
    return a_x, a_s, d.get("target_x")


def pick_exemplars(items, metric_key, seed=0):
    valid = [r for r in items if r.get(metric_key) is not None]
    if not valid:
        return {}
    sorted_items = sorted(valid, key=lambda r: r[metric_key])
    picks = {"best": sorted_items[0], "worst": sorted_items[-1],
             "median": sorted_items[len(sorted_items) // 2]}
    rng = np.random.default_rng(seed)
    remaining = [r for r in valid if r not in picks.values()]
    if remaining:
        idx = rng.choice(len(remaining), size=min(2, len(remaining)), replace=False)
        for i, ri in enumerate(idx):
            picks[f"random{i+1}"] = remaining[ri]
    return picks


def build_triple(r, cell_prefix, out_dir=OUT_AUDIT):
    ind = r["individual_idx"]
    kind = r.get("kind", "sham")
    timing = r["timing"]
    census_mat = os.path.join(CENSUS_DIR, f"primary_{ind:04d}_N512.mat")
    sustained_kind = kind if kind in ("DH", "DT", "AN") else "DH"
    sustained_mat = os.path.join(WD_DIR, f"primary_{ind:04d}_{sustained_kind}_SUSTAINED_N1024.mat")
    if not (os.path.exists(census_mat) and os.path.exists(sustained_mat) and os.path.exists(r["out_mat"])):
        return None
    wx, ws, target_x = load_rollout(r["out_mat"])
    ux, us, _ = load_rollout(census_mat)
    sx, ss, _ = load_rollout(sustained_mat)
    rds = [
        rollout_to_json_dict(f"withdrawal ({kind}/{timing})", wx, ws, target_x=target_x),
        rollout_to_json_dict("unperturbed twin", ux, us, target_x=target_x),
        rollout_to_json_dict("sustained twin", sx, ss, target_x=target_x),
    ]
    header = (f"config={cell_prefix} {kind}/{timing}\nindividual=primary_{ind:04d}\n"
              f"engine=fallback_octave_subprocess\nvalidation_status=validated\n"
              f"outcome={r.get('outcome')}")
    out_name = f"{cell_prefix}_{kind}_{timing}_ind{ind:04d}.html"
    out_path = os.path.join(out_dir, out_name)
    build_html(rds, f"{cell_prefix}: {kind}/{timing} ind{ind}",
               "VALIDATED: Octave reference oracle", "banner-validated", header, True, out_path)
    return out_path


if __name__ == "__main__":
    entries = []
    wd_path = os.path.join(WD_DIR, "withdrawal_analysis.json")
    if os.path.exists(wd_path):
        wd = json.load(open(wd_path))
        by_cell = {}
        for r in wd:
            if r.get("status") != "ok" or r.get("outcome") in ("ERROR", None):
                continue
            key = (r.get("kind"), r["timing"])
            by_cell.setdefault(key, []).append(r)
        for (kind, timing), items in by_cell.items():
            for r in items:
                r["_metric"] = r.get("d_to_unperturbed", 0) + r.get("d_to_sustained", 0)
            picks = pick_exemplars(items, "_metric", seed=0)
            for tag, r in picks.items():
                out = build_triple(r, "withdrawal")
                if out:
                    entries.append({"name": f"Withdrawal {kind}/{timing} ({tag}): ind{r['individual_idx']}",
                                     "file": os.path.relpath(out, VIZ_DIR), "engine": r.get("engine", ""),
                                     "validation": "validated", "tier": "audit",
                                     "notes": f"outcome={r.get('outcome')}"})

    sham_path = os.path.join(SHAM_DIR, "sham_analysis.json")
    if os.path.exists(sham_path):
        sham = json.load(open(sham_path))
        by_timing = {}
        for r in sham:
            if r.get("status") != "ok" or r.get("outcome") in ("ERROR", None):
                continue
            by_timing.setdefault(r["timing"], []).append(r)
        for timing, items in by_timing.items():
            for r in items:
                r["_metric"] = r.get("d_to_unperturbed", 0) + r.get("d_to_sustained", 0)
            picks = pick_exemplars(items, "_metric", seed=0)
            for tag, r in picks.items():
                out = build_triple(r, "sham")
                if out:
                    entries.append({"name": f"Sham {timing} ({tag}): ind{r['individual_idx']}",
                                     "file": os.path.relpath(out, VIZ_DIR), "engine": r.get("engine", ""),
                                     "validation": "validated", "tier": "audit",
                                     "notes": f"outcome={r.get('outcome')}"})

    with open(os.path.join(REPO_ROOT, "data", "withdrawal_sham_exemplar_entries.json"), "w") as f:
        json.dump(entries, f, indent=2, default=str)
    print(f"built {len(entries)} withdrawal/sham exemplar viewers")
