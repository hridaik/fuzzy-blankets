"""Direction sets for D4 (class-0 base)."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from d4 import *
import p2_library as PL

BR_DISP = (0.05, 10.0); BR_PULSE = (0.05, 50.0)

def dirs_disp1(): return [dict(id=f"disp1_r{r}_t{int(t)}", kind="disp1", role=r, theta=t, br=BR_DISP) for r in range(8) for t in np.arange(0, 360, 22.5)]
def dirs_body(eig_dirs=None):
    out = []
    if eig_dirs is not None:
        for k, u in enumerate(eig_dirs): out.append(dict(id=f"body_eig{k}", kind="body", u=(np.asarray(u) / np.linalg.norm(u)).tolist(), br=BR_DISP))
    rng = np.random.default_rng(424242)
    for k in range(20):
        u = rng.standard_normal(16); out.append(dict(id=f"body_rand{k:02d}", kind="body", u=(u / np.linalg.norm(u)).tolist(), br=BR_DISP))
    return out
def dirs_pulse_single():
    B = base_info(); return [dict(id=f"pulsec_r{r}_l{l}", kind="pulse", type="sec", cells=[B["cell_of_slot"][r]], ch=l, br=BR_PULSE) for r in range(8) for l in (1, 2, 3, 4)]
def dirs_region():
    B = base_info(); out = []
    for gi, (cx, cy) in enumerate(PL.region_centres(B["pos"])):
        ins = [int(c) for c in range(8) if np.hypot(B["pos"][0, c] - cx, B["pos"][1, c] - cy) <= PL.DISC_RADIUS]
        if not ins: continue
        for l in (1, 2, 3, 4): out.append(dict(id=f"region_g{gi}_l{l}", kind="pulse", type="sec", cells=ins, ch=l, centre=[cx, cy], br=BR_PULSE))
    return out
def dirs_global(): return [dict(id=f"global_l{l}", kind="pulse", type="sec", cells=list(range(8)), ch=l, br=BR_PULSE) for l in (1, 2, 3, 4)]

def job(spec): return find(spec, *spec["br"])
