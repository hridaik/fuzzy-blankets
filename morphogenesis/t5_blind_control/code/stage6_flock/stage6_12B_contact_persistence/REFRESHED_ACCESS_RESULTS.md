# Stage 6.12B-B — Refreshed Access Results

All 5 states, K∈{2,4}, q∈{24,8,4,2,1}, strategies {random, nearest,
kinematic, kinematic_radius_free, oracle} (+ `fixed_reference` for K=2 on
the 3 states with 6.12B-A data), `N_STREAMS=3`. Total effort matched
across q (K birds forced every one of 24 control steps, regardless of
cadence). Full data: `data/refreshed_access_612b.json`; aggregates:
`data/analysis_summary_612b.json["refreshed_access"]`.

## Central comparison 1 — does refreshing itself matter? (random q=24 vs. mean of random q∈{8,4,2,1})

| K | fixed (q=24) mean Δ | fixed 90% CI (state-clustered) | refreshed mean Δ | refreshed 90% CI |
|---|---|---|---|---|
| 2 | +0.0119 | [+0.0023, +0.0271] | +0.0419 | [+0.0036, +0.0818] |
| 4 | +0.0798 | [+0.0112, +0.1512] | +0.0231 | [+0.0060, +0.0448] |

**No consistent direction.** At K=2, refreshed random has a higher mean
than fixed random (+0.042 vs +0.012), consistent with "temporal access
maintenance helps." At K=4, the OPPOSITE holds (fixed +0.080 vs refreshed
+0.023). Both K's confidence intervals are wide (state-clustered over only
5 states) and OVERLAP substantially with each other and with the other K's
value. **This does not support a clean "refreshing itself matters"
conclusion at either K** — the K=4 fixed-q24 mean is dominated by one
state (`s612b_02`: 0.244, an outlier — see `STATISTICAL_ANALYSIS.md`).

## Central comparison 2 — contact-aware selection vs. plain refreshing

Comparing `kinematic` (physics-assisted predicted-contact) to `random`
refreshing at each q (full table in `data/analysis_summary_612b.json`):
results are MIXED and mostly within each other's confidence intervals —
`kinematic` beats `random` at K4_q8 (+0.074 vs +0.014) and K2_q8 (+0.059
vs +0.058, essentially tied), but LOSES to `random` at K2_q2 (+0.0002 vs
+0.099), K4_q4 (+0.002 vs +0.021), and K4_q2 (+0.001 vs +0.051). **No
cadence shows contact-aware selection reliably beating plain refreshed
access** at this sample size.

## Central comparison 3 — room above deployable methods (oracle vs. predicted vs. random)

Across all 10 (K,q) cells, **oracle does NOT consistently exceed the
deployable strategies** — it is the largest of the five strategies in only
2/10 cells (K4_q8, K2_q2-ish territory is close) and is smaller than
`random` alone in most cells (e.g. K2_q8: oracle +0.007 vs random +0.058;
K2_q4: oracle +0.009 vs kinematic_radius_free +0.060). See
`CONTACT_PREDICTOR_ANALYSIS.md`'s caveat: this stage's oracle construction
predicts from the PAIRED NO-CONTROL future, which is a weaker guide once
forcing itself has perturbed the flock's trajectory — this is a genuine
limitation of the specific oracle used, not necessarily evidence that no
better upper-bound strategy exists.

## Fixed-reference comparison (K=2 only, 3 states with 6.12B-A coverage)

The static best-fixed-set reference (held for the WHOLE 24-step control
period, no refreshing) is included in `data/refreshed_access_612b.json`'s
`K2_q*_fixed_reference` cells for `s612b_00`, `s612b_01`, `s612b_03`. Its
performance is within the same noisy range as the other strategies at
every q — it does not stand out as either clearly superior or clearly
inferior. (Duration-semantics caveat: this reference set was chosen and
confirmed at `d=8` in 6.12B-A, then held for a full 24-step window here —
an intentional, disclosed adaptation, not a like-for-like replication.)

## Development vs. holdout role

`data/analysis_summary_612b.json["refreshed_access"]["by_role"]` splits
every cell's per-state values by development/holdout role. Given only 3
development and 2 holdout states, this split is too small to support a
separate "confirmed on holdout" claim for any specific (K,q,strategy)
comparison — reported for completeness and for `STATISTICAL_ANALYSIS.md`'s
uncertainty accounting, not as a confirmatory holdout test in the sense
Stage 6.12B-A's S_star/holdout-stream design achieves.

## Interpretation

**None of the three central comparisons shows a clean, consistent
directional finding at this sample size (5 states, 3 streams/cell).**
Every comparison has state-clustered confidence intervals wide enough to
be consistent with "no real difference" for most cell/strategy pairs. This
is itself informative: it does NOT support Case 1 or Case 2's clean
stories (temporal access maintenance mattering, with or without
sophisticated selection) at the tested precision — see
`FINAL_STAGE612B_FINDINGS.md` and `NEXT_STAGE_DECISION.md` for how this
factors into the overall endpoint call.
