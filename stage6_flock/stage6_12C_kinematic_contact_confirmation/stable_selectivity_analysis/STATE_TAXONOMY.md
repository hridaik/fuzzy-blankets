# State Taxonomy

Computed by `code/analysis.py:state_taxonomy()`. Combines, per state:
random/median effect, per-stream clairvoyant oracle (A), state-stable mean
oracle (B), cross-validated stable oracle (C), stable-actuator variance
fraction, ranking reliability (Spearman rho at m=6 training streams),
winner-recurrence statistics, and identity-valid fraction (from Stage
6.12C's own `IDENTITY_AND_DISRUPTION.md`, not recomputed here).

## Master table (12-stream, search+confirm pooled unless noted)

| state | random | A (clairvoyant) | B (state-mean) | C (CV-stable) | Var_actuator frac | rank reliability (rho, m=6) | max win freq | winner entropy (norm) | frac pairs stable |
|---|---|---|---|---|---|---|---|---|---|
| s612c_00 | 0.00000 | 0.01332 | 0.00433 | 0.00059 | 0.000 | -0.180 | 0.42 | 0.88 | 0.542 |
| s612c_01 | 0.00549 | 0.03388 | 0.02183 | 0.01303 | 0.000 | -0.086 | 0.25 | 0.95 | 0.189 |
| s612c_02 | 0.00481 | 0.24220 | 0.08630 | 0.01843 | 0.000 | 0.010 | 0.25 | 0.95 | 0.084 |
| s612c_03 | 0.00227 | 0.02900 | 0.00911 | -0.00037 | 0.000 | -0.066 | 0.25 | 0.95 | 0.084 |
| s612c_04 | 0.00287 | 0.02227 | 0.00900 | 0.00374 | 0.000 | -0.231 | 0.25 | 0.95 | 0.032 |
| s612c_05 | 0.00679 | 0.01957 | 0.01157 | 0.00294 | 0.000 | 0.103 | 0.42 | 0.94 | 0.553 |
| s612c_06 | 0.00000 | 0.00788 | 0.00270 | 0.00123 | 0.032 | 0.091 | 0.42 | 0.88 | 0.379 |
| s612c_07 | -0.00260 | 0.04186 | 0.01151 | -0.00081 | 0.010 | 0.124 | 0.17 | 0.97 | 0.042 |
| s612c_08 | 0.00045 | 0.00383 | 0.00162 | 0.00053 | 0.042 | 0.313 | 0.25 | 0.95 | 0.189 |
| s612c_09 | 0.00043 | 0.01120 | 0.00209 | -0.00189 | 0.000 | -0.069 | 0.25 | 0.95 | 0.116 |

Identity-valid fraction per state (from Stage 6.12C's own
`IDENTITY_AND_DISRUPTION.md`, reused not recomputed): held at 91.1% pooled
across all 10 states, with `s612c_03` a clear disruption-prone outlier
(55.6% conservative-valid). Notably `s612c_03` also has the SMALLEST (most
negative) `C` value in this table (-0.00037) -- consistent with disruption
risk eating into whatever cross-validated advantage might otherwise appear,
though with n=10 states this is a single co-occurrence, not a tested
association.

## Task-brief candidate categories, applied with an explicit continuum caveat

The task brief warns against forcing discrete categories onto a continuous
quantity. Applying its three named categories as a coarse, threshold-based
label ONLY for readability (thresholds stated, not tuned):
`stable-selective` = `Var_actuator_frac > 0.3` AND `C` retains > 50% of the
`A-random` headroom; `low-headroom` = `A` within 30% of `random` (or
`random<=0`); `stochastic-opportunity` = everything else with `A > random`
but `Var_actuator_frac` small or `C` collapsing toward `random`.

**Result: all 10/10 states classify as `stochastic-opportunity` under this
rule.** No state in this sample reaches `Var_actuator_frac > 0.3` (max
observed: 0.042, `s612c_08`), and no state's `C` retains more than about a
third of its `A - random` gap (the largest retention, `s612c_01`:
`(C-random)/(A-random) = (0.01303-0.00549)/(0.03388-0.00549) = 0.266`).

**This uniform classification should be read with real caution** -- it is a
consequence of a fixed threshold applied to a small (n=10), noisy sample,
not proof that literally every possible flock configuration in this system
behaves this way. What CAN be said without the threshold: within THIS
sample, the states span a wide range of `A` (0.008-0.242) and `B`
(0.0016-0.086) magnitude, but none of that range translates into a
correspondingly wide range of stable, cross-validated selectivity --
`Var_actuator_frac` stays low (0.0-0.042) and `C` stays modest and
inconsistent in sign relative to random EVERYWHERE, regardless of how large
`A` or `B` happen to be in that state. The states differ enormously in HOW
MUCH per-stream opportunity exists, but not in whether that opportunity is
predictable in advance.

## Reading

There is no evidence in this sample of a distinct "stable-selective" state
type as the task brief's Case A/Decision-1 framing would require. Every
state's story is the same shape: real per-stream variability (state-stable
and clairvoyant oracles both well above random), essentially no actuator
main effect (variance decomposition), and no train/test rank transfer
(reliability). The states differ in scale (how large the stochastic
opportunity is), not in kind (whether it's exploitable in advance).
