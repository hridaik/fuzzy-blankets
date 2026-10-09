"""D4 tables (markdown) from per-direction JSONs -> data/v2/d4_tables.md. Descriptive only."""
import sys, os, json, glob, collections
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from d4_analyze import parse
from d4_full import dirs_region, DATA
cent = {s["id"]: s.get("centre") for s in dirs_region()}
R = []
for f in sorted(glob.glob(os.path.join(DATA, "v2", "d4", "dir_*.json"))):
    r = json.load(open(f)); c, m = parse(r["id"]); R.append((c, m, r))
def f3(x): return "—" if x is None else f"{x:.2f}"
def st(v):
    v = [x for x in v if x is not None]
    return (len(v), min(v), float(np.median(v)), max(v)) if v else None
L = []
def row(name, rs, key):
    s = st([r[key] for r in rs]); n = len(rs)
    return f"| {name} | {n} | {0 if s is None else s[0]} | " + (" | ".join(f3(x) for x in s[1:]) if s else "— | — | —") + " |"
for key, nm in (("swap", "FATE-SWAP"), ("switch", "SHAPE-SWITCH")):
    L += [f"## {nm} threshold by actuator class", "", "| class | directions | with threshold | min | median | max |", "|---|---|---|---|---|---|"]
    for c in ("disp1", "body_eigpos", "body_eigbelief", "body_random", "pulse_single", "pulse_region", "pulse_global"):
        L.append(row(c, [r for cc, m, r in R if cc == c], key))
    L.append("")
for c, label in (("disp1", "single-cell displacement"), ("pulse_single", "single-cell secretion pulse")):
    for key, nm in (("swap", "FATE-SWAP"), ("switch", "SHAPE-SWITCH")):
        L += [f"## {nm} by role, {label}", "", "| role | directions | with threshold | min | median | max |", "|---|---|---|---|---|---|"]
        for ro in range(8): L.append(row(str(ro), [r for cc, m, r in R if cc == c and m["role"] == ro], key))
        L.append("")
L += ["## FATE-SWAP by ligand, single-cell pulse", "", "| ligand | directions | with threshold | min | median | max |", "|---|---|---|---|---|---|"]
for lg in range(1, 5): L.append(row(str(lg), [r for cc, m, r in R if cc == "pulse_single" and m["lig"] == lg], "swap"))
L += ["", "## FATE-SWAP by ligand, regional pulse", "", "| ligand | directions | with threshold | min | median | max |", "|---|---|---|---|---|---|"]
for lg in range(1, 5): L.append(row(str(lg), [r for cc, m, r in R if cc == "pulse_region" and m["lig"] == lg], "swap"))
L += ["", "## Regional pulses by centre", "", "| centre | position | with FATE-SWAP (of 4 ligands) | min | median |", "|---|---|---|---|---|"]
for g in sorted({m["g"] for cc, m, r in R if cc == "pulse_region"}):
    rs = [r for cc, m, r in R if cc == "pulse_region" and m["g"] == g]; s = st([r["swap"] for r in rs]); ce = cent.get(rs[0]["id"])
    L.append(f"| g{g} | {None if ce is None else [round(float(x),2) for x in ce]} | {0 if s is None else s[0]} | " + (f"{s[1]:.2f} | {s[2]:.2f}" if s else "— | —") + " |")
L += ["", "## Global pulses", "", "| ligand | FATE-SWAP | above | SHAPE-SWITCH | above |", "|---|---|---|---|---|"]
for cc, m, r in R:
    if cc == "pulse_global": L.append(f"| {m['lig']} | {f3(r['swap'])} | {r.get('swap_just_above')} | {f3(r['switch'])} | {r.get('switch_just_above')} |")
L += ["", "## SHAPE-SWITCH directions (all)", "", "| id | threshold | identity outcome just above |", "|---|---|---|"]
for cc, m, r in R:
    if r["switch"] is not None: L.append(f"| {r['id']} | {r['switch']:.3f} | {r.get('switch_just_above')} |")
L += ["", "## Non-monotone windows (outcome label non-monotone in amplitude)", "", "| class | count | ids |", "|---|---|---|"]
nm = collections.defaultdict(list)
for cc, m, r in R:
    if r["nonmonotone"]: nm[cc].append(r["id"])
for c, v in nm.items(): L.append(f"| {c} | {len(v)} | {', '.join(v[:12])}{' …' if len(v)>12 else ''} |")
L += ["", "## Outcome labels at top amplitude", "", "| class | " + " | ".join(sorted({r['outcomes_top'] for _,_,r in R})) + " |", "|---|" + "---|" * len({r['outcomes_top'] for _,_,r in R})]
labs = sorted({r['outcomes_top'] for _,_,r in R})
for c in ("disp1", "body_eigpos", "body_eigbelief", "body_random", "pulse_single", "pulse_region", "pulse_global"):
    cn = collections.Counter(r["outcomes_top"] for cc, m, r in R if cc == c); L.append(f"| {c} | " + " | ".join(str(cn.get(l, 0)) for l in labs) + " |")
open(os.path.join(DATA, "v2", "d4_tables.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
