"""D4: minimal durable interventions by amplitude bisection on the class-0 adult base state (primary_0000, continuation at b=320).
Outcome after an intervention (run to stationarity, extended up to 3 segments of 192 bins):
  SAME         same shape (d_pair to the base end state < tau) and same roles (slot assignment equal)
  FATE-SWAP    same shape, roles changed
  SHAPE-SWITCH ends outside class 0 (d_pair >= tau): label class1 if within tau of the class-1 exemplar, else other
  NONCONV      not stationary (or a cycle) after 3 segments
Thresholds per direction: lowest amplitude with outcome >= FATE-SWAP ('swap') and lowest with SHAPE-SWITCH ('switch'), by log-bisection to 1% relative tolerance
inside the bracket found on a coarse log grid. 'none' = no threshold up to a_max."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *

TAU = json.load(open(os.path.join(SEALED, "thresholds_v2.json")))["tau_pair"]
SEG = 192; MAXSEG = 3; PULSE_W = 4; REL_TOL = 0.01; GRID_N = 7
BASE = dict(name="c0", ind=Ind("primary", 0), cont=path("census", "primary_0000_A"))
_cache = {}

def base_info():
    if "b" in _cache: return _cache["b"]
    A = load(BASE["cont"]); b0 = int(np.ravel(A["b_end"])[0]); pos, sec, _ = state(A); sl, _ = slot_assignment(pos, sec)
    ex1 = state(load(path("census", "secondary_0005_A")))[:2]
    _cache["b"] = dict(b0=b0, pos=pos, sec=sec, slots=sl, ex1=ex1, cell_of_slot={int(s): int(c) for c, s in enumerate(sl)}); return _cache["b"]

def classify(m, b_start):
    B = base_info(); st = stationarity(m, offset=b_start)
    if st["kind"] != "FIXED": return dict(label="NONCONV", stationary=st)
    pos, sec, _ = state(m); d = d_pair_pos(pos, sec, B["pos"], B["sec"])
    if d >= TAU:
        d1 = d_pair_pos(pos, sec, *B["ex1"]); return dict(label="SHAPE-SWITCH", to="class1" if d1 < TAU else "other", d_base=float(d), d_class1=float(d1), stationary=st)
    sl, _ = slot_assignment(pos, sec); sw = int((sl != B["slots"]).sum())
    return dict(label="FATE-SWAP" if sw else "SAME", n_changed=sw, d_base=float(d), stationary=st)

RANK = {"SAME": 0, "FATE-SWAP": 1, "SHAPE-SWITCH": 2, "NONCONV": 2}

def evaluate(spec, amp, tag):
    """Run one intervention of amplitude amp. spec: dict(id, kind, ...). Returns classification dict (cached on disk via json sidecar)."""
    B = base_info(); b0 = B["b0"]; ind = BASE["ind"]; name = f"{spec['id']}_a{amp:.6g}"
    side = path("d4", name)[:-4] + ".class.json"
    if os.path.exists(side): return json.load(open(side))
    kick = None; ev = None
    if spec["kind"] == "disp1":
        d = np.zeros((2, 8)); c = B["cell_of_slot"][spec["role"]]; th = math.radians(spec["theta"]); d[:, c] = amp * np.array([math.cos(th), math.sin(th)]); kick = dict(type="pos", dpos=d)
    elif spec["kind"] == "body":
        kick = dict(type="pos", dpos=amp * np.asarray(spec["u"]).reshape(2, 8, order="F"))
    elif spec["kind"] == "pulse":
        cells = spec["cells"]; ev = [dict(type=spec["type"], cells=cells, ch=spec["ch"], amp=amp, onset=b0 + 2, w=PULSE_W)]
    else: raise ValueError(spec["kind"])
    cont = BASE["cont"]; segs = []; b = b0
    for j in range(MAXSEG):
        out = path("d4", f"{name}_{j}")
        sim(out, SEG, ind, cont=cont, kick=kick if j == 0 else None, events=ev, meta=dict(stage="D4", spec={k: v for k, v in spec.items() if k != "u"}, amp=amp, seg=j))
        segs.append(out); cont = out; b += SEG
        full = {k: np.hstack([load(s)[k] for s in segs]) for k in ("positions", "secretion", "v_expect")}; full["n"] = 8
        if stationarity(full, offset=b0)["kind"] is not None: break
    res = classify(full, b0); res.update(amp=float(amp), spec_id=spec["id"], n_seg=len(segs))
    json.dump(res, open(side, "w")); return res

def find(spec, a_min, a_max):
    """Coarse log grid, then log-bisection of each threshold. Returns dict with thresholds and all evaluations."""
    grid = [a_min * (a_max / a_min) ** (k / (GRID_N - 1)) for k in range(GRID_N)]
    ev = {}
    def E(a):
        a = float(f"{a:.6g}")
        if a not in ev: ev[a] = evaluate(spec, a, "")
        return ev[a]
    top = E(grid[-1])
    out = dict(id=spec["id"], a_min=a_min, a_max=a_max, outcomes_top=top["label"])
    if RANK[top["label"]] == 0:                       # no durable effect at a_max: still scan the grid for non-monotone windows
        for a in grid[:-1]: E(a)
        out.update(swap=None, switch=None, nonmonotone=any(RANK[v["label"]] > 0 for v in ev.values()))
    else:
        for a in grid[:-1]: E(a)
        for key, pred in (("swap", lambda v: RANK[v["label"]] >= 1 and v["label"] != "NONCONV"), ("switch", lambda v: v["label"] in ("SHAPE-SWITCH", "NONCONV"))):
            hits = [a for a in grid if pred(ev[float(f"{a:.6g}")])]
            if not hits: out[key] = None; continue
            hi = min(hits); lows = [a for a in grid if a < hi]
            if not lows: out[key] = hi; continue
            lo = max(lows)
            while hi / lo > 1 + REL_TOL:
                mid = math.sqrt(lo * hi)
                if pred(E(mid)): hi = mid
                else: lo = mid
            out[key] = hi
    out["evals"] = {f"{a:.6g}": dict(label=v["label"], to=v.get("to"), n_changed=v.get("n_changed")) for a, v in sorted(ev.items())}
    # identity outcome just above each threshold
    for key in ("swap", "switch"):
        if out.get(key):
            above = min((a for a in ev if a >= out[key] * 0.999), default=None)
            out[key + "_just_above"] = ev[above]["label"] + (("->" + ev[above].get("to", "")) if ev[above].get("to") else "") if above else None
    ra = [RANK[ev[a]["label"]] for a in sorted(ev)]
    out["nonmonotone"] = bool(any(ra[i + 1] < ra[i] for i in range(len(ra) - 1)))
    json.dump(out, open(os.path.join(DATA, "v2", "d4", f"dir_{spec['id']}.json"), "w"), indent=0)
    return out
