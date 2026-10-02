"""Part D (Tier 1: Kuchling DH/DT/AN) + Part E (sham) withdrawal runs.

Timings:
  DEV-SHORT: on from bin0 (fresh individual), off at bin 64
  DEV-LONG:  on from bin0, off at bin W=332 (measured: stationarity bin of
             SUSTAINED kuchling_head on the canonical individual -- the
             larger of DH=332/DT=246, declared fixed for all conditions)
  ADULT:     starts from the individual's Part-B converged state, perturbed
             from bin0 (of this NEW run) for W=332 bins, then off
Horizon: N=1024 throughout (covers on-time + post-off reconvergence with
margin, per COMPUTE_PLAN.md), cascade to N=2048 if not stationary.

SUSTAINED twin: perturbation never switched off, run to stationarity
(reuses N=512/2048 cascade like Part B, since DH/DT's own sustained
stationarity bins, 332/246, are well under 512).
"""
import json
import os
import sys
import time
import hashlib
import tempfile
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import scipy.io as sio

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M0B_SPM = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "sources", "spm12")
M0B_SPM_DEM = os.path.join(M0B_SPM, "toolbox", "DEM")
M0B_ORACLE = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "oracle")
M1_ORACLE = os.path.join(REPO_ROOT, "oracle")
CENSUS_DIR = os.path.join(REPO_ROOT, "data", "census")
WD_DIR = os.path.join(REPO_ROOT, "data", "withdrawal")
os.makedirs(WD_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(REPO_ROOT, "code"))

W_BINS = 332  # DEV-LONG / ADULT off-bin, per module docstring
DEV_SHORT_OFF = 64
RAMP_W = 4  # justified in TIMESCALES.md / WITHDRAWAL.md from m0c's ramp-width check
N_DEFAULT = 1024
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


def run_fresh_perturbed(seed, kind, off_bin, n_bins, out_mat):
    """DEV-SHORT / DEV-LONG / SUSTAINED: fresh individual (bin0), perturbed."""
    off_clause = f"{off_bin}" if off_bin is not None else "[]"
    script = (
        f"addpath('{M0B_SPM}'); addpath('{M0B_SPM_DEM}'); addpath('{M0B_ORACLE}'); addpath('{M1_ORACLE}'); "
        f"global PERTURBATION; PERTURBATION = struct('kind','{kind}','cells',[],"
        f"'ramp_w',{RAMP_W},'ramp_onset_bin',1,'off_bin',{off_clause},'n_bins',{n_bins}); "
        f"DEM = dem_setup_perturbed(2,{n_bins},{seed},[],[],[]); "
        f"DEM = spm_ADEM(DEM); "
        + _save_call(out_mat)
    )
    return _octave_run(script)


def run_adult_perturbed(census_mat, seed, kind, off_bin, n_bins, out_mat):
    """ADULT: starts from the Part-B converged state, perturbed from bin0
    of THIS run for off_bin bins, then off."""
    d = sio.loadmat(census_mat)
    pos = d["positions"]; sec = d["secretion"]
    v0 = d["v_expect"][:, -1].reshape(8, 8, order="F")
    a_x0 = pos[:, -1].reshape(2, 8, order="F")
    a_s0 = sec[:, -1].reshape(4, 8, order="F")
    fd, state_mat = tempfile.mkstemp(suffix=".mat", dir=WD_DIR)
    os.close(fd)
    sio.savemat(state_mat, {"v0": v0, "a_x0": a_x0, "a_s0": a_s0})
    script = (
        f"addpath('{M0B_SPM}'); addpath('{M0B_SPM_DEM}'); addpath('{M0B_ORACLE}'); addpath('{M1_ORACLE}'); "
        f"global PERTURBATION; PERTURBATION = struct('kind','{kind}','cells',[],"
        f"'ramp_w',{RAMP_W},'ramp_onset_bin',1,'off_bin',{off_bin},'n_bins',{n_bins}); "
        f"S=load('{state_mat}'); "
        f"DEM = dem_setup_from_state(2,{n_bins},{seed},S.v0,S.a_x0,S.a_s0,true); "
        f"DEM = spm_ADEM(DEM); "
        + _save_call(out_mat)
    )
    elapsed = _octave_run(script)
    os.remove(state_mat)
    return elapsed


def config_hash():
    h = hashlib.sha256()
    for p in [os.path.join(M1_ORACLE, "dem_morphogenesis_Gg_perturbed.m"),
              os.path.join(M1_ORACLE, "dem_setup_from_state.m")]:
        if os.path.exists(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:16]


def _job(args):
    ind_idx, kind, timing, an_cell_seed = args
    kind_oct = {"DH": "kuchling_head", "DT": "kuchling_tail", "AN": "kuchling_head"}[kind]
    cells_note = None
    if kind == "AN":
        cells_note = an_cell_seed % 8  # pre-declared per-individual cell for AN
    out_mat = os.path.join(WD_DIR, f"primary_{ind_idx:04d}_{kind}_{timing}_N{N_DEFAULT}.mat")
    try:
        if timing == "DEV-SHORT":
            elapsed = run_fresh_perturbed(ind_idx, kind_oct, DEV_SHORT_OFF, N_DEFAULT, out_mat)
        elif timing == "DEV-LONG":
            elapsed = run_fresh_perturbed(ind_idx, kind_oct, W_BINS, N_DEFAULT, out_mat)
        elif timing == "ADULT":
            census_mat = os.path.join(CENSUS_DIR, f"primary_{ind_idx:04d}_N512.mat")
            if not os.path.exists(census_mat):
                census_mat = os.path.join(CENSUS_DIR, f"primary_{ind_idx:04d}_N2048.mat")
            elapsed = run_adult_perturbed(census_mat, ind_idx, kind_oct, W_BINS, N_DEFAULT, out_mat)
        elif timing == "SUSTAINED":
            elapsed = run_fresh_perturbed(ind_idx, kind_oct, None, 512, out_mat)
        else:
            raise ValueError(timing)
    except Exception as e:
        return {"individual_idx": ind_idx, "kind": kind, "timing": timing,
                "status": "error", "error": str(e)[-2000:]}

    mat = sio.loadmat(out_mat)
    stat, stat_bin = is_stationary(mat)
    return {
        "individual_idx": ind_idx, "kind": kind, "timing": timing, "status": "ok",
        "elapsed": elapsed, "stationary": stat, "stationary_at_bin": stat_bin,
        "out_mat": out_mat, "an_cell": cells_note,
        "engine": "fallback_octave_subprocess", "engine_config_hash": config_hash(),
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="all", choices=["all", "sustained", "withdrawal"])
    args = ap.parse_args()

    jobs = []
    for i in range(20):
        for kind in ("DH", "DT", "AN"):
            if args.which in ("all", "sustained"):
                jobs.append((i, kind, "SUSTAINED", i))
            if args.which in ("all", "withdrawal"):
                for timing in ("DEV-SHORT", "DEV-LONG", "ADULT"):
                    jobs.append((i, kind, timing, i))

    print(f"{len(jobs)} withdrawal/sustained runs queued")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_job, j): j for j in jobs}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"  [{len(results)}/{len(jobs)}] ind{r['individual_idx']} {r['kind']}/{r['timing']}: "
                  f"{r['status']} ({r.get('elapsed', 0):.1f}s)", flush=True)
    total = time.time() - t0
    print(f"Total: {total:.1f}s")
    with open(os.path.join(WD_DIR, f"withdrawal_manifest_{args.which}.json"), "w") as f:
        json.dump({"total_wall_s": total, "results": results}, f, indent=2, default=str)
