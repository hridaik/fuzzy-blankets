"""Full-trajectory playback data for a small, curated set of illustrative
(seed, condition, candidate) examples, chosen to span the (C,G,L,D) surface
and the five control scenarios -- NOT an exhaustive re-run of every
seed x condition x candidate combination (per user request: "a few selected
illustrative and explanatory examples... chosen well to span them
illustratively").

Unlike run_archetype_validation.py (scalar metrics only, I0 only), this
script also saves the FULL per-timestep heading array for one representative
replicate per (seed, condition) group, so the demo's Control submode can
play back real heading arrows frame-by-frame (mirroring the main Control
tab), not just the four scalar traces.

Physical-regime convention (must match run_landscape.py / RESULTS_6_6.md
exactly, so metrics at t=20 reproduce already-published numbers): the
control profile always forces the SEED's own reference I0's shell/near-
exterior, per build_condition(lattice, ref["I0"], ...) -- never a
candidate's own shell -- then arbitrary OTHER candidates are evaluated as
passive observers within that one shared resulting trajectory, exactly as
in the main landscape (task brief's "one representative realization;
information scores estimated from the recent ensemble around that time").
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from common_66 import (
    lattice_100, R_REPLICATES, T_U, T_R, K_BOUNDARY_BUDGET, dump_json,
)
from flock_sim.metrics import target_heading_fraction
from windowed_data import run_condition_replicates, build_window_dataset
from predictive_cache import PredictiveCache
from landscape import evaluate_candidate
from archetypes import build_condition
from run_landscape import reference_I0, SEED_OFFSETS

STAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = STAGE_DIR / "data"
LOG_DIR = STAGE_DIR / "logs"

# (seed, condition) -> list of (label, candidate) where candidate is
# "I0" or an explicit sorted node-id list picked from the already-generated
# landscape (see logs/pick_illustrative_candidates.txt for how each was
# chosen -- avg-internal-Moore-degree-filtered picks from
# code/make_figures.py's own compactness heuristic, or an explicit
# face-validity-inspected example).
CURATED = {
    (2, "no_control"): [
        ("Reference I0 (natural)", "I0"),
        ("Scattered-but-connected (diagonal snake)",
         [11, 13, 22, 25, 26, 28, 29, 32, 34, 37, 43, 46, 56, 67, 69, 76, 78, 86, 89, 98]),
    ],
    (2, "shell_only"): [
        ("Reference I0 (shell retarget)", "I0"),
        ("High-integration / low-leakage pick",
         [4, 5, 6, 7, 8, 9, 13, 14, 15, 17, 18, 19, 24, 26, 27, 28, 29, 34, 39, 48]),
    ],
    (2, "same_direction"): [("Reference I0 (same-direction exterior)", "I0")],
    (2, "opposite"): [("Reference I0 (opposite exterior)", "I0")],
    (2, "disordered"): [("Reference I0 (disordered exterior)", "I0")],
    (3, "same_direction"): [("Reference I0 (global-cascade case)", "I0")],
    (4, "disordered"): [
        ("Reference I0 (disordered exterior)", "I0"),
        ("Jointly high-C/high-G/low-L/high-D pick", "IDEAL"),
    ],
}

IDEAL_PICK_4_DISORDERED = [67, 73, 74, 75, 76, 77, 78, 79, 83, 84, 85, 86, 87, 88, 89, 94, 95, 96, 97, 98]


def resolve_candidate(spec, I0):
    if spec == "I0":
        return I0
    if spec == "IDEAL":
        return np.array(IDEAL_PICK_4_DISORDERED, dtype=int)
    return np.array(sorted(spec), dtype=int)


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_illustrative_trajectories.log"
    t_start = time.time()
    lattice = lattice_100()
    out = []
    with open(log_path, "a") as logf:
        logf.write(f"\n=== run_illustrative_trajectories start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        for (seed, condition), entries in CURATED.items():
            rng = np.random.default_rng(seed * 7 + 1)
            ref = reference_I0(lattice, seed, rng)
            I0, h_star, z_t0 = ref["I0"], ref["h_star"], ref["z_t0"]
            cond = build_condition(lattice, I0, h_star, condition, f_E=1.0, t0=0, t_u=T_U)
            nt = T_U + T_R
            seed_offset = SEED_OFFSETS[condition]
            z_reps = run_condition_replicates(z_t0, lattice, cond["interventions"], nt=nt,
                                               n_rep=R_REPLICATES, seed_offset=seed_offset)
            z_hist_repr = z_reps[0]  # (nt+1, 100) -- the SAME representative used elsewhere

            candidates = [(label, resolve_candidate(spec, I0)) for label, spec in entries]
            series_by_cand = {label: dict(t=[], C=[], G=[], L=[], D=[], He=[], Dc=[], Hstar=[])
                               for label, _ in candidates}

            t0 = time.time()
            for t in range(1, nt + 1):
                wds = build_window_dataset(z_reps, t=t)
                cache = PredictiveCache(lattice, wds.train_prev, wds.train_next,
                                         wds.val_prev, wds.val_next)
                for label, I in candidates:
                    row = evaluate_candidate(cache, lattice, wds.representative_z, I, K=K_BOUNDARY_BUDGET)
                    hstar = float(target_heading_fraction(wds.representative_z, I, h_star))
                    s = series_by_cand[label]
                    s["t"].append(t)
                    s["C"].append(row["C_internal"])
                    s["G"].append(row["G_internal"])
                    s["L"].append(row["L_blanket"])
                    s["D"].append(row["D_local"])
                    s["He"].append(row["external_entropy"])
                    s["Dc"].append(row["directional_contrast"])
                    s["Hstar"].append(hstar)

            elapsed = time.time() - t0
            line = f"seed={seed} condition={condition} n_candidates={len(candidates)} elapsed={elapsed:.1f}s"
            print(line)
            logf.write(line + "\n")
            logf.flush()

            for label, I in candidates:
                out.append(dict(
                    seed=seed, condition=condition, label=label,
                    candidate_node_ids=I.tolist(),
                    t0=ref["t0"], h0=ref["h0"], h_star=h_star, h_opp=cond["h_opp"],
                    T_u=T_U, T_r=T_R,
                    shell=cond["shell"].tolist(), near_exterior=cond["near_exterior"].tolist(),
                    controlled_exterior=cond["controlled_exterior"].tolist(),
                    z_hist=z_hist_repr.tolist(),
                    series=series_by_cand[label],
                ))
        total = time.time() - t_start
        logf.write(f"=== done, total {total:.1f}s, {len(out)} trajectories ===\n")
    dump_json(out, DATA_DIR / "illustrative_trajectories.json")
    print(f"DONE total={total:.1f}s -> data/illustrative_trajectories.json ({len(out)} trajectories)")


if __name__ == "__main__":
    main()
