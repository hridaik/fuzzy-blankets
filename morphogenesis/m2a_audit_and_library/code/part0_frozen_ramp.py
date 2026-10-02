"""Part 0.3b control: freeze the developmental ramp (s = const for all bins) and test whether the M1
stationarity criterion still fires at bin 246 / whether individuals still converge to the same state."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from m2a_sim import *
from concurrent.futures import ProcessPoolExecutor
OUT = os.path.join(DATA, "part0"); 
def job(a):
    name, s, v0, seed = a
    simulate(f"{OUT}/frozen_{name}.mat", 512, seed=seed, v0=v0, ramp_mode="const", ramp_const=s)
    return name
if __name__ == "__main__":
    jobs = [("primary0000_s0617", 0.617, None, 0), ("primary0000_s0865", 0.865, None, 0),
            ("secondary0000_s0617", 0.617, secondary_v0(0), 0), ("primary0001_s0617", 0.617, None, 1)]
    with ProcessPoolExecutor(4) as ex:
        for r in ex.map(job, jobs): print(r, flush=True)
