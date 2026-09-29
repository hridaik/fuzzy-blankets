# Translating-Flock Programme — Final Synthesis

This document closes the translating-flock research programme (Stage
6.5–6.12C plus the `final_translating_flock_closure/` pass). It does not
collapse the programme into one success percentage: identity, intervention
efficacy, selectivity, organizational role, causal topology, and timing are
each separate axes with their own established/provisional/negative status.

## 1. Identity — can the same flock be followed reliably enough?

- **Established (positive, with correction).** A frozen material-association
  identity tracker, `ForwardMaterialTrace611` (Jaccard≥0.30, calibrated
  independently of any control outcome), achieves zero erroneous
  cross-population transfers across 72 full-episode traces
  (`material_identity_step2_20260921/`). This superseded the original
  Stage 6.11 `LineageTracker611`, whose "3/5 successful blind adaptive
  control" claim was WITHDRAWN after a forensic audit found it could jump
  to zero-material-overlap populations with no confidence gate
  (`evidence_recovery_20260921/`).
- **Established (disclosed limitation).** `split_flag`/`merge_flag` are
  Jaccard-overlap heuristics, never validated against an independently
  confirmed PHYSICAL split/merge ground truth. The Stage 6.12 correction
  pass renamed the original `confirmed_split`/`confirmed_merge` labels to
  `material_split_flag`/`material_merge_flag` specifically to stop
  overclaiming physical confirmation from an advisory flag. This
  discipline is preserved throughout Closure A/B/C
  (`IDENTITY_AND_DISRUPTION.md`).
- **Established (worked examples).** Seed 501: a temporary tracker
  detour with underlying material continuity preserved. Seed 502: a
  wrong-population transfer under the ORIGINAL (withdrawn) tracker,
  corrected by the material-association tracker. Seed 503: a genuine
  tracker substitution / material fragmentation event, i.e. the historic
  large "turn" attributed to seed 503 belongs to an unrelated population
  (`causal_reconciliation_step3_20260922/FINAL_STAGE611_ADJUDICATION.md`).

## 2. Intervention efficacy — can forcing sometimes alter the material target?

- **Established (weak positive, heterogeneous).** Pooled across states,
  sustained fixed-schedule forcing does not generically move the flock
  (Stage 6.12: pooled `G_sus` mean ≈0, 90% CI spans 0). But this pooled
  null hides real state-to-state heterogeneity: individual seeds (e.g.
  501, 504) show demonstrable forcing effects while others (500) are
  clean negative controls. Identity validity (94-100%) does not explain
  the weak pooled effect — it is a genuine dynamical finding, not an
  identity-tracking artifact.
- **Established (duration-dependent risk).** Longer forcing durations
  (d=24 at K∈{2,4}) elevate target-loss rate to 15.5% (Stage 6.12B) vs
  0.8% for short schedules; at K=1 this elevated risk was NOT observed
  (Stage 6.12C: 0% target-loss at both d=8 and d=24) — a
  cardinality-specific effect, not a universal duration effect.

## 3. Stable exterior selectivity — does a particular exterior actuator have reproducible leverage?

- **Established (negative).** Across Stage 6.9 through 6.12C, choosing a
  specific exterior actuator by any tested static feature (kinematic
  predicted-contact score, historical authority ranking, dev-set-selected
  best actuator) never reliably outperforms random selection on genuinely
  held-out evaluation. Stage 6.12C's exhaustive K=1 confirmatory pass (10
  states, 12 physics streams/candidate) found the deployable kinematic
  predictor's ranking correlation with outcome consistent with zero (CI
  spans 0).
