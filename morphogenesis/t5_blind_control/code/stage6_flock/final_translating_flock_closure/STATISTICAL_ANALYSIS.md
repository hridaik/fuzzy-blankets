# Statistical Analysis — Method Notes

Full implementation: `code/analysis_closure.py`.

## Independent unit = STATE, not rollout, not actuator

Every summary in this closure aggregates raw rollouts to one row per
`(state, actuator)` (mean over physics streams), then to one row per
`(state, class)` (mean over the ≤3 sampled actuators in that class in that
state) BEFORE combining across states. Raw rollouts and raw actuators are
never treated as independent replicates when computing a confidence
interval or a class comparison — this is the same discipline
`stable_selectivity_analysis/` established was missing from earlier
per-actuator-pooled summaries, carried forward here structurally rather
than re-derived.

## Class-level summaries (Closure A)

`class_level_summary()`: for each class, one value per state
(mean-of-actuator-means), then a percentile bootstrap (4000 resamples,
resampling STATES, not rollouts) gives a 90% CI on the class's mean
`DeltaJ_conservative`. Reported both for the ordinary metric and the
`_minus_j`-corrected metric.

## Paired class comparisons

`paired_comparison(cls_a, cls_b)`: restricted to states where BOTH classes
have ≥1 sampled actuator (class availability varies by state — see
`STATE_MANIFEST.md`). For each such state, `diff = mean(cls_a) -
mean(cls_b)`; the reported CI bootstraps over these per-state diffs. A
class comparison with `n_states < 3` is reported but flagged as
underpowered rather than treated as a null result — sparsity itself is
disclosed, not hidden by silently excluding thin comparisons.

## Closure B: geometric vs. directed association

`geometric_vs_directed()`: computes a Spearman rank correlation between
`DeltaJ_conservative` and each of (geometric contact count, live directed
access count, temporal-reachability fraction) SEPARATELY WITHIN each
state's own rollout set, then summarizes the distribution of per-state
correlations across states (median + state-bootstrap CI) — never a single
correlation pooled across all rollouts from all states (which would treat
within-state stream variation and between-state variation as
exchangeable, which they are not: `stable_selectivity_analysis/
VARIANCE_DECOMPOSITION.md` found ~20-28% of total ΔJ variance is
physics-stream/opportunity variance, not actuator- or state-level).

## Closure C: onset vs. actuator variance

`closureC_analysis()`: for each of the first 4 states, computes (a) the
range of onset-mean `DeltaJ_conservative` across the 4 onsets, and (b) the
mean within-onset actuator-mean spread (max−min actuator mean at a fixed
onset, averaged over onsets that have ≥2 actuators). Whether (a) > (b) is
reported per state and pooled as a simple count — deliberately NOT dressed
up as a formal variance-components model (the task spec explicitly asks
for "simple descriptive/mixed-effects summaries," not "a full
high-powered variance decomposition").

## What is explicitly NOT done anywhere in this analysis

- No after-the-fact per-stream or per-actuator maximum is reported as an
  effect estimate (the `ORACLE_WINNERS_CURSE.md` lesson).
- No new actuator-level feature search or ranking beyond the four
  predeclared organizational classes.
- No pooling of rollouts across states into a single N for a t-test/CI (a
  state-clustering violation the Stage 6.12 correction memo already
  flagged once).
