# Seed 504 causal adjudication

Same harness as `seed_501_causal.md` — `code/seed_generic_schedule_effect.py 504`.
Trigger t0=47 (bit-exact reproducible), target_heading=3, 47 simulated
steps, 25 replicates.

## Identity baseline (prior passes, cited)

v1 and material identity agree cleanly through the actual recorded
episode; prior work characterized this seed as showing "positive
short-horizon authority without persistent reorganization" — a real but
transient control-window response that did not clearly persist. Explicit
task instruction: preserve the distinction between short-horizon response
and persistent successful transition; do not call this intrinsically
uncontrollable.

## This pass's addition: exact v2 replay

`V2_REPLAY_AND_FIELD_READOUT.md`: v1 and material anchors agree exactly
(both low, "no turn," at every radius) — but v2's own EXACT anchor is a
striking outlier, HIGH (0.72–0.88) at every radius, DESPITE 90/94 frames
of exact v1==v2 membership agreement. This means v2's centroid, even when
its tracked membership matches v1's almost throughout, lands in a more-
aligned neighborhood at the final frame — a genuine, disclosed
complication for treating this seed as "anchor-clean," though it does not
by itself overturn the membership-based "no turn" reading (see that
document for full discussion).

## Schedule-effect results — the most striking result in the 5-seed sweep

| branch | n | mean end-of-release | median | std | p90 |
|---|---|---|---|---|---|
| no_forcing | 25 | 0.021 | 0.016 | 0.020 | 0.048 |
| historical_schedule | 25 | **0.389** | 0.072 | 0.404 | 0.917 |
| matched_random | 25 | 0.450 | 0.119 | 0.419 | 0.928 |

### Paired differences (CRN)

| comparison | n | mean diff | std | 90% CI | fraction positive |
|---|---|---|---|---|---|
| historical − no_forcing | 25 | **+0.367** | 0.402 | [0.235, 0.499] | **84%** |
| historical − matched_random | 25 | −0.061 | 0.601 | [−0.259, 0.137] | 44% |

## Interpretation — read the mean AND the median together

The mean end-of-release alignment under forcing (historical: 0.389;
matched random: 0.450) is dramatically higher than no forcing (0.021),
and the paired comparison is strong: 84% of replicates favor the
historical schedule over no forcing, 90% CI on the paired mean entirely
positive and well clear of zero ([0.235, 0.499]) — a clearly demonstrated
intervention effect, the strongest paired signal of any seed in this
sweep.

**But the MEDIAN (0.072) is far below the MEAN (0.389), and std (0.40) is
comparable to the mean** — this is a heavily right-skewed, likely
bimodal outcome distribution: most replicates show a modest response,
while a substantial minority reach very high alignment (p90 = 0.917).
**This directly refines, rather than simply overturning, the prior
"short-horizon response without persistent reorganization"
characterization**: under repeated stochastic replicates from the same
trigger state, sustained forcing CAN and sometimes DOES produce a
persistent (measured at end of RELEASE, not just end of control)
reorganization for this seed — but unreliably, not as the typical
outcome. The single historical recorded run apparently landed on the
"modest response" side of this distribution, which is why it was
previously characterized as non-persistent; this pass's replicates show
that characterization describes the TYPICAL case, not the ONLY possible
one.

**Actuator selectivity: not demonstrated** — matched random forcing does
at least as well on average (mean 0.450 vs. 0.389), and the paired
historical-vs-random comparison is centered near zero (mean −0.061, CI
crosses zero, 44% positive).

## Fields

| dimension | evidence status |
|---|---|
| physical_turn_of_material_target | not demonstrated under no forcing (real recorded run and this pass's no_forcing replicates both stay low); **demonstrated as POSSIBLE, unreliably, under sustained forcing** (bimodal: median low, mean/p90 high) |
| strict_identity_continuity | valid throughout (prior passes; clean v1/material agreement, this pass) |
| intervention_effect | **demonstrated** (paired mean +0.367, 90% CI entirely positive, strongest signal of the 5 seeds) — but highly variable, not a reliable single-outcome effect |
| actuator_selectivity | not demonstrated (historical vs. matched random centered near zero) |
| persistence_after_release | **refined finding**: persistence occurs in a minority of replicates (right-skewed distribution), not reliably — "short-horizon response ≠ persistent transition" is preserved as the TYPICAL case, while this pass shows persistent transition is not impossible, just uncommon under the tested budget |
| organizational_disruption | not demonstrated (checked: no elevated death rate — 25/25 continuing in all three branches, unlike seed 502) |
