"""D6: confirm three D4 thresholds on two other (relabelled) class-0 individuals (primary_0001, primary_0002). Each threshold is tested at the D4 bracket pair
(largest amplitude below, smallest above, ~1 % apart); directions are mapped through the individual's role map (role-indexed actuation).
Thresholds: global_l1 FATE-SWAP, global_l4 SHAPE-SWITCH, body_rand03 FATE-SWAP (whole-body displacement, role-mapped)."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
import d4
TAU = d4.TAU; SEG = 192; MAXSEG = 3
def base_of(i):
    ind = Ind("primary", i); cont = path("census", f"{ind.name}_A"); A = load(cont); b0 = int(np.ravel(A["b_end"])[0]); pos, sec, _ = state(A); sl, _ = slot_assignment(pos, sec)
    return ind, cont, b0, pos, sec, sl
def classify(m, b0, pos0, sec0, sl0, ex1):
    st = stationarity(m, offset=b0)
    if st["kind"] != "FIXED": return "NONCONV"
    pos, sec, _ = state(m)
    if d_pair_pos(pos, sec, pos0, sec0) >= TAU: return "SHAPE-SWITCH"
    sl, _ = slot_assignment(pos, sec); return "FATE-SWAP" if (sl != sl0).any() else "SAME"
def evaluate(i, spec, amp):
    ind, cont0, b0, pos0, sec0, sl = base_of(i); ex1 = None
    name = f"{ind.name}_{spec['id']}_a{amp:.6g}"; kick = None; ev = None
    if spec["kind"] == "body":
        B0 = d4.base_info(); u0 = np.asarray(spec["u"]).reshape(2, 8, order="F"); u = np.zeros((2, 8))
        for c in range(8): u[:, int(np.where(sl == B0["slots"][c])[0][0])] = u0[:, c]
        kick = dict(type="pos", dpos=amp * u)
    else: ev = [dict(type="sec", cells=list(range(8)), ch=spec["ch"], amp=amp, onset=b0 + 2, w=4)]
    cont = cont0; segs = []
    for j in range(MAXSEG):
        out = path("d6", f"{name}_{j}"); sim(out, SEG, ind, cont=cont, kick=kick if j == 0 else None, events=ev, meta=dict(stage="D6", spec=spec["id"], amp=amp)); segs.append(out); cont = out
        full = {k: np.hstack([load(s)[k] for s in segs]) for k in ("positions", "secretion", "v_expect")}; full["n"] = 8
        if stationarity(full, offset=b0)["kind"] is not None: break
    return classify(full, b0, pos0, sec0, sl, ex1)
def bracket(did, key):
    r = json.load(open(os.path.join(DATA, "v2", "d4", f"dir_{did}.json"))); hi = r[key]
    rank = (lambda v: v["label"] in ("SHAPE-SWITCH", "NONCONV")) if key == "switch" else (lambda v: v["label"] in ("FATE-SWAP", "SHAPE-SWITCH", "NONCONV"))
    lo = max(float(a) for a, v in r["evals"].items() if not rank(v) and float(a) < hi)
    return lo, hi
SPECS = [("global_l1", "swap", dict(id="global_l1", kind="pulse", ch=1)), ("global_l4", "switch", dict(id="global_l4", kind="pulse", ch=4)), ("body_rand03", "swap", None)]
def job(i, k):
    did, key, spec = SPECS[k]
    if spec is None: spec = [s for s in __import__("d4_dirs").dirs_body() if s["id"] == did][0]
    lo, hi = bracket(did, key); a = evaluate(i, spec, lo); b = evaluate(i, spec, hi)
    return dict(ind=i, direction=did, threshold=key, lo=lo, hi=hi, outcome_lo=a, outcome_hi=b)
if __name__ == "__main__":
    T = [(job, (i, k)) for i in (1, 2) for k in range(3)]; res = run_tasks(T, workers=3, label="D6")
    json.dump(res, open(os.path.join(DATA, "v2", "d6_results.json"), "w"), indent=1)
    for r in res: print(r)
