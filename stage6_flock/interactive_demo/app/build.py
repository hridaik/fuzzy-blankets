"""Inlines interactive_demo/data/*.json into app/index.html's
/*__DEMO_DATA__*/ placeholder, producing a single self-contained
build/index.html that opens with no server (file://, no CORS issues)."""
from __future__ import annotations

import json
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DEMO_DIR = APP_DIR.parent
DATA_DIR = DEMO_DIR / "data"
BUILD_DIR = DEMO_DIR / "build"


def main():
    manifest = json.loads((DATA_DIR / "manifest.json").read_text())
    scenarios = {}
    for entry in manifest["primary_scenarios"] + manifest["canonical_scenarios"]:
        sid = entry["scenario_id"]
        scenarios[sid] = json.loads((DATA_DIR / f"{sid}.json").read_text())

    payload = json.dumps(dict(manifest=manifest, scenarios=scenarios), separators=(",", ":"))

    template = (APP_DIR / "index.html").read_text()
    out = re.sub(
        r"/\*__DEMO_DATA__\*/.*?/\*__END_DEMO_DATA__\*/",
        lambda m: payload,
        template, flags=re.S,
    )
    assert out != template, "placeholder not found -- check app/index.html"

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BUILD_DIR / "index.html"
    out_path.write_text(out)
    print(f"wrote {out_path}  ({out_path.stat().st_size/1024:.0f} KB, {len(scenarios)} scenarios inlined)")


if __name__ == "__main__":
    main()
