# Winner's-Curse / Maximum-of-Noise Null Analysis

Computed by `code/analysis.py:permutation_null()`. No new simulation --
resamples existing `ΔJ_conservative` values only. 2,000 permutations per
state for the per-stream/state-stable oracles; 200 permutations per state
(each requiring its own 150-rep CV-oracle recomputation) for the
cross-validated-oracle null, since that one is nested and more expensive to
recompute per permutation.

## Null construction (exactly as specified)

Within each state, for each physics stream `r` independently, apply a
random permutation of the 20 candidate labels to that stream's column of
`ΔJ_conservative` values. This preserves, EXACTLY: each stream's own set of
20 outcome values (so each stream's difficulty/marginal distribution is
untouched), and the marginal distribution across all cells. It DESTROYS: any
correlation of a specific candidate index's value across different streams
-- i.e., it is the null hypothesis "candidate identity carries no stable
information; the appearance of a good/bad actuator in any one stream is
purely that stream's own realization."

## Result 1: the per-stream clairvoyant oracle (A) is a mathematical identity under this null, not just an approximate match

`A = mean_r max_j ΔJ(j,r)` is a function of each stream's COLUMN OF VALUES
ONLY, not of which candidate produced which value. Permuting labels within a
column cannot change that column's maximum. Confirmed numerically: observed
A and permutation-null-mean A are equal to numerical precision (excess ~1e-18)
in every one of the 10 states, both at 8-stream (confirm-only) and 12-stream
(pooled) granularity.

**This is the central, decisive fact of this document: the ENTIRE per-stream
clairvoyant-oracle advantage over random (16.8x at confirm-only precision,
`CROSS_VALIDATED_ORACLE.md`) is, by construction, exactly what "maximum of
20 noisy candidates, no stable identity" produces. A per-stream oracle
value can never be used as evidence of stable actuator selectivity -- it is
mathematically incapable of distinguishing the two hypotheses.** This is why
the task brief's Definition A must never be called "selective headroom" on
its own (`CROSS_VALIDATED_ORACLE.md`'s section 9 discipline).

## Result 2: the state-stable mean oracle (B) -- Stage 6.12C's actual reported "outcome oracle" -- shows ~zero, and on average slightly NEGATIVE, excess over the null

| granularity | observed B (mean across states) | null B mean | **excess (observed - null)** |
|---|---|---|---|
| confirm-only (8 streams; this is Stage 6.12C's own 0.0222 number) | 0.02224 | 0.02381 | **-0.00157** |
| 12-stream pooled | 0.01601 | 0.01670 | **-0.00070** |

Per-state excess (confirm-only): positive in only 3/10 states
(`s612c_00` +0.00084, `s612c_01` +0.00923, `s612c_07` +0.00171), negative or
~zero in the other 7 (largest negative: `s612c_02` -0.02, itself the state
with by far the largest raw B value -- exactly the pattern expected if `B`'s
apparent state-to-state variation is itself substantially winner's-curse
noise, since `B` is also a max, just of within-stream means rather than raw
values, so it inherits (a damped version of) the same order-statistic
inflation as `A`).

**Stage 6.12C's headline "outcome oracle ≈6.9x random" finding is, under
this null, NOT distinguishable from a system with zero stable actuator
identity.** The observed value is not merely "not clearly above the null" --
its state-clustered mean sits slightly BELOW the null mean.

## Result 3: the cross-validated stable oracle (C) shows a small, inconsistent, largely-null-consistent excess

| granularity | observed C (mean) | null C mean | excess |
|---|---|---|---|
| confirm-only | 0.00544 | 0.00503 | +0.00041 |
| 12-stream pooled | 0.00383 | 0.00358 | +0.00025 |

Per-state excess is positive in 5/10 states and negative in 5/10 (confirm-
only granularity), with the largest single positive excess
(`s612c_01`, +0.0194) roughly matched in magnitude by the largest single
negative excess (`s612c_02`, -0.0139) -- consistent with sampling noise
around a small or zero true excess rather than a systematic effect. The
aggregate excess (~7-8% of the observed C value) is the same order of
magnitude as `CROSS_VALIDATED_ORACLE.md`'s state-clustered CI width for
`C - random`, which spans zero.

## Conclusion

All three converging lines of evidence -- (1) `A`'s null-identical-by-
construction result, (2) `B`'s near-zero-to-negative excess, (3) `C`'s
small and sign-inconsistent excess -- say the same thing: **this 10-state,
K=1, d=8 sample does not contain evidence of stable actuator identity beyond
what a "no stable identity" null already produces.** The large numbers in
Stage 6.12C's oracle table are real properties of the DATA (the maximum
observed outcome really was that large in that stream), but they are not
evidence that CANDIDATE IDENTITY, as opposed to REALIZED PHYSICS STREAM, is
what produced them.
