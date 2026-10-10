# Stage 6.12B — Final Findings

**Scope reminder**: Part I used only existing Stage 6.12 data (no new
simulation). Part II sampled 5 fresh states (3 dev, 2 holdout, seeds
62200-62204); 6.12B-A (exhaustive K=1/K=2, d∈{4,8}) ran on 3 of those
states; 6.12B-B (refresh cadence × strategy) ran on all 5. All numbers
below carry small-sample caveats spelled out in `STATISTICAL_ANALYSIS.md`.

## Part I — Correction

### 1. Did Stage 6.12's identity semantics overstate valid continuation?

**Yes.** `confirmed_split`/`confirmed_merge` were `ForwardMaterialTrace611`
advisory flags, never an independently validated physical criterion.
Identity-valid fraction drops from ~97% (original) to 64.0% (conservative)
once split/merge-flagged and unresolved rollouts are excluded.

### 2. Does the near-zero random fixed-set effect survive corrected analysis?

**Mostly, at the pooled/state-clustered level — but with real state
heterogeneity underneath.** Both `J_assoc` and `J_conservative` pooled
means remain within a state-clustered 90% CI that spans zero. Two states
(of 9) individually showed large, opposite-signed effects
(`STATE_LEVEL_REANALYSIS.md`).

## Part II — Prospective test

### 3. Do truly superior fixed singleton/pair actuator sets exist?

**Weak evidence they do, but they are hard to identify.** Exhaustive
search found a small, mostly-positive held-out advantage for the
development-selected best set over random comparators (G_sel positive in
10/12 state-cell combinations, magnitude +0.002 to +0.018) — but
dev-to-holdout RANK stability among finalists was poor (-0.55 to +0.86,
often near zero), consistent with the task brief's "highly stochastic"
interpretation: real between-set structure may exist, but is not reliably
identifiable from the single development stream used here.

### 4. Can they be identified by predicted future contact rather than current distance?

**Partially, and better than by distance.** The physics-assisted kinematic
predictor (current position/heading + known speed + true R, no future
truth) correlates positively with realized paired effect overall
(ρ≈0.23-0.29) and in EVERY one of the 3 searched states individually
(+0.14 to +0.30) — the most consistent signal in this whole analysis.
Static t0 distance, by contrast, is NEGATIVELY correlated overall (ρ≈-0.30),
reversing the (already weak) Stage 6.12 finding.

### 5. Does refreshing actuator identity improve control at matched total effort?

**Not demonstrably.** K=2 shows refreshed-random > fixed-random
(+0.042 vs +0.012); K=4 shows the OPPOSITE (fixed +0.080 vs refreshed
+0.023). Both state-clustered CIs are wide and overlapping.

### 6. Is random refreshing sufficient?

**No clear evidence either way** — see Q5; the K=4 result argues against a
simple "refreshing helps" story on its own.

### 7. Does contact-aware refreshing outperform random refreshing?

**No consistent advantage found.** Kinematic-predicted-contact selection
beat random refreshing in some (K,q) cells and lost in others, with no
cadence showing a reliable win.

### 8. How much better is an oracle future-contact schedule?

**Not clearly better than the deployable strategies** — oracle was the top
strategy in only 2/10 (K,q) cells, often BELOW plain random refreshing.
This stage's oracle uses the paired NO-CONTROL future trajectory as its
information source, which is a weaker guide once forcing itself perturbs
the flock — a disclosed limitation of this specific construction, not
proof that no better upper bound exists (`CONTACT_PREDICTOR_ANALYSIS.md`).

### 9. Is sustained access actually the missing ingredient?

**Not established by this data.** Neither the refreshing comparison (Q5-7)
nor the oracle comparison (Q8) supports "maintaining access over time" as
a clean, reproducible fix at the tested sample size. Additionally, 6.12B-B's
longer, matched-effort (24-step) interventions showed a MUCH higher target
-loss rate (15.5% `lost_dead`, vs. 0.8% in Stage 6.12's shorter
interventions) — longer sustained forcing carries materially higher
disruption risk in this system, a genuine complication for any
"just maintain access longer" strategy.

### 10. Is there now a sufficiently real selective-control problem to justify building a learned authority model?

**Not yet, but there is one specific, reproducible lead worth confirming
at scale**: the physics-assisted kinematic predicted-contact score. It is
the only quantity in either Stage 6.12 or Stage 6.12B that shows a
positive, same-signed correlation with paired intervention effect across
EVERY state it was tested on. Everything else tested (static distance,
cumulative realized contact, refresh cadence, contact-aware refreshing,
oracle access) was either near-zero, sign-inconsistent, or both. See
`NEXT_STAGE_DECISION.md`.
