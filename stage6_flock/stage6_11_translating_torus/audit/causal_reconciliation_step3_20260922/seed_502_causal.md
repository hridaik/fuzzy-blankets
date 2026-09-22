# Seed 502 causal adjudication

Same harness as `seed_501_causal.md` — `code/seed_generic_schedule_effect.py 502`.
Trigger t0=30 (bit-exact reproducible), target_heading=1, 47 simulated
steps, 25 replicates requested.

## Identity baseline (prior passes, cited)

v1 permanently diverges from the material target around t=32
(`material_identity_step2_20260921/seed_502_identity.md`); the material
target itself does not turn substantially in the actual recorded episode
(≈0.19→0.10); the reported later v1 rise (≈0.75) belongs to a materially
distinct, 50-vs-28-member-mismatched population by episode end.

## This pass's addition: exact v2 replay

`V2_REPLAY_AND_FIELD_READOUT.md`: v1 and v2 anchors are numerically
IDENTICAL at every radius (both converge on the same wrong population);
the material anchor is dramatically and consistently lower at every
radius (0.06–0.13 vs. 0.19–0.80). **This is the strongest reconfirmation
in the whole 5-seed sweep that anchor choice matters and that v1/v2
agreeing with each other does not make them right** — the two
probabilistic trackers here corroborate each other while both diverging
sharply from the material-continuity readout.

## Schedule-effect results

**Notable finding before the alignment numbers**: forcing is associated
with a substantially ELEVATED target-loss (`dead` trace) rate for this
seed specifically — 5/25 (20%) no_forcing replicates lose the material
target entirely, vs. 13/25 (52%) for historical_schedule and 11/25 (44%)
for matched_random. This sharply reduces the number of replicates with a
valid paired alignment reading (n=10 for historical-vs-no-forcing, n=7
for historical-vs-random).

| branch | n (valid) | mean end-of-release | median | n died / 25 |
|---|---|---|---|---|
| no_forcing | 20 | 0.155 | 0.098 | 5 (20%) |
| historical_schedule | 12 | 0.137 | 0.066 | 13 (52%) |
| matched_random | 14 | 0.191 | 0.127 | 11 (44%) |

### Paired differences (CRN, small n due to the death-rate reduction above)

| comparison | n | mean diff | std | 90% CI | fraction positive |
|---|---|---|---|---|---|
| historical − no_forcing | 10 | +0.027 | 0.113 | [−0.032, 0.086] | 50% |
| historical − matched_random | 7 | −0.120 | 0.233 | [−0.265, 0.026] | 14% |

## Interpretation

**No evidence that the historical intervention raises the material
target's alignment** — the paired difference vs. no forcing is a coin
flip (50% positive, CI straddling zero), and vs. matched random the point
estimate favors RANDOM forcing over the historical choice (though n=7 is
too small to treat this as a reliable signal by itself — reported for
completeness, not overclaimed).

**The more robust, better-powered finding is the elevated death rate**:
sustained forcing (whether historical or random) roughly 2–2.5×'s the
rate at which the material target loses detectable coherence entirely,
relative to no forcing (20% → 44–52%). This is consistent with, and adds
causal texture to, the prior identity finding that this seed's material
target is comparatively fragile — actuators forcing a heading here appear
more likely to disrupt the target to the point of losing it than to turn
it.

**Per the task's explicit instruction, this is NOT interpreted as
"seed 502's original target is intrinsically uncontrollable."** It is
interpreted narrowly: under the TESTED intervention approach (the
historical top-K-by-authority actuator set, held for the full control
duration, exactly as the original implementation did it), no turning
effect is demonstrated, and a fragility/loss effect is. Whether a
different actuator budget, duration, or selection principle could turn
this target without destroying it is not evaluated here.

## Fields

| dimension | evidence status |
|---|---|
| physical_turn_of_material_target | contradicted (real recorded run: 0.19→0.10; this pass's replicates: no clear rise, paired diff ≈0) |
| strict_identity_continuity | v1 permanently diverges at t≈32 (prior passes); this pass's replicates show markedly reduced material-target SURVIVAL under forcing (44–52% death vs. 20% unforced) |
| intervention_effect | not demonstrated (paired mean ≈0, CI crosses zero) |
| actuator_selectivity | not demonstrated (point estimate favors random, but n too small for a confident claim either way) |
| persistence_after_release | not applicable in most replicates (target frequently lost before release) |
| organizational_disruption | **demonstrated in a specific sense**: elevated target-LOSS (death) rate under forcing relative to no forcing — a form of disruption distinct from the split/fragmentation outcome tracked for seed 503, but conceptually related (control-associated loss of a trackable, coherent target) |
