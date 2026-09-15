"""Build interactive_demo/v2/data/tab3_control.json.

Pure re-export of the existing V1/V2/V3 demo bundles at
interactive_demo/data/seed16__{method}__cw.json (target = clockwise turn,
the majority target in the primary manifest). Same seed-16 flock, same
timeline.identify=6 for every method (single fixed interior, only the
control policy differs) -- exactly the "interface structure matters" story.

No science is rerun: trajectory, roles, actuators, per-timestep metrics,
summary and ensemble numbers are copied verbatim from the frozen bundles
already used by the original interactive demo (interactive_demo/README.md
documents the schema and interactive_demo/data/export_scenarios.py /
verify_bundles.py as their generator + independent-recompute check).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "interactive_demo/data"
OUT = Path(__file__).resolve().parents[2] / "data" / "tab3_control.json"

manifest = json.load(open(DATA / "manifest.json"))
methods = manifest["primary_methods"]

PRIMARY = {"no_control", "fiedler_boundary", "random_exterior", "connected_patch",
           "sparse_interface_multicover", "full_dynamical_shell"}

bundles = {}
shared_lattice = None
shared_roles = None
shared_timeline = None
for m in methods:
    mid = m["id"]
    d = json.load(open(DATA / f"seed16__{mid}__cw.json"))
    if shared_lattice is None:
        shared_lattice = d["lattice"]
        shared_roles = d["roles"]
        shared_timeline = d["timeline"]
        shared_neighbors = d["neighbors"]
        shared_initial_heading = d["initial_heading"]
        shared_target_heading = d["target_heading"]
    else:
        assert d["roles"]["core"] == shared_roles["core"], f"{mid}: interior changed across methods"
        assert d["timeline"]["identify"] == shared_timeline["identify"]
    bundles[mid] = {
        "label": m["label"], "subtitle": m["subtitle"], "short": m["short"],
        "diagnostic": m["diagnostic"], "tier": "primary" if mid in PRIMARY else "more",
        "actuators": d["actuators"],
        "headings": d["trajectory"],
        "metrics": d["metrics"],
        "summary": d["summary"],
        "ensemble": d["ensemble"],
        "why": d.get("why"),
    }

out = {
    "provenance": {
        "source": "interactive_demo/data/seed16__{method}__cw.json (V1-V3 sparse-interface-control demo bundles)",
        "generator": "interactive_demo/data/export_scenarios.py, independently checked by verify_bundles.py",
        "seed": 16, "target": "cw (90 degree clockwise turn)",
        "note": "One fixed interior (roles.core), identified once at t=identify, shared across every method below -- only the actuator-selection policy differs.",
    },
    "lattice": shared_lattice,
    "neighbors": shared_neighbors,
    "roles": {"interior": shared_roles["core"], "dynamical_shell": shared_roles["dynamic_shell"],
              "fiedler": shared_roles["fiedler"]},
    "timeline": shared_timeline,
    "initial_heading": shared_initial_heading,
    "target_heading": shared_target_heading,
    "methods": bundles,
    "method_order": [m["id"] for m in methods],
    "default_method": "sparse_interface_multicover",
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out))
print("wrote", OUT, OUT.stat().st_size, "bytes")
