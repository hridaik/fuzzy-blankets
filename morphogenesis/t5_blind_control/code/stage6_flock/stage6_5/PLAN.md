# PLAN.md — Stage 6.5

Planning document, written before any inference code ran. Records scope
decisions so later results can be checked against intent rather than
rationalized after the fact.

## What Stage 6.5 is and is not

It is methodological preparation for Stage 7 (moving shepherding model). It
removes two conveniences Stage 6 relied on:

1. Privileged access to the simulator's source-level Moore-neighbour graph
   when identifying the interaction interface (`B^D`).
2. A permanently frozen interior identity `I_t = I_0`.

It is **not** a re-optimization of the V3 controller. No new multicover `q`
search, no Fiedler threshold tuning, no controller-ranking sweep. Those
knobs stay exactly as V3 froze them
(`v3_refinement/configs/protocol_v3.yaml`).

## Reused, unmodified, from Stage 6

- `python/flock_sim/*` (simulator, lattice, spectral, metrics, interventions) —
  imported, never edited.
- `v2_interface_control/code/common_v2.py` (`find_flock`, `dynamical_shell`,
  `T_U`, `T_R`, `TW`) and `v3_refinement/code/{common_v3,selection_rules_v3,
  coverage_metrics}.py` — imported for flock discovery, the true shell
  (evaluation-only), and the multicover controller logic.
- The V3 frozen dev/held-out flock pools
  (`v3_refinement/code/common_v3.py:DEV_SEEDS`,
  `v3_refinement/data/held_out_flocks.json`) — reused directly rather than
  re-scanning seeds, to avoid a second source of undisclosed seed selection.

## Flock-pool scope (fixed before any inference code ran)

Full-scale replication of Part 1/2/3 across all 10 dev + 6 held-out V3
flocks, at N_traj up to 200 with bootstrap resampling and a full identity
closed-loop, is out of proportion to a *methodological preparation* stage.
Scope is deliberately narrowed and stated up front:

- **Boundary-inference development** (estimator choice, regularization,
  stopping rule, bootstrap count, shortlist size — Part 1.1-1.7): dev seeds
  `2, 3, 4` (first three of V3's frozen ten). Multiple flocks, so decisions
  are not fit to one instance; capped at three for compute.
- **Sample-efficiency curve** (Part 1.9): the canonical flock (seed 2) only —
  this is a within-flock diagnostic of data requirements, not a
  cross-flock generalization claim, so one flock is the right scope, stated
  as such.
- **Held-out evaluation** (Part 1.8, 1.10, Part 2, Gate A): the first three
  of V3's six frozen held-out seeds (17-40 scan range), reusing
  `v3_refinement/data/held_out_flocks.json` if present, else recomputing by
  the identical procedure. Never touched during development.
- **Collective-identity analysis** (Part 3-6): the canonical flock (seed 2)
  as the primary worked example for the figures and closed-loop
  proof-of-concept, plus the same three dev flocks (2,3,4) for the
  representation-disagreement table (Part 4) so the comparison is not a
  single-instance anecdote.

All of this is a documented scope reduction, not a discovered limitation —
consistent with how V1/V2/V3 documented their own (METHODS_AUDIT.md section
13; REFINEMENT_PLAN.md). If a reviewer wants the full 10+6-flock replication,
the code is written to take a flock list as a parameter and it is a
compute-time exercise, not a redesign.

## Architectural firewall (Part 1's hard requirement)

`boundary_inference/code/` is split into two import-disjoint groups:

- **Inference-side** (`api.py`, `nodewise_model.py`, `greedy_selection.py`,
  `bootstrap.py`, `screening.py`): accepts only `z[trajectory, time, bird]`,
  `I0`, and integer trajectory-id splits. Never imports `flock_sim.lattice`,
  `flock_sim.spectral`, `common_v2.dynamical_shell`, or anything carrying
  `neighbor_ids`/`B^D`/graph distance.
- **Evaluation-side** (`ground_truth_eval.py`, `trajectory_gen.py`,
  `control_compare.py`, `run_*` drivers): allowed to import the lattice,
  because it either (a) generates trajectories by running the real
  simulator, which necessarily uses the lattice, or (b) reveals `B^D`/`B^F`
  only after `\hat B` has been frozen.

`tests/test_no_lattice_leakage.py` asserts this by static analysis of the
inference-side modules' import graph (AST-based, not a string grep that a
comment could fool) plus a runtime check that the inference API's function
signatures never accept a `Lattice` argument.

## Estimator choice (frozen after a short comparison on dev flocks only)

Primary: **nodewise multinomial logistic regression**, one classifier per
`i in I0`, features = one-hot(`X_{I0,t}`) + one-hot(`X_{B,t}`) for the
candidate boundary `B` (`sklearn.linear_model.LogisticRegression`,
`multi_class='multinomial'`, `solver='lbfgs'`, L2 penalty; a single
exterior-bird's marginal screening pass additionally tries L1/`saga` as a
sparsity check — see `BOUNDARY_INFERENCE_RESULTS.md` for which was kept).
Reasons documented in `PROTOCOL_6_5.md` once frozen, not here.

## Freeze point

`PROTOCOL_6_5.md` + `configs/protocol_6_5.yaml` are written and hashed
**after** Part 1.1-1.7 dev-flock decisions are made and **before** any
held-out number (Part 1.8+, Part 2, Gate A) is computed. The hash is
recorded in `RESULTS_6_5.md` and `logs/`. No threshold in that file changes
after this point; if a later step needs a different number, that is
reported as a limitation, not silently patched in.
