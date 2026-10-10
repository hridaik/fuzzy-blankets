# Stage 6.11/6.12/6.12B Flock Control: Current Research Status

**Date**: 2026-09-22
**Git commit**: `940a5f672bc9b8302c0436e5a531cea6ae1f6ce1` (Stage 6.11 sections
below); Stage 6.12 section added at repository state
`9ba830d0f8410b5e4bf071472bbd6b290fa714f9`.

## Stage 6.12 addendum (control readiness / selective addressability)

See `stage6_flock/stage6_12_control_readiness/` for the full deliverable
set (`README.md`, `FINAL_STAGE612_FINDINGS.md`,
`NEXT_STAGE_RECOMMENDATIONS.md`, plus the supporting analysis docs). Summary:

- **Established (at this stage's reduced Monte Carlo precision — see
  below)**: on 9 freshly sampled states (6 development, 3 holdout;
  seeds 61200–61209, independent of seeds 500–504) and the full frozen
  `K∈{1,2,4,8} × d∈{1,2,4,8,16,24}` budget grid, sustained random exterior
  forcing does **not** generically move materially-tracked flocks in this
  sample: pooled `G_sus` = +0.0011 (90% CI [-0.0083, +0.0107]), and no
  budget shows a reliable positive effect across states. At the frozen
  primary search budget (K=4, d=8), a development-selected best-found
  actuator set (`S_star`) does **not** reproducibly beat random actuator
  sets on fresh held-out physics streams (`G_sel` small and
  sign-inconsistent across all 9 states; one development state's `S_star`
  reversed sharply on holdout, -0.106). This generalizes Stage 6.11's
  established finding (historical actuator choice never beat matched
  random forcing) to fresh, generic states and a full budget grid, rather
  than just the 5 historical seeds.
- **Established**: identity failure does NOT explain the weak behavioral
  effect — `ForwardMaterialTrace611` strict validity held in 94–100% of
  Phase-A rollouts per cell and 100% of Phase-C holdout evaluations; splits
  are common (34% of rollouts) but almost always remain advisory-flagged
  continuations, not validity failures.
- **Provisional/exploratory**: successful rollouts (rare, 2.6% of Phase A)
  show roughly 10× more sustained actuator-target contact than unsuccessful
  ones, while initial (`t0`) proximity barely discriminates — a lead for a
  future contact-persistence-aware authority estimator, never used to
  select this stage's own actuator sets. A small 3-state check found no
  large sensitivity to using the physics-assisted (true-R) pool instead of
  the primary position-only nearest-20 pool.
- **DISCLOSED, LOAD-BEARING LIMITATION**: this run used ~2–8% of the task
  brief's nominal Monte Carlo budget (3 random sets × 2 streams/cell in
  Phase A vs. a nominal 32×8; 6 dev + 3 holdout states vs. a nominal
  24+12; one frozen search budget rather than the full grid for Phase
  B/C) because per-step simulation+detection cost (~0.14s/step) made the
  full design infeasible in this session. The K×d grid itself and the
  state-sampling design were preserved in full. **The finding "no
  selective-addressability regime was demonstrated" is therefore
  provisional, not definitive** — see
  `stage6_12_control_readiness/NEXT_STAGE_RECOMMENDATIONS.md` for the
  recommended full-precision re-run before any control-architecture
  decision is made on this basis.
- **What the next task may NOT assume**: that a learned authority/actuator-
  selection estimator is validated or ready to build against this
  intervention class — Stage 6.12's own prerequisite question ("does a
  nontrivial actuator-selection problem exist?") did not receive a clear
  "yes" at the precision achieved. Do not skip straight to controller
  design citing Stage 6.12 as having established selectivity.

## Stage 6.12 correction + Stage 6.12B addendum (contact-persistence benchmark)

See `stage6_flock/stage6_12_control_readiness/STAGE612_CORRECTION_MEMO.md`
(Part I, existing-data reanalysis) and
`stage6_flock/stage6_12B_contact_persistence/` (Part II, prospective;
`DECISION_MEMO.md` is the entry point). Summary:

