import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from m2a_sim import *
D = DATA + "/r0/"; KW = dict(seed=0, ramp_mode="abs", ramp_ref=32.0, engine="m2a", GV1=np.exp(8.4), noise_seed=11, noise_horizon=720)
simulate(D + "nsplit_A.mat", 200, cont_file=D + "split320_A.mat", **KW)
simulate(D + "nsplit_B.mat", 200, cont_file=D + "nsplit_A.mat", **KW)
