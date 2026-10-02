"""Part E: sham controls. For the same 20 individuals used in Part D, apply
a magnitude-matched random-Fourier-feature sham field instead of DH's
squared-position distortion, at the same 3 timings (DEV-SHORT, DEV-LONG,
ADULT). RMS-matched per-individual to that individual's SUSTAINED-DH twin
(declared scope: matched to DH only, not separately to DT/AN -- see
COMPUTE_PLAN.md's declared reduction).
"""
import json
import os
import sys
import time
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import scipy.io as sio

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M0B_SPM = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "sources", "spm12")
M0B_SPM_DEM = os.path.join(M0B_SPM, "toolbox", "DEM")
M0B_ORACLE = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "oracle")
M1_ORACLE = os.path.join(REPO_ROOT, "oracle")
WD_DIR = os.path.join(REPO_ROOT, "data", "withdrawal")
SHAM_DIR = os.path.join(REPO_ROOT, "data", "sham")
os.makedirs(SHAM_DIR, exist_ok=True)

W_BINS = 332
DEV_SHORT_OFF = 64
RAMP_W = 4
N_DEFAULT = 1024
K_FOURIER = 4
FREQ_RANGE = (0.1, 0.45)  # cycles per template unit, declared


def compute_dh_rms(sustained_dh_mat):
    d = sio.loadmat(sustained_dh_mat)
    pos = d["positions"]
    N = pos.shape[1]
    x1 = pos.T.reshape(N, 2, 8, order="F")[:, 0, :]
    distortion = x1 ** 2 - x1
    return float(np.sqrt(np.mean(distortion ** 2)))


def sham_params_for(ind_idx):
    rng = np.random.default_rng(600000 + ind_idx)
    freqs = rng.uniform(FREQ_RANGE[0], FREQ_RANGE[1], size=(K_FOURIER, 2))
    signs = rng.choice([-1, 1], size=(K_FOURIER, 2))
    freqs = freqs * signs
    phases_x = rng.uniform(0, 2 * np.pi, size=K_FOURIER)
    phases_y = rng.uniform(0, 2 * np.pi, size=K_FOURIER)
    return freqs, phases_x, phases_y


def _octave_run(script, timeout=1800):
    cmd = (f"source $(conda info --base)/etc/profile.d/conda.sh && conda activate octave-dem && "
           f"octave --no-gui --eval \"{script}\"")
    t0 = time.time()
    result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)
    elapsed = time.time() - t0
    if result.returncode != 0:
        raise RuntimeError(f"Octave failed: {result.stdout[-1500:]}\n{result.stderr[-1500:]}")
    return elapsed


def _save_call(out_mat):
    return (f"n=size(DEM.M(1).pE.x,2); m=size(DEM.M(1).pE.s,1); "
            f"positions=DEM.qU.a{{2}}(1:2*n,:); secretion=DEM.qU.a{{2}}(2*n+1:2*n+4*n,:); "
            f"v_expect=DEM.qU.v{{2}}; free_energy_J=DEM.J; target_x=DEM.M(1).pE.x; "
            f"target_s=DEM.M(1).pE.s; "
            f"save('-v7','{out_mat}','positions','secretion','v_expect','free_energy_J','target_x','target_s','n','m');")


def _param_struct(scale, freqs, phx, phy, off_bin, n_bins):
    freq_str = "[" + ";".join(f"{f[0]} {f[1]}" for f in freqs) + "]"
    phx_str = "[" + " ".join(str(p) for p in phx) + "]"
    phy_str = "[" + " ".join(str(p) for p in phy) + "]"
    off_clause = f"{off_bin}" if off_bin is not None else "[]"
    return (f"struct('kind','sham','cells',[],'ramp_w',{RAMP_W},'ramp_onset_bin',1,"
            f"'off_bin',{off_clause},'n_bins',{n_bins},'sham_freqs',{freq_str},"
            f"'sham_phases_x',{phx_str},'sham_phases_y',{phy_str},'sham_scale',{scale})")


