"""Part C batch driver: runs the declared perturbation catalog through the
fallback engine (Octave), at published horizon (N=32) and sustained (N=512),
parallelized across available cores via a process pool. Pilot-timed first
(see PERTURBATIONS_EXECUTED.md for the recorded estimate).

Declared reduction (disclosed, not silent): Kuchling's 'anomalous cell' and
'rescue' perturbations are run for 3 of 8 cells (0, 3, 7 -- spanning head,
mid-body, tail positions in the template) rather than all 8, due to session
time budget; see PERTURBATIONS_EXECUTED.md reduction table.
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "data", "oracle_traces", "perturbations")


def _job(args):
    kind, params, n_bins, seed, out_name = args
    from fallback_engine import run  # re-import in worker process
    out_mat = os.path.join(OUT_DIR, out_name)
    t0 = time.time()
    try:
        mat, elapsed = run({"L": 2}, n_bins=n_bins, noise_seed=seed,
                            interventions={"kind": kind, "params": params},
                            out_mat=out_mat)
        return {"out_name": out_name, "kind": kind, "params": params,
                "n_bins": n_bins, "elapsed": elapsed, "status": "ok"}
    except Exception as e:
        return {"out_name": out_name, "kind": kind, "params": params,
                "n_bins": n_bins, "elapsed": time.time() - t0,
                "status": "error", "error": str(e)}


def build_job_list():
    jobs = []

    def add(kind, params, name_suffix):
        for n_bins in (32, 512):
            out_name = f"{name_suffix}_N{n_bins}.mat"
            jobs.append((kind, dict(params), n_bins, 0, out_name))

    # --- Kuchling 2020 ---
    add("kuchling_head", {"cells": [], "ramp_w": 0, "ramp_onset_bin": 1}, "kuchling_head")
    add("kuchling_tail", {"cells": [], "ramp_w": 0, "ramp_onset_bin": 1}, "kuchling_tail")
    for c in (0, 3, 7):  # declared reduction: 3 of 8 cells, not all 8
        add("kuchling_head", {"cells": [c], "ramp_w": 0, "ramp_onset_bin": 1},
            f"kuchling_anomalous_cell{c}")
        add("kuchling_rescue", {"cells": [c], "ramp_w": 0, "ramp_onset_bin": 1},
            f"kuchling_rescue_cell{c}")

    # --- Friston 2015 Figure 5, DECLARED INTERPRETATION (not established) ---
    friston_configs = [
        ("position_all", 0.5, "friston_exogenous_x0.5"),
        ("position_row1", 2.0, "friston_verticalgrad_x2"),
        ("secretion", 2.0, "friston_intracellular_x2"),
        ("secretion", 0.5, "friston_intracellular_x0.5_captionreading"),
        ("sig2", 0.25, "friston_signal2_x0.25"),
        ("sig3", 0.25, "friston_signal3_x0.25"),
    ]
    for channel, factor, name in friston_configs:
        add("friston_scale", {"cells": [], "friston_channel": channel,
                               "friston_factor": factor, "ramp_w": 0,
                               "ramp_onset_bin": 1}, name)

    # --- ramp-width integrator-artifact check (kuchling_head only) ---
    for w in (1, 4, 8):
        for n_bins in (32,):
            out_name = f"kuchling_head_rampw{w}_N{n_bins}.mat"
            jobs.append(("kuchling_head", {"cells": [], "ramp_w": w, "ramp_onset_bin": 1},
                         n_bins, 0, out_name))

    return jobs


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    jobs = build_job_list()
    print(f"{len(jobs)} jobs queued")

    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(_job, j): j for j in jobs}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"  [{len(results)}/{len(jobs)}] {r['out_name']}: {r['status']} "
                  f"({r['elapsed']:.1f}s)")

    total_elapsed = time.time() - t0
    print(f"\nTotal wall time: {total_elapsed:.1f}s for {len(jobs)} jobs")
    with open(os.path.join(OUT_DIR, "batch_results.json"), "w") as f:
        json.dump({"total_wall_s": total_elapsed, "n_jobs": len(jobs),
                   "results": results}, f, indent=2)
