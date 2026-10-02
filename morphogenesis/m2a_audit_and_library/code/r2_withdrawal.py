"""R2: withdrawal battery under v2 (canonical clock). Individuals primary 0-19; perturbations DH, DT, AN, SHAM_DH, SHAM_AN;
timings DEV-SHORT (0 -> 2*T_dev), DEV-LONG (0 -> W), ADULT (continuation from b_adult, on for W bins, then off).
Twins: matched UNPERTURBED (same protocol/horizon), SUSTAINED (DH, DT, AN)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *

K_FOURIER, FREQ_RANGE = 4, (0.1, 0.45)         # M1's sham family (declared there)
NIND = 20
W = None
def W_bins():
    global W
    if W is None: W = json.load(open(path("pilot", "W")[:-4] + ".json"))["W"]
    return W
SHORT_OFF = int(2 * T_DEV)
H_AFTER = 320                                   # bins run after switch-off (>= ~35 contraction time constants; checked by stationarity)

def sham_params(i):
    rng = np.random.default_rng(600000 + i)     # as M1
    f = rng.uniform(*FREQ_RANGE, size=(K_FOURIER, 2)) * rng.choice([-1, 1], size=(K_FOURIER, 2))
    return f, rng.uniform(0, 2 * np.pi, K_FOURIER), rng.uniform(0, 2 * np.pi, K_FOURIER)

def events(kind, i, onset, off):
    c = AN_CELL(i); allc = list(range(8))
    if kind in ("DH", "DT"): return [dict(type="kuch", cells=allc, sign=1 if kind == "DH" else -1, onset=onset, off=off, w=RAMP_W)]
    if kind == "AN": return [dict(type="kuch", cells=[c], sign=1, onset=onset, off=off, w=RAMP_W)]
    cal = json.load(open(os.path.join(SEALED, "sham_calibration_v2.json")))
    f, px, py = sham_params(i)
    if kind == "SHAM_DH": return [dict(type="sham", cells=allc, freqs=f, phx=px, phy=py, amp=cal["rms_dh"], onset=onset, off=off, w=RAMP_W)]
    if kind == "SHAM_AN": return [dict(type="sham", cells=[c], freqs=f, phx=px, phy=py, amp=cal["rms_an"][str(i)], onset=onset, off=off, w=RAMP_W)]
    raise ValueError(kind)

def horizons():
    W_ = W_bins()
    return dict(short=SHORT_OFF + 576, long=W_ + H_AFTER + 64, adult=W_ + H_AFTER, sustained=max(W_ + 384, 768))

# ---- tasks (module-level for multiprocessing) ----
def t_sustained(i, kind):
    ind = Ind("primary", i); h = horizons()
    sim(path("r2", f"{ind.name}_SUST_{kind}"), h["sustained"], ind, events=events(kind, i, 0, None), meta=dict(stage="R2", pert=kind, timing="SUSTAINED"))
def t_unp_fresh(i):
    ind = Ind("primary", i); h = horizons()
    sim(path("r2", f"{ind.name}_UNP_FRESH"), max(h["long"], h["short"]), ind, meta=dict(stage="R2", pert="none", timing="FRESH"))
def t_unp_adult(i):
    ind = Ind("primary", i); h = horizons()
    A = path("census", f"{ind.name}_A")
    sim(path("r2", f"{ind.name}_UNP_ADULT"), h["adult"], ind, cont=A, meta=dict(stage="R2", pert="none", timing="ADULT"))
def t_pert(i, kind, timing):
    ind = Ind("primary", i); h = horizons(); W_ = W_bins()
    if timing == "DEV-SHORT":
        sim(path("r2", f"{ind.name}_{kind}_{timing}"), h["short"], ind, events=events(kind, i, 0, SHORT_OFF), meta=dict(stage="R2", pert=kind, timing=timing))
    elif timing == "DEV-LONG":
        sim(path("r2", f"{ind.name}_{kind}_{timing}"), h["long"], ind, events=events(kind, i, 0, W_), meta=dict(stage="R2", pert=kind, timing=timing))
    else:
        A = path("census", f"{ind.name}_A")
        sim(path("r2", f"{ind.name}_{kind}_{timing}"), h["adult"], ind, cont=A, events=events(kind, i, B_ADULT, B_ADULT + W_), meta=dict(stage="R2", pert=kind, timing=timing))

def calibrate_sham():
    """RMS-match as M1: RMS over (bins, cells) of the DH distortion x1^2 - x1 along the SUSTAINED DH twin (all cells) / the
    SUSTAINED AN twin (the single anomalous cell). DH: individual 0 (individuals are equivalent up to relabelling); AN: per individual."""
    def rms(m, cells):
        P = m["positions"].reshape(8, 2, -1)[cells, 0, :]
        return float(np.sqrt(np.mean((P ** 2 - P) ** 2)))
    out = dict(rms_dh=rms(load(path("r2", "primary_0000_SUST_DH")), list(range(8))), rms_an={})
    for i in range(NIND):
        out["rms_an"][str(i)] = rms(load(path("r2", f"primary_{i:04d}_SUST_AN")), [AN_CELL(i)])
    json.dump(out, open(os.path.join(SEALED, "sham_calibration_v2.json"), "w"), indent=1)
    return out

if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "1":   # sustained twins + unperturbed twins
        tasks = [(t_sustained, (i, k)) for i in range(NIND) for k in ("DH", "DT", "AN")] + [(t_unp_fresh, (i,)) for i in range(NIND)] + [(t_unp_adult, (i,)) for i in range(NIND)]
        run_tasks(tasks, label="R2-1")
        print(calibrate_sham())
    elif stage == "2":
        tasks = [(t_pert, (i, k, t)) for t in ("ADULT", "DEV-LONG", "DEV-SHORT") for i in range(NIND) for k in ("DH", "DT", "AN", "SHAM_DH", "SHAM_AN")]
        run_tasks(tasks, label="R2-2")
