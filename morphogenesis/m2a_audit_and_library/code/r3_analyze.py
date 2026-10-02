import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
from r2_analyze import wilson
import r3_kicks as K
tau = json.load(open(os.path.join(SEALED, "thresholds_v2.json")))["tau_pair"]
rows = []
for i in range(K.NIND3):
    ind = Ind("primary", i); A = load(path("census", f"{ind.name}_A")); Up, Us, _ = state(A)
    for kind in K.KINDS:
        for s in (range(1) if kind == "K2" else range(K.NSEED)):
            p = path("r3", f"{ind.name}_{kind}_s{s:02d}")
            if not os.path.exists(p): continue
            m = load(p); P, S, _ = state(m); st = stationarity(m, offset=B_ADULT)
            pos1, sec1, v1 = state(m, 0); dev1 = float(np.linalg.norm(pos1 - Up)) ; dsec1 = float(np.linalg.norm(sec1 - state(A)[1]))
            if st["kind"] is None: sh = dict(shape="NONCONVERGED")
            else:
                d = d_pair_pos(P, S, Up, Us); sh = dict(shape="RETURNED" if d < tau else "NEW-FORM", d_unpert=float(d))
            ro = roles(P, S, Up, Us) if st["kind"] else dict(relabelled=None)
            rows.append(dict(ind=i, kind=kind, seed=s, stationary=st, kick_dpos_bin1=dev1, kick_dsec_bin1=dsec1, **sh, **ro))
json.dump(rows, open(os.path.join(DATA, "v2", "r3_results.json"), "w"))
for kind in K.KINDS:
    v = [r for r in rows if r["kind"] == kind]; sh = collections.Counter(r["shape"] for r in v); rl = sum(1 for r in v if r.get("relabelled"))
    cc = collections.Counter(str(r["cycles"]) for r in v if r.get("relabelled")); sb = [r["stationary"]["bin"] - B_ADULT for r in v if r["stationary"]["bin"]]
    nf = [r for r in v if r["shape"] == "NEW-FORM"]
    print(kind, len(v), dict(sh), "relab", f"{rl}/{len(v)}", wilson(rl, len(v)), dict(cc.most_common(4)), "stationary after kick (bins) med/max", np.median(sb) if sb else None, max(sb) if sb else None,
          "kick size bin1 min/max", round(min(r["kick_dpos_bin1"] + r["kick_dsec_bin1"] for r in v), 3), round(max(r["kick_dpos_bin1"] + r["kick_dsec_bin1"] for r in v), 3))
    if nf: print("   NEW-FORM:", [(r["ind"], r["seed"], round(r["d_unpert"], 3)) for r in nf][:10])
