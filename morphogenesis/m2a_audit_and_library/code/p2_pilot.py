"""Part 2 amplitude/linearity pilot at S_FP (individual primary 0): representative pulses of each actuator class at 3 amplitudes x {+a, -a, +2a}.
Declared acceptance: linearity error (x2 scaling) and sign-reversal error both < 5% of the response norm. Amplitude per class = the LARGEST pilot
amplitude meeting it (largest-signal linear regime)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
import p2_library as L
from concurrent.futures import ProcessPoolExecutor
AMPS = [0.03, 0.1, 0.3]
REP = {"pos": dict(cls="POS", cells=[0], k=1, id="POS_c0_x"), "sec": dict(cls="SEC", cells=[0], k=1, id="SEC_c0_l1"),
       "gain": dict(cls="GAIN", cells=[0], k=1, id="GAIN_c0_l1"), "gsec": dict(cls="GLOBAL_SEC", cells=list(range(8)), k=1, id="GLOB_SEC_l1"),
       "ggain": dict(cls="GLOBAL_GAIN", cells=list(range(8)), k=1, id="GLOB_GAIN_l1")}
UNIT = {"pos": "pos", "sec": "sec", "gain": "gain", "gsec": "sec", "ggain": "gain"}

def job(rep, amp, mult):
    ind = Ind("primary", 0); b0 = B_ADULT; spec = REP[rep]; kind = UNIT[rep]
    on = b0 + L.ONSET_LAG; typ = {"pos": "pos", "sec": "sec", "gain": "gain"}[kind]
    ev = [dict(type=typ, cells=spec["cells"], ch=spec["k"], amp=mult * amp, onset=on, w=L.PULSE_W)]
    out = path("p2pilot", f"{rep}_a{amp}_m{mult:+.0f}")
    sim(out, L.WINDOW, ind, cont=path("census", f"{ind.name}_A"), events=ev, meta=dict(stage="P2-pilot", rep=rep, amp=amp, mult=mult))
def twin():
    ind = Ind("primary", 0); sim(path("p2pilot", "TWIN"), L.WINDOW, ind, cont=path("census", f"{ind.name}_A"), meta=dict(stage="P2-pilot", twin=True))

def resp(name, tw):
    m = load(path("p2pilot", name)); return np.vstack([m["positions"] - tw["positions"], m["secretion"] - tw["secretion"]])

def analyse():
    tw = load(path("p2pilot", "TWIN")); out = {}
    for rep in REP:
        out[rep] = []
        for a in AMPS:
            R1 = resp(f"{rep}_a{a}_m+1", tw); Rm = resp(f"{rep}_a{a}_m-1", tw); R2 = resp(f"{rep}_a{a}_m+2", tw)
            n1 = np.linalg.norm(R1)
            out[rep].append(dict(amp=a, resp_norm=float(n1), x2_err=float(np.linalg.norm(R2 - 2 * R1) / np.linalg.norm(2 * R1)),
                                 sign_err=float(np.linalg.norm(Rm + R1) / n1), peak=float(np.abs(R1).max())))
    json.dump(out, open(os.path.join(DATA, "v2", "p2_pilot.json"), "w"), indent=1); return out

if __name__ == "__main__":
    tasks = [(job, (rep, a, m)) for rep in REP for a in AMPS for m in (1, -1, 2)] + [(twin, ())]
    run_tasks(tasks, workers=8, label="P2-pilot")
    print(json.dumps(analyse(), indent=1))
