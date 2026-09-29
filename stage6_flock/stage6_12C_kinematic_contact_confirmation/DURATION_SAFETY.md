# Stage 6.12C — Duration Safety Sub-Study

Analysis code: `code/analysis_612c.py` (`duration_analysis`). Reduced
scope per `README.md`: 5 of the 10 states (predeclared subset,
`s612c_00`..`s612c_04`), K=1, d=8 vs. d=24, top-kinematic-predicted
candidate and one matched random candidate, 6 PAIRED confirmatory
physics streams (identical seeds at both durations). Full data:
`data/duration_substudy_612c.json` (10 rows = 5 states × 2 candidates).

## Per-state paired comparison

| state | top-kin ΔJ_cons d=8 | top-kin ΔJ_cons d=24 | random ΔJ_cons d=8 | random ΔJ_cons d=24 | top-kin lost/dead @d24 | random lost/dead @d24 |
|---|---|---|---|---|---|---|
| s612c_00 | 0.00000 | -0.00142 | 0.00000 | 0.00000 | 0/6 | 0/6 |
| s612c_01 | -0.01198 | +0.01722 | -0.00090 | +0.00150 | 0/6 | 0/6 |
| s612c_02 | 0.00030 | 0.00661 | 0.15098 | 0.13817 | 0/6 | 0/6 |
| s612c_03 | 0.01963 | -0.00170 | 0.00390 | 0.00217 | 0/6 | 0/6 |
| s612c_04 | 0.01172 | -0.00618 | 0.00275 | -0.00469 | 0/6 | 0/6 |

## Summary (5 states, 6 paired streams each = 30 paired rollouts per arm)

| quantity | value |
|---|---|
| top-kinematic mean ΔJ_conservative, d=8 | 0.00394 |
| top-kinematic mean ΔJ_conservative, d=24 | 0.00291 |
| matched-random mean ΔJ_conservative, d=8 | 0.03135 (dominated by s612c_02's outlier +0.151) |
| matched-random mean ΔJ_conservative, d=24 | 0.02743 |
| top-kinematic lost/dead rate at d=24 | 0/30 = 0.0% |
| matched-random lost/dead rate at d=24 | 0/30 = 0.0% |
| top-kinematic `V_conservative` rate at d=24 | 30/30 = 100% |
| matched-random `V_conservative` rate at d=24 | 27/30 = 90% |

## Interpretation

**No elevated target-loss risk detected at this scope (K=1, longer
duration), unlike Stage 6.12B's finding for K=2/K=4.** Stage 6.12B found a
15.5% `lost_dead` rate for matched-effort 24-step interventions (at
K∈{2,4}, forcing multiple birds for the full 24-step control window,
followed by a further 24-step release). This sub-study's K=1, single-
actuator forcing shows **0% lost/dead at d=24 in both arms** (30 paired
streams each) — consistent with the physically reasonable expectation
that forcing a single exterior bird is a much smaller perturbation to the
flock's collective dynamics than forcing 2-4 birds for the same duration,
and this sub-study should NOT be read as contradicting Stage 6.12B's
disruption finding — the two results are about different forcing
cardinalities (K=1 here vs. K∈{2,4} there), a distinction the task brief's
own caution ("do not infer duration toxicity merely from cross-stage
percentage comparisons") anticipates. This is a direct, paired K=1-only
test, and it finds no K=1-specific 8-vs-24 loss-rate difference.

**Longer forcing does not reliably increase the top-kinematic candidate's
effect either** — mean ΔJ_conservative is nominally slightly LOWER at
d=24 (0.00291) than at d=8 (0.00394), and the paired per-state pattern is
sign-inconsistent (2/5 states higher at d=24, 3/5 lower). Given this
sub-study's small scope (5 states), this should be read as "no evidence
that extending K=1 forcing from 8 to 24 steps helps," not as "extending
duration definitely does not help."

**The matched-random candidate outperforms the top-kinematic candidate at
BOTH durations in this 5-state subset** (0.031 vs 0.004 at d=8; 0.027 vs
0.003 at d=24) — consistent with, not contradicting, this stage's primary
finding (`K1_EXHAUSTIVE_RESULTS.md`, `PREDICTOR_VALIDATION.md`) that the
kinematic predictor does not reliably identify higher-effect candidates.
This particular 5-state comparison is additionally skewed by
`s612c_02`'s single large random-candidate effect (+0.151 at d=8); the
sub-study was not designed or powered to isolate predictor quality from
duration safety cleanly at this scale, and duration-safety conclusions
(the lost/dead-rate finding above) are more robust here than the
paired-effect-magnitude comparison.
