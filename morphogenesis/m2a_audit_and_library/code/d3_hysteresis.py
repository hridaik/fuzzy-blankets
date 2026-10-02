"""D3: hysteresis by quasi-static continuation. From an adult fixed point, step a parameter up in declared increments (each step: smooth
raised-cosine change over 4 bins, then settle to the state-based criterion, extending the segment while not stationary), to the maximum, then back
down to baseline. Families: DH_eps (g.x1 = (1-e) x + e x^2), DT_eps (-x^2), PREC (global sensory-precision multiplier F = exp(phi)).
Every step is a CONTINUATION of the previous one (full state), absolute clock T_dev = 32."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *

SEG = 192; MAXSEG = 4          # settle segment length; up to MAXSEG segments per step
FAM = {"DH": dict(kind="eps", sign=1, lo=0.0, hi=1.0, step=0.05), "DT": dict(kind="eps", sign=-1, lo=0.0, hi=1.0, step=0.05),
       "PREC": dict(kind="prec", lo=0.0, hi=6.0, step=0.5)}      # PREC: phi = ln F, V = exp(3 + phi)
STARTS = {"c0": ("primary_0000", "census", "primary_0000_A"), "c1": ("secondary_0005", "census", "secondary_0005_A")}

def levels(f):
    c = FAM[f]; n = int(round((c["hi"] - c["lo"]) / c["step"]))
    up = [round(c["lo"] + k * c["step"], 6) for k in range(n + 1)]
    return up + up[-2::-1]            # up to hi, then back down to lo

def step_job(fam, start, k, lev_prev, lev, prev_cont, b0, ind):
    """one parameter step as a chain of settle segments; returns (final cont path, record)."""
    c = FAM[fam]; tag = f"{fam}_{start}_s{k:03d}"
    if c["kind"] == "eps":
        ev = [dict(type="kuche", cells=list(range(8)), sign=c["sign"], amp0=lev_prev, amp=lev, onset=b0 + 1, w=RAMP_W)]; prec = None
    else:
        ev = None; prec = dict(F=float(np.exp(lev)), F0=float(np.exp(lev_prev)), onset=b0 + 1, off=None, w=RAMP_W)
    segs = []; cont = prev_cont; b = b0
    for j in range(MAXSEG):
        out = path("d3", f"{tag}_{j}")
        # events carry the step only in the first segment; later segments hold the new level (amp0=amp)
        e = ev if j == 0 else ([dict(type="kuche", cells=list(range(8)), sign=c["sign"], amp0=lev, amp=lev, onset=0, w=RAMP_W)] if ev else None)
        p = prec if j == 0 else (dict(F=float(np.exp(lev)), F0=float(np.exp(lev)), onset=0, off=None, w=RAMP_W) if prec else None)
        sim(out, SEG, ind, cont=cont, events=e, prec=p, meta=dict(stage="D3", fam=fam, start=start, step=k, level=lev))
        segs.append(out); cont = out; b += SEG
        m = load(out); st = stationarity(m, offset=b - SEG)
        if st["kind"] is not None: break
    full = {kk: np.hstack([load(s)[kk] for s in segs]) for kk in ("positions", "secretion", "v_expect")}; full["n"] = 8
    st = stationarity(full, offset=b0)
    pos, sec, v = state(full)
    rec = dict(fam=fam, start=start, step=k, level=lev, kind=st["kind"], settle_bin=None if st["bin"] is None else st["bin"] - b0, n_seg=len(segs), b_end=b)
    return cont, rec, full

def chain(fam, start):
    nm, st, fn = STARTS[start]; ind = Ind("primary" if nm.startswith("primary") else "secondary", int(nm.split("_")[1]))
    cont = path(st, fn); b = int(np.ravel(load(cont)["b_end"])[0]); lev = levels(fam); recs = []
    ref0 = load_ref(); ref1 = state(load(path("census", "secondary_0005_A")))[:2]
    prev = FAM[fam]["lo"]
    for k, L in enumerate(lev):
        if k == 0: lev_prev = L
        else: lev_prev = lev[k - 1]
        cont, rec, full = step_job(fam, start, k, lev_prev, L, cont, b, ind); b = rec["b_end"]
        pos, sec, v = state(full); sl, _ = slot_assignment(pos, sec)
        rec.update(slots=sl.tolist(), d_ref0=float(d_pair_pos(pos, sec, *ref0)), d_ref1=float(d_pair_pos(pos, sec, *ref1)), max_belief_min=float(softmax_cols(v).max(0).min()))
        if rec["kind"] == "CYCLE2":
            p2, s2, _ = state(full, -2); rec["cycle_amp"] = float(np.linalg.norm(pos - p2))
        recs.append(rec)
        json.dump(recs, open(os.path.join(DATA, "v2", f"d3_{fam}_{start}.json"), "w"))
    return recs

if __name__ == "__main__":
    tasks = [(chain, (f, s)) for f in FAM for s in STARTS]
    run_tasks(tasks, workers=6, label="D3")
