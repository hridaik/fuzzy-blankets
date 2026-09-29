# Stage 6.12C — K=1 Exhaustive Primary Results

Full data: `data/k1_candidates_612c.json` (200 rows = 10 states × 20
candidates), `data/k1_rollouts_612c.json` (2,400 rows = 200 candidates ×
12 physics streams). Analysis code: `code/analysis_612c.py`
(`l_pred_analysis`). All numbers below use ONLY the 8 CONFIRMATORY
streams per candidate; the 4 SEARCH streams are reserved for the
reproducibility oracle (`ORACLE_DECOMPOSITION.md`).

## Primary estimand: L_pred

```
L_pred(state) = mean_confirm(ΔJ_conservative of top-C_hat_kin candidate)
                / median_j [ mean_confirm(ΔJ_conservative(j)) ]
```

| state | top candidate | C_hat_kin | top ΔJ_cons | median ΔJ_cons | L_pred | top − median |
|---|---|---|---|---|---|---|
| s612c_00 | 35 | 11.0 | 0.00000 | 0.00000 | undefined (median=0) | 0.00000 |
| s612c_01 | 266 | 73.0 | -0.00918 | -0.00043 | 21.28 | -0.00875 |
| s612c_02 | 128 | 41.0 | 0.00071 | 0.00231 | 0.31 | -0.00160 |
| s612c_03 | 237 | 65.0 | 0.01472 | 0.00473 | 3.11 | +0.00999 |
| s612c_04 | 331 | 86.0 | 0.01090 | 0.00422 | 2.58 | +0.00668 |
| s612c_05 | 235 | 7.0 | 0.00826 | 0.01486 | 0.56 | -0.00659 |
| s612c_06 | 355 | 5.0 | 0.00012 | 0.00000 | undefined (median=0) | +0.00012 |
| s612c_07 | 326 | 160.0 | 0.00992 | 0.00522 | 1.90 | +0.00469 |
| s612c_08 | 354 | 129.0 | -0.00163 | 0.00070 | -2.33 | -0.00233 |
| s612c_09 | 185 | 212.0 | 0.00021 | 0.00069 | 0.30 | -0.00048 |

**L_pred is undefined for 2/10 states** (the median-candidate confirmatory
effect is exactly 0.0 — both `s612c_00` and `s612c_06` have a
no-forcing-quality median candidate at this small K=1, d=8 budget). The
ratio summary below uses only the 8 states where the denominator is
nonzero; this is disclosed, not hidden, because a ratio near a zero
denominator is numerically unstable and can produce a misleadingly large
summary statistic (see `s612c_01`'s L_pred=21.28, driven by a tiny
denominator of -0.00043, not a large numerator).

### Summary (state-clustered, n=10 states; ratio summary n=8 valid states)

| quantity | J_conservative (primary) | J_assoc (sensitivity) |
|---|---|---|
| L_pred median | **1.227** | 0.653 |
| L_pred mean | 3.465 (unstable, driven by near-zero denominators) | -1.420 (unstable) |
| L_pred 90% CI (state-clustered bootstrap) | [0.301, 8.327] | [-5.191, 1.101] |
| fraction of (valid) states with L_pred > 0 | 87.5% (7/8) | 75% (6/8) |
| **top − median (absolute, all 10 states, ratio-free)** | **mean +0.00017, 90% CI [-0.0026, +0.0030]** | mean -0.00137, 90% CI [-0.0035, +0.0005] |
| fraction of ALL 10 states with top > median | **40%** | — |

## Reading these two summaries together (do not report only the ratio)

The **ratio** (`L_pred`) summary looks favorable at first glance (median
1.23, 87.5% of valid states positive) — but this is substantially an
artifact of small, noisy denominators near zero, not a robust magnitude
claim. The **absolute difference** (top-predicted-candidate's mean
confirmatory ΔJ_conservative minus the median candidate's), which does
not have this instability and uses all 10 states, is essentially flat:
mean **+0.00017** (an effect roughly 20-30× smaller than the historical
Stage 6.11/6.12/6.12B alignment-utility effect sizes of order 0.01-0.1),
with a 90% state-clustered CI **[-0.0026, +0.0030] that spans zero**, and
only 4/10 states show the top-predicted candidate actually beating the
median candidate. **The honest primary reading is: on this confirmatory
sample, the top-kinematic-predicted candidate does not reliably or
substantially outperform a typical (median) candidate in absolute terms**,
even though the RATIO summary, taken alone and without the
zero-denominator caveat, would have suggested a more favorable picture.
This is exactly the kind of result the task brief's "contextualize any
lift against the full 0-1 utility scale" instruction is meant to catch.

Under `J_assoc` (sensitivity), the picture is, if anything, slightly
worse (fewer positive states, negative mean absolute difference) — the
primary conclusion is not an artifact of the conservative identity
convention specifically.
