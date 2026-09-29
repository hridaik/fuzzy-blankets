# Cross-Validated Stable-Outcome Oracle (PRIMARY decision analysis)

Computed by `code/analysis.py:cv_stable_oracle()` / `three_oracles()`. Per
state, repeated (500 reps) random splits of the 12 available streams into
`m_train=6` and `m_test=6`. Per split: `j_star_train = argmax_j
mean_train ΔJ_conservative(j)`; evaluate that SAME candidate's mean on the
TEST streams; compare to the TEST median candidate. `CV_stable_lift =
mean_test ΔJ(j_star_train) / median_j mean_test ΔJ(j)`.

## Ratio form is unstable near zero -- exactly the L_pred problem again

Just as Stage 6.12C's `K1_EXHAUSTIVE_RESULTS.md` found for `L_pred`, the
ratio form of `CV_stable_lift` is dominated by states/splits where the test
median is near zero. State `s612c_06` (random-median = 0.0 in the original
Stage 6.12C table) has only **7.8% of its 500 splits produce a well-defined
ratio** (`frac_valid_reps=0.078`), and its mean ratio over those few valid
splits is 262 -- a single near-zero-denominator artifact, not a real
262x lift. The aggregate mean ratio across states (32.6) is dominated by
this instability and is **not reported as the headline number** for exactly
this reason; the median ratio (1.25) and, primarily, the **ratio-free
absolute difference** below are used instead.

## Primary (ratio-free) result

`j_star_test_minus_median = mean_test ΔJ(j_star_train) - median_j
mean_test ΔJ(j)`, averaged over the 500 splits, per state:

| state | mean(j*_test - median_test) | CV_stable_lift (median ratio) |
|---|---|---|
| s612c_00 | +0.00039 | undefined (median_test = 0 in essentially every split) |
| s612c_01 | +0.00653 | 1.09 |
| s612c_02 | +0.01340 | 3.12 |
| s612c_03 | -0.00268 | 0.51 |
| s612c_04 | +0.00014 | 1.13 |
| s612c_05 | -0.00612 | 0.53 |
| s612c_06 | +0.00129 | 29.04 (unreliable, see above) |
| s612c_07 | +0.00258 | 0.73 |
| s612c_08 | +0.00027 | 1.79 |
| s612c_09 | -0.00236 | 0.17 |

**Aggregate (state-clustered, n=10 states, 20,000-resample bootstrap, matching
Stage 6.12C's own discipline):** mean `j*_test - median_test` = **+0.00134**,
90% CI **[-0.00116, +0.00419]** -- spans zero. **7/10 states show a positive
sign, but the magnitude is tiny** (roughly half the size of the ALREADY-tiny
random/median baseline effect of ~0.002-0.003) and the CI does not exclude
zero.

## Three-oracle magnitude comparison (see `ORACLE_WINNERS_CURSE.md` for the null test)

Using confirmatory streams only (matching Stage 6.12C's own primary
precision), state-clustered means across the 10 states:

| quantity | mean ΔJ_conservative | ratio vs. random |
|---|---|---|
| random/median | 0.00323 | 1.0x |
| **A: per-stream clairvoyant oracle** (`argmax_j ΔJ(j,r)`, averaged over streams -- true Def. A, computed here for the first time; Stage 6.12C never reported this number, see `DATA_DESIGN_AUDIT.md`) | 0.05436 | 16.8x |
| **B: state-stable mean oracle** (`argmax_j mean_r ΔJ(j,r)` -- this IS Stage 6.12C's reported "outcome oracle," 0.0222) | 0.02224 | 6.9x |
| **C: cross-validated stable oracle** (select on train streams, evaluate on held-out test streams -- the reproducibility-relevant quantity) | **0.00528** | **1.63x** |

(12-stream/search+confirm-pooled version gives the same qualitative pattern:
A=0.0425 (20.7x), B=0.0160 (7.8x), C=0.0037 (1.8x) -- see
`data/stable_selectivity_results.json["three_oracles"]["full_12stream"]`.)

State-clustered 90% CI for C (12-stream): **[0.00069, 0.00725]**; for
`C - random`: **[-0.00067, +0.00442]**, spanning zero.

## Reading

**Each step from clairvoyant (A) to state-stable-in-sample (B) to
cross-validated-out-of-sample (C) collapses the apparent advantage by
roughly an order of magnitude** (16.8x -> 6.9x -> 1.6x of random). The
cross-validated stable oracle -- the ONLY one of the three that answers "can
I identify the best actuator BEFORE seeing the evaluation physics
stream," which is the operationally relevant question for any future
controller -- shows an advantage over random/median that is small in
absolute terms, inconsistent in sign across states, and not
state-clustered-reliable (CI spans zero). This is the primary evidence, from
this bounded follow-up, that **Stage 6.12C's large outcome-oracle number
does not reflect actionable, reproducible actuator selectivity.** See
`ORACLE_WINNERS_CURSE.md` for the complementary permutation-null evidence
that reaches the same conclusion by a different route.

## Historical search(4)->confirm(8) split, for reference

Stage 6.12C's own protocol-frozen split (`ORACLE_DECOMPOSITION.md`'s
"search-selected best" row) is a cruder, single-split version of this same
cross-validation idea (4 train streams, 8 test streams, one split, not
resampled). Reproduced here directly from the candidate JSON (not
recomputed with new logic) for cross-reference:
`data/stable_selectivity_results.json["cv_stable_oracle"]["historical_search_train_confirm_test"]`.
Its aggregate (mean ΔJ_conservative = 0.0025, essentially AT or slightly
BELOW random) is consistent with the repeated-CV numbers above -- both
analyses, using different resampling strategies, agree that a
train-selected best candidate does not reliably outperform the median
candidate on unseen streams.
