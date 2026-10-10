# Stage 6.5 — removing two Stage-6 conveniences before Stage 7

Additive track. Does not modify `v1_mechanism_audit/`, `v2_interface_control/`,
`v3_refinement/`, or `interactive_demo/` (imports reusable library code from
them unmodified: `python/flock_sim/*`, `v2_interface_control/code/common_v2.py`,
`v3_refinement/code/{common_v3,selection_rules_v3}.py`). Stage 6 is frozen
evidence; nothing here changes its numbers, figures, or conclusions.

## Why this stage exists

Stage 6 established the true one-step interaction interface `B^D` and the
persistent-collective control result, but leaned on two conveniences the
general moving-shepherding problem (Stage 7) will not offer:

1. **Privileged structural knowledge.** `B^D` was read directly from the
   simulator's known Moore-lattice graph (`lattice.neighbor_ids`), not
   discovered from data.
2. **A permanently frozen interior.** `I_t = I_0` for the whole control
   episode, by construction (birds occupy fixed lattice sites in this
   port).

Stage 6.5 asks: can an approximate functional boundary be inferred from
trajectories alone, with the true `B^D` hidden until evaluation (Part 1-2)?
And what changes if "the same collective" means fixed membership, lineage
continuity, or current functional organization, rather than a permanently
frozen `I_0` (Part 3-6)? This is methodological preparation for Stage 7, not
a new large benchmark and not a re-optimization of the V3 controller.

## Reading order

1. `PLAN.md` -- scope decisions made before any inference code ran (flock
   pools, the architectural firewall, why the estimator changed solvers).
2. `PROTOCOL_6_5.md` + `boundary_inference/configs/protocol_6_5.yaml`
   (hashed) -- the frozen boundary-inference protocol.
3. `boundary_inference/BOUNDARY_INFERENCE_RESULTS.md` -- Hard Gate A.
4. `collective_identity/COLLECTIVE_IDENTITY_RESULTS.md`.
5. `RESULTS_6_5.md` -- full results across both parts.
6. `../STAGE6_5_SYNTHESIS.md` (one level up, alongside `STAGE6_SYNTHESIS.md`)
   -- the six-question summary.

## Layout

```
boundary_inference/
    code/       inference-side (lattice-free, see tests/test_no_lattice_leakage.py)
                + evaluation-side drivers (trajectory generation, ground-truth
                reveal, control comparison)
    configs/    frozen protocol_6_5.yaml + its sha256
    data/       dev sweep, sample-efficiency curve, held-out evaluation,
                bootstrap membership, control comparison -- one JSON per experiment
    figures/    Figures 6.5A-C
    tests/      architectural (no-lattice-leakage) + synthetic-recovery tests

collective_identity/
    code/       three identity definitions (M/L/F), their metrics, the
                pathwise boundary-integrity diagnostic, the closed-loop
                adaptive-control proof of concept
    configs/    (none needed beyond boundary_inference's -- no separate
                threshold-freeze required for Part 3-6's definitions, which
                are fixed by construction in definitions.py, not tuned)
    data/       identity evaluation, adaptive control, pathwise boundary
    figures/    Figures 6.5D-G
    tests/      unit tests for the three definitions and their metrics

logs/           (reserved for future run logs; every driver script prints
                its own provenance to stdout today)
```

## Architectural firewall

`boundary_inference/code/{nodewise_model,greedy_selection,bootstrap,
graph_inference,api}.py` never import the lattice, the true `B^D`, or any
structural feature -- enforced by
`boundary_inference/tests/test_no_lattice_leakage.py` (AST-based static
analysis of every import/identifier/function-signature in those five files,
plus a runtime check). Every other file in `boundary_inference/code/`
(`trajectory_gen.py`, `ground_truth_eval.py`, `control_compare.py`, and the
`run_*.py` drivers) is evaluation-side and is allowed to touch the lattice,
because its entire purpose is generating data or revealing ground truth
*after* `\hat B` is frozen.

## Running

```
cd stage6_flock
python3 -m pytest stage6_5/ -q

cd stage6_5/boundary_inference/code
python3 run_dev_sweep.py                        # Part 1.1-1.7 (dev flocks only)
# -- freeze PROTOCOL_6_5.md / configs/protocol_6_5.yaml here --
python3 run_sample_efficiency.py 0.05 0.005      # Part 1.9
python3 run_held_out_evaluation.py 0.05 0.005    # Part 1.8/1.10, Gate A
python3 run_bootstrap_membership.py 0.05 0.005   # Part 1.7
python3 run_control_comparison.py                # Part 2
python3 make_figures_part1.py                    # Figures 6.5A-C

cd ../../collective_identity/code
python3 run_identity_evaluation.py               # Part 3-4
python3 run_adaptive_control.py                  # Part 5
python3 run_pathwise_boundary.py                 # Part 6
python3 make_figures_part2.py                    # Figures 6.5D-G
```
