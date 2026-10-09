"""Append the M2a section (protocol v2 exemplars, OBSERVABLE + AUDIT builds) to index.html without touching the existing M1 rows. Idempotent (marker comments)."""
import json, os, re, html
HERE = os.path.dirname(os.path.abspath(__file__)); IDX = os.path.join(HERE, "index.html")
ents = json.load(open(os.path.join(HERE, "output", "m2a", "entries.json"))); sel = json.load(open(os.path.join(HERE, "output", "m2a", "exemplar_selection.json")))
src = open(IDX).read()
src = re.sub(r"<!--M2A-START-->.*?<!--M2A-END-->\n?", "", src, flags=re.S); src = re.sub(r"<!--M2A-RULE-START-->.*?<!--M2A-RULE-END-->\n?", "", src, flags=re.S)
rule = ("<!--M2A-RULE-START--><div class=\"rule\"><b>M2a (protocol v2) exemplars.</b> Rule (declared before generation, as above): per batch, median / best / worst by the batch's hidden-tier metric plus two uniformly random picks (seeds recorded in "
        "<a href='output/m2a/exemplar_selection.json'>output/m2a/exemplar_selection.json</a>). Each exemplar has an OBSERVABLE build (positions and secreted levels only; opaque treatment captions) and an AUDIT build "
        "(adds the role-map overlay and, where stated, eigenmode / unstable-direction arrows). Single-scenario exemplars (class-1 individuals, sweeps, edge state, eigenmodes) are all shown. Frames: every bin up to 600 frames, otherwise every k-th bin (declared in each label). "
        "No browser was available in the build session: the pages were verified structurally only.</div><!--M2A-RULE-END-->\n")
rows = ["<!--M2A-START-->", "<tr><th colspan='6'>M2a — protocol v2 (white-box harness)</th></tr>"]
for e in ents:
    rows.append(f"<tr><td>{html.escape(e['name'])}</td><td><a href='{e['file_observable']}'>OBSERVABLE</a> &middot; <a href='{e['file_audit']}'>AUDIT</a></td><td>m2a state-exporting engine (bit-identical to SPM12 spm_ADEM)</td>"
                f"<td><span class='banner-validated'>validated (engine)</span></td><td>OBSERVABLE + AUDIT</td><td>{html.escape(e.get('notes',''))}</td></tr>")
rows.append("<!--M2A-END-->")
src = src.replace("<table>", rule + "<table>", 1).replace("</table>", "\n".join(rows) + "\n</table>", 1)
open(IDX, "w").write(src); print(len(ents), "M2a entries added")
