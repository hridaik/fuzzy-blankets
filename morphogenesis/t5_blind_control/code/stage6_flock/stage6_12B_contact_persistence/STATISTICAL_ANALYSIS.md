# Stage 6.12B — Statistical Analysis

## Clustering discipline

Every Stage 6.12B-B comparison (`analysis_612b.py::cluster_ci`) resamples
STATE-LEVEL means (5 states, or the relevant dev/holdout subset), never
individual rollouts — matching Part I's correction of Stage 6.12's naive
unclustered CI. Physics-stream-level variation (`N_STREAMS=3`) and
within-state actuator/strategy variation are absorbed into each state's
own mean before the state-level bootstrap runs; they are not a source of
spurious extra "independent" observations.

## Reported uncertainty is wide, and that is the honest finding

Every 90% CI in `REFRESHED_ACCESS_RESULTS.md`'s central comparisons spans
at least an order of magnitude in width relative to its point estimate,
and most overlap heavily with zero and with each other's strategy/cadence
value. With only 5 states (3 development + 2 holdout), this is the
expected consequence of the disclosed compute reduction — not a sign of a
coding error (`rng_crn_diagnostic_612b.py` confirms the CRN machinery
itself is correct).

## Outlier state: `s612b_02`

`s612b_02_seed62202` (development, target size 46) has by far the largest
magnitude values in `data/analysis_summary_612b.json["refreshed_access"]`
— e.g. K2 refreshed-random mean Δ=0.136 vs. the other 4 states' 0.00005 to
0.064; K4 fixed-q24 mean Δ=0.244 vs. the other 4 states' 0.003 to 0.125.
**This single state accounts for a large share of the pooled means'
magnitude in several cells.** This was NOT excluded (task brief S23:
"do not exclude difficult states because they reduce performance" — the
symmetric principle applies to states that inflate an apparently positive
result too) — but it is disclosed explicitly here so a reader does not
mistake a state-clustered mean dominated by one state for a broadly
reproduced effect. `s612b_02` was not part of the 6.12B-A exhaustive
search subset, so its behavior there is unknown.

## Development vs. holdout

3 development / 2 holdout states is too small to treat as a genuine
confirmatory split for 6.12B-B's strategy/cadence comparisons (unlike
6.12B-A, which has a proper per-state development-STREAM vs. holdout-
STREAM design for the S_star confirmation itself). `by_role` breakdowns
are reported in `data/analysis_summary_612b.json` for transparency, not
presented as a validated holdout confirmation of any specific q/strategy
choice — consistent with `REFRESHED_ACCESS_RESULTS.md`'s framing.

## What would be needed to sharpen this

Given the effect sizes observed are frequently smaller than or comparable
to the state-clustered noise floor, the single highest-value next step
(if this line of inquiry continues) is more STATES, not more streams per
state — state-level heterogeneity, not within-state physics noise, is the
dominant source of uncertainty throughout both Stage 6.12 and Stage 6.12B.
