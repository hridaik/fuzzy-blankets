# Stage 6.12C — Incremental Predictive Value Analysis

Analysis code: `code/analysis_612c.py` (`incremental_value_analysis`).
Predeclared, non-ML analyses only, per the task brief: (1) within-state
rank association stratified by direct-contact-at-t0 status; (2) a simple
rank regression of `ΔJ_conservative` on `[direct_contact_t0,
static_distance, kinematic_score]` with within-state rank-normalization
(a simple fixed-effect-style approximation, not a learned model) and a
state-clustered bootstrap for uncertainty.

## 1. Stratified by direct-contact-at-t0 status

`direct_contact_t0` (audit/structural quantity — whether candidate j is
already within true R of some target member at t0) is RARE in the
nearest-20 pool: only **2/10 states** had ≥4 candidates with
`direct_contact_t0=1` (enough to compute a within-state rank
correlation at all); the other **9/10 states*** effectively had
zero-or-near-zero candidates in direct contact at t0 (*the two counts sum
to 11 because state-level "has ≥4 in each stratum" is not mutually
exclusive with small strata; in practice contact-at-t0 candidates are a
small minority of the pool in nearly every state).

| stratum | mean state-level ρ (C_hat_kin vs ΔJ_conservative) | median |
|---|---|---|
| candidates in direct contact at t0 (n=2 states with ≥4 such candidates) | 0.042 | 0.042 |
| candidates NOT in direct contact at t0 (n=9 states with ≥4 such candidates) | 0.050 | 0.148 |

**No meaningful difference between strata** — the kinematic predictor's
(already weak) correlation with outcome does not depend on whether the
candidate already happens to be touching the target at t0. This is a
genuine null on this specific stratified check, not a confirmation that
current contact adds value beyond the kinematic score, nor the reverse.

## 2. Rank regression (within-state rank-normalized, state-clustered bootstrap, n=200 candidate-rows, 10 states)

```
rank(ΔJ_conservative) ~ direct_contact_t0 + static_distance(closer=higher) + kinematic_score
```

| predictor | coefficient | 90% CI (state-clustered bootstrap, 2,000 resamples) |
|---|---|---|
| `direct_contact_t0` | +0.0256 | [-0.116, +0.163] — spans zero |
| `static_distance` (closer = higher rank) | +0.0483 | [-0.140, +0.264] — spans zero |
| `kinematic_score` | +0.0756 | [-0.134, +0.234] — spans zero |

## Interpretation

**None of the three predictors — current direct contact, static t0
distance, or the frozen kinematic score — shows a state-clustered-
reliable partial association with realized paired effect at this state
count.** The point estimates are directionally consistent with each
predictor contributing something positive (kinematic score has the
largest point-estimate coefficient of the three, +0.076, matching its
status as "the most promising lead" from Stage 6.12B), but every
coefficient's 90% CI comfortably spans zero. This is exactly what
`PREDICTOR_VALIDATION.md`'s state-clustered-null finding would predict —
a weak, noisy signal does not become a strong, reliable one just by
adding two more predictors to a simple regression at n=10 states.

**This analysis does not establish that the kinematic score has
incremental value beyond current contact or static distance** — nor does
it rule that out; the confidence intervals are too wide, at this state
count, to distinguish "weak positive," "zero," or even "weak negative"
incremental value for any of the three candidate predictors. A much
larger state count (well beyond this stage's N_STATES=10) would be needed
to sharpen this specific comparison, and per the task brief's own
compute-budget lesson from Stage 6.12/6.12B, state count — not stream
depth — is the binding constraint on doing so.
