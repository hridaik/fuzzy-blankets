"""Part 1 under protocol v2 (canonical clock).
1.1  16-cell census: 30 individuals (randn(16,16)/8, primary idx 0-29), segment A 320 + B 192; extended (+512 each, up to 2048) while not stationary.
1.2  other perturbation families (individuals primary 0-9; timings of R2: sustained, DEV-LONG (0->W), ADULT (continuation, W bins on)):
       PL  = Pio-Lopez-2022 high sensory precision, all cells: M(1).V = exp(3) * F; F chosen by a 3-value pilot (exp(1), exp(2), exp(3) i.e. V = exp(4..6))
       FR  = Friston-2015 Fig.5 intracellular sensitivity x2 (m0c declared interpretation: g.s of every cell x2)
1.3  Pio-Lopez high identity expectation k=2,4 (initial beliefs: primary i's draw with the first k cells' rows 4,5 set to exp(6)), 10 individuals each."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
import r2_withdrawal as R2

# ---- 1.1 ----
def cell16(i):
    ind = Ind("primary", i)
    A = sim(path("p1_16", f"{ind.name}_A"), B_ADULT, ind, L=4, meta=dict(stage="P1.1"))
    B = sim(path("p1_16", f"{ind.name}_B"), 192, ind, L=4, cont=A, meta=dict(stage="P1.1"))
    return ind.name

# ---- 1.2 ----
PL_VALUES = {"pl4": np.exp(1.0), "pl5": np.exp(2.0), "pl6": np.exp(3.0)}   # F = V/exp(3)  (V = exp(4), exp(5), exp(6))
def fam_events(fam, onset, off):
    if fam == "FR": return [dict(type="fscale", cells=list(range(8)), ch=3, amp=2.0, onset=onset, off=off, w=RAMP_W)]
    return []
def fam_prec(fam, F, onset, off):
    return dict(F=F, onset=onset, off=off, w=RAMP_W) if fam == "PL" else None

def fam_job(i, fam, timing, F=None, tag=""):
    ind = Ind("primary", i); W = R2.W_bins(); h = R2.horizons()
    if timing == "SUSTAINED":
        sim(path("p1_fam", f"{ind.name}_{fam}{tag}_SUST"), h["sustained"], ind, events=fam_events(fam, 0, None), prec=fam_prec(fam, F, 0, None), meta=dict(stage="P1.2", fam=fam, timing=timing))
    elif timing == "DEV-LONG":
        sim(path("p1_fam", f"{ind.name}_{fam}{tag}_DEV-LONG"), h["long"], ind, events=fam_events(fam, 0, W), prec=fam_prec(fam, F, 0, W), meta=dict(stage="P1.2", fam=fam, timing=timing))
    else:
        A = path("census", f"{ind.name}_A")
        sim(path("p1_fam", f"{ind.name}_{fam}{tag}_ADULT"), h["adult"], ind, cont=A, events=fam_events(fam, B_ADULT, B_ADULT + W), prec=fam_prec(fam, F, B_ADULT, B_ADULT + W),
            meta=dict(stage="P1.2", fam=fam, timing=timing))

def pl_pilot(name):
    F = PL_VALUES[name]; ind = Ind("primary", 0)
    sim(path("p1_pilot", f"PL_{name}_sust"), 600, ind, prec=fam_prec("PL", F, 0, None), meta=dict(stage="P1.2-pilot", V=f"exp({ {'pl4':4,'pl5':5,'pl6':6}[name] })"))

# ---- 1.3 ----
def hi_v0(i, k):
    from m2a_common import draw_v0_octave
    v = draw_v0_octave(i).copy(); v[3:5, :k] = np.exp(6.0); return v

class IndV(Ind):
    def __init__(self, i, k): super().__init__("primary", i); self.k = k; self._v0 = hi_v0(i, k)
    @property
    def name(self): return f"primary_{self.idx:04d}_k{self.k}"
    def v0(self): return self._v0

def hi_job(i, k):
    ind = IndV(i, k)
    A = sim(path("p1_hi", f"{ind.name}_A"), B_ADULT, ind, meta=dict(stage="P1.3", k=k))
    sim(path("p1_hi", f"{ind.name}_B"), 192, ind, cont=A, meta=dict(stage="P1.3", k=k))

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "16": run_tasks([(cell16, (i,)) for i in range(30)], label="P1.1")
    elif which == "plpilot": run_tasks([(pl_pilot, (n,)) for n in PL_VALUES], workers=3, label="P1.2-pilot")
    elif which == "hi": run_tasks([(hi_job, (i, k)) for k in (2, 4) for i in range(10)], label="P1.3")
    elif which == "fam":
        F = float(sys.argv[2]); tasks = []
        for i in range(10):
            for t in ("SUSTAINED", "DEV-LONG", "ADULT"):
                tasks.append((fam_job, (i, "FR", t))); tasks.append((fam_job, (i, "PL", t, F)))
        run_tasks(tasks, label="P1.2")
