# Seed 500 causal adjudication (reference/sanity case)

Same schedule-effect harness/CRN methodology as `seed_501_causal.md` —
`code/seed_generic_schedule_effect.py 500`. Trigger t0=61 (bit-exact
reproducible), target_heading=1, 47 simulated steps, 25 replicates.

## Identity baseline (prior passes, cited)

v1 and material identity agree throughout the actual recorded episode
(Step 1/Step 2) — the clean sanity case. v1's own displayed
target-alignment fraction stays low across the real control window
(0.12→0.06; `data/online_control_611__seed500.json`), consistent with
"no turn."

## This pass's addition: exact v2 replay

`V2_REPLAY_AND_FIELD_READOUT.md`: v1 and material anchors give IDENTICAL
field-direction readings at every radius in the actual recorded
trajectory (both trace the same population); v2's anchor differs only
slightly and stays in the same low range. No anchor-sensitivity issue.

## Schedule-effect results

| branch | n | mean end-of-release | median | std | final status |
|---|---|---|---|---|---|
| no_forcing | 25 | 0.050 | 0.045 | 0.030 | 25/25 continuing |
| historical_schedule | 25 | 0.059 | 0.053 | 0.033 | 25/25 continuing |
| matched_random | 25 | 0.063 | 0.071 | 0.033 | 25/25 continuing |

### Paired differences (CRN)

| comparison | n | mean diff | std | 90% CI | fraction positive |
|---|---|---|---|---|---|
| historical − no_forcing | 25 | +0.0093 | 0.0279 | [0.0001, 0.0185] | 68% |
| historical − matched_random | 25 | −0.0040 | 0.0236 | [−0.0118, 0.0037] | 52% |

## Interpretation

**All three branches stay uniformly low** (means 0.05–0.06, far below a
"turn" — compare seed 501's no_forcing mean of 0.26 and historical mean of
0.60). The paired historical-vs-no-forcing effect is tiny (mean +0.009)
and only barely distinguishable from zero at this sample size (90% CI
just clears zero: [0.0001, 0.0185]) — a qualitatively different, much
weaker signal than seeds 501/503's clear paired effects. historical-vs-
matched-random shows no effect (CI straddles zero comfortably).

**This is a useful negative control for the harness itself**: the same
methodology that found clear, substantial intervention effects for seeds
501 and 503 does NOT manufacture a similarly large effect for seed 500 —
consistent with seed 500's established "no turn" character, and evidence
that the schedule-effect harness is not trivially biased toward finding
an effect regardless of the underlying dynamics.

## Fields

| dimension | evidence status |
|---|---|
| physical_turn_of_material_target | not demonstrated (all branches, including no forcing, stay low; consistent with prior "no turn" finding) |
| strict_identity_continuity | valid throughout (prior passes; reconfirmed by clean v1/v2/material anchor agreement, this pass) |
| intervention_effect | marginal / not clearly demonstrated (paired mean +0.009, 90% CI barely excludes zero, much weaker than 501/503) |
| actuator_selectivity | not demonstrated |
| persistence_after_release | not applicable (no substantial rise to persist) |
| organizational_disruption | not evaluated (not the priority case; not systematically checked, only noted in passing) |
