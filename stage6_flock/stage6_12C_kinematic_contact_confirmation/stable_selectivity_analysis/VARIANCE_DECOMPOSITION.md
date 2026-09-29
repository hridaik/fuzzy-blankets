# Variance Decomposition

Computed by `code/analysis.py:variance_decomposition()`. Per state, a
two-way random-effects, method-of-moments ANOVA on the 20 (candidate) x 12
(stream) `ΔJ_conservative` matrix (search+confirm pooled; confirm-only
repeated as the primary-precision check; `ΔJ_assoc` as a sensitivity check).

## Method (stated explicitly, per the task brief's own caution)

For state matrix `X[j,r]`, grand mean `mu`, row (actuator) means, column
(stream) means:

```
SS_actuator = R * sum_j (row_mean_j - mu)^2         df = J-1
SS_stream   = J * sum_r (col_mean_r - mu)^2         df = R-1
SS_residual = SS_total - SS_actuator - SS_stream    df = (J-1)(R-1)
Var_actuator_hat = (MS_actuator - MS_residual) / R
Var_stream_hat   = (MS_stream   - MS_residual) / J
Var_residual_hat = MS_residual
```

**There is exactly one observation per (actuator, stream) cell.** This
design CANNOT separate a genuine actuator x stream interaction from plain
per-cell measurement/simulation noise -- both land in the single
`Var_residual_or_interaction` term. This report never claims to split them
further. Negative raw variance estimates (which occur when `MS_actuator <
MS_residual`, i.e. actuator identity explains no more variance than pure
noise would) are clipped to 0 for the reported fraction, but the RAW
(unclipped) estimate is also reported, since clipping alone can visually
overstate a near-zero-but-negative true effect as "exactly zero, no
information."

## Per-state results (12-stream: 4 search + 8 confirm pooled)

| state | Var_actuator (raw) | Var_actuator (clipped) | Var_stream | Var_residual/interaction | **Var_actuator / Var_total** |
|---|---|---|---|---|---|
| s612c_00 | -0.0000016 | 0.0 | 0.0000068 | 0.0000452 | 0.000 |
| s612c_01 | -0.0000031 | 0.0 | 0.0004429 | 0.0003742 | 0.000 |
| s612c_02 | -0.0000376 | 0.0 | 0.0004335 | 0.0107229 | 0.000 |
| s612c_03 | -0.0000031 | 0.0 | 0.0000682 | 0.0002262 | 0.000 |
| s612c_04 | -0.0000028 | 0.0 | 0.0000361 | 0.0000924 | 0.000 |
| s612c_05 | -0.0000009 | 0.0 | 0.0005638 | 0.0002676 | 0.000 |
| s612c_06 | +0.0000002 | 0.0000002 | 0.0000000 | 0.0000066 | 0.032 |
| s612c_07 | +0.0000093 | 0.0000093 | 0.0003491 | 0.0005407 | 0.010 |
| s612c_08 | +0.0000006 | 0.0000006 | 0.0000061 | 0.0000078 | 0.042 |
| s612c_09 | -0.0000014 | 0.0 | 0.0000052 | 0.0000458 | 0.000 |

(full per-state MS/variance breakdown, all significant digits, in
`data/stable_selectivity_results.json["variance_decomposition"]`)

## Aggregate

| quantity | 12-stream (search+confirm) | confirm-only (8-stream) | ΔJ_assoc, 12-stream (sensitivity) |
|---|---|---|---|
| mean Var_actuator / Var_total across states | **0.0084** | 0.0062 | 0.0096 |
| median Var_actuator / Var_total | **0.0** | 0.0 | 0.0 |
| mean Var_stream / Var_total | 0.281 | 0.248 | 0.195 |
| mean Var_residual(or interaction) / Var_total | 0.710 | 0.746 | 0.795 |
| # states (of 10) with positive raw Var_actuator estimate | 3 | 3 | (see JSON) |

## Reading

**Stable actuator identity explains essentially none of the
candidate x stream variance in this data, under either outcome metric, at
either stream-count granularity.** In 7/10 states the raw (unclipped)
actuator-variance estimate is negative -- i.e., candidate identity explains
LESS cross-cell variance than the residual/noise term alone, which is the
signature of no stable actuator effect, not merely "hard to detect." In the
3/10 states with a positive raw estimate (`s612c_06`, `s612c_07`,
`s612c_08`), the fraction is still small (3-4%) and these are also the three
lowest-random-baseline, lowest-headroom states overall (see
`STATE_TAXONOMY.md`) -- there is no state in this sample where actuator
identity accounts for a large share of the total variance.

By contrast, `Var_stream` (some physics futures are globally easier/harder
for EVERY candidate, on average ~20-28% of total variance) is consistently
larger than `Var_actuator`, and the residual/interaction term dominates
everywhere (71-80% of total variance) -- consistent with realization-specific
actuator x stream opportunity (the `actuator_x_stream[s,j,r]` term in the
conceptual model) being the dominant source of the outcome-oracle's
apparent headroom, not a `actuator_effect[s,j]` main effect. This is
corroborated independently by `RANK_RELIABILITY.md` (near-zero train/test
correlation) and decisively by `ORACLE_WINNERS_CURSE.md` (permutation-null
excess near zero).
