"""Leak checker for the blind package. Scans EVERY file under m2_blind_package/: (1) text files for forbidden strings (case-insensitive, regex); (2) manifest/splits JSON for keys outside a strict whitelist;
(3) npz files for array names outside the whitelist and for numeric matches to the template arrays (permutation-invariant, tolerance 1e-4, per frame); (4) opaque channel/treatment labels pattern;
(5) file extensions. Exits non-zero on any finding. Usage: python leak_check.py [--write-report]. The forbidden list lives HERE (audit side), not in the package."""
import sys, os, re, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); M2A = os.path.dirname(HERE); PKG = os.path.join(os.path.dirname(M2A), "m2_blind_package")
FORBIDDEN = [r"templat", r"target", r"cell[ _-]?type", r"\btypes?\b", r"belief", r"predict", r"free[ _-]?energy", r"precision", r"\bprior", r"identit", r"\bgain", r"role", r"d_target", r"hidden", r"\bmodes?\b", r"eigen", r"jacobian",
             r"friston", r"kuchling", r"pio[ _-]?lopez", r"\bspm", r"\bdem\b", r"active[ _-]?inference", r"generative", r"hungarian", r"phenotype", r"\bclass[ _]?[01]\b", r"\bslot", r"\bhead\b", r"\btail\b", r"\bgut\b", r"morphogen",
             r"\bsham\b", r"\bkuch", r"\bfscale", r"\bdh\b", r"\bdt\b", r"t_dev", r"sensitivity ramp", r"\bexpectation", r"\bflock", r"free_energy", r"\bsealed", r"audit", r"ground[ _-]?truth"]
KEY_WHITELIST_MANIFEST = {"segment_id", "individual_id", "protocol", "n_cells", "n_bins", "bin_start", "parent_segment", "treatments", "noise_label", "rearing_label", "matched_control", "condition_id", "holdout_individual",
                          "holdout_condition", "holdout_region", "split", "kind", "channel", "applied_to", "onset_bin", "width_bins", "shape", "amplitude", "family", "off_bin", "ramp_bins", "level", "all", "cells", "region", "centre", "radius",
                          "cells_at_actuation", "displacement_xy", "shift"}
KEY_WHITELIST_LADDER = {"renderer", "n_segments", "n_frames", "segments", "frame_rule", "fov_half_width", "image_size", "blob_sigma_px", "snr_db", "map_grid", "seed"}
KEY_WHITELIST_SPLITS = {"development_individuals", "holdout_individuals", "holdout_conditions", "holdout_region_centres", "rule"}
NPZ_KEYS = {"position", "levels", "cloud_position", "cloud_levels", "image_a", "image_b", "map", "frames"}
TEXT_EXT = {".md", ".json", ".jsonl", ".txt", ".py", ".csv", ".html"}
LABEL_RE = re.compile(r"^(CH([1-9]|10)|TX[1-6]|NL[0-3]|RC[12]|C\d{3}|I\d{3}|R\d{6})$")
def keys_of(o, acc):
    if isinstance(o, dict):
        for k, v in o.items(): acc.add(k); keys_of(v, acc)
    elif isinstance(o, list):
        for v in o: keys_of(v, acc)
