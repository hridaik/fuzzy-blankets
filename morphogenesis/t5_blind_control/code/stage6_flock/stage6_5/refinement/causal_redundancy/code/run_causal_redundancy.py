"""Part A driver (Hard Gate A). Runs A1-A5 on the 3 held-out flocks already
frozen in boundary_inference/data/held_out_evaluation.json (seeds 17, 18,
20), using the frozen inference outputs (B_hat, B^D) without refitting the
inference pipeline. Writes data/causal_redundancy.json.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from load_frozen_inputs import (  # noqa: E402
    load_flock_with_frozen_boundary, generate_perturbation_checkpoints, exterior_classes,
    N_PERTURBATION_TRAJ, CHECKPOINT_T, PERTURBATION_TRAJ_SEED_OFFSET,
)
from perturbation_experiment import run_all_classes, pooled_class_distribution  # noqa: E402
from stress_test import fit_models, natural_excess_losses, intervention_excess_losses, compute_delta_shift  # noqa: E402

HELD_OUT_SEEDS = [17, 18, 20]
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def run_one_flock(seed: int) -> dict:
    print(f"=== seed {seed} ===")
    fl = load_flock_with_frozen_boundary(seed)
    classes = exterior_classes(fl)
    print(f"  |I0|={len(fl['I0'])} |B_hat|={len(fl['B_hat'])} |B_D|={len(fl['B_D'])} "
          f"included_shell={classes['included_shell']} omitted_shell={classes['omitted_shell']} "
          f"non_shell_sample={classes['non_shell_sample']} (of {classes['n_non_shell_total']} total)")

    checkpoints = generate_perturbation_checkpoints(fl)

    # A2-A4: perturbation experiment, exact D_j^do per class
    perturbation = run_all_classes(fl, checkpoints, classes)
    pooled = {cls: pooled_class_distribution(res) for cls, res in perturbation.items()}
    for cls, p in pooled.items():
        print(f"  D_do_joint[{cls}]: mean={p['mean']:.5f} median={p['median']:.5f} "
              f"p90={p['p90']:.5f} max={p['max']:.5f} (n={p['n']})")

    # A5: stress-test the frozen predictive models under intervention
    models = fit_models(fl)
    natural = natural_excess_losses(fl, models, checkpoints)
    print(f"  Delta-ell (exact, natural): B_D={natural['excess']['B_D']:.5f} "
          f"B_hat={natural['excess']['B_hat']:.5f}")

    stress_by_class = {}
    shift_by_class = {}
    for cls_name, bird_ids in classes.items():
        if cls_name == "n_non_shell_total":
            continue
        intervention = intervention_excess_losses(fl, models, checkpoints, bird_ids)
        shift = compute_delta_shift(natural, intervention)
        stress_by_class[cls_name] = intervention
        shift_by_class[cls_name] = shift
        if shift:
            mean_shift_bhat = float(np.mean([v["B_hat"] for v in shift.values()]))
            mean_shift_bd = float(np.mean([v["B_hat"] for v in shift.values()]))
            print(f"  mean Delta_shift(B_hat)[{cls_name}] = {mean_shift_bhat:.5f}")

    return dict(
        seed=seed,
        n_I0=len(fl["I0"]),
        B_hat=fl["B_hat"], B_D=fl["B_D"],
        classes=classes,
        recovery_vs_BD_part1=fl["recovery_vs_BD"],
        excess_loss_natural_part1=fl["excess_loss_natural_part1"],
        perturbation=perturbation,
        pooled_class_distribution=pooled,
        natural_exact=natural,
        intervention_exact_by_class=stress_by_class,
        delta_shift_by_class=shift_by_class,
    )


def main():
    all_results = {}
    for seed in HELD_OUT_SEEDS:
        all_results[seed] = run_one_flock(seed)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "causal_redundancy.json"
    with open(out_path, "w") as f:
        json.dump(dict(
            seeds=HELD_OUT_SEEDS,
            n_perturbation_traj=N_PERTURBATION_TRAJ,
            checkpoint_t=CHECKPOINT_T,
            perturbation_traj_seed_offset=PERTURBATION_TRAJ_SEED_OFFSET,
            results=all_results,
        ), f, indent=1, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else o)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
