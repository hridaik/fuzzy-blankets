"""Part C: robustness of converged bodies. Takes the first 20 primary
individuals by ID (regardless of census class), applies 4 kick types
(K1 at 2 sigmas, K2, K3, K4 = 5 conditions), re-runs to stationarity.
"""
import json
import os
import sys
import time
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import scipy.io as sio

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M0C_CODE = os.path.join(REPO_ROOT, "..", "m0c_port_completion", "code")
CENSUS_DIR = os.path.join(REPO_ROOT, "data", "census")
KICK_DIR = os.path.join(REPO_ROOT, "data", "kicks")
os.makedirs(KICK_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(REPO_ROOT, "code"))
from analysis import nearest_neighbour_spacing  # noqa: E402

MEAN_NN_SPACING = float(nearest_neighbour_spacing().mean())
STATIONARITY_THR = 1.0e-3
STATIONARITY_WINDOW = 32


def is_stationary(mat, thr=STATIONARITY_THR, window=STATIONARITY_WINDOW):
    pos = mat["positions"]
    sec = mat["secretion"]
    dx = np.linalg.norm(np.diff(pos, axis=1), axis=0)
    ds = np.linalg.norm(np.diff(sec, axis=1), axis=0)
    below = (dx < thr) & (ds < thr)
    for i in range(len(below) - window + 1):
        if below[i:i + window].all():
            return True, i + 1
    return False, None


def load_final_state(census_mat_path, n_cells=8):
    d = sio.loadmat(census_mat_path)
    pos = d["positions"]
    sec = d["secretion"]
    N = pos.shape[1]
    a_x_final = pos[:, -1].reshape(2, n_cells, order="F")
    a_s_final = sec[:, -1].reshape(4, n_cells, order="F")
    v_final = d["v_expect"][:, -1].reshape(n_cells, n_cells, order="F")
    return a_x_final, a_s_final, v_final


def apply_kick(kind, a_x, a_s, v, seed, individual_idx):
    rng = np.random.default_rng(500000 + seed)
    a_x2, a_s2, v2 = a_x.copy(), a_s.copy(), v.copy()
    log = {"kind": kind}
    if kind == "K1_sigma0.5":
        sigma = 0.5 * MEAN_NN_SPACING
        a_x2 = a_x + rng.normal(scale=sigma, size=a_x.shape)
        log["sigma"] = sigma
    elif kind == "K1_sigma1.5":
        sigma = 1.5 * MEAN_NN_SPACING
        a_x2 = a_x + rng.normal(scale=sigma, size=a_x.shape)
        log["sigma"] = sigma
    elif kind == "K2":
        mean_code = a_s.mean(axis=1, keepdims=True)
        a_s2 = np.tile(mean_code, (1, a_s.shape[1]))
    elif kind == "K3":
        v2 = rng.standard_normal(v.shape) / 8.0
    elif kind == "K4":
        # one pre-declared cell (by seed) displaced by 3 spacing units
        cell = individual_idx % 8
        direction = rng.standard_normal(2)
        direction = direction / np.linalg.norm(direction)
        a_x2[:, cell] = a_x[:, cell] + 3.0 * MEAN_NN_SPACING * direction
        log["cell"] = int(cell)
    else:
        raise ValueError(kind)
    return a_x2, a_s2, v2, log


def config_hash():
    h = hashlib.sha256()
    for base, fname in [
        (os.path.join(REPO_ROOT, "..", "m0b_reference_port", "oracle"), "dem_morphogenesis_Mg.m"),
        (os.path.join(REPO_ROOT, "oracle"), "dem_setup_from_state.m"),
    ]:
        p = os.path.join(base, fname)
        if os.path.exists(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:16]


