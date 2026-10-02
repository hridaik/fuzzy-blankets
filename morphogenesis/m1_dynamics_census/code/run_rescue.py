"""Part A: rescue implementation fix. Canonical individual (seed 0) + 10
census individuals (seeds 1..10), AN alone vs R-text vs R-caption (sweep
1.5/2/4), anomalous perturbation SUSTAINED (N=512), cell chosen fixed
(cell index 5, 1-based -- a non-endpoint, non-symmetric cell) for all
individuals for comparability; each run also checked for a "position
switch" (whether the Hungarian role-map for the anomalous cell's original
target slot ends up held by a DIFFERENT cell than in the unperturbed twin).
"""
import json
import os
import sys
import time
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M0B_SPM = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "sources", "spm12")
M0B_SPM_DEM = os.path.join(M0B_SPM, "toolbox", "DEM")
M0B_ORACLE = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "oracle")
M1_ORACLE = os.path.join(REPO_ROOT, "oracle")
DATA_DIR = os.path.join(REPO_ROOT, "data", "rescue")
os.makedirs(DATA_DIR, exist_ok=True)

ANOMALOUS_CELL = 5  # 1-based Octave cell index, fixed across individuals


def _job(args):
    kind, ind_idx, extra = args

    params = {"cells": [ANOMALOUS_CELL], "ramp_w": 4, "ramp_onset_bin": 1,
              "anomaly_sign": 1}
    if kind == "R-caption":
        params["rescue_factor"] = extra
        tag = f"Rcaption_f{extra}"
    elif kind == "R-text":
        tag = "Rtext"
    elif kind == "AN":
        tag = "AN"
    else:
        raise ValueError(kind)

    out_mat = os.path.join(DATA_DIR, f"ind{ind_idx:03d}_{tag}_N512.mat")
    oct_kind = {"AN": "kuchling_head", "R-text": "kuchling_rescue_text",
                "R-caption": "kuchling_rescue_caption"}[kind]

    param_str = f"struct('cells',[{ANOMALOUS_CELL}],'ramp_w',4,'ramp_onset_bin',1,'anomaly_sign',1"
    if kind == "R-caption":
        param_str += f",'rescue_factor',{extra}"
    param_str += ")"

    script = (
        f"addpath('{M0B_SPM}'); addpath('{M0B_SPM_DEM}'); addpath('{M0B_ORACLE}'); addpath('{M1_ORACLE}'); "
        f"params = {param_str}; params.kind='{oct_kind}'; "
        f"run_perturbed('{oct_kind}', params, 512, {ind_idx}, '{out_mat}');"
    )
    cmd = (f"source $(conda info --base)/etc/profile.d/conda.sh && conda activate octave-dem && "
           f"octave --no-gui --eval \"{script}\"")
    t0 = time.time()
    result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=1800)
    elapsed = time.time() - t0
    if result.returncode != 0:
        return {"kind": kind, "individual": ind_idx, "tag": tag, "status": "error",
                "error": (result.stdout + result.stderr)[-2000:], "elapsed": elapsed}
    return {"kind": kind, "individual": ind_idx, "tag": tag, "out_mat": out_mat,
            "elapsed": elapsed, "anomalous_cell": ANOMALOUS_CELL, "status": "ok"}


if __name__ == "__main__":
    individuals = list(range(11))  # 0 = canonical, 1-10 = census individuals
    jobs = []
    for ind in individuals:
        jobs.append(("AN", ind, None))
        jobs.append(("R-text", ind, None))
        for factor in (1.5, 2.0, 4.0):
            jobs.append(("R-caption", ind, factor))

    print(f"{len(jobs)} rescue-fix runs queued")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_job, j): j for j in jobs}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"  [{len(results)}/{len(jobs)}] ind{r['individual']} {r['tag']}: "
                  f"({r['elapsed']:.1f}s)", flush=True)
    total = time.time() - t0
    print(f"Total: {total:.1f}s")
    with open(os.path.join(DATA_DIR, "rescue_manifest.json"), "w") as f:
        json.dump({"total_wall_s": total, "results": results}, f, indent=2)
