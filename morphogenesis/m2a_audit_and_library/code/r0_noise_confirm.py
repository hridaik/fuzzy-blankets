import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from m2a_sim import *
from concurrent.futures import ProcessPoolExecutor
D = DATA + "/r0/"; KW = dict(seed=0, ramp_mode="abs", ramp_ref=32.0, engine="m2a")
def job(a):
    k, sd = a
    simulate(D + f"noise_conf_k{k}_s{sd}.mat", 400, cont_file=D + "split320_A.mat", GV1=np.exp(k), noise_seed=sd, noise_horizon=720, **KW); return a
if __name__ == "__main__":
    with ProcessPoolExecutor(8) as ex:
        for r in ex.map(job, [(k, s) for k in (10.6, 8.4, 6.0) for s in (11, 12, 13)]): print(r, flush=True)