- **Correction, established**: Stage 6.12's `confirmed_split`/
  `confirmed_merge` event labels were `ForwardMaterialTrace611` advisory
  flags, never checked against an independently validated physical-split
  criterion — renamed `material_split_flag`/`material_merge_flag` in new
  outputs (originals untouched). Stage 6.12's identity-valid fraction was
  optimistic under this correction (97%→64% conservative). The pooled
  near-zero susceptibility/selectivity conclusion survives state-clustered
  reanalysis (both original Stage 6.12 CIs were computed by treating 1,296
  nested rollouts as independent — invalid, now superseded by a
  state-clustered bootstrap) but hides substantial state-level
  heterogeneity (two states showed large, opposite-signed effects). The
  original "sustained contact predicts success" mechanism finding does NOT
  survive being recomputed as a paired causal effect rather than an
  absolute-outcome comparison — most mechanism diagnostics show weak or
  sign-inconsistent correlation with paired ΔJ; only `direct_contacts_at_t0`
  and a NEW physics-assisted kinematic predicted-contact score (Stage
  6.12B) show a modest, consistent positive signal.
- **Stage 6.12B, established (fresh 5-state sample, seeds 62200-62204,
  independent of Stage 6.12's 61200-61399)**: exhaustive K=1/K=2 fixed-set
  search found a small, mostly-positive (10/12 cells) held-out advantage
  for development-selected best sets over random comparators, but
  dev→holdout RANK stability among finalists was poor — consistent with
  "real between-set structure may exist but is not reliably identifiable
  from limited development data" rather than either "no selectivity" or
  "selectivity is easy to find." A physics-assisted kinematic predicted-
  contact score (deployable: current position/heading/known speed/true R,
  no future truth) is the single most consistent positive signal found in
  either Stage 6.12 or 6.12B — positive in every state it was tested on.
  Refreshing actuator identity at matched total effort showed NO
  consistent advantage over a fixed set (opposite direction at K=2 vs
  K=4), contact-aware refreshing did not consistently beat plain
  refreshed-random access, and an oracle future-contact strategy did not
  clearly dominate either (a disclosed limitation of this stage's specific
  oracle construction, not a settled physical-impossibility finding).
  Longer, matched-effort (24-step) interventions showed a much higher
  target-loss rate (15.5%) than Stage 6.12's shorter fixed-schedule
  interventions (0.8%).
- **DISCLOSED, LOAD-BEARING LIMITATION**: Stage 6.12B used 5 states (3 dev
  + 2 holdout, exhaustive search run on only 3), far below the task
  brief's practical target of ≥12 dev + ≥6 holdout — state count, not
  physics-stream depth, is identified as the dominant source of
  uncertainty throughout (`stage6_12B_contact_persistence/
  STATISTICAL_ANALYSIS.md`).
- **What the next task may and may not assume**: do NOT build the learned
  contact-aware authority estimator yet. The recommended next step
  (`stage6_12B_contact_persistence/NEXT_STAGE_DECISION.md`) is a further
  focused confirmatory experiment — a larger-state-count validation of the
  kinematic predicted-contact signal, and a stronger oracle construction
  to settle whether deployable prediction or fundamental access is the
  bottleneck — before any controller-architecture commitment. Do not cite
  Stage 6.12B as having validated a contact-aware controller design; it
  identifies the most promising LEAD, not a validated mechanism.

## Stage 6.12C addendum (kinematic contact predictor confirmation)

See `stage6_flock/stage6_12C_kinematic_contact_confirmation/` for the full
deliverable set (`README.md` is the entry point; `FINAL_STAGE612C_
FINDINGS.md` and `NEXT_STAGE_DECISION.md` are the synthesis). This is the
focused confirmatory experiment Stage 6.12B's own `NEXT_STAGE_DECISION.md`
recommended: does the frozen, physics-assisted kinematic future-contact
predictor prospectively identify higher-effect exterior actuators on a
properly powered fresh state sample, and — separately — does future
physical contact itself carry the causal headroom, or is something else
going on. Summary:

- **Established (10 fresh confirmatory states, seeds 63200-63209, 10/10
  qualified on first attempt, disjoint from every prior seed range;
  4.85h total runtime)**: a real, state-clustering-robust selective
  causal headroom exists for singleton-actuator choice in this system —
  the non-deployable outcome oracle (best-found actuator per physics
  stream) achieves mean `ΔJ_conservative` ≈6.9× the random/median
  candidate, with a 90% state-clustered CI cleanly separated from every
  other strategy tested. But a genuine forced-future realized-contact
  oracle — using each candidate's OWN forced trajectory, not the weaker
  paired-no-control-future oracle Stage 6.12B used — does NOT capture this
  headroom (its mean sits at or slightly below the random baseline). This
  decisively selects **Case C** among the task brief's four named
  endpoints: real selective headroom exists, but it is not explained by
  physical contact between actuator and target
  (`stage6_12C_.../ORACLE_DECOMPOSITION.md`).
- **Established**: the deployable kinematic-predicted-contact score
  (Stage 6.12B's single most promising lead) does NOT reliably identify
  higher-effect candidates at this state count. Its ratio-based primary
  estimand (`L_pred`, median 1.23) looks favorable in isolation but is
  driven by near-zero denominators in 2/10 states; the ratio-free
  absolute comparison is flat (mean +0.00017, 90% CI
  [-0.0026, +0.0030], only 4/10 states positive). The state-level
  Spearman ρ between the predictor and held-out effect is weakly positive
  on average (median +0.145) but its state-clustered CI spans zero
  ([-0.035, +0.180]), and a top-vs-bottom-quartile comparison shows a mild
  REVERSAL. The K=2 pair-aggregation-rule secondary check shows the same
  pattern (`stage6_12C_.../K1_EXHAUSTIVE_RESULTS.md`,
  `PREDICTOR_VALIDATION.md`, `K2_SECONDARY.md`).
- **Established**: at K=1 (single-actuator forcing), extending duration
  from d=8 to d=24 shows NO elevated target-loss rate (0% lost/dead at
  both durations, 5-state paired sub-study) — genuinely different from
  Stage 6.12B's 15.5% loss rate at K∈{2,4}, d=24. This is a
  cardinality-specific finding, not a contradiction of Stage 6.12B
  (`stage6_12C_.../DURATION_SAFETY.md`).
- **DISCLOSED, LOAD-BEARING LIMITATION**: this run used N_STATES=10, half
  the task brief's nominal N_STATES=20, and reduced K=2/duration-sub-study
  stream depth, because per-step simulation cost made the full design
  infeasible in one session (see `stage6_12C_.../README.md`'s reduction
  table — the K=1 primary arm was NOT reduced, running the full
  20-candidate × 12-stream design at all 10 states). Every "not
  established" finding above is a CI-spans-zero finding, not a
  CI-excludes-a-meaningful-effect finding — a larger state count remains
  the single highest-value lever for sharpening these questions further.
- **What the next task may and may not assume**: do NOT build a
  contact-aware authority estimator based on physical proximity or
  predicted/realized future contact — this stage directly tested that
  mechanism with both a deployable proxy and a genuine non-deployable
  upper bound, and both failed to track the real effect headroom that
  clearly exists. The next task should investigate what DOES separate
  high- from low-effect actuators if not contact (candidate hypotheses —
  local density/social-field-mediated disruption, timing/phase effects,
  or irreducibly state-specific structure with no generalizable predictor
  at all — are listed, untested, in `stage6_12C_.../NEXT_STAGE_
  DECISION.md`). Do not cite Stage 6.12C as having validated the
  kinematic predictor or any contact-based mechanism as controller-ready.

## Stage 6.12C follow-up: stable-selectivity analysis (bounded, analysis-only)

See `stage6_flock/stage6_12C_kinematic_contact_confirmation/
stable_selectivity_analysis/` for the full deliverable set (`README.md` is
the entry point; `FINAL_STABLE_SELECTIVITY_FINDINGS.md` and
`NEXT_EXPERIMENT_DECISION.md` are the synthesis). This is a bounded,
analysis-only decomposition of Stage 6.12C's own already-frozen K=1, d=8
exhaustive candidate x stream data — no new simulation was run. It resolves
the question Stage 6.12C's Case-C finding left open: is the large per-
stream outcome-oracle advantage a reproducible property of particular
actuators, or mostly winner's-curse/maximum-of-noise inflation with no
stable identity that can be selected on before the physics realization is
known. Summary:

- **Established (same 10 states, 2,400-rollout dataset Stage 6.12C already
  produced, reanalyzed only)**: cross-validated actuator selection (train on
  a subset of the 12 available physics streams, test on the rest, repeated
  many times) collapses toward the random/median baseline — mean lift
  +0.0013 over median, 90% state-clustered CI [-0.0012, +0.0042], spans
  zero, sign-inconsistent across states (7/10 positive, 3/10 negative).
  Stable-actuator variance (`Var_actuator/Var_total`, two-way method-of-
  moments decomposition) is 0.0–4.2% in every one of the 10 states (mean
  0.84%, median 0.0%; 7/10 states show a NEGATIVE raw estimate). Train/test
  ranking reliability across repeated stream splits stays within noise of
  zero (mean Spearman ρ ≈0.001 at 6 training streams) with no trend toward
  stabilizing as training-stream count grows from 1 to 6
  (`VARIANCE_DECOMPOSITION.md`, `RANK_RELIABILITY.md`,
  `CROSS_VALIDATED_ORACLE.md`).
- **Established, decisive**: a permutation null that destroys stable
  candidate identity across streams while preserving every stream's own
  outcome distribution reproduces Stage 6.12C's headline "outcome oracle"
  number (0.0222, confirm-only precision) almost exactly (null mean 0.0238,
  observed EXCESS -0.0016 — i.e. slightly BELOW the no-stable-identity
  null). For the true per-stream clairvoyant oracle (`argmax_j ΔJ(j,r)`,
  averaged over streams — a DIFFERENT, larger quantity, 0.0544, that this
  follow-up establishes Stage 6.12C's own code never actually reported
  despite its prose describing it that way, see `DATA_DESIGN_AUDIT.md`'s
  provenance correction), the permutation-null excess is exactly zero by
  mathematical construction, not merely small (`ORACLE_WINNERS_CURSE.md`).
  **This means Stage 6.12C's ~6.9× headline number cannot be used as
  evidence of actuator selectivity: a system engineered to have NO stable
  actuator effect at all would produce approximately the same number.**
- **Established**: Stage 6.12C's contact metric
  (`mech_cumulative_contact_edges`) is audited from source
  (`intervention_612.py`) and found to be undirected, field-of-view-free
  geometric proximity (`distance<=R` only) — NOT the simulator's own
  directed, FOV-gated causal-influence relation (`live_edges` in
  `moving_flock.py`, which additionally requires the RECEIVER's forward
  half-plane and is asymmetric). Stage 6.12C's Case-C conclusion should be
  read as "not explained by GEOMETRIC proximity," not "not explained by any
  causal-interaction channel" — a directed FOV-aware contact oracle has
  never been computed by any stage to date (`CONTACT_METRIC_AUDIT.md`).
- **Provisional/disclosed gap**: the fields needed to test whether high-
  effect actuators later become organizationally embedded in the target
  (entry event, time-to-entry, post-entry membership duration) were never
  persisted by Stage 6.12C and are NOT reconstructed here (would require
  re-simulation, out of scope for a bounded analysis task). The two weak
  proxies that ARE available (contact-during-forcing, final target size)
  show no consistent, state-clustered association with effect
  (`MEMBERSHIP_EMBEDDING_CLUES.md`) — an absence of testable data, not
  evidence against the hypothesis.
- **DISCLOSED SCOPE**: this follow-up inherits Stage 6.12C's own n=10-state
  sample and adds no new states or physics streams — every "near-zero"
  finding above is a CI-spans-zero/small-magnitude finding, not a
  CI-excludes-any-possible-effect finding. A larger state and/or stream
  count remains the single highest-value lever for sharpening any of these
  conclusions further, exactly as every prior stage in this programme has
  already flagged for its own findings.
- **What the next task may and may not assume**: do NOT proceed to static
  actuator-feature discovery (density, phase-as-a-fixed-candidate-feature,
  or any refinement of the kinematic/contact family) — this follow-up shows
  raw candidate identity itself carries almost no reproducible cross-stream
  signal, so a smarter static feature built on top of it is unmotivated
  without first showing SOME static feature beats cross-validated random
  selection, which nothing tested to date has done
  (`NEXT_EXPERIMENT_DECISION.md`, Decision 2). Candidate next directions
  raised as hypotheses, not findings: phase/timing-conditioned control
  (this dataset used a single fixed onset uniformly); short probe-then-
  adapt/uncertainty-aware control; the directed FOV-gated contact oracle
  audited above but never computed; a larger state count. The interior-
  actuation experiment is NOT ruled out by this follow-up (a methodology-
  only note, `INTERIOR_ACTUATION_METHOD_NOTE.md`, establishes the
  forced-bird-exclusion scoring correction it will need) — Decision 2
  argues against static EXTERIOR-feature discovery specifically, and
  whether interior membership changes the variance/reliability structure
  remains untested.

## Final translating-flock closure (Closures A/B/C — organizational role, directed causal interface, timing)

See `stage6_flock/final_translating_flock_closure/` for the full
deliverable set (`README.md` is the entry point;
`FINAL_CLOSURE_FINDINGS.md` and `stage6_flock/
TRANSLATING_FLOCK_FINAL_SYNTHESIS.md` are the synthesis). This is the
FINAL bounded experimental pass on the translating-flock programme before
it moves to morphogenesis: 8 fresh states (seeds 64200-64207, disjoint
from every prior seed range), K=1/d=8/release=24, 240 Closure-A/B rollouts
+ 57 Closure-C timing rollouts (297 total, ≈27 minutes combined wall
time — within the "hundreds, not thousands" target with no scope
reduction needed). Summary:

- **Established (negative), Closure A**: organizational role (core
  member / boundary member / live exterior causal parent / near exterior
  non-parent, assigned from the simulator's own `live_edges` at
  intervention onset, with the `A_minus_j`/`J_minus_j` interior-actuation
  scoring correction applied per `INTERIOR_ACTUATION_METHOD_NOTE.md`) has
  NO reproducible class-level effect. Every class-level 90% CI spans zero;
  the pooled interior-vs-exterior comparison spans zero with inconsistent
  per-state sign (5/8 states positive, 3/8 negative, magnitudes spanning
  more than an order of magnitude). This EXTENDS the prior individual-
  actuator negative finding (`stable_selectivity_analysis/`): coarsening
  from individual identity to a 4-way structural-role classification does
  not recover a reproducible effect either
  (`ORGANIZATIONAL_ROLE_RESULTS.md`).
- **Established (negative), Closure B**: the simulator's true directed,
  FOV-gated `live_edges` relation (`recv,src,dvec = mf.live_edges(r,z)`,
  directed `src -> recv`, requires `D<=R` AND the RECEIVER's own forward
  half-plane) was computed directly for the first time in this programme
  and found NOT to explain intervention effect any better than the old
  geometric proximity metric — per-state Spearman ρ with
  ΔJ_conservative: geometric contact −0.107 [90% CI −0.302,+0.096], live
  directed access −0.118 [−0.270,+0.036], ≤3-hop temporal reachability
  −0.090 [−0.293,+0.115] — all three indistinguishable from each other
  and from zero. Live exterior causal parents did not outperform
  near-exterior non-parents (+0.0031 [−0.0097,+0.0160], n=3 co-occurring
  states) despite being ~9x closer to the target on average
  (`LIVE_EDGE_CAUSAL_INTERFACE.md`). This closes the question
  `stable_selectivity_analysis/CONTACT_METRIC_AUDIT.md` left open: the
  prior "not explained by geometric proximity" finding is now also "not
  explained by the true directed causal-interaction channel either."
- **Provisional (weak/inconclusive, disclosed sparsity), Closure C**: in
  a bounded sample (n=3 of the intended 4 states contributed usable
  rollouts — `sclosure_00` had zero available boundary/live-parent
  actuators at any tested onset), pooled within-onset actuator-identity
  spread (0.0109, 90% CI [0.0011,0.0207]) was numerically LARGER than
  pooled onset-time range (0.0040, 90% CI [0.0000,0.0080]); only 1/3
  states showed onset variation dominating actuator variation. Timing
  variation is NOT shown to dominate actuator-identity variation in this
  sample — reported as inconclusive, not oversold into a positive
  "timing matters" finding (`TIMING_SUSCEPTIBILITY.md`).
- **Established (disclosed regime property)**: at the interaction density
  used throughout this whole programme (`R_PRIMARY=0.9`, expected live
  degree ≈0.77), a materially-defined target's boundary and live exterior
  causal parents are frequently EMPTY at a single instant — 5/8 fresh
  states had zero of each at t0. This limited the boundary/live-parent
  comparisons above to 3/8 (Closure A/B) and 3/4 (Closure C) states; the
  core-vs-non-parent and pooled interior-vs-exterior comparisons (full
  8-state samples) independently support the same "no stable privilege"
  conclusion, so this sparsity is disclosed as a scope limitation on the
  boundary/live-parent-specific sub-comparisons, not as grounds to doubt
  the headline finding (`STATE_MANIFEST.md`).
- **Decision reached**: per the task's decision language, the "none of
  these are strong" branch applies — no stable spatial, organizational,
  topological, or (within this bounded sample) temporal actuator-selection
  interface was demonstrated. Control opportunity in the translating-flock
  system continues to look predominantly stochastic/trajectory-
  conditioned under every intervention class and timing variant tested
  across the entire programme. **The translating-flock research programme
  is now CLOSED.** No further flock experiments were initiated after
  these three closures, per the task's hard-stop discipline; see
  `stage6_flock/TRANSLATING_FLOCK_FINAL_SYNTHESIS.md` for the full
  programme-level synthesis and
  `final_translating_flock_closure/MORPHOGENESIS_HANDOFF.md` for what
  carries forward to the next (morphogenesis) programme.
- **Visualization**: `interactive_demo/v3/` extends `interactive_demo/v2/`
  (untouched) with 5 new tabs (7-11: readiness & winner's-curse, contact
  audit, Closure A organizational roles, Closure C timing, final
  synthesis), preserving v2's design language/conventions throughout;
  builds independently via `v3/src/build_v3.py`.

## Purpose of this file

No authoritative top-level "Research Programme Handoff" document exists
in this repository (checked by search; this is stated, not invented).
This file is a repository-level status summary so a fresh agent or
researcher does not need hidden prior-conversation context to know what
is established, what is provisional, what is withdrawn, and what the next
task may assume. It is **not** a historical rewrite — every claim below
cites the audit directory that established it, and none of those
directories were modified to produce this file.

## Supporting audit directories, in order

1. `stage6_flock/stage6_11_translating_torus/audit/evidence_recovery_20260921/`
   — forensic recovery of what the original Stage 6.11 implementation
   actually did; withdrew the "3/5 successful blind adaptive controls"
   claim.
2. `stage6_flock/stage6_11_translating_torus/audit/material_identity_step2_20260921/`
   — built and calibrated `ForwardMaterialTrace611`, a simple
   material-overlap identity tracker, independently of the control seeds;
   re-adjudicated seeds 500–504 with it.
3. `stage6_flock/stage6_11_translating_torus/audit/identity_causal_reconciliation_20260921/`
   — hardened identity validation against same-world hard negatives;
   seed-503 split forensics; partial seed 501/503 adjudication.
4. `stage6_flock/stage6_11_translating_torus/audit/causal_reconciliation_step3_20260922/`
   — this pass: completed episode-level identity validation, an RNG/CRN
   audit, exact v2 replay, and identity-aware causal (schedule-effect)
   adjudication for all 5 seeds.

## Established findings

- **The original "3/5 successful blind adaptive controls" claim is
  WITHDRAWN.** (evidence_recovery_20260921; reaffirmed by every
  subsequent pass.) At least one reported "success" (seed 503) is now
  established to describe a population that is not materially descended
  from the flock selected and actuated at qualification.
- **v1 (`LineageTracker611`) can and does jump to unrelated, zero-
  material-overlap populations**, via a global-MAP-over-branching-
  histories mechanism with no margin/confidence gate. Confirmed at
  bird-ID resolution for seed 503 t=46→47 and (differently) for seed
  500's early uncontrolled phase. This is a real, structural tracker
  defect, not the primary subject of intervention analysis.
- **A frozen, simple material-association rule
  (`ForwardMaterialTrace611`, Jaccard≥0.30) exists**, calibrated on
  uncontrolled natural data independent of the control seeds, and
  hardened against same-world hard negatives (not just cross-episode
  ones). Across 72 full-episode sequential traces on natural data (36
  already-used-for-calibration + 36 genuinely untouched holdout), **zero
  erroneous transfers to unrelated populations were observed**
  (`causal_reconciliation_step3_20260922/IDENTITY_EPISODE_VALIDATION.md`).
  A small (~0.03–0.04%) non-subset same-frame false-accept risk exists at
  the pairwise level but did not manifest in any sequential trace tested.
  **This is a material ASSOCIATION layer, not a complete strict-identity
  decision** — split/merge/genealogy semantics sit above it.
- **Physical turn, identity continuity, intervention effect, and
  actuator selectivity are four separate questions**, and collapsing them
  produced the withdrawn claim. They are now tracked separately for every
  seed (`causal_reconciliation_step3_20260922/FINAL_STAGE611_ADJUDICATION.md`).
- **Seed 501**: the materially-continuous target undergoes a real,
  identity-valid physical turn (≈0.23→0.97) that persists through
  release. A repeated-replicate, CRN-paired schedule-effect comparison
  (25 replicates) shows sustained forcing DOES raise the material
  target's alignment relative to no forcing (demonstrated), but the
  specific historical actuator choice does NOT demonstrably outperform
  duration/cardinality/cadence/pool-matched random forcing (not
  demonstrated).
- **Seed 502**: v1 permanently diverges from the material target around
  t=32; the material target itself does not turn substantially
  (≈0.19→0.10); the reported later v1 rise belongs to a materially
  distinct population. v1 and v2 (exact replay) agree numerically with
  EACH OTHER at every field-direction radius while both diverge sharply
  from the material anchor — the strongest anchor-sensitivity case in the
  5-seed sweep. This pass's repeated-replicate comparison shows no
  demonstrated intervention effect on alignment, but a clearly elevated
  target-LOSS rate under forcing (44–52% of replicates lose the material
  target entirely, vs. 20% unforced) — a disruption signature distinct
  from seed 503's fragmentation but comparable in kind.
- **Seed 503**: the qualification-time target undergoes a **likely
  physical split** at t=47 (persistent daughter separation, no
  re-fusion, one daughter losing detectable coherence within 3 steps) —
  not formally "confirmed" (no independently validated physical-split
  threshold exists in this repository, and this pass declined to invent
  one to classify this specific seed). The large, historically-reported
  0.86 turn belongs to a THIRD, wholly unrelated, zero-overlap population
  — not either split daughter, and (new in this pass) v2's own EXACTLY
  computed anchor independently contradicts v1's high reading too (v2
  sides with the material trace's low readings, not v1's high one). A
  repeated-replicate causal comparison shows intervention raises the
  material-continuing daughter's own alignment (demonstrated) without a
  detectably elevated fragmentation rate relative to no forcing
  (organizational disruption not demonstrated as intervention-specific —
  split events are common, >50% of replicates, under all tested
  conditions including no forcing).
- **Seed 500**: reference/sanity case; v1 and material identity agree
  throughout at every field-direction radius; this pass's schedule-effect
  harness correctly does NOT manufacture a large intervention effect here
  (paired mean +0.009, 90% CI barely excludes zero) — a useful negative
  control on the harness itself.
- **Seed 504**: v1 and material identity agree throughout, but v2's exact
  anchor is a striking outlier (high, 0.72–0.88) despite 90/94 frames of
  v1==v2 membership agreement — a disclosed complication, not resolved
  further. This pass's repeated-replicate comparison REFINES the prior
  "positive short-horizon authority without persistent reorganization"
  finding rather than simply preserving it: under sustained forcing, a
  persistent (end-of-release) rise is demonstrated on average (paired
  mean +0.367, 90% CI [0.235, 0.499], the strongest paired signal of the
  5 seeds) but is highly unreliable (median 0.07 vs. mean 0.39 — a
  right-skewed/bimodal outcome). "Short-horizon response ≠ reliable
  persistent transition" is preserved as the TYPICAL case; this pass
  shows persistent transition is possible, just uncommon, under the
  tested budget.
- **Across all 5 seeds, actuator selectivity is never demonstrated.**
  Wherever an intervention effect exists (501, 503, 504), the specific
  historical top-K-by-authority actuator choice never distinguishably
  outperforms duration/cardinality/cadence/pool-matched random forcing.
  This is the most consistently replicated finding of the whole
  programme.
- **Trigger-state reproduction is exact for all 5 seeds** — independently
  verified bit-for-bit from each raw episode seed
  (`causal_reconciliation_step3_20260922/RNG_AND_CRN_AUDIT.md`).
- **`branch_adjudication_611.py` (Step 1's original 9-branch
  counterfactual adjudication script) is exactly reproducible** (verified
  for seed 501: 0 mismatches across 99 readout values) and architecturally
  CRN-clean (all branches per seed share one physics RNG stream; every
  branch's own decision-side randomness uses an independent generator).

## Provisional findings (evidence exists, not fully closed)

- Whether the ONLINE CONTROLLER's own re-inference (as opposed to a fixed
  schedule replay of its final actuator choices) adds anything beyond
  what schedule replay already shows — the "policy effect" estimand —
  is not yet closed for any seed; it requires decoupling the control
  loop's auxiliary decision-code RNG consumption from the physics stream,
  a larger audit-only engineering effort not completed in this pass.
  (`causal_reconciliation_step3_20260922/RNG_AND_CRN_AUDIT.md` §5,
  `NEXT_CONTROLLER_SPEC_INPUTS.md`.)
- Whether the field-direction readout's anchor-sensitivity finding
  (robust for 501, not for 502/503) survives EXACT v2 anchoring (as
  opposed to v1-as-proxy) — being closed in this pass; see
  `V2_REPLAY_AND_FIELD_READOUT.md` for seed-by-seed results.
- Full per-frame material tracing of Step 1's original 9 named
  counterfactual branches (as opposed to this pass's own, cheaper,
  materially-scored 3-branch schedule-effect harness) — not completed for
  all 5 seeds due to compute cost (~29 CPU-minutes per seed for the full
  9-branch reproduction); disclosed in
  `causal_reconciliation_step3_20260922/COUNTERFACTUAL_MATERIAL_TRACES.md`.

## Explicitly withdrawn claims

- "3/5 successful blind adaptive controls" (original Stage 6.11 report).
- "Seed 503 is the one seed with an unambiguous, all-readout-corroborated
  real turn" (Step 1's own `FIVE_SEED_CAUSAL_ADJUDICATION.md`) — narrowly
  contradicted: that corroboration was established on counterfactual
  branches whose own re-simulated trajectories did not reproduce the
  actual recorded run's t=47 split; applied to the real run, the
  "same-population" assumption does not hold past that point.

## Conceptual boundaries that remain load-bearing

- **Traveling-wave identity is explicitly OUT OF SCOPE for the flock
  experiment.** Identity here means flock/material-organizational
  identity with gradual local turnover permitted — never "does the same
  traveling pattern persist."
- **Material association (Jaccard overlap) is not the same thing as
  strict identity.** A confirmed physical split or merge should terminate
  strict same-object continuity even though material descendants can be
  tracked genealogically for analysis. No physical-split/merge threshold
  has been validated in this repository yet — any future use of one
  requires independent calibration first, the same way the primary
  association threshold was calibrated.
- **v1 and v2 are trackers, not ground truth.** Neither has ever been
  treated as ground truth in any pass to date, and this file does not
  start now.

## What the next task (controller redesign) may and may not assume

See `stage6_flock/stage6_11_translating_torus/audit/causal_reconciliation_step3_20260922/NEXT_CONTROLLER_SPEC_INPUTS.md`
for the full, itemized list. Controller redesign was explicitly out of
scope for every pass to date, including this one.