def _job(args):
    ind_idx, kind = args
    sys.path.insert(0, M0C_CODE)
    census_path = os.path.join(CENSUS_DIR, f"primary_{ind_idx:04d}_N512.mat")
    if not os.path.exists(census_path):
        census_path = os.path.join(CENSUS_DIR, f"primary_{ind_idx:04d}_N2048.mat")
    a_x, a_s, v = load_final_state(census_path)
    a_x2, a_s2, v2, klog = apply_kick(kind, a_x, a_s, v, ind_idx, ind_idx)

    out_mat = os.path.join(KICK_DIR, f"primary_{ind_idx:04d}_{kind}_N512.mat")
    script = (
        f"addpath('{os.path.join(REPO_ROOT, '..', 'm0b_reference_port', 'sources', 'spm12')}'); "
        f"addpath('{os.path.join(REPO_ROOT, '..', 'm0b_reference_port', 'sources', 'spm12', 'toolbox', 'DEM')}'); "
        f"addpath('{os.path.join(REPO_ROOT, '..', 'm0b_reference_port', 'oracle')}'); "
        f"addpath('{os.path.join(REPO_ROOT, 'oracle')}'); "
    )
    import subprocess
    import tempfile
    fd, state_mat = tempfile.mkstemp(suffix=".mat", dir=KICK_DIR)
    os.close(fd)
    sio.savemat(state_mat, {"v0": v2, "a_x0": a_x2, "a_s0": a_s2})
    octave_script = script + (
        f"S=load('{state_mat}'); "
        f"DEM=dem_setup_from_state(2,512,{ind_idx},S.v0,S.a_x0,S.a_s0,false); "
        f"tic; DEM=spm_ADEM(DEM); el=toc; "
        f"n=size(DEM.M(1).pE.x,2); m=size(DEM.M(1).pE.s,1); "
        f"positions=DEM.qU.a{{2}}(1:2*n,:); secretion=DEM.qU.a{{2}}(2*n+1:2*n+4*n,:); "
        f"v_expect=DEM.qU.v{{2}}; free_energy_J=DEM.J; target_x=DEM.M(1).pE.x; "
        f"target_s=DEM.M(1).pE.s; "
        f"save('-v7','{out_mat}','positions','secretion','v_expect','free_energy_J','elapsed','target_x','target_s','n','m'); "
    ).replace("elapsed", "el")
    t0 = time.time()
    cmd = f"source $(conda info --base)/etc/profile.d/conda.sh && conda activate octave-dem && octave --no-gui --eval \"{octave_script}\""
    result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=1800)
    elapsed = time.time() - t0
    os.remove(state_mat)
    if result.returncode != 0:
        return {"individual_idx": ind_idx, "kick": kind, "status": "error",
                "error": result.stdout[-2000:] + result.stderr[-2000:], "elapsed": elapsed,
                "kick_log": klog}

    mat = sio.loadmat(out_mat)
    stat, stat_bin = is_stationary(mat)
    j = mat["free_energy_J"][0]
    has_nan = bool(np.isnan(j).any() or np.isinf(j).any())
    return {
        "individual_idx": ind_idx, "kick": kind, "status": "ok",
        "elapsed": elapsed, "stationary": stat, "stationary_at_bin": stat_bin,
        "nan_or_inf_free_energy": has_nan, "out_mat": out_mat,
        "kick_log": klog, "engine": "fallback_octave_subprocess",
        "engine_config_hash": config_hash(),
    }


if __name__ == "__main__":
    kick_kinds = ["K1_sigma0.5", "K1_sigma1.5", "K2", "K3", "K4"]
    jobs = [(i, k) for i in range(20) for k in kick_kinds]
    print(f"{len(jobs)} kick runs queued")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_job, j): j for j in jobs}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"  [{len(results)}/{len(jobs)}] ind{r['individual_idx']} {r['kick']}: "
                  f"{r['status']} ({r['elapsed']:.1f}s)", flush=True)
    total = time.time() - t0
    print(f"Total: {total:.1f}s")
    with open(os.path.join(KICK_DIR, "kicks_manifest.json"), "w") as f:
        json.dump({"total_wall_s": total, "results": results}, f, indent=2, default=str)
