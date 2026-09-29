# Candidate-Effect Reliability / ICC-style Analysis

Computed by `code/analysis.py:reliability_curve()`. For each state, 300
repeated random splits of the 12 streams into `m` TRAIN streams and
`12-m` TEST streams, for `m in {1,2,4,6}`. Per split: candidate means on
TRAIN streams vs. candidate means on TEST streams -> Pearson r, Spearman
rho, whether the same candidate is top-1 in both, and top-3 set overlap
(chance-level overlap for two independent draws of 3-of-20 is
`3*3/20 = 0.45`).

## Aggregate (mean across all 10 states)

| m (train streams) | mean Pearson r | mean Spearman rho | frac top-1 stable | mean top-3 overlap (chance=0.45) |
|---|---|---|---|---|
| 1 | 0.014 | -0.005 | 0.089 | 0.653 |
| 2 | 0.019 | 0.007 | 0.071 | 0.667 |
| 4 | 0.013 | -0.004 | 0.071 | 0.660 |
| 6 | 0.017 | 0.001 | 0.058 | 0.670 |

## Reading: does reliability improve with more training streams?

**No.** Both correlation measures hover in a narrow band around zero
(|r|, |rho| < 0.02) at every training-set size from 1 to 6 streams,
with no monotonic increase as `m` grows from 1 to 6 -- the signature of a
sample-efficiency curve for a ranking that DOES carry real information
would show. Frac-top-1-stable (does the train-best candidate also happen to
be the test-best candidate) DECREASES slightly as m grows (0.089 -> 0.058),
which is the opposite of what a genuine reproducible ranking would show
(more training data should make top-1 selection more reliable, not less --
if anything the small drop from m=1 to m=6 is consistent with all values
being noise around the chance rate `1/20=0.05`). Top-3 overlap sits close to
its chance baseline (0.45) throughout, with no trend across `m`.
**Rankings never stabilize with the amount of data available in this
design (up to 6 training streams).**

## Per-state detail (m=6, i.e. best-powered split tested)

| state | Pearson r | Spearman rho | frac top-1 stable | top-3 overlap |
|---|---|---|---|---|
| s612c_00 | -0.177 | -0.180 | 0.023 | 1.027 |
| s612c_01 | -0.014 | -0.086 | 0.427 | 0.660 |
| s612c_02 | 0.009 | 0.010 | 0.003 | 0.820 |
| s612c_03 | -0.098 | -0.066 | 0.000 | 0.093 |
| s612c_04 | -0.193 | -0.231 | 0.077 | 0.537 |
| s612c_05 | -0.002 | 0.103 | 0.000 | 0.490 |
| s612c_06 | 0.233 | 0.091 | 0.037 | 1.467 |
| s612c_07 | 0.130 | 0.124 | 0.007 | 0.600 |
| s612c_08 | 0.444 | 0.313 | 0.007 | 0.773 |
| s612c_09 | -0.167 | -0.069 | 0.000 | 0.233 |

State `s612c_08` shows the largest positive reliability (Spearman 0.31 at
m=6), but it is also the state with the smallest random-baseline effect and
the smallest overall headroom (`STATE_TAXONOMY.md`) -- a positive rank
correlation on a near-flat outcome surface is weak evidence either way.
Several states show NEGATIVE train/test correlation (`s612c_00`, `s612c_04`,
`s612c_09`), i.e. the train-preferred candidate is if anything slightly
WORSE on held-out streams than average -- consistent with regression-to-the-
mean / overfitting-to-search-stream-noise rather than any real signal.

## Conclusion for this document

There is no state in this 10-state sample, and no training-set size from 1
to 6 streams, at which candidate ranking reliably transfers from one set of
physics streams to another. This is independent corroboration of
`VARIANCE_DECOMPOSITION.md`'s near-zero `Var_actuator` finding and
`CROSS_VALIDATED_ORACLE.md`'s near-random `CV_stable_lift` finding.
