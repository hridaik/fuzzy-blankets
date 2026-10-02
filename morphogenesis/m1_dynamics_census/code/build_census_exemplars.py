"""Part H: build viewer exemplars for the Part B census, per the declared
exemplar rule (median, best, worst by d_target, plus 2 uniformly random
picks, seed recorded)."""
import json
import os
import sys
import numpy as np
import scipy.io as sio

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIZ_DIR = os.path.join(REPO_ROOT, "..", "viz")
sys.path.insert(0, VIZ_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "code"))
from build_viewer import rollout_to_json_dict, add_image_panel, build_html  # noqa: E402
from build_index import build_index  # noqa: E402
from analysis import d_target, P_X, P_S  # noqa: E402

CENSUS_DIR = os.path.join(REPO_ROOT, "data", "census")
OBSLADDER_DIR = os.path.join(REPO_ROOT, "data", "obsladder", "census")
OUT_AUDIT = os.path.join(VIZ_DIR, "output", "audit")
OUT_OBS = os.path.join(VIZ_DIR, "output", "observable")
os.makedirs(OUT_AUDIT, exist_ok=True)
os.makedirs(OUT_OBS, exist_ok=True)


def load_rollout(mat_path, n_cells=8):
    d = sio.loadmat(mat_path)
    pos = d["positions"]; sec = d["secretion"]
    N = pos.shape[1]
    a_x = pos.T.reshape(N, 2, n_cells, order="F")
    a_s = sec.T.reshape(N, 4, n_cells, order="F")
    return a_x, a_s, d.get("target_x")


def select_exemplars(manifest, seed=0):
    metrics = {}
    for r in manifest["results"]:
        mat = sio.loadmat(r["out_mat"])
        a_x = mat["positions"][:, -1].reshape(2, 8, order="F")
        a_s = mat["secretion"][:, -1].reshape(4, 8, order="F")
        dist, _, _, _ = d_target(a_x, a_s)
        metrics[r["individual_id"]] = (dist, r["out_mat"])
    ids = list(metrics.keys())
    vals = np.array([metrics[i][0] for i in ids])
    order = np.argsort(vals)
    best, worst, median = ids[order[0]], ids[order[-1]], ids[order[len(order) // 2]]
    rng = np.random.default_rng(seed)
    remaining = [i for i in ids if i not in (best, worst, median)]
    random_picks = list(rng.choice(remaining, size=2, replace=False))
    return {"best": best, "worst": worst, "median": median, "random": random_picks,
            "seed": seed, "metrics": metrics}


def build_exemplar_pair(ind_id, mat_path, tag):
    a_x, a_s, target_x = load_rollout(mat_path)
    header = (f"config=census {tag}\nindividual={ind_id}\n"
              f"engine=fallback_octave_subprocess\nvalidation_status=validated\n"
              f"N={a_x.shape[0]} bins")
    rd_audit = rollout_to_json_dict(f"{ind_id} ({tag})", a_x, a_s, target_x=target_x)
    npz_path = os.path.join(OBSLADDER_DIR, f"{ind_id}.npz")
    if os.path.exists(npz_path):
        npz = np.load(npz_path)
        rd_audit = add_image_panel(rd_audit, npz["O3a"], image_stride=8)
    out_audit = os.path.join(OUT_AUDIT, f"census_{ind_id}_{tag}_audit.html")
    build_html([rd_audit], f"Census exemplar: {ind_id} ({tag})",
               "VALIDATED: Octave reference oracle", "banner-validated", header, True, out_audit)

    rd_obs = rollout_to_json_dict(f"{ind_id} ({tag})", a_x, a_s)
    out_obs = os.path.join(OUT_OBS, f"census_{ind_id}_{tag}_observable.html")
    build_html([rd_obs], f"Census exemplar: {ind_id} ({tag}) [observable]",
               "VALIDATED: Octave reference oracle", "banner-validated", header, False, out_obs)
    return out_audit, out_obs


if __name__ == "__main__":
    manifest = json.load(open(os.path.join(CENSUS_DIR, "census_manifest.json")))
    sel = select_exemplars(manifest, seed=0)
    print("Exemplar selection:", {k: v for k, v in sel.items() if k != "metrics"})

    entries = []
    for tag in ("best", "worst", "median"):
        ind_id = sel[tag]
        mat_path = sel["metrics"][ind_id][1]
        out_audit, out_obs = build_exemplar_pair(ind_id, mat_path, tag)
        entries.append({"name": f"Census {tag}: {ind_id}", "file": os.path.relpath(out_audit, VIZ_DIR),
                         "engine": "fallback_octave_subprocess", "validation": "validated", "tier": "audit",
                         "notes": f"d_target={sel['metrics'][ind_id][0]:.4f}"})
    for i, ind_id in enumerate(sel["random"]):
        mat_path = sel["metrics"][ind_id][1]
        out_audit, out_obs = build_exemplar_pair(ind_id, mat_path, f"random{i+1}")
        entries.append({"name": f"Census random{i+1}: {ind_id}", "file": os.path.relpath(out_audit, VIZ_DIR),
                         "engine": "fallback_octave_subprocess", "validation": "validated", "tier": "audit",
                         "notes": f"d_target={sel['metrics'][ind_id][0]:.4f}, seed={sel['seed']}"})

    with open(os.path.join(REPO_ROOT, "data", "census_exemplar_selection.json"), "w") as f:
        json.dump({k: v for k, v in sel.items() if k != "metrics"}, f, indent=2, default=str)

    print(json.dumps(entries, indent=2))
