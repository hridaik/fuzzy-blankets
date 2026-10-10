# Identity Validity and Disruption Across Closures A/B/C

All rollouts in this closure use the same identity machinery as every
prior stage (`ForwardMaterialTrace611`, frozen Jaccard≥0.30 rule) and the
same two-tier validity definition:

- `V` (association-continuity): 1 iff the trace's `status == "continuing"`
  for every frame in the release-evaluation window — split/merge-flagged
  continuations still count.
- `V_conservative`: 1 iff `V==1` AND zero split flags, zero merge flags,
  zero unresolved steps anywhere in the traced rollout. Strict lower
  bound; PRIMARY for this closure, as in Stage 6.12/6.12B/6.12C.

## Closure A/B campaign (K=1, d=8, release=24; 8 states, 272 rollouts)

| actuator class | n | V rate | V_conservative rate | material_split_flag | material_merge_flag | lost_dead |
|---|---|---|---|---|---|---|
| core_member | 96 | 0.896 | 0.542 | 0.344 | 0.135 | 0.052 |
| boundary_member | 28 | 0.893 | 0.393 | 0.464 | 0.286 | 0.000 |
| live_exterior_parent | 20 | 1.000 | 0.350 | 0.450 | 0.500 | 0.000 |
| near_exterior_non_parent | 96 | 0.875 | 0.542 | 0.385 | 0.094 | 0.031 |
| **all classes pooled** | 240 | 0.896 | 0.508 | 0.383 | 0.167 | 0.033 |

**Observation** (descriptive, n too small per class for a formal test):
`V_conservative` is lower for `boundary_member` (0.393) and
`live_exterior_parent` (0.350) than for `core_member`/`near_exterior_
non_parent` (0.542 each) — consistent with the Closure-C timing
sub-study's independent observation (below) that forcing an actuator with
active live causal access to the target is more disruptive to strict
organizational continuity than forcing a distant exterior bird or an
already-embedded core member. `live_exterior_parent` shows the highest
`material_merge_flag` rate (0.500) of any class — plausible mechanism: an
exterior bird being forced INTO alignment with a target it already has
live causal access to is more likely to be swept into (or trigger a
merge-flagged overlap with) that target's traced lineage. This is
reported as a descriptive pattern in a 20-96-observation-per-class
sample, not a formally tested hypothesis.

## Closure C timing sub-study (K=1, d=8, release=24, varying onset; 57 rollouts)

Pooled across the 3 states with any usable data (`sclosure_01`,
`sclosure_02`, `sclosure_03` — see `TIMING_SUSCEPTIBILITY.md`'s disclosed
sparsity note; `sclosure_00` contributed zero rollouts):

- `V` rate: **0.789** (45/57).
- `V_conservative` rate: **0.404** (23/57).
- Event breakdown: `none` 23, `lost_dead` 12, `material_merge_flag` 12,
  `material_split_flag` 10.

This is materially LOWER identity-validity than Stage 6.12's historical
random/exterior-actuator baseline (94-100% `V`, Stage 6.12 Phase A/C). The
timing sub-study exclusively forces `live_exterior_parent`/
`boundary_member` actuators — i.e. actuators that, by construction, are
either already inside the target's organizational boundary or have an
active live causal channel into it. This is consistent with (not
independent proof of, given n=3 states) the general pattern that forcing
an actuator with genuine causal access to the target is more disruptive
to organizational continuity than forcing an arbitrary distant exterior
bird — a plausible mechanism (a live-connected or boundary actuator is,
almost by definition, closer to co-mingling with the target than a
distant exterior bird with no live channel), not claimed here as a
formally tested hypothesis (that would require a matched no-effect
comparison this closure's small n cannot support).

## Interior-actuator scoring correction check

For every interior/boundary actuator, `A_minus_j`/`J_*_minus_j` is
computed alongside the ordinary metric (see
`ORGANIZATIONAL_ROLE_RESULTS.md`). Spot-checked: when the forced interior
bird has already left the traced target lineage by the late-release
evaluation window (a common outcome — forcing an interior bird toward
`h_star` can itself cause it to depart the tracked material lineage), the
corrected and uncorrected metrics are numerically identical by
construction (excluding an absent member from a fraction changes nothing)
— this is the CORRECT behavior per
`INTERIOR_ACTUATION_METHOD_NOTE.md`, not a bug, and was directly verified
against one example rollout during code review (bird 360,
`sclosure_00_seed64200`, core-member actuator: departed the target by
frame 24 of 32, so `A_release_late == A_minus_j_release_late` in that
case).

## Persistence

Late-release alignment (`A_release_late`, `end_of_release_alignment`) and
the release-window trajectory are recorded for every rollout in
`data/closureAB_rollouts.json`/`data/closureC_timing_rollouts.json` but not
separately re-plotted here — see `figures/` and
`interactive_demo/v3` tab 9/10 for the visual summaries.
