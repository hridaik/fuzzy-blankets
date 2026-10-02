"""M1-comparable AN correction (protocol v1 settings, EXACT): the pipeline of m1 run_withdrawal.py with the single anomalous cell
actually passed ('cells' = [an_cell+1], 1-based). 20 individuals x {DEV-SHORT, DEV-LONG, ADULT} at N=1024 (M1 timings 64 / 332 / 332)
+ 20 SUSTAINED AN twins at N=512. Reuses data/twins (matched unperturbed twins, N=1024). Writes only into m2a data."""
import os, sys, json, time, tempfile
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(__file__))
from m2a_common import *
OUT = os.path.join(DATA, "v1_an"); os.makedirs(OUT, exist_ok=True)
W_BINS, SHORT_OFF, RAMP_W, N_DEFAULT = 332, 64, 4, 1024

def run(i, timing):
    cell = i % 8 + 1                                  # M1's pre-declared AN cell (1-based for Octave)
    out = os.path.join(OUT, f"primary_{i:04d}_ANfix_{timing}.mat")
    if os.path.exists(out): return out
    save = ("n=size(DEM.M(1).pE.x,2); positions=DEM.qU.a{2}(1:2*n,:); secretion=DEM.qU.a{2}(2*n+1:6*n,:); "
            "v_expect=DEM.qU.v{2}; free_energy_J=DEM.J; ")
    save += f"save('-v7','{out}','positions','secretion','v_expect','free_energy_J');"
    if timing == "SUSTAINED": off, N = "[]", 512
    else: off, N = (SHORT_OFF if timing == "DEV-SHORT" else W_BINS), N_DEFAULT
    pert = (f"global PERTURBATION; PERTURBATION = struct('kind','kuchling_head','cells',[{cell}],'ramp_w',{RAMP_W},"
            f"'ramp_onset_bin',1,'off_bin',{off},'n_bins',{N}); ")
    if timing == "ADULT":
        d = sio.loadmat(f"{M1}/data/census/primary_{i:04d}_N512.mat")
        st = os.path.join(OUT, f"state_{i:04d}.mat")
        sio.savemat(st, {"v0": d["v_expect"][:, -1].reshape(8, 8, order="F"), "a_x0": d["positions"][:, -1].reshape(2, 8, order="F"),
                         "a_s0": d["secretion"][:, -1].reshape(4, 8, order="F")})
        setup = f"S=load('{st}'); DEM = dem_setup_from_state(2,{N},{i},S.v0,S.a_x0,S.a_s0,true); "
    else:
        setup = f"DEM = dem_setup_perturbed(2,{N},{i},[],[],[]); "
    octave(pert + setup + "DEM = spm_ADEM(DEM); " + save)
    return out

if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    jobs = [(i, t) for t in ("SUSTAINED", "DEV-SHORT", "DEV-LONG", "ADULT") for i in range(20)]
    t0 = time.time()
    with ProcessPoolExecutor(8) as ex:
        futs = [ex.submit(run, *j) for j in jobs]
        for k, f in enumerate(futs):
            f.result()
            if k % 8 == 7: print(k + 1, len(jobs), round(time.time() - t0), flush=True)
