import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
from r1_analyze import full
ref = load_ref(); rp, rs = ref
R2 = json.load(open(os.path.join(DATA, "v2", "r2_results.json")))
out = {}
# mirror partners of reference slots (reflection y -> -y about y=0)
mir = {}
for i in range(8):
    q = rp[:, i] * np.array([1, -1]); d = np.linalg.norm(rp - q[:, None], axis=0); j = int(d.argmin()); mir[i] = (j, float(d[j]))
out["mirror_partner_of_slot"] = {str(k): v for k, v in mir.items()}
# (a) role-indexed AN
rows = []
for r in R2:
    if r["kind"] != "AN": continue
    i = r["ind"]; c = AN_CELL(i); ind = Ind("primary", i)
    A = load(path("census", f"primary_{i:04d}_A")); sl, _ = slot_assignment(*state(A)[:2])
    tw = load(path("r2", f"primary_{i:04d}_UNP_{'ADULT' if r['timing']=='ADULT' else 'FRESH'}")); sl_end, _ = slot_assignment(*state(tw)[:2])
    rows.append(dict(ind=i, cell=c, timing=r["timing"], slot=int(sl[c]) if r["timing"] == "ADULT" else int(sl_end[c]), relabelled=bool(r["relabelled"]), n_changed=r["n_cells_changed"],
                     cycles=r["cycles"], fate=bool(r["target_fate_changed"]), shape=r["shape"], took=r["took_effect"], dev=r["window_max_dev"]))
out["AN_rows"] = rows
tab = collections.defaultdict(lambda: collections.defaultdict(list))
for x in rows: tab[x["timing"]][x["slot"]].append(x)
det = {}
for t, d in tab.items():
    det[t] = {}
    for s, xs in sorted(d.items()):
        key = {(x["relabelled"], x["fate"], str(x["cycles"])) for x in xs}
        det[t][str(s)] = dict(n=len(xs), inds=[x["ind"] for x in xs], outcomes=[list(k) for k in key], deterministic=len(key) == 1, window_dev=[round(min(x["dev"] for x in xs), 3), round(max(x["dev"] for x in xs), 3)])
out["AN_by_role"] = det
json.dump(out, open(os.path.join(DATA, "v2", "reanalysis_a.json"), "w"), indent=1, default=str)
for t in det:
    print(t)
    for s, v in det[t].items(): print("  slot", s, "mirror", mir[int(s)][0], v)