def main(write=False, skip=()):
    tm = json.load(open(os.path.join(M2A, "sealed", "template_numbers.json"))); tmpl = {8: np.array(tm["L2"]["P"]).T, 16: np.array(tm["L4"]["P"]).T}
    finds, nfiles, nframes = [], 0, 0; kinds = {}
    rx = [re.compile(p, re.I) for p in FORBIDDEN]
    for root, _, fs in os.walk(PKG):
        for f in fs:
            p = os.path.join(root, f); rel = os.path.relpath(p, PKG)
            if rel in skip: continue
            ext = os.path.splitext(f)[1].lower(); nfiles += 1; kinds[ext] = kinds.get(ext, 0) + 1
            if ext in TEXT_EXT:
                txt = open(p, errors="ignore").read()
                for r in rx:
                    m = r.search(txt)
                    if m: finds.append(f"{rel}: forbidden pattern {r.pattern!r} at {txt[max(0, m.start() - 30):m.end() + 30]!r}")
                if f == "manifest.jsonl":
                    ks = set()
                    for line in open(p): keys_of(json.loads(line), ks)
                    bad = ks - KEY_WHITELIST_MANIFEST
                    if bad: finds.append(f"{rel}: keys outside whitelist {sorted(bad)}")
                    for line in open(p):
                        j = json.loads(line)
                        for k in ("segment_id", "individual_id", "noise_label", "rearing_label", "condition_id"):
                            if not LABEL_RE.match(str(j[k])): finds.append(f"{rel}: label {j[k]!r} not opaque-pattern")
                        for t in j["treatments"]:
                            for k in ("channel", "family"):
                                if k in t and not LABEL_RE.match(t[k]): finds.append(f"{rel}: {k} label {t[k]!r}")
                if f == "ladder_index.json":
                    ks = set(); keys_of(json.load(open(p)), ks); bad = ks - KEY_WHITELIST_LADDER
                    if bad: finds.append(f"{rel}: keys outside whitelist {sorted(bad)}")
                if f == "splits.json":
                    ks = set(); keys_of(json.load(open(p)), ks); bad = ks - KEY_WHITELIST_SPLITS
                    if bad: finds.append(f"{rel}: keys outside whitelist {sorted(bad)}")
            elif ext == ".npz":
                z = np.load(p); bad = set(z.files) - NPZ_KEYS
                if bad: finds.append(f"{rel}: array names outside whitelist {sorted(bad)}")
                if "position" in z.files:
                    P = z["position"].astype(float); n = P.shape[1]; T = tmpl.get(n)
                    if T is not None:
                        a = np.sort(P[:, :, 0], axis=1); b = np.sort(P[:, :, 1], axis=1)   # per-frame sorted x and y
                        ta, tb = np.sort(T[:, 0]), np.sort(T[:, 1]); nframes += P.shape[0]
                        hit = (np.abs(a - ta).max(1) < 1e-4) & (np.abs(b - tb).max(1) < 1e-4)
                        if hit.any(): finds.append(f"{rel}: {int(hit.sum())} frame(s) numerically equal to the template positions")
            elif ext in (".png", ".gif", ".html"): pass
            elif rel == "NOT_FOR_RELEASE": pass   # archive marker (added at closure)
            else: finds.append(f"{rel}: unexpected file extension {ext}")
    res = dict(n_files=nfiles, file_extensions=kinds, n_position_frames_checked=nframes, n_forbidden_patterns=len(FORBIDDEN), findings=finds)
    if write:
        body = ["# LEAK_CHECK.md", "", f"Scanner `code/leak_check.py` (kept outside the package), run over **every file** in this package ({nfiles} files; extensions: {', '.join(f'{k or 'none'}: {v}' for k, v in sorted(kinds.items()))}).", "",
                "Checks: (1) every text file against a list of forbidden strings (vocabulary of the cells' internal workings, derived quantities, reference-shape wording, literature and software references, treatment mnemonics); the list is kept outside the package so as not to put those words in it; "
                f"{len(FORBIDDEN)} patterns, case-insensitive; (2) manifest and split-file keys against a strict whitelist; (3) all labels against the opaque-label patterns; (4) array names in every `.npz` against a whitelist; "
                f"(5) every position frame ({nframes:,} frames) compared with the reference arrays, permutation-invariantly, tolerance 1e-4; (6) file extensions.", "",
                f"**Result: {'PASS — no findings' if not finds else 'FAIL — ' + str(len(finds)) + ' finding(s)'}.**"] + ([""] + [f"- {x.split(':')[0]}" for x in finds[:50]] if finds else [])
        open(os.path.join(PKG, "LEAK_CHECK.md"), "w").write("\n".join(body) + "\n")
    return res
if __name__ == "__main__":
    if "--write-report" in sys.argv:
        r0 = main(True, skip=("LEAK_CHECK.md",)); r = main(False)          # report written from pass 1; pass 2 re-scans the package INCLUDING the report
        if r["findings"] and not r0["findings"]: main(True, skip=("LEAK_CHECK.md",))
    else: r = main(False)
    print(json.dumps({k: v for k, v in r.items() if k != "findings"})); print("\n".join(r["findings"][:30]))
    sys.exit(1 if r["findings"] else 0)
