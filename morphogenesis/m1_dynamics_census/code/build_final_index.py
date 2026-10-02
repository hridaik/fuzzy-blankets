"""Consolidates all exemplar entries (census, kicks, withdrawal, sham) into
one index.html, per Part H."""
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIZ_DIR = os.path.join(REPO_ROOT, "..", "viz")
sys.path.insert(0, VIZ_DIR)
from build_index import build_index  # noqa: E402

RULE_TEXT = (
    "Per batch: median, best and worst by the declared hidden-tier metric "
    "(d_target for census; d_pair-to-pre-kick for Part C; d_pair to the "
    "relevant twin for Part D/E), plus 2 uniformly random picks (seed=0, "
    "numpy default_rng). Recorded per-batch in "
    "data/*_exemplar_selection.json / *_exemplar_entries.json."
)


def load_entries(path):
    if os.path.exists(path):
        return json.load(open(path))
    return []


if __name__ == "__main__":
    entries = []
    # census (built directly, not via a json file -- reconstruct from disk)
    census_sel_path = os.path.join(REPO_ROOT, "data", "census_exemplar_selection.json")
    if os.path.exists(census_sel_path):
        sel = json.load(open(census_sel_path))
        for tag in ("best", "worst", "median"):
            entries.append({"name": f"Census {tag}", "file": f"output/audit/census_{sel[tag]}_{tag}_audit.html",
                             "engine": "fallback_octave_subprocess", "validation": "validated", "tier": "audit"})
        for i, ind_id in enumerate(sel["random"]):
            entries.append({"name": f"Census random{i+1}", "file": f"output/audit/census_{ind_id}_random{i+1}_audit.html",
                             "engine": "fallback_octave_subprocess", "validation": "validated", "tier": "audit"})

    entries += load_entries(os.path.join(REPO_ROOT, "data", "kick_exemplar_entries.json"))
    entries += load_entries(os.path.join(REPO_ROOT, "data", "withdrawal_sham_exemplar_entries.json"))

    out_path = os.path.join(VIZ_DIR, "index.html")
    build_index(entries, out_path, RULE_TEXT)
    print(f"index.html built with {len(entries)} entries at {out_path}")
