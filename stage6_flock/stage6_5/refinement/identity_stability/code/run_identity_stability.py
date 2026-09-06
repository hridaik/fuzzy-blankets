"""Part C driver, evaluation-only half (C1, C2 calibration, C3 envelope,
C5). The closed-loop re-run (C7/C8) is in run_closed_loop_stabilized.py,
run only after this script's outputs are frozen.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))
COLLECTIVE_IDENTITY_CODE = ROOT / "stage6_5" / "collective_identity" / "code"
sys.path.insert(0, str(COLLECTIVE_IDENTITY_CODE))
CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.interventions import make_pulse  # noqa: E402
from common_v2 import find_flock, dynamical_shell, T_U, T_R  # noqa: E402
from selection_rules_v3 import min_actuators_for_multicover  # noqa: E402
from definitions import material_track, lineage_track, functional_track  # noqa: E402
from identity_metrics import track_membership_metrics, per_definition_trajectory_report  # noqa: E402

from jitter_analysis import jitter_report  # noqa: E402
from calibrate_lambda_T import calibrate, generate_baseline, INFORMATIVE_SEEDS  # noqa: E402
from regularized_lineage import regularized_lineage_track  # noqa: E402
from validity_guard import compute_envelope, retrospective_guard  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CONTROLLED_SEED_OFFSET = 770_000  # SAME formula as collective_identity/code/run_identity_evaluation.py
FROZEN_Q, FROZEN_GAMMA = 2, 0.5
N_REP_C5 = 8  # matches Stage 6.5's own Part 4 replicate count, for the SAME 3 flocks + 2 new ones


def run_controlled_episode(fl: dict, seed: int) -> np.ndarray:
    lattice, I0, h_star, z_t0 = fl["lattice"], fl["I0"], fl["h_star"], fl["z_t0"]
    B_D = dynamical_shell(lattice, I0)
    A = min_actuators_for_multicover(B_D, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA)
    interventions = make_pulse(A, h_star, t0=0, t_u=T_U)
    res = run_simulation(nn=lattice.nn, nt=T_U + T_R, seed=seed, init_z=z_t0,
                          interventions=interventions, lattice=lattice)
    return res.z_hist


def part_c1_jitter(baselines: list[dict]) -> dict:
    reports = {}
    for b in baselines:
        seed, z_hist, fl = b["seed"], b["z_hist"], b["fl"]
        I0 = fl["I0"]
        track = lineage_track(z_hist, I0, t_start=0, t_end=z_hist.shape[0] - 1)
        reports[seed] = jitter_report(z_hist, track)
        print(f"  seed={seed}: corr(D_X,T_I)={reports[seed]['pearson_corr_DX_TI']:.3f} "
              f"n_low_DX_high_TI={reports[seed]['n_low_DX_high_TI']}/{reports[seed]['n_steps']}")
    return reports


def part_c5_representation_comparison(lambda_T: float, envelope_F: dict) -> list[dict]:
    results = []
    for seed in INFORMATIVE_SEEDS:
        fl = find_flock(seed)
        I0, lattice, h_star = fl["I0"], fl["lattice"], fl["h_star"]
        n_I0 = len(I0)
        episodes = []
        for r in range(N_REP_C5):
            seed_r = CONTROLLED_SEED_OFFSET + 1000 * seed + r
            z_hist = run_controlled_episode(fl, seed_r)
            n = z_hist.shape[0]

            track_M = material_track(I0, n)
            track_L = lineage_track(z_hist, I0, t_start=0, t_end=n - 1)
            track_Lreg = regularized_lineage_track(z_hist, I0, t_start=0, t_end=n - 1, lambda_T=lambda_T)
            track_F = functional_track(z_hist, I0, t_start=0, t_end=n - 1, lattice=lattice)
            guard_result = retrospective_guard(track_F, n_I0, envelope_F)
            track_Fguard = guard_result["guarded_track"]

            per_rep = {}
            for name, track in [("M", track_M), ("L", track_L), ("L_reg", track_Lreg),
                                 ("F", track_F), ("F_guard", track_Fguard)]:
                report = per_definition_trajectory_report(z_hist, I0, track, h_star, T_U, T_R)
                mem = track_membership_metrics(I0, track)
                per_rep[name] = dict(
                    success=report["success"], persistence=report["persistence"],
                    Hstar_end=report["Hstar_end"],
                    final_size=mem["size"][-1], final_R0=mem["R0"][-1],
                    total_turnover=int(sum(mem["turnover"])),
                )
            per_rep["F_guard"]["identity_collapse_unresolved"] = guard_result["identity_collapse_unresolved"]
            per_rep["F_guard"]["identity_valid_success"] = bool(
                per_rep["F_guard"]["success"] and not guard_result["identity_collapse_unresolved"]
            )
            episodes.append(per_rep)
        results.append(dict(seed=seed, n_rep=N_REP_C5, episodes=episodes))
        for name in ("M", "L", "L_reg", "F", "F_guard"):
            succ = np.mean([e[name]["success"] for e in episodes])
            size = np.mean([e[name]["final_size"] for e in episodes])
            print(f"  seed={seed} rep={name:8s} p_success={succ:.2f} mean_final_size={size:.1f}")
    return results


def main():
    print("=== C1: detector jitter vs. physical change (baseline continuations) ===")
    baselines = [generate_baseline(s) for s in INFORMATIVE_SEEDS]
    jitter = part_c1_jitter(baselines)
    with open(DATA_DIR / "jitter_analysis.json", "w") as f:
        json.dump(jitter, f, indent=1)
    print(f"Wrote {DATA_DIR / 'jitter_analysis.json'}")

    print("\n=== C2: calibrate lambda_T on baseline continuations ===")
    calib = calibrate(baselines)
    with open(DATA_DIR / "regularized_lineage_calibration.json", "w") as f:
        json.dump(calib, f, indent=1)
    print(f"chosen_lambda_T={calib['chosen_lambda_T']} (fallback={calib['chose_by_fallback']})")
    for r in calib["grid_results"]:
        print(f"  lambda_T={r['lambda_T']}: low_DX turnover orig={r['mean_turnover_low_DX_original']:.2f} "
              f"reg={r['mean_turnover_low_DX_regularized']:.2f} | high_DX turnover orig="
              f"{r['mean_turnover_high_DX_original']:.2f} reg={r['mean_turnover_high_DX_regularized']:.2f} "
              f"criterion_met={r['criterion_met']}")

    print("\n=== C3: identity-validity envelope (baseline continuations) ===")
    tracks_Lreg = [regularized_lineage_track(b["z_hist"], b["fl"]["I0"], 0, b["z_hist"].shape[0] - 1,
                                              lambda_T=calib["chosen_lambda_T"]) for b in baselines]
    tracks_F = [functional_track(b["z_hist"], b["fl"]["I0"], 0, b["z_hist"].shape[0] - 1, b["fl"]["lattice"])
                for b in baselines]
    n_I0_list = [len(b["fl"]["I0"]) for b in baselines]
    envelope_Lreg = compute_envelope(tracks_Lreg, n_I0_list)
    envelope_F = compute_envelope(tracks_F, n_I0_list)
    print(f"envelope (L_reg): {envelope_Lreg}")
    print(f"envelope (F): {envelope_F}")
    with open(DATA_DIR / "validity_envelope.json", "w") as f:
        json.dump(dict(L_reg=envelope_Lreg, F=envelope_F, informative_seeds=INFORMATIVE_SEEDS), f, indent=1)
    print(f"Wrote {DATA_DIR / 'validity_envelope.json'}")

    print("\n=== C5: representation comparison on controlled episodes ===")
    c5_results = part_c5_representation_comparison(calib["chosen_lambda_T"], envelope_F)
    with open(DATA_DIR / "representation_comparison.json", "w") as f:
        json.dump(dict(seeds=INFORMATIVE_SEEDS, n_rep=N_REP_C5, lambda_T=calib["chosen_lambda_T"],
                        envelope_F=envelope_F, results=c5_results), f, indent=1)
    print(f"Wrote {DATA_DIR / 'representation_comparison.json'}")


if __name__ == "__main__":
    main()
