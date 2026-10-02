"""Part 0.1c compute: matched UNPERTURBED twins of M1's withdrawal runs, using
the identical M1 pipeline (dem_setup_perturbed / dem_setup_from_state, N=1024)
with PERTURBATION.kind='none'. M1 never stored these (it compared end-states
to the N=512 census), so deviation-during-window could not be computed."""
import json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(__file__))
from m2a_common import *

OUT = os.path.join(DATA, "twins"); os.makedirs(OUT, exist_ok=True)
SAVE = ("n=size(DEM.M(1).pE.x,2); positions=DEM.qU.a{2}(1:2*n,:); secretion=DEM.qU.a{2}(2*n+1:6*n,:); "
        "v_expect=DEM.qU.v{2}; free_energy_J=DEM.J; ")

def job(a):
    kind, i = a
    out = os.path.join(OUT, f"primary_{i:04d}_UNPERT_{kind}_N1024.mat")
    if os.path.exists(out): return (a, 0)
    pert = "global PERTURBATION; PERTURBATION = struct('kind','none','cells',[],'ramp_w',4,'ramp_onset_bin',1,'n_bins',1024); "
    if kind == "FRESH":
        s = pert + f"DEM = dem_setup_perturbed(2,1024,{i},[],[],[]); "
    else:
        c = os.path.join(M1, "data", "census", f"primary_{i:04d}_N512.mat")
        d = sio.loadmat(c)
        st = os.path.join(OUT, f"state_{i:04d}.mat")
        sio.savemat(st, {"v0": d["v_expect"][:, -1].reshape(8, 8, order="F"),
                         "a_x0": d["positions"][:, -1].reshape(2, 8, order="F"),
                         "a_s0": d["secretion"][:, -1].reshape(4, 8, order="F")})
        s = pert + f"S=load('{st}'); DEM = dem_setup_from_state(2,1024,{i},S.v0,S.a_x0,S.a_s0,true); "
    t0 = time.time()
    octave(s + "DEM = spm_ADEM(DEM); " + SAVE + f"save('-v7','{out}','positions','secretion','v_expect','free_energy_J');")
    return (a, time.time() - t0)

if __name__ == "__main__":
    jobs = [(k, i) for i in range(20) for k in ("FRESH", "ADULT")]
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(job, jobs): print(r, flush=True)
