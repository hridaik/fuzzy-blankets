"""Protocol v2 helpers: absolute clock, continuations, individuals, metadata sidecars, parallel runner, outcome analysis."""
import hashlib, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(__file__))
from m2a_sim import simulate, load, unpack
from m2a_common import *

T_DEV = 32.0            # CANONICAL clock (published schedule)
T_DEV_SECONDARY = 512.0  # M1's effective census clock
B_ADULT = int(10 * T_DEV)  # 320: adult fixed point (1-s < 1e-8)
RAMP_W = 4              # raised-cosine on/off width (M1 TIMESCALES recommendation)
AN_CELL = lambda ind: ind % 8   # pre-declared single anomalous cell (0-based), as M1 intended (individual index mod 8)
V2 = os.path.join(DATA, "v2"); os.makedirs(V2, exist_ok=True)
_ENGINE = None

def engine_id():
    global _ENGINE
    if _ENGINE is None:
        h = hashlib.sha256()
        for f in sorted(os.listdir(M2A_ORACLE)):
            if f.endswith(".m"): h.update(open(os.path.join(M2A_ORACLE, f), "rb").read())
        h.update(open(os.path.join(SPM12, "spm_ADEM.m"), "rb").read())
        _ENGINE = "m2a-oracle+spm12-spm_ADEM:" + h.hexdigest()[:16]
    return _ENGINE

class Ind:
    """An individual = initial beliefs. primary idx: Octave randn(8,8)/8 after seeding (as M1); secondary idx: std exp(2)."""
    def __init__(self, kind, idx): self.kind, self.idx = kind, idx
    @property
    def name(self): return f"{self.kind}_{self.idx:04d}"
    def v0(self): return None if self.kind == "primary" else secondary_v0(self.idx)
    @property
    def seed(self): return self.idx if self.kind == "primary" else 0

def path(stage, name): 
    d = os.path.join(V2, stage); os.makedirs(d, exist_ok=True); return os.path.join(d, name + ".mat")

def sim(out, N, ind, T_dev=T_DEV, events=None, cont=None, GV1=None, noise_seed=None, noise_horizon=None, L=2, meta=None, force=False, kick=None, prec=None, V1=None):
    """One v2 segment. cont = path of previous segment's .mat (continuation on the SAME absolute clock) or None (fresh from b=0)."""
    if os.path.exists(out) and not force: return out
    t0 = time.time()
    simulate(out, N, seed=ind.seed, L=L, v0=ind.v0() if cont is None else None, ramp_mode="abs", ramp_ref=float(T_dev),
             events=events, engine="m2a", cont_file=cont, GV1=GV1, noise_seed=noise_seed, noise_horizon=noise_horizon, kick=kick, prec=prec, V1=V1)
    side = dict(protocol="v2", engine=engine_id(), individual=ind.name, T_dev=T_dev, N=N, continuation_of=cont,
                events=[{k: (np.asarray(v).tolist() if not isinstance(v, (str, int, float, type(None))) else v) for k, v in e.items()} for e in (events or [])],
                GV1=GV1, noise_seed=noise_seed, noise_horizon=noise_horizon, kick=None if kick is None else {k: (np.asarray(v).tolist() if not isinstance(v, str) else v) for k, v in kick.items()}, L=L, prec=prec, V1=V1, wall_s=time.time() - t0, meta=meta or {})
    json.dump(side, open(out[:-4] + ".json", "w"))
    return out

def run_tasks(tasks, workers=8, label=""):
    """tasks: list of (func, args) with module-level funcs. Runs in parallel, prints progress."""
    t0 = time.time(); done = 0; res = []
    with ProcessPoolExecutor(workers) as ex:
        futs = [ex.submit(f, *a) for f, a in tasks]
        for fu in futs:
            res.append(fu.result()); done += 1
            if done % max(1, len(tasks) // 20) == 0 or done == len(tasks):
                print(f"[{label}] {done}/{len(tasks)} {time.time()-t0:.0f}s", flush=True)
    return res

# ---- state / outcome analysis (hidden tier; audit only) ----
def state(m, b=-1, n=8):
    pos = m["positions"][:, b].reshape(n, 2).T; sec = m["secretion"][:, b].reshape(4, n, order="F"); v = m["v_expect"][:, b].reshape(n, n, order="F")
    return pos, sec, v

def speed_series(m):
    """per-bin max(position speed, secretion speed, belief speed) -- state-based stationarity metric (v2)."""
    dp = np.linalg.norm(np.diff(m["positions"], axis=1), axis=0); ds = np.linalg.norm(np.diff(m["secretion"], axis=1), axis=0)
    dv = np.linalg.norm(np.diff(m["v_expect"], axis=1), axis=0)
    return np.maximum(np.maximum(dp, ds), dv)

STAT_THR_V2 = 1e-6; STAT_WIN_V2 = 32   # DECLARED before analysis (THRESHOLDS_v2.md)
def stationary_bin(m, thr=STAT_THR_V2, win=STAT_WIN_V2, offset=0):
    """First (absolute) bin from which speed < thr for ALL later bins in the run (needs >= win bins); None if never."""
    sp = speed_series(m); ok = sp < thr
    if len(ok) < win or not ok[-win:].all(): return None
    bad = np.nonzero(~ok)[0]
    return int((bad.max() + 1 if len(bad) else 0) + 1 + offset)

def concat(paths, keys=("positions", "secretion", "v_expect")):
    ms = [load(p) for p in paths]
    out = {k: np.hstack([m[k] for m in ms]) for k in keys}
    out["n"] = ms[0]["n"]; return out

def lag_speed(m, L):
    return np.maximum.reduce([np.linalg.norm(m[k][:, L:] - m[k][:, :-L], axis=0) for k in ("positions", "secretion", "v_expect")])

def stationarity(m, offset=0, thr=STAT_THR_V2, win=STAT_WIN_V2):
    """v2 stationarity (declared after the W pilot found a period-2 cycle under sustained DH):
    FIXED  : lag-1 speed < thr for all later bins (>= win at the end);
    CYCLE2 : lag-1 speed >= thr at the end but lag-2 speed < thr for all later bins (period-2 limit cycle of the D-step map);
    None   : neither (NONCONVERGED). Returns dict(kind, bin) with bin absolute (offset = bins before this segment)."""
    for L, kind in ((1, "FIXED"), (2, "CYCLE2")):
        s = lag_speed(m, L)
        if len(s) < win + 1 or not (s[-win:] < thr).all(): continue
        bad = np.nonzero(s >= thr)[0]
        return dict(kind=kind, bin=int((bad.max() + 1 if len(bad) else 0) + L + offset))
    return dict(kind=None, bin=None)
