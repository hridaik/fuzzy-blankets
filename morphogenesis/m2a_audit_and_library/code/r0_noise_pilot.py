"""R0.3: pilot process-noise precision G(1).V (SPM's own mechanism) from the adult state (continuation at b=320, T_dev=32).
Noise smoothness: spm_DEM_z with M(1).E.s = 1 bin (Gaussian kernel, as SPM). RMS positional fluctuation = RMS over cells and
coordinates of the time-std of position over the last 300 bins, vs reference-phenotype nearest-neighbour spacing."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from m2a_sim import *
from concurrent.futures import ProcessPoolExecutor
D = DATA + "/r0/"; KW = dict(seed=0, ramp_mode="abs", ramp_ref=32.0, engine="m2a")
KS = [3, 5, 7, 9, 11, 13, 15, 16]

def job(k):
    simulate(D + f"noise_pilot_k{k}.mat", 400, cont_file=D + "split320_A.mat", GV1=np.exp(k), noise_seed=5, noise_horizon=720, **KW)
    return k

if __name__ == "__main__":
    with ProcessPoolExecutor(8) as ex:
        for k in ex.map(job, KS): print(k, flush=True)
