# Closure C — Timing Susceptibility

## Question

Is outcome variation across intervention ONSET time materially larger than
variation across actuator identity at a fixed onset? This is a small,
deliberately bounded check, not an attempt to discover that "a moving
flock needs adaptive control" (already conceptually obvious) or to build
one.

## Design (as run)

First 4 states of the 8-state manifest (`sclosure_00`..`sclosure_03`).
Onset offsets `{0,4,8,12}` real steps. At each onset: recompute material
target, live edges, actuator classes (`live_exterior_parent`,
`boundary_member`), up to 2 actuators/class, 3 physics streams. K=1, d=8,
release=24. 57 rollouts total, 7.6 minutes wall time (see
`logs/run_closureC_timing.txt`).

## Disclosed data sparsity — read before the numbers below

The two class policies used here (`live_exterior_parent`,
`boundary_member`) are, per `STATE_MANIFEST.md`, frequently EMPTY at any
given instant in this interaction regime. In practice:

- **sclosure_00**: zero of either class at ALL four onsets — contributes
  0 rollouts, excluded entirely.
- **sclosure_01**: a class was available only at onsets 8 and 12 (not 0
  or 4).
- **sclosure_02**: a class was available only at onset 12.
- **sclosure_03**: classes were available at onsets 0, 4, and 8 (not 12).

So the usable per-state onset comparison is 1–3 onsets, not the full 4, for
every state, and only 3/4 states contribute any data at all. This is a
direct consequence of the same live-degree sparsity documented in
`STATE_MANIFEST.md` and `ORGANIZATIONAL_ROLE_RESULTS.md`, not a bug in the
timing sub-study. It means this closure's own numbers below are read as a
genuinely small, underpowered check — exactly the "deliberately small"
scope the task spec asked for, but smaller in USABLE onset coverage than
the nominal 4-onset design intended, and that reduction is disclosed here
rather than papered over.

## Results

| state | onsets with data | onset-mean range of ΔJ_conservative | mean within-onset actuator spread | onset ≥ actuator? |
|---|---|---|---|---|
| sclosure_01 | 8, 12 | 0.0 | 0.0 | no |
| sclosure_02 | 12 only | 0.0 (single onset, no range) | 0.0294 | no |
| sclosure_03 | 0, 4, 8 | 0.0121 | 0.0033 | **yes** |

Pooled across the 3 states with any data (state-bootstrap, 90% CI):

- Mean onset-range of ΔJ_conservative: **0.0040**, 90% CI **[0.0000,
  0.0080]**.
- Mean within-onset actuator spread: **0.0109**, 90% CI **[0.0011,
  0.0207]**.
- States where onset variation ≥ within-onset actuator variation: **1/3**.

## Interpretation

In this small, sparsity-limited sample, onset-time variation is **not**
clearly larger than actuator-identity variation — if anything, the
pooled point estimate for within-onset actuator spread (0.0109) exceeds
the pooled onset-range point estimate (0.0040), and only 1 of the 3
states with usable data shows onset dominating. Both quantities are small
in absolute terms and both CIs are wide relative to their means, given
n=3 states.

**Per the task's own decision language, this is read as: timing
variation is NOT shown to dominate over stable actuator-identity variation
in this bounded sample.** This does not contradict the (already
established, `stable_selectivity_analysis/`) finding that stable actuator
identity itself explains very little variance — it means that, at least
in the classes and sample tested here, neither "which actuator" nor
"when" cleanly dominates the other; most of the outcome variation in this
system continues to look consistent with the previously-established
stochastic-opportunity (physics-stream) pattern rather than being cleanly
attributable to either axis tested in this closure.

This finding is NOT oversold into "the flock needs adaptive control" (a
trivial, already-known fact) — the only claim made here is the
quantitative comparison above, and it is a weak/inconclusive one given the
disclosed sparsity. A future attempt at this question would need either a
denser interaction regime (larger R, or a different definition of
"boundary"/"live parent" less sensitive to single-instant live-degree
sparsity) or a larger onset/state grid — both explicitly out of scope for
this closure's hard stop.
