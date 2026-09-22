# Stage 6.11 Material Identity — Step 2 (2026-09-21)

## Frozen scope

This directory resolves flock identity with the simplest defensible
forward material-continuity model (`ForwardMaterialTrace611`), validates
it **independently of the five historical control seeds**, and uses it,
frozen and unchanged, to re-adjudicate seeds 500–504.

**Not touched in this task**: flock dynamics, candidate detector
(`detect_69.propose`), control policy, actuator-selection rule, authority
estimator, intervention duration, interaction radius, any historical
simulation path, v1 (`lineage_611.LineageTracker611`), or v2
(`lineage_v2_611.LineageTrackerV2`). `thingness_611.py` was not wired into
qualification or identity; its metrics were not even computed in this pass
(the task explicitly forbade using it to qualify or terminate a lineage).

**Correction acknowledged and acted on**: the Step-1 visual concern was a
misstatement of the seed number. The actual transition of concern is
**seed 503, t=46→47**, not seed 500. Step-1's own material-retention CSV
already flagged this exact transition as zero-overlap
(`evidence_recovery_20260921/data/material_retention_seed503.csv`, row
t=47: `overlap_zero_displayed=True`). This directory investigates it first,
in full bird-ID detail (`seed503_t46_t47_forensics.py`,
`seed_503_t46_t47_forensics.md`).

## Exact commands (reproduction, in order)

```
conda activate fuzzy-blankets
cd stage6_flock/stage6_11_translating_torus/audit/material_identity_step2_20260921/code

# 1. Reproduce/confirm Step-1 findings (no new code needed -- see step2_reproduction_check.md)

# 2. Seed 503 t=46->47 deep forensics (bird-ID level, full replay)
python3 seed503_t46_t47_forensics.py

# 3. Calibrate the identity rule from UNCONTROLLED data only (seeds 236-247,
#    disjoint from 500-504) -- ~4 minutes, Louvain over 12*181 steps
python3 calibrate_identity_rule.py
# then freeze the rule (see identity_rule_spec.md for the exact frozen values
# written into data/identity_rule_calibration.json's "frozen_rule" key)

# 4. Known-history synthetic identity tests (A-G) against the frozen rule
python3 synthetic_identity_tests.py

# 5. Apply the frozen, unchanged rule to seeds 500-504
python3 apply_trace_to_seeds.py

# 6. Re-evaluate Step-1's ID-independent readouts against the new trace
python3 rescoring_reassessment.py

# 7. Plots
python3 make_comparison_plots.py

# 8. Interactive-demo instrumentation (adds a ForwardMaterialTrace611 panel
#    to interactive_demo/v2 tab 6, alongside the existing v1/material-
#    retention panels; no tracker code touched)
cd ../../../../../interactive_demo/v2/src
python3 data_prep/prep_tab6_translation.py
python3 data_prep/prep_tab6_forward_trace.py
python3 build_v2.py
```

All scripts are deterministic given the repository's existing, unmodified
`data/viz_bundle_611__seed*.json`, `data/observational_corpus_611__val.npz`,
and Step-1 artifacts under `../evidence_recovery_20260921/`. No simulator
RNG is consumed by any script here — `detect_69.propose` and
`ForwardMaterialTrace611` are both deterministic given `(r, z)`.

## Repository commit used

`940a5f672bc9b8302c0436e5a531cea6ae1f6ce1` (same as Step 1; no commits were
made to tracker/controller/world code by this task either).

## Data provenance summary

| input | source | role |
|---|---|---|
| `data/viz_bundle_611__seed{500..504}.json` | production, Stage 6.11 | ground-truth (r,z) trajectories, replayed not re-simulated |
| `data/observational_corpus_611__val.npz` | Stage 6.11 predictive-model dev pipeline, 12 uncontrolled episodes, seeds 236-247 | **calibration data for the identity rule** — disjoint from 500-504, never touched by any control/outcome label |
| `../evidence_recovery_20260921/*` (Step 1) | this audit programme | cited for cross-checks, not modified |
| `code/detect_69.py`, `code/lineage_611.py` (imported, unmodified) | production | candidate detector reused as-is; v1 reused as a comparator only |

## No-redesign statement

`ForwardMaterialTrace611` (`code/forward_material_trace_611.py`) is a new,
standalone, audit-only module. It is never imported by, or wired into,
`run_online_control_611.py` or any controller/authority code. It consumes
the same detector output (`detect_69.propose`) that v1 already uses,
unmodified, and never receives `target_heading`, actuator identity, or any
outcome metric in its continuation-scoring path — this is enforced
structurally (see `forward_material_trace_611.py`'s `Rule.accept` type:
a pure function of set-overlap numbers only) not just by convention.
