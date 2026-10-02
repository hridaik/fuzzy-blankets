"""Part 0.3c variant B: continue to 2048 bins with the N=512 ramp schedule held in ABSOLUTE bins
(s = 1-exp(-2*bin/512), i.e. what 'the same run, longer' means; plain N=2048 rescales the ramp)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from m2a_sim import *
from concurrent.futures import ProcessPoolExecutor
def job(a):
    name, v0, seed = a
    simulate(f"{DATA}/part0/longabs_{name}_N2048.mat", 2048, seed=seed, v0=v0, ramp_mode="abs", ramp_ref=512.0)
    return name
if __name__ == "__main__":
    jobs = [("primary_0000", None, 0), ("primary_0001", None, 1), ("secondary_0000", secondary_v0(0), 0)]
    with ProcessPoolExecutor(3) as ex:
        for r in ex.map(job, jobs): print(r, flush=True)
