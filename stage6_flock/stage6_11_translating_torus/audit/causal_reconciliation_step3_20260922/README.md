# Stage 6.11 Causal Reconciliation, Step 3 — 2026-09-22

## Purpose

Completes the identity-aware causal reconciliation of Stage 6.11 that
`identity_causal_reconciliation_20260921` (Step 3's immediate predecessor)
left partially scoped. Per this task's explicit instruction not to
silently truncate scope again, this pass executes all feasible sections
of the full specification and documents, precisely, what could not be
completed and why — rather than pre-selecting a narrower scope.

**No controller redesign was performed.** Nothing in this directory
implements new online target logic, a new authority estimator, receding-
horizon optimization, motion-aware actuator pruning, or production
abstention rules. All simulation/replay infrastructure here is audit-only.

## Repository state at the start of this pass

No top-level "Research Programme Handoff" document exists in the
repository (confirmed by search; recorded here rather than invented). The
authoritative prior state was: `evidence_recovery_20260921/` (Step 1),
`material_identity_step2_20260921/` (Step 2), and
`identity_causal_reconciliation_20260921/` (Step 2.5 — hardened identity
validation, seed 503 split forensics, seed 501/503 partial adjudication).
This pass builds on all three, cited throughout, without overwriting any
of them.

## Exact commands (reproduction, in order)

```
conda activate fuzzy-blankets
cd stage6_flock/stage6_11_translating_torus/audit/causal_reconciliation_step3_20260922/code

# Task 0: complete episode-level identity validation (~8-10 min)
python3 identity_episode_validation.py

# Task F0: RNG/CRN audit (~seconds)
python3 rng_crn_diagnostic.py

# Trigger-state reproduction check, all 5 seeds (~1 min)
python3 reproduce_trigger_states.py

# Task F1: seed 501 schedule effect (~9 min)
python3 seed501_schedule_effect.py

# Task F2: seed 503 disruption/schedule effect (~10 min)
python3 seed503_schedule_effect.py

# Task F3: seeds 500, 502, 504 (generic version of the above; ~9 min each)
python3 seed_generic_schedule_effect.py 500
python3 seed_generic_schedule_effect.py 502
python3 seed_generic_schedule_effect.py 504

# Task D: exact v2 replay + field-direction anchor sweep, all 5 seeds (~15-30 min)
python3 v2_replay_and_field_readout.py

# Task E prerequisite: branch_adjudication_611.py reproducibility check
# (EXPENSIVE: ~25-30+ CPU-minutes for ONE seed, due to the repaired-
# authority/beam-search branches' rollout budgets)
python3 verify_branch_adjudication_reproducibility.py 501
```

All scripts are read-only with respect to production tracker/controller/
simulator code. `ForwardMaterialTrace611` and its frozen rule
(Jaccard≥0.30, unchanged) are imported from
`material_identity_step2_20260921/code/`, never edited or retuned.

## Repository commit used

`940a5f672bc9b8302c0436e5a531cea6ae1f6ce1` (same commit Step 1/Step 2/
Step 2.5 used — no tracker/controller/world-code commits were made by
this pass either).

## What this pass completed

See each deliverable document for full detail. Summary:

- **Task 0** (episode-level identity validation): complete. Zero
  erroneous transfers to unrelated populations across 72 full-episode
  traces (dev + untouched holdout). `IDENTITY_EPISODE_VALIDATION.md`.
- **Task F0** (RNG/CRN audit): complete. Same-seed alone is NOT valid CRN
  for a naive no-control-vs-control comparison of the actual production
  loop (control-phase auxiliary decision code shares the physics RNG
  stream); a dedicated-physics-stream harness fixes this, verified.
  All 5 seeds' trigger states independently reproduced bit-exact.
  `RNG_AND_CRN_AUDIT.md`.
- **Task F1** (seed 501 causal): complete for the schedule-effect
  estimand (25 CRN-paired replicates: intervention effect demonstrated,
  actuator selectivity not demonstrated). Policy-effect estimand not
  attempted (disclosed, see below). `seed_501_causal.md`,
  `seed_501_controller_timeline.md`.
- **Task F2** (seed 503 causal/disruption): complete for the same
  estimand. Intervention effect demonstrated; actuator selectivity not
  demonstrated; organizational disruption not demonstrated as
  intervention-specific (split rate high under all conditions including
  no forcing). `seed_503_causal.md`, `seed_503_disruption_analysis.md`.
- **Task F3** (seeds 500, 502, 504): same schedule-effect harness applied.
  `seed_500_causal.md`, `seed_502_causal.md`, `seed_504_causal.md`.
- **Task D** (exact v2 replay): complete for all 5 seeds' actual recorded
  trajectories, with the historical field-direction readout recomputed at
  v1/v2/material anchors across the full radius grid.
  `V2_REPLAY_AND_FIELD_READOUT.md`.
- **Task E** (counterfactual branch tracing): PARTIAL, disclosed in
  detail in `COUNTERFACTUAL_MATERIAL_TRACES.md`. Step 1's original 9
  named branches were NOT re-instrumented with full per-frame material
  traces for all 5 seeds, because reproducing even one seed's 9 branches
  (specifically the repaired-authority/beam-search branches' rollout
  budgets) costs 25-30+ CPU-minutes, and `branch_adjudication_611.py`
  persisted only summary readouts, not raw trajectories, so exact
  per-frame reconstruction requires a full re-run. What WAS completed: (a)
  verification that `branch_adjudication_611.py` is architecturally
  CRN-clean and (for seed 501) exactly reproducible; (b) a purpose-built,
  materially-scored, much cheaper 3-branch (no-forcing / historical /
  matched-random) schedule-effect harness applied to all 5 seeds with full
  per-replicate material-trace persistence (Task F1-F3 above) — which
  answers the specification's actual scientific questions (intervention
  effect, actuator selectivity, disruption) even though it does not
  reproduce Step 1's specific 9-branch taxonomy.
