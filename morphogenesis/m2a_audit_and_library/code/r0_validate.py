"""R0 validation: R0.1 clock control, R0.2(a) split continuation, R0.2(b) null continuation, ablations."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from m2a_sim import *
from concurrent.futures import ProcessPoolExecutor
D = DATA + "/r0/"; H = 1100; TD = 32.0
KW = dict(seed=0, ramp_mode="abs", ramp_ref=TD, engine="m2a")

def chain(b0):
    simulate(D + f"split{b0}_A.mat", b0, **KW)
    simulate(D + f"split{b0}_B.mat", H - b0, cont_file=D + f"split{b0}_A.mat", **KW)
    return b0

def single(_):
    simulate(D + "single.mat", H, **KW); return "single"

def clock512(_):
    simulate(D + "clock512.mat", 512, seed=0, ramp_mode="abs", ramp_ref=512.0, engine="m2a"); return "clock512"

def ablation(ab):
    simulate(D + f"abl_{ab}.mat", 60, cont_file=D + "split300_A.mat", ablate=ab, **KW); return ab

if __name__ == "__main__":
    # ablations need split300_A first
    with ProcessPoolExecutor(8) as ex:
        futs = [ex.submit(single, 0), ex.submit(clock512, 0)] + [ex.submit(chain, b) for b in (64, 300, 320, 1000)]
        for f in futs: print(f.result(), flush=True)
        futs = [ex.submit(ablation, a) for a in ("Ahist", "pu", "qu_hi", "qa", "qv0")]
        for f in futs: print(f.result(), flush=True)
