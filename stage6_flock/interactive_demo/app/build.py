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

    template = (APP_DIR / "index.html").read_text()
    out = inline(template, "DEMO_DATA", demo_payload)
    out = inline(out, "REFINEMENT_DATA", refinement_payload)
    out = inline(out, "REFINEMENT_VIZ", viz_payload)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BUILD_DIR / "index.html"
    out_path.write_text(out)
    print(f"wrote {out_path}  ({out_path.stat().st_size/1024:.0f} KB, {len(scenarios)} scenarios inlined, "
          f"refinement bundle {'included' if refinement_path.exists() else 'MISSING'}, "
          f"refinement viz data {'included' if viz_path.exists() else 'MISSING'})")


if __name__ == "__main__":
    main()
