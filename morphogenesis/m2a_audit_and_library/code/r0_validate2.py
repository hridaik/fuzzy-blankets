"""R0.2 extras: ablations at a DYNAMIC split point (b0=64, T_dev=32) and a split at b0=300 on the slow T_dev=512 clock (non-zero speed)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from m2a_sim import *
from concurrent.futures import ProcessPoolExecutor
D = DATA + "/r0/"; KW = dict(seed=0, ramp_mode="abs", ramp_ref=32.0, engine="m2a")
def abl(ab): simulate(D + f"abl64_{ab}.mat", 40, cont_file=D + "split64_A.mat", ablate=ab, **KW); return ab
def t512(_):
    k = dict(seed=0, ramp_mode="abs", ramp_ref=512.0, engine="m2a")
    simulate(D + "t512_single.mat", 400, **k); return "t512_single"
def t512split(_):
    k = dict(seed=0, ramp_mode="abs", ramp_ref=512.0, engine="m2a")
    simulate(D + "t512_A.mat", 300, **k); simulate(D + "t512_B.mat", 100, cont_file=D + "t512_A.mat", **k); return "t512_split"
if __name__ == "__main__":
    with ProcessPoolExecutor(8) as ex:
        fs = [ex.submit(abl, a) for a in ("Ahist", "pu", "qu_hi", "qa", "qv0")] + [ex.submit(t512, 0), ex.submit(t512split, 0)]
        for f in fs: print(f.result(), flush=True)
