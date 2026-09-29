# Stage 6.12C — Final Findings

**Scope reminder**: 10 fresh confirmatory states (seeds 63200-63209,
10/10 qualified on first attempt, disjoint from every prior seed range),
K=1 exhaustive primary (20 candidates × 12 physics streams/state), K=2
secondary (26 pairs × 6 confirmatory streams/state), duration-safety
sub-study (5 predeclared states, d=8 vs d=24). Total wall time 4.85h. This
is a disclosed, user-approved reduction from the task brief's N_STATES=20
full design (`README.md`'s reduction table) — read every finding below at
that precision.

## 1. Does the frozen kinematic predictor prospectively identify
   higher-effect actuators?

**Not reliably, at this state count.** The primary estimand's ratio form
(L_pred, median 1.23, 87.5% of valid states positive) looks favorable in
isolation, but is driven substantially by near-zero denominators in 2/10
states and is unstable. The ratio-FREE absolute comparison (top-predicted
candidate's mean confirmatory ΔJ_conservative minus the median
candidate's) is essentially flat: **mean +0.00017, 90% state-clustered CI
[-0.0026, +0.0030]**, with only 4/10 states showing the top candidate
actually beating the median (`K1_EXHAUSTIVE_RESULTS.md`). The
predictor-ranking correlation is weakly positive on average (median
state-level ρ=+0.145) but its CI also spans zero
(`PREDICTOR_VALIDATION.md`), and a top-quartile-vs-bottom-quartile
comparison shows a mild REVERSAL (bottom quartile candidates had a
slightly higher realized mean effect than top-quartile candidates).

## 2. Is future contact itself causally uninformative, or is the
   deployable predictor just estimating it poorly?

**Neither, cleanly — this is the stage's sharpest and most useful
finding.** The oracle decomposition (`ORACLE_DECOMPOSITION.md`) shows:

- A genuinely large, state-clustering-robust selective-effect headroom
  DOES exist: the non-deployable outcome oracle (best singleton per
  stream) achieves mean ΔJ_conservative ≈6.9× the random/median
  candidate, with a 90% CI cleanly separated from every other strategy.
- But the forced-future CONTACT oracle — a genuine, non-deployable upper
  bound on "found the actuator with the most realized future physical
  contact" — does NOT capture this headroom. Its mean sits at or slightly
  BELOW the random baseline.
- The deployable kinematic predictor tracks the (weak) contact oracle,
  not the (strong) outcome oracle, and the two oracles agree on the same
  "best" candidate in only 1/10 states.

**This rules out both "no headroom exists" (Case D) and "contact is the
mechanism but the deployable predictor estimates it poorly" (Case B).**
The headroom is real; contact — even measured with a genuine forced-future
upper bound, not just the deployable proxy — is not where it lives.

## 3. Does the frozen K=2 pair-aggregation rule beat random pairs?

**Not reliably.** Top-predicted pairs beat the random-pair median in 6/10
states, mean lift +0.0109, 90% CI spans zero. The low-predicted-contact
comparator pair showed an even larger (noise-driven, single-pair,
state-`s612c_02`-dominated) mean than the top-predicted pair — an internal
inconsistency that further undercuts confidence in the aggregation rule
at this scale (`K2_SECONDARY.md`).

## 4. Does the kinematic score add incremental value beyond current
   contact or static distance?

**Not established either way at this state count.** A simple, predeclared
rank regression shows the kinematic score with the largest point-estimate
coefficient of the three predictors tested, but every coefficient's
state-clustered 90% CI spans zero (`INCREMENTAL_VALUE_ANALYSIS.md`).

## 5. Duration safety: is 24-step forcing riskier than 8-step forcing at K=1?

**No elevated target-loss detected at K=1** (0% lost/dead at both d=8 and
d=24, 5-state paired sub-study) — a genuinely different, K=1-specific
result from Stage 6.12B's 15.5% loss rate at K∈{2,4}, d=24. This is NOT a
contradiction of Stage 6.12B (different forcing cardinality) — it
specifically shows that single-actuator forcing does not carry the same
extended-duration disruption risk that multi-actuator forcing does
(`DURATION_SAFETY.md`).

## 6. Identity and disruption

Conservative identity validity held in 91.1% of K=1 confirmatory
rollouts, materially higher than Stage 6.12's pooled 64.0% (K=1, d=8 is a
much smaller perturbation than Stage 6.12's full K×d grid). One state
(`s612c_03`, 55.6% conservative-valid) is a clear disruption-prone
outlier within this sample (`IDENTITY_AND_DISRUPTION.md`).

## Prior-data caveat (disclosed, unaffected by this stage's own result)

Stage 6.12B's 3-state exhaustive data showed ρ≈-0.06 for the specific
K1,d8 cell this stage treats as primary (vs. +0.78 for K1,d4 and +0.43
for K2,d8; the headline pooled ρ≈0.23-0.29 spans multiple cells). This
stage's own confirmatory K1,d8 result (median state-level ρ=+0.145, CI
spanning zero) is directionally more positive than that prior single
K1,d8 reading but still not state-clustered-reliable — this caveat is
recorded regardless of which way this stage's own result went, and it
went in a direction consistent with "weakly positive, unreliable at this
precision," not a clean replication of either the K1,d4 lead or the K1,d8
null.

## What this stage does NOT establish

- That the kinematic predictor is useless — CIs span zero, they do not
  exclude a true small positive effect.
- That future physical contact never matters for any intervention in this
  system — only that, specifically for K=1 singleton actuator selection
  at d=8, the realized/predicted contact oracles do not explain the
  effect headroom that clearly exists.
- That K=1 forcing is safe at ALL durations or cardinalities — only that
  this specific 5-state, K=1, d=8-vs-24 paired comparison found no
  elevated loss rate.

See `NEXT_STAGE_DECISION.md` for the explicit Case A/B/C/D call and what
the next task may and may not assume.
