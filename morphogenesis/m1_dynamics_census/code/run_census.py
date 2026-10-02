"""Part B: census of stable forms. 200 primary individuals (v0=randn(8,8)/8,
the code's own distribution, seeds 0..199) + 50 secondary individuals
(v0 std=exp(2), the 2015 paper's literal stated precision for INITIAL
expectations -- log precision -4 => std=exp(2), per m0b DISCREPANCIES_UPDATE.md
correction -- seeds 1000..1049, generated with numpy since this is not the
code's own default draw).

Cascading horizon: N=512 first; any individual not stationary by bin 512
(per THRESHOLDS.md's frozen criterion) is re-run once at N=2048.
"""
import json
import os
import sys
import time
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M0C_CODE = os.path.join(REPO_ROOT, "..", "m0c_port_completion", "code")
DATA_DIR = os.path.join(REPO_ROOT, "data", "census")
os.makedirs(DATA_DIR, exist_ok=True)

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


def config_hash():
    """Hash of the engine configuration this run uses (Part of every
    rollout's manifest, per the ground rules)."""
    h = hashlib.sha256()
    for fname in ("run_and_export.m",):
        p = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "oracle", fname)
        if os.path.exists(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:16]


def individual_v0(kind, idx):
    """Returns (noise_seed_for_octave, v0_override_or_None)."""
    if kind == "primary":
        return idx, None  # Octave draws v=randn(8,8)/8 itself, seeded by idx
    elif kind == "secondary":
        rng = np.random.default_rng(100000 + idx)
        v0 = rng.standard_normal((8, 8)) * np.exp(2.0)
        return idx, v0
    raise ValueError(kind)


def _job(args):
    kind, idx = args
    sys.path.insert(0, M0C_CODE)
    from fallback_engine import run

    seed, v0 = individual_v0(kind, idx)
    ind_id = f"{kind}_{idx:04d}"
    out_mat = os.path.join(DATA_DIR, f"{ind_id}_N512.mat")
    t0 = time.time()
    mat, elapsed = run({"L": 2}, initial_state=v0, n_bins=512, noise_seed=seed,
                        out_mat=out_mat)
    stat, stat_bin = is_stationary(mat)
    n_bins_used = 512
    cascaded = False
    if not stat:
        out_mat2 = os.path.join(DATA_DIR, f"{ind_id}_N2048.mat")
        mat2, elapsed2 = run({"L": 2}, initial_state=v0, n_bins=2048, noise_seed=seed,
                              out_mat=out_mat2)
        stat2, stat_bin2 = is_stationary(mat2)
        elapsed += elapsed2
        n_bins_used = 2048
        cascaded = True
        stat, stat_bin = stat2, stat_bin2
        out_mat = out_mat2

    return {
        "individual_id": ind_id, "kind": kind, "idx": idx, "seed": seed,
        "n_bins_used": n_bins_used, "cascaded": cascaded,
        "stationary": stat, "stationary_at_bin": stat_bin,
        "elapsed_s": elapsed, "out_mat": out_mat,
        "engine": "fallback_octave_subprocess",
        "engine_config_hash": config_hash(),
    }


if __name__ == "__main__":
    jobs = [("primary", i) for i in range(200)] + [("secondary", i) for i in range(50)]
    print(f"{len(jobs)} individuals queued")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_job, j): j for j in jobs}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"  [{len(results)}/{len(jobs)}] {r['individual_id']}: "
                  f"stationary={r['stationary']}@{r['stationary_at_bin']} "
                  f"N={r['n_bins_used']} ({r['elapsed_s']:.1f}s)", flush=True)

    total = time.time() - t0
    print(f"\nTotal wall time: {total:.1f}s for {len(jobs)} individuals")
    with open(os.path.join(DATA_DIR, "census_manifest.json"), "w") as f:
        json.dump({"total_wall_s": total, "n_individuals": len(jobs),
                   "results": results}, f, indent=2)
