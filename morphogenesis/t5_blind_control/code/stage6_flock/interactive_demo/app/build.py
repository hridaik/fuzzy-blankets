"""Inlines interactive_demo/data/*.json into app/index.html's
/*__DEMO_DATA__*/, /*__REFINEMENT_DATA__*/ and /*__REFINEMENT_VIZ__*/
placeholders, producing a single self-contained build/index.html that opens
with no server (file://, no CORS issues)."""
from __future__ import annotations

import json
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DEMO_DIR = APP_DIR.parent
DATA_DIR = DEMO_DIR / "data"
BUILD_DIR = DEMO_DIR / "build"


def inline(template: str, placeholder: str, payload: str) -> str:
    pattern = r"/\*__" + placeholder + r"__\*/.*?/\*__END_" + placeholder + r"__\*/"
    out = re.sub(pattern, lambda m: payload, template, flags=re.S)
    assert out != template, f"placeholder {placeholder} not found -- check app/index.html"
    return out


def main():
    manifest = json.loads((DATA_DIR / "manifest.json").read_text())
    scenarios = {}
    for entry in manifest["primary_scenarios"] + manifest["canonical_scenarios"]:
        sid = entry["scenario_id"]
        scenarios[sid] = json.loads((DATA_DIR / f"{sid}.json").read_text())
    demo_payload = json.dumps(dict(manifest=manifest, scenarios=scenarios), separators=(",", ":"))

    refinement_path = DATA_DIR / "refinement_bundle.json"
    refinement_payload = refinement_path.read_text() if refinement_path.exists() else "null"
    viz_path = DATA_DIR / "refinement_viz_data.json"
    viz_payload = viz_path.read_text() if viz_path.exists() else "null"
    # Stage 6.6 "Collective Landscape" tab: a separate bundle produced by
    # stage6_6_collective_landscape/code/export_demo_data.py (its own
    # generator, independent of derive_refinement_viz_data.py's pipeline).
    # Given its own 4th placeholder rather than folded into REFINEMENT_VIZ's
    # JSON, so each science pipeline keeps writing/owning one file and this
    # script never has to merge two independently-generated JSON trees by
    # hand -- see STAGE6_6_VISUALIZATION_NOTES.md "Part 1 -- data flow".
    landscape_path = DATA_DIR / "collective_landscape_bundle.json"
    landscape_payload = landscape_path.read_text() if landscape_path.exists() else "null"

    # Stage 6.7 "Blind Boundary & Causal Interface" toggle inside the
    # Collective Landscape tab: its own bundle, own generator
    # (stage6_7_blind_boundary/code/export_demo_data_67.py), own placeholder
    # -- same "each pipeline owns one file" convention as LANDSCAPE_DATA above.
    stage67_path = DATA_DIR / "stage6_7_bundle.json"
    stage67_payload = stage67_path.read_text() if stage67_path.exists() else "null"

    # Stage 6.8 "Dynamic Interfaces" sub-tab and Stage 6.9 "Translation pilot"
    # sub-view: one bundle each, same "each pipeline owns one file" convention
    # as LANDSCAPE_DATA / STAGE67_DATA above. Generators:
    #   stage6_8_dynamic_interactions/code/export_demo_data_68.py
    #   stage6_9_translating_collective/code/export_demo_data_69.py
    stage68_path = DATA_DIR / "stage6_8_bundle.json"
    stage68_payload = stage68_path.read_text() if stage68_path.exists() else "null"
    stage69_path = DATA_DIR / "stage6_9_bundle.json"
    stage69_payload = stage69_path.read_text() if stage69_path.exists() else "null"
    # Stage 6.10 "Steering & release" sub-view, third internal view of the same
    # Dynamic Interfaces tab. Same convention again: one bundle, one generator
    #   stage6_10_emergence_adaptive_control/code/export_demo_data_610.py
    stage610_path = DATA_DIR / "stage6_10_bundle.json"
    stage610_payload = stage610_path.read_text() if stage610_path.exists() else "null"

    template = (APP_DIR / "index.html").read_text()
    out = inline(template, "DEMO_DATA", demo_payload)
    out = inline(out, "REFINEMENT_DATA", refinement_payload)
    out = inline(out, "REFINEMENT_VIZ", viz_payload)
    out = inline(out, "LANDSCAPE_DATA", landscape_payload)
    out = inline(out, "STAGE67_DATA", stage67_payload)
    out = inline(out, "STAGE68_DATA", stage68_payload)
    out = inline(out, "STAGE69_DATA", stage69_payload)
    out = inline(out, "STAGE610_DATA", stage610_payload)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BUILD_DIR / "index.html"
    out_path.write_text(out)
    n_snapshots = 0
    if landscape_path.exists():
        n_snapshots = len(json.loads(landscape_payload).get("snapshots", {}))
    print(f"wrote {out_path}  ({out_path.stat().st_size/1024:.0f} KB, {len(scenarios)} scenarios inlined, "
          f"refinement bundle {'included' if refinement_path.exists() else 'MISSING'}, "
          f"refinement viz data {'included' if viz_path.exists() else 'MISSING'}, "
          f"landscape bundle {'included (' + str(n_snapshots) + ' snapshots)' if landscape_path.exists() else 'MISSING'}, "
          f"stage 6.7 bundle {'included' if stage67_path.exists() else 'MISSING'}, "
          f"stage 6.8 bundle {'included' if stage68_path.exists() else 'MISSING'}, "
          f"stage 6.9 bundle {'included' if stage69_path.exists() else 'MISSING'}, "
          f"stage 6.10 bundle {'included' if stage610_path.exists() else 'MISSING'})")


if __name__ == "__main__":
    main()
