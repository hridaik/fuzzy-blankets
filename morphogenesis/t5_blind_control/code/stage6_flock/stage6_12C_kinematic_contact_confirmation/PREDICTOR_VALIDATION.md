# Stage 6.12C — Predictor-Ranking Validation

Analysis code: `code/analysis_612c.py` (`predictor_ranking_analysis`). All
20 candidates per state are ranked by the frozen `C_hat_kin` (never by
outcome); the realized outcome used for validation is `mean_confirm
ΔJ_conservative`, held out from the predictor.

## Per-state Spearman ρ (C_hat_kin vs. held-out mean confirmatory ΔJ_conservative)

| state | ρ | rank of TRUE best-effect candidate (0=best) | recall true-top3 in predictor-top3 | recall true-top3 in predictor-top5 |
|---|---|---|---|---|
| s612c_00 | +0.183 | 7 | 0.00 | 0.00 |
| s612c_01 | -0.325 | 2 | 0.33 | 0.33 |
| s612c_02 | +0.148 | 18 | 0.33 | 0.33 |
| s612c_03 | +0.146 | 0 | 0.33 | 0.33 |
| s612c_04 | +0.240 | 16 | 0.33 | 0.67 |
| s612c_05 | -0.105 | 11 | 0.00 | 0.00 |
| s612c_06 | +0.144 | 1 | 0.33 | 0.33 |
| s612c_07 | +0.129 | 17 | 0.00 | 0.33 |
| s612c_08 | -0.204 | 1 | 0.33 | 0.33 |
| s612c_09 | +0.392 | 2 | 0.33 | 0.67 |

## Summary (n=10 states, state-clustered)

| quantity | value |
|---|---|
| median state-level ρ | **+0.145** |
| mean state-level ρ | +0.075 |
| 90% CI (state-clustered bootstrap) | **[-0.035, +0.180]** — spans zero |
| fraction of states with ρ > 0 | 7/10 = 70% |
| mean rank of the true best-effect candidate under C_hat_kin (0=best, 19=worst) | 7.5 (chance expectation under a uninformative ranking ≈ 9.5) |
| mean recall of true top-3 effect candidates within predictor's top-3 | 0.233 (chance ≈ 3/20 = 0.15) |
| mean recall of true top-3 effect candidates within predictor's top-5 | 0.333 (chance ≈ 5/20 = 0.25) |
| top-quartile (by C_hat_kin) mean ΔJ_conservative | 0.00620 |
| bottom-quartile (by C_hat_kin) mean ΔJ_conservative | 0.00685 — **higher than the top quartile** |
| pooled ρ across all 200 candidate-rows (CONTEXT ONLY, not the primary claim) | +0.074 |

## Interpretation

**Weak, sign-inconsistent, state-clustered-null.** The median state-level
ρ (+0.145) is modestly positive and 7/10 states individually show a
positive sign, but the state-clustered 90% CI **spans zero**
([-0.035, +0.180]) — this is the primary, properly-uncertainty-accounted
reading, and it does not support a reliably positive predictor-outcome
relationship at this state count. The rank/recall diagnostics tell a
consistent story: the predictor does modestly better than chance on
average (mean rank of the true best is 7.5 vs. chance ≈9.5; recall in
top-5 is 0.33 vs. chance ≈0.25) but with enormous per-state variance —
the true best-effect candidate landed at predictor-rank 0 in one state
(`s612c_03`) and at rank 18 (second-WORST predicted) in another
(`s612c_02`). **The top-vs-bottom-quartile comparison is a genuine null
or even a mild reversal**: bottom-quartile candidates had a slightly
HIGHER mean realized effect than top-quartile candidates (0.00685 vs.
0.00620) — the opposite of what the predictor claims to do.

## Comparison against the prior-data caveat (disclosed in README.md)

The existing Stage 6.12B 3-state exhaustive data showed ρ≈-0.06 for the
K1,d8 cell specifically (vs. +0.78 for K1,d4 and +0.43 for K2,d8). This
stage's confirmatory K1,d8 result — median state-level ρ=+0.145, CI
spanning zero — is directionally MORE positive than that single prior
K1,d8 cell's pooled reading, but still does not clear a state-clustered
significance bar, and is much weaker than the K1,d4/K2,d8 cells that drove
Stage 6.12B's headline pooled ρ≈0.23-0.29 figure. **This confirmatory run
neither cleanly replicates nor cleanly contradicts the prior K1,d8 lead —
it sharpens it into "weakly positive on average, but not
state-clustered-reliable, and with large per-state sign variance,"** which
is a materially more cautious statement than either prior number in
isolation would suggest.