def _job(args):
    ind_idx, timing = args
    sustained_dh = os.path.join(WD_DIR, f"primary_{ind_idx:04d}_DH_SUSTAINED_N1024.mat")
    if not os.path.exists(sustained_dh):
        return {"individual_idx": ind_idx, "timing": timing, "status": "error",
                "error": f"missing SUSTAINED-DH twin: {sustained_dh}"}
    rms = compute_dh_rms(sustained_dh)
    freqs, phx, phy = sham_params_for(ind_idx)

    out_mat = os.path.join(SHAM_DIR, f"primary_{ind_idx:04d}_sham_{timing}_N{N_DEFAULT}.mat")
    try:
        if timing in ("DEV-SHORT", "DEV-LONG"):
            off_bin = DEV_SHORT_OFF if timing == "DEV-SHORT" else W_BINS
            params = _param_struct(rms, freqs, phx, phy, off_bin, N_DEFAULT)
            script = (
                f"addpath('{M0B_SPM}'); addpath('{M0B_SPM_DEM}'); addpath('{M0B_ORACLE}'); addpath('{M1_ORACLE}'); "
                f"global PERTURBATION; PERTURBATION = {params}; "
                f"DEM = dem_setup_perturbed(2,{N_DEFAULT},{ind_idx},[],[],[]); "
                f"DEM = spm_ADEM(DEM); " + _save_call(out_mat)
            )
            elapsed = _octave_run(script)
        elif timing == "ADULT":
            census_mat = os.path.join(REPO_ROOT, "data", "census", f"primary_{ind_idx:04d}_N512.mat")
            d = sio.loadmat(census_mat)
            v0 = d["v_expect"][:, -1].reshape(8, 8, order="F")
            a_x0 = d["positions"][:, -1].reshape(2, 8, order="F")
            a_s0 = d["secretion"][:, -1].reshape(4, 8, order="F")
            fd, state_mat = tempfile.mkstemp(suffix=".mat", dir=SHAM_DIR)
            os.close(fd)
            sio.savemat(state_mat, {"v0": v0, "a_x0": a_x0, "a_s0": a_s0})
            params = _param_struct(rms, freqs, phx, phy, W_BINS, N_DEFAULT)
            script = (
                f"addpath('{M0B_SPM}'); addpath('{M0B_SPM_DEM}'); addpath('{M0B_ORACLE}'); addpath('{M1_ORACLE}'); "
                f"global PERTURBATION; PERTURBATION = {params}; "
                f"S=load('{state_mat}'); "
                f"DEM = dem_setup_from_state(2,{N_DEFAULT},{ind_idx},S.v0,S.a_x0,S.a_s0,true); "
                f"DEM = spm_ADEM(DEM); " + _save_call(out_mat)
            )
            elapsed = _octave_run(script)
            os.remove(state_mat)
        else:
            raise ValueError(timing)
    except Exception as e:
        return {"individual_idx": ind_idx, "timing": timing, "status": "error", "error": str(e)[-2000:]}

    return {"individual_idx": ind_idx, "timing": timing, "status": "ok",
            "elapsed": elapsed, "dh_rms_matched": rms, "out_mat": out_mat,
            "engine": "fallback_octave_subprocess"}


if __name__ == "__main__":
    jobs = [(i, t) for i in range(20) for t in ("DEV-SHORT", "DEV-LONG", "ADULT")]
    print(f"{len(jobs)} sham runs queued")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_job, j): j for j in jobs}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"  [{len(results)}/{len(jobs)}] ind{r['individual_idx']} {r['timing']}: "
                  f"{r['status']} ({r.get('elapsed', 0):.1f}s)", flush=True)
    total = time.time() - t0
    print(f"Total: {total:.1f}s")
    with open(os.path.join(SHAM_DIR, "sham_manifest.json"), "w") as f:
        json.dump({"total_wall_s": total, "results": results}, f, indent=2, default=str)
