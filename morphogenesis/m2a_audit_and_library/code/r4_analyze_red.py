import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
from r2_analyze import wilson
import r4_noise as R4
tau = json.load(open(os.path.join(SEALED, "thresholds_v2.json")))["tau_pair"]
def tm(m, n=100):   # time-mean of the last n bins
    P = m["positions"][:, -n:].mean(1).reshape(8, 2).T; S = m["secretion"][:, -n:].mean(1).reshape(4, 8, order="F"); return P, S
rows = []
for lvl in R4.LEVELS:
    for i in range(10):
        U = tm(load(path("r4", f"primary_{i:04d}_RED_{lvl}_UNP")))
        for k in ("DH", "SHAM_DH"):
            m = load(path("r4", f"primary_{i:04d}_RED_{lvl}_{k}")); P = tm(m)
            d = d_pair_pos(*P, *U); ro = roles(*P, *U)
            rows.append(dict(level=lvl, ind=i, kind=k, d_pair=float(d), shape="REVERTED" if d < tau else "NOVEL", relabelled=ro["relabelled"], n_changed=ro["n_cells_changed"], cycles=ro["cycles"]))
json.dump(rows, open(os.path.join(DATA, "v2", "r4_red_results.json"), "w"))
for lvl in R4.LEVELS:
    for k in ("DH", "SHAM_DH"):
        v = [r for r in rows if r["level"] == lvl and r["kind"] == k]; rl = sum(r["relabelled"] for r in v)
        print(lvl, k, collections.Counter(r["shape"] for r in v), f"relabelled {rl}/10", wilson(rl, 10), "max d_pair", round(max(r["d_pair"] for r in v), 3))