- **Visualization** (spec §14): PARTIAL, disclosed. Full synchronized,
  frame-by-frame, one-click-navigable playback of every branch (as
  literally specified) was not attempted — it would require exporting
  full per-frame `(r, z, interior, actuators)` data for ~150 simulated
  rollouts (25 replicates × 3 branches × 5 seeds) into the existing
  `interactive_demo/v2` viewer's frame format, a large data/engineering
  task on top of everything else in this pass. What WAS built: a
  standalone chart artifact —
  https://claude.ai/artifact/HGwoB52qgiY5mwjfR6b5Uw — showing every
  replicate's end-of-release alignment as a strip plot, per seed per
  branch, with paired-difference table view, covering all 5 seeds'
  causal comparisons in one place. This satisfies "visualization is part
  of verification" in a reduced but genuine form; it does not replace the
  literal spec ask, and that gap is listed in
  `NEXT_CONTROLLER_SPEC_INPUTS.md` as follow-on work.
- **`FINAL_STAGE611_ADJUDICATION.md`**: complete, all 5 seeds, full column
  set, `not evaluated` used honestly wherever this pass's evidence does
  not speak to a dimension.
- **`stage6_flock/CURRENT_RESEARCH_STATUS.md`**: written at the end of
  this pass as the repository-level handoff spec §16 requires.

## No-redesign statement

Nothing under `code/` imports, patches, subclasses, or monkeypatches
`run_online_control_611.py`, `lineage_611.py`, `lineage_v2_611.py`,
`control_authority_611.py`, `intervention_api_611.py`, or
`moving_flock_611.py`. Every script either (a) replays already-recorded
production data read-only, or (b) constructs a NEW, separate rollout using
`MovingFlock611.step`/`step_cached` with production's own physics update
equations, called with different (never mutated) generator objects for
audit-only CRN pairing — never a different update rule.
