# Stage 6.12B — Contact-Persistence Benchmark

**Git commit at start of this stage**: `9ba830d0f8410b5e4bf071472bbd6b290fa714f9`
plus the Stage 6.12 deliverable commit from immediately prior in this
session. **Date**: 2026-09-22.

## Scientific question

Stage 6.12 (broad readiness map, `stage6_flock/stage6_12_control_
readiness/`) found that typical random fixed actuator sets have
approximately zero average effect on a materially-tracked moving flock,
and that a sparse development search did not find fixed sets that reliably
beat random sets on held-out physics streams. Part I of this task
(`STAGE612_CORRECTION.md`, full memo in the Stage 6.12 directory)
re-examined that evidence with corrected identity semantics and
state-clustered uncertainty; the null largely survives, but with important
caveats (state heterogeneity, a much-weakened but not entirely absent
contact-persistence lead).

Stage 6.12B tests, prospectively, whether the missing ingredient is:

**A.** no useful controllability at all in this regime;
**B.** controllability exists, but good FIXED actuator sets are rare and
were under-searched;
**C.** controllability depends on MAINTAINING access over time
(spatiotemporal, refreshing actuator identity) rather than on selecting
one static set at `t0`.

## Two sub-experiments

- **6.12B-A** (`run_fixed_set_exhaustive_612b.py`): exhaustive K=1 (20
  sets) and K=2 (190 sets) fixed-set search at `d∈{4,8}`, with genuine
  development→holdout confirmation, directly testing (B).
- **6.12B-B** (`run_refreshed_access_612b.py`): matched-total-effort
  comparison of refresh cadence `q∈{24,8,4,2,1}` and 5-6 actuator-selection
  strategies (random, nearest, kinematic-predicted-contact [physics-assisted
  and radius-free variants], oracle-future-contact [audit-only upper
  bound], and a static best-fixed-set reference), directly testing (C).

Both reuse Stage 6.12's frozen simulator/detector/identity-tracker/primary
pool unmodified (`common_612b.py` imports `common_612`/`intervention_612`
from `stage6_12_control_readiness/code/`), and both persist
`V_conservative`/`J_conservative` at compute time (see
`IDENTITY_SEMANTICS_CORRECTION.md`).

## Disclosed scale reductions (frozen before results; see EXPERIMENT_SPEC.md)

| Quantity | Task-brief target | This run |
|---|---|---|
| Development states (sampled) | ≥12 | 3 |
| Holdout states (sampled) | ≥6 | 2 |
| 6.12B-A: states searched exhaustively | all sampled states | 3 of 5 (2 dev, 1 holdout) |
| 6.12B-A: dev physics streams/set | ≥8 | 1 |
| 6.12B-A: holdout physics streams/finalist | ≥24 | 4 |
| 6.12B-B: physics streams/cell | not specified, "meaningful depth" | 3 |
| 6.12B-A: K,d coverage | K∈{1,2} exhaustive, d∈{4,8} | **preserved in full — no reduction** |
| 6.12B-B: q,K,strategy grid | q∈{24,8,4,2,1}, K∈{2,4}, 5-6 strategies | **preserved in full — no reduction** |

Exhaustive set coverage and the full q/strategy/K grid structure are never
reduced — only physics-stream depth and state count, per the task brief's
own stated priority order (S27).

## Commands (run from `code/`, `conda activate fuzzy-blankets`)

```
python3 world_sampling_612b.py            # -> data/state_manifest_612b.json
python3 rng_crn_diagnostic_612b.py        # CRN verification
python3 run_fixed_set_exhaustive_612b.py  # 6.12B-A -> data/fixed_set_exhaustive_612b.json
python3 run_refreshed_access_612b.py      # 6.12B-B -> data/refreshed_access_612b.json
python3 contact_predictor_analysis_612b.py
python3 analysis_612b.py
python3 viz_612b.py
```

## Seed manifest

World-sampling seed range: **62200–62399** (fresh; never overlaps Stage
6.12's 61200–61399, seeds 500–504, or any prior audit). RNG stream
separation (physics vs. design) documented in `RNG_PROTOCOL` (inherited
from Stage 6.12, verified again here by
`rng_crn_diagnostic_612b.py`). Exact seeds in
`data/state_manifest_612b.json` / `STATE_MANIFEST.md`.

## Deliverables

See `DECISION_MEMO.md`, `STAGE612_CORRECTION.md`,
`IDENTITY_SEMANTICS_CORRECTION.md`, `STATE_LEVEL_REANALYSIS.md`,
`CONTACT_EFFECT_REANALYSIS.md`, `EXPERIMENT_SPEC.md`, `STATE_MANIFEST.md`,
`FIXED_SET_EXHAUSTIVE_RESULTS.md`, `CONTACT_PREDICTOR_ANALYSIS.md`,
`REFRESHED_ACCESS_RESULTS.md`, `IDENTITY_AND_DISRUPTION.md`,
`STATISTICAL_ANALYSIS.md`, `FINAL_STAGE612B_FINDINGS.md`,
`NEXT_STAGE_DECISION.md`, plus `data/*.json` and `figures/*.png`.