- **Established (winner's-curse diagnosis).** The large apparent
  per-stream-maximum "oracle" effect (≈6.9× random) is not evidence of
  actuator selectivity: `stable_selectivity_analysis/` found stable
  actuator identity explains 0-4.2% (mean 0.84%) of total outcome
  variance in every one of 10 states, cross-validated best-actuator lift
  has a 90% CI spanning zero, and the apparent oracle advantage is
  statistically indistinguishable from a permutation null that destroys
  actuator identity entirely (excess ≈ −0.0016, at/below the null).
- This conclusion was NOT reopened in the final closure pass, per the task
  spec — no further static actuator-feature search was performed.

## 4. Organizational-role privilege — do core/boundary/live-parent/non-parent classes differ?

**Established (negative).** Closure A (8 fresh states, 240 K=1/d=8
rollouts, `A_minus_j`-corrected interior scoring) found every class-level
90% CI spans zero (core −0.0038 [−0.0158,+0.0085]; boundary −0.0141
[−0.0371,+0.0089]; live parent −0.0075 [−0.0336,+0.0187]; non-parent
−0.0021 [−0.0148,+0.0100]), and the pooled interior-vs-exterior comparison
spans zero with inconsistent per-state sign (5/8 positive, 3/8 negative).
No stable organizational-role privilege was demonstrated — see
`final_translating_flock_closure/ORGANIZATIONAL_ROLE_RESULTS.md`.
**Disclosed structural finding, independent of the effect-size result**:
at the mean-field interaction density used throughout this programme
(`R_PRIMARY=0.9`, expected live degree ≈0.77), a materially-defined
target's boundary and live exterior causal parents are frequently EMPTY
at a single instant (5/8 fresh states had zero of each at t0) —
organizational-boundary and live-causal-parent status are themselves
comparatively rare/transient events in this regime, which limited the
boundary/live-parent comparisons to 3/8 states and bears on how strong a
"privileged interface" claim this system could ever support.

## 5. Directed causal topology — does actual FOV-gated influence explain more than geometric proximity?

**Established (negative).** Using the SAME Closure-A rollouts, Closure B
found the simulator's true directed `live_edges` relation and short
(≤3-hop) temporal reachability are statistically indistinguishable from
plain geometric contact in their association with intervention effect
(per-state Spearman ρ: geometric −0.107 [−0.302,+0.096], live directed
−0.118 [−0.270,+0.036], temporal reach −0.090 [−0.293,+0.115] — all CIs
span zero and overlap heavily). Live exterior causal parents did not
outperform near exterior non-parents (+0.0031 [−0.0097,+0.0160], n=3),
despite being ~9x closer to the target on average. Prior stages' "contact"
(`mech_cumulative_contact_edges`) was established by
`CONTACT_METRIC_AUDIT.md` to be undirected and FOV-free — materially
different from the simulator's actual directed, FOV-gated `live_edges`
relation, which this closure computed directly for the first time in the
programme and found carries no additional explanatory power over the
geometric proxy it was suspected of under-testing. See
`final_translating_flock_closure/LIVE_EDGE_CAUSAL_INTERFACE.md`.

## 6. Timing — how large is onset dependence relative to actuator dependence?

**Provisional (weak/inconclusive, disclosed small-sample limitation).**
It was already conceptually obvious that a moving flock needs
time-dependent control; Closure C asked only the quantitative comparison.
In a bounded, sparsity-limited sample (n=3 of the intended 4 states
contributed usable data), pooled within-onset actuator-identity spread
(0.0109, 90% CI [0.0011,0.0207]) was numerically LARGER than pooled
onset-time range (0.0040, 90% CI [0.0000,0.0080]); only 1/3 states showed
onset variation dominating. Timing variation is NOT shown to dominate
actuator-identity variation in this sample — not oversold into a positive
finding. See `final_translating_flock_closure/TIMING_SUSCEPTIBILITY.md`.

## 7. Persistence and disruption — what interventions preserve organizational identity?

Across Stage 6.12/6.12B/6.12C, short K=1 schedules (d≤8) preserve identity
validity at ≥94% (`V`) / substantially lower under the conservative
`V_conservative` definition (Stage 6.12 correction pass: 97%→64% once
split/merge-flagged continuations are excluded from "valid"). Longer/larger
schedules (K≥2, d=24) show materially elevated target-loss. See
`final_translating_flock_closure/IDENTITY_AND_DISRUPTION.md` for the
closure-specific persistence figures.

## 8. Final translating-flock conclusion

**Demonstrated:** a reliable material-identity tracking layer; occasional,
state-heterogeneous, non-generic intervention efficacy; the specific
falsification of static exterior-actuator selectivity as a control
strategy (both via direct search and via winner's-curse-corrected
reanalysis); a precise, code-level distinction between geometric contact
and the simulator's true directed causal-interaction relation.

**Contradicted:** the original Stage 6.11 "3/5 successful adaptive
control" claim; the informal assumption that a large per-actuator maximum
effect implies a controllable, selectable actuator advantage; the
assumption that geometric "contact" throughout Stage 6.12/6.12B/6.12C was
already testing the simulator's real causal-interaction channel.

**Unresolved / not further pursued by design:** whether a longer-horizon,
online/adaptive (probe-then-act) control policy could exploit the
stochastic-opportunity structure this programme repeatedly found — flagged
as a plausible future direction by `NEXT_EXPERIMENT_DECISION.md` but
explicitly NOT built here, per this closure's own scope discipline and the
task's hard stop on further flock work.

**Not worth pursuing further within this programme:** any additional
static single-actuator-feature discovery effort (three independent
falsification passes: raw contact, kinematic prediction, and the
winner's-curse-corrected oracle audit); any claim built on a per-stream or
per-actuator maximum without a held-out/cross-validated check.

## Decision

Per the task's decision-language rules, the applicable branch is **"none
of these are strong"**: no stable spatial/organizational actuator
interface was demonstrated in the translating flock (Closure A); true
directed causal-interface membership showed no discernible advantage over
geometric proximity, both weak (Closure B); timing variation was not
shown to dominate actuator-identity variation in this bounded sample
(Closure C). Control opportunity in this translating-flock system
continues to look predominantly stochastic/trajectory-conditioned under
every intervention class and timing variant tested across the whole
programme — not attributable to a stable spatial, organizational,
topological, or (within this closure's small sample) temporal
actuator-selection interface. Full detail in
`final_translating_flock_closure/FINAL_CLOSURE_FINDINGS.md`.

The translating-flock programme is CLOSED as of this document. The next
research programme is morphogenesis; see
`final_translating_flock_closure/MORPHOGENESIS_HANDOFF.md` for what
carries forward.
