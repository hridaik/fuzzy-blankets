"""Part H: build viewer exemplars for each Part C kick OUTCOME CLASS
(median/best/worst by d_pair-to-pre-kick, + 2 random), synced against the
individual's pre-kick (census) state.
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
KICK_DIR = os.path.join(REPO_ROOT, "data", "kicks")
OUT_AUDIT = os.path.join(VIZ_DIR, "output", "audit")
OUT_OBS = os.path.join(VIZ_DIR, "output", "observable")


def load_rollout(mat_path, n_cells=8):
    d = sio.loadmat(mat_path)
    pos = d["positions"]; sec = d["secretion"]
    N = pos.shape[1]
    a_x = pos.T.reshape(N, 2, n_cells, order="F")
    a_s = sec.T.reshape(N, 4, n_cells, order="F")
    return a_x, a_s, d.get("target_x")


if __name__ == "__main__":
    analysis = json.load(open(os.path.join(KICK_DIR, "kicks_analysis.json")))
    by_outcome = {}
    for r in analysis:
        by_outcome.setdefault(r["outcome"], []).append(r)

    entries = []
    for outcome, items in by_outcome.items():
        # sort by d_pair (all ~0, but keep the rule mechanically)
        items_sorted = sorted(items, key=lambda r: r.get("d_pair_to_pre_kick") or 0)
        picks = {"best": items_sorted[0], "worst": items_sorted[-1],
                 "median": items_sorted[len(items_sorted) // 2]}
        rng = np.random.default_rng(0)
        remaining = [r for r in items if r not in picks.values()]
        if remaining:
            idx = rng.choice(len(remaining), size=min(2, len(remaining)), replace=False)
            for i, ri in enumerate(idx):
                picks[f"random{i+1}"] = remaining[ri]

        for tag, r in picks.items():
            ind = r["individual_idx"]
            kick = r["kick"]
            census_mat = os.path.join(CENSUS_DIR, f"primary_{ind:04d}_N512.mat")
            post_x, post_s, target_x = load_rollout(r["out_mat"])
            pre_x, pre_s, _ = load_rollout(census_mat)

            rd_pre = rollout_to_json_dict(f"pre-kick (ind{ind})", pre_x, pre_s, target_x=target_x)
            rd_post = rollout_to_json_dict(f"post-{kick} (ind{ind})", post_x, post_s, target_x=target_x)
            header = (f"config=Part C kick, outcome={outcome}, kick={kick}\nindividual=primary_{ind:04d}\n"
                      f"engine=fallback_octave_subprocess\nvalidation_status=validated")
            out_name = f"kick_{outcome}_{kick}_ind{ind:04d}_{tag}_audit.html"
            out_audit = os.path.join(OUT_AUDIT, out_name)
            build_html([rd_pre, rd_post], f"Kick: {outcome}/{kick} ind{ind} ({tag})",
                       "VALIDATED: Octave reference oracle", "banner-validated", header, True, out_audit)
            entries.append({"name": f"Kick {outcome}/{kick} ({tag}): ind{ind}",
                             "file": os.path.relpath(out_audit, VIZ_DIR),
                             "engine": "fallback_octave_subprocess", "validation": "validated",
                             "tier": "audit", "notes": f"d_pair={r.get('d_pair_to_pre_kick')}"})

    with open(os.path.join(REPO_ROOT, "data", "kick_exemplar_entries.json"), "w") as f:
        json.dump(entries, f, indent=2, default=str)
    print(f"built {len(entries)} kick exemplar viewers")
