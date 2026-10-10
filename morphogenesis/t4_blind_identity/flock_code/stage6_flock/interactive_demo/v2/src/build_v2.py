"""Assemble interactive_demo/v2/build/index.html from src/ + data/.

Mirrors the original demo's convention (interactive_demo/app/build.py):
author HTML/CSS/JS as plain files, inline everything into one self-contained
file with no bundler. Opens directly via file://, no server required.
"""
import json
from pathlib import Path

SRC = Path(__file__).resolve().parent
V2 = SRC.parent
DATA = V2 / "data"
BUILD = V2 / "build"

CSS_FILES = ["css/main.css"]
DATA_FILES = [
    ("TAB1_DATA", "tab1_boundary.json"),
    ("TAB2_DATA", "tab2_causal_access.json"),
    ("TAB3_DATA", "tab3_control.json"),
    ("TAB4_DATA", "tab4_landscape.json"),
    ("TAB5_DATA", "tab5_adaptive.json"),
    ("TAB6_DATA", "tab6_translation.json"),
]
JS_FILES = ["js/shared.js", "js/tab1.js", "js/tab2.js", "js/tab3.js", "js/tab4.js",
            "js/tab5.js", "js/tab6.js", "js/main.js"]


def main():
    template = (SRC / "template.html").read_text()

    css = "\n".join((SRC / f).read_text() for f in CSS_FILES)

    data_js = []
    for const_name, fname in DATA_FILES:
        obj = json.loads((DATA / fname).read_text())
        data_js.append(f"const {const_name} = {json.dumps(obj)};")
    data_js = "\n".join(data_js)

    js = "\n".join((SRC / f).read_text() for f in JS_FILES)

    out = template.replace("/*__CSS__*/", css).replace("/*__DATA__*/", data_js).replace("/*__JS__*/", js)

    BUILD.mkdir(parents=True, exist_ok=True)
    out_path = BUILD / "index.html"
    out_path.write_text(out)
    print("wrote", out_path, f"{out_path.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
