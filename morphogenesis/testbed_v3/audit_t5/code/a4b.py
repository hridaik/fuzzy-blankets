"""A4b: true duration curve at the body centre: noise-free amplitude threshold vs pulse duration (disc r = 1.5 at the centroid, ramp = min(5, dur/4) as T5's rig default), dishes 6000 (b), 6003 (a), 6007 (a).
Dose = amp x dur x cells (nominal). Switch criterion: mean rho on the other side 100 tu after the pulse (as A3)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regret import *
DURS = [2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 20.0, 40.0]; out = {}
for seed in (6000, 6003, 6007):
    start = state_of(seed); ex = make_dish(seed); ex.run_sched(20.0, [], sham=False, obs_times=[]); s0 = snap(ex); ctr = ex.w.X[ex.w.alive].mean(0); exnf = make_noisefree(seed, s0, start)
    cells = int((np.linalg.norm(ex.w.X - ctr, axis=1) <= 1.5).sum()); rows = []
    lab = 'L4' if start == 'a' else 'L3'
    for dur in DURS:
        ramp = min(5.0, dur / 4.0); T_end = 20.0 + dur + 100.0
        def f(amp): restore(exnf, s0); acts = [mk_action(lab, {'type': 'disc', 'xy': ctr.tolist(), 'radius': 1.5}, amp, 20.0, dur, ramp)]; return switched(exnf, s0, acts, T_end, start)
        lo, hi = None, None; a = 2.0
        if f(a):
            hi = a
            while a > 0.05:
                a /= 2
                if f(a): hi = a
                else: lo = a; break
        else:
            lo = a
            while a < 300:
                a *= 2
                if f(a): hi = a; break
                lo = a
        if hi is None or lo is None: rows.append(dict(dur=dur, thr_amp=None, dose=None, bracket='none_to_300' if hi is None else 'below')); print(seed, dur, 'no threshold up to', a, flush=True); continue
        for _ in range(8):
            m = float(np.sqrt(lo * hi))
            if f(m): hi = m
            else: lo = m
        rows.append(dict(dur=dur, thr_amp=hi, dose=hi * dur * cells, ramp=ramp, integral=hi * dur)); print(seed, dur, round(hi, 3), round(hi * dur * cells, 1), flush=True)
    out[seed] = dict(start=start, cells=cells, rows=rows)
json.dump(out, open(os.path.join(AUD, 'data', 'a4b_duration.json'), 'w'), indent=1, default=float)
