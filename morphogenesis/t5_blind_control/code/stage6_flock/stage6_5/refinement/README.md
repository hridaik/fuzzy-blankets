# stage6_5/refinement/

Additive refinement of `stage6_5/` (boundary inference + collective identity),
resolving three questions Stage 6.5 raised but did not settle. Nothing in
`stage6_5/` above this directory is read-write here: `RESULTS_6_5.md`, the two
part-level results files, their `data/`, and `configs/protocol_6_5.yaml` are
frozen evidence and are imported (as Python modules / JSON) but never edited.

## Reading order

1. `PLAN.md` — scope decisions, written before any refinement code ran.
2. `PROTOCOL_6_5R.md` — every threshold used below, frozen (and hashed) before
   the results they gate were computed. Mirrors `../PROTOCOL_6_5.md`'s own
   convention: each part's thresholds are frozen only after that part's
   *development*-only diagnostics are in, and before its held-out/closed-loop
   numbers exist.
3. `causal_redundancy/CAUSAL_REDUNDANCY_RESULTS.md` — Hard Gate A: is the
   Stage 6.5 predictive boundary also causally sufficient under intervention?
4. `control_generalization/CONTROL_GENERALIZATION_RESULTS.md` — Hard Gate B:
   does inferred-boundary control beat null intervention across a genuinely
   discriminating set of held-out flocks, not just one?
5. `identity_stability/IDENTITY_STABILITY_RESULTS.md` — how much of Stage
   6.5's identity turnover and collapse was detector jitter vs. real, and
   does a lineage/validity-constrained identity fix it without freezing the
   collective back to `I_0`?
6. `RESULTS_6_5R.md` — index cross-linking the three results files above.
7. `../../STAGE6_5_REFINED_SYNTHESIS.md` — the six-question summary, one
   level up, alongside (not replacing) `STAGE6_5_SYNTHESIS.md`.

## Layout

```
causal_redundancy/{code,data,figures,tests}/    Part A / Hard Gate A
control_generalization/{code,data,figures,tests}/   Part B / Hard Gate B
identity_stability/{code,data,figures,tests}/   Part C / Hard Gate C
logs/                                            freeze-time hashes, one per protocol section
```

Each subpackage's `code/` holds library modules plus `run_*.py` drivers plus
`make_figures_*.py`, invoked from that subpackage's `code/` directory, writing
only to its own `data/`/`figures/` — matching `boundary_inference/` and
`collective_identity/`'s existing convention one level up.

## What is reused, unmodified

- The simulator (`python/flock_sim/*`).
- `v2_interface_control/code/common_v2.py` (`find_flock`, `dynamical_shell`,
  `evaluate_arm`, `T_U`, `T_R`, `TW`) and `v3_refinement/code/{common_v3,
  selection_rules_v3}.py` (dev/held-out flock pools, the frozen `q=2,
  gamma=0.5` multicover controller law).
- `boundary_inference/code/{api,nodewise_model,greedy_selection,bootstrap,
  graph_inference,trajectory_gen,ground_truth_eval,control_compare}.py` — the
  frozen inference pipeline and its evaluation harness, imported exactly as
  Part 1/2 froze them. No hyperparameter here is re-tuned.
- `collective_identity/code/{definitions,identity_metrics,adaptive_control,
  pathwise_boundary}.py` — the three identity definitions and the closed-loop
  /pathwise-leakage harnesses, extended (not edited) by new modules in
  `identity_stability/code/`.

## What is new here

- `causal_redundancy/code/exact_intervention.py` — a closed-form counterfactual
  one-step propagator (see `PLAN.md` for the derivation): because the ported
  generative model's action-to-next-heading map does not depend on the
  current state, and the policy posterior driving action choice depends on
  the current state only through each bird's lattice-neighbour headings, the
  one-step marginal `p(z_{i,t+1} | z_t)` — and its counterfactual
  `do(z_j := z'_j)` version — can be computed exactly, with no simulator
  rollout or Monte-Carlo noise. This is the main new piece of machinery this
  refinement adds; everything else composes existing Stage 6.5/V2/V3 code.
- `control_generalization/code/seed_scan.py` — a frozen discriminating-flock
  screen over new seeds (41+), never touched during Stage 6.5's own
  development or held-out evaluation.
- `identity_stability/code/{regularized_lineage,validity_guard,
  guarded_controller,jitter_analysis}.py` — temporal regularization and an
  anti-collapse validity guard layered on top of the existing lineage/
  functional identity definitions.
