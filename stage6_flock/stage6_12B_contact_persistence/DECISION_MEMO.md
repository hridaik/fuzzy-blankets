# Stage 6.12B — Decision Memo (top-level summary)

This is the one-page entry point. Full detail in `FINAL_STAGE612B_
FINDINGS.md` (10-question answer set) and `NEXT_STAGE_DECISION.md`
(endpoint decision + reasoning).

## Part I (correction, existing Stage 6.12 data)

`confirmed_split`/`confirmed_merge` were mislabelled tracker advisory
flags, corrected to `material_split_flag`/`material_merge_flag`
throughout (`IDENTITY_SEMANTICS_CORRECTION.md`). Identity-valid fraction
was optimistic (97%→64% conservative). The pooled near-zero
susceptibility/selectivity conclusion survives state-clustered
reanalysis, but hides substantial state-level heterogeneity, and the
original "sustained contact predicts success" mechanism finding does not
survive being recomputed as a paired causal effect (`STAGE612_CORRECTION.md`,
full memo in `stage6_12_control_readiness/STAGE612_CORRECTION_MEMO.md`).
No contradiction blocked proceeding to Part II.

## Part II (prospective test, 5 fresh states)

- **6.12B-A (exhaustive K=1/K=2)**: weak, mostly-positive held-out
  advantage for development-selected best sets exists, but which specific
  set is best is not reliably identifiable from limited development data
  (`FIXED_SET_EXHAUSTIVE_RESULTS.md`).
- **Contact predictor validation**: the physics-assisted kinematic
  predicted-contact score is the single most consistent, cross-state
  positive signal found across this whole research programme
  (`CONTACT_PREDICTOR_ANALYSIS.md`).
- **6.12B-B (refreshed access)**: no consistent evidence that refreshing
  actuator identity, contact-aware refreshing, or even an (imperfect)
  oracle-access strategy reliably beats fixed random forcing at matched
  effort — but every comparison has wide, small-sample confidence
  intervals (`REFRESHED_ACCESS_RESULTS.md`). Longer, matched-effort
  interventions carry a much higher target-loss rate (15.5% vs 0.8%
  previously) — a genuine complication (`IDENTITY_AND_DISRUPTION.md`).

## Decision

**Conditional Decision A** (`NEXT_STAGE_DECISION.md`): do not yet build
the learned authority estimator; run one focused confirmatory experiment
on the kinematic-contact-predictor lead at a properly powered state count,
and settle the oracle-construction question, before committing to
controller architecture.
