# Next Experiment Decision

## Decision: Decision 2

**Clairvoyant headroom exists but stable actuator selectivity is weak,
and much of the apparent oracle advantage is explained by a
no-stable-identity permutation null.** Do NOT proceed to a candidate-feature
discovery / static-organizational-feature programme (that was the implicit
direction of `NEXT_STAGE_DECISION.md`'s "recommended concrete next step,"
a local-density predictor tested with the same oracle-decomposition
discipline). This follow-up's evidence argues against that direction
specifically because it targets STATIC, per-candidate features -- and this
follow-up shows static candidate identity itself carries almost no
reproducible signal, so a smarter static feature built on top of it is
unlikely to fare differently without first establishing that SOME static
feature can beat cross-validated random selection, which nothing tested so
far (kinematic score, static distance, contact-at-t0, geometric
contact-during-forcing, or raw identity) has done.

## Why not Decision 1

Decision 1 requires: cross-validated best actuator beats random/median
meaningfully; ranking reliability nontrivial; actuator variance
appreciable. **All three fail in this data:**
- `CV_stable_lift`'s ratio-free form: mean +0.0013, 90% CI
  [-0.0012, +0.0042] -- spans zero, and is roughly half the magnitude of the
  already-tiny random baseline (`CROSS_VALIDATED_ORACLE.md`).
- Ranking reliability: mean Spearman rho across states ≈ 0.0007 at the
  best-powered split (6 training streams), no trend toward improvement with
  more training data (`RANK_RELIABILITY.md`).
- `Var_actuator/Var_total`: 0.0-4.2% in every state, 7/10 states with a
  negative raw estimate (`VARIANCE_DECOMPOSITION.md`).

## Why not Decision 3

Decision 3 requires genuinely distinct state types -- some
stable-selective, some stochastic-opportunity -- calling for a state-level
gate. **Not supported: every one of the 10 states shows the same
qualitative pattern** (large per-stream/state-mean oracle values, ~zero
actuator variance, ~zero cross-validated advantage) -- they differ in SCALE
(how much per-stream opportunity exists) but not in KIND (whether that
opportunity is predictable in advance, `STATE_TAXONOMY.md`). A state-level
gate implies some states would route to "pick an actuator confidently" and
others to "don't bother" -- but no state in this sample supports the first
branch, so there is nothing for a gate to select between yet. This may
still be worth testing with a larger state sample (see caveats below), but
it is not what THIS sample shows.

## What SHOULD be investigated next

Following Decision 2's own implication (`CONFIRMATORY_PROTOCOL.md`'s and the
task brief's own Decision-2 text): **do not hunt static actuator features.**
Candidate concrete directions, in rough priority order:

1. **Phase/timing-conditioned control.** This entire dataset used a single
   fixed d=8 onset at t0 for every candidate, uniformly
   (`CONFIRMATORY_PROTOCOL.md`). If the dominant source of variance is
   `Var_stream` (which physics future unfolds) rather than `Var_actuator`
   (which bird is forced), the natural next lever is WHEN to act relative to
   the target's own internal dynamics, not WHICH exterior bird to act on --
   directly testable by repeating a scaled-down version of this same K=1
   exhaustive design at several different onset offsets within an existing
   or new state, using the SAME oracle-decomposition and permutation-null
   discipline this follow-up used.
2. **Short probe-then-adapt / uncertainty-aware control.** Since a
   candidate's own past-stream performance does not predict its future-
   stream performance (`RANK_RELIABILITY.md`), a controller that commits to
   one actuator based on prior information is working against the grain of
   this system. A controller that probes cheaply (or adapts mid-forcing) and
   reacts to the REALIZED early trajectory, rather than pre-committing to a
   predicted-best actuator, is better matched to a stochastic-opportunity
   regime than either a contact-based or a to-be-discovered static-feature
   selector would be.
3. **The directed, FOV-gated contact oracle Stage 6.12C never computed**
   (`CONTACT_METRIC_AUDIT.md`) -- cheap to add (the `live_edges` function
   already exists, unmodified, in `moving_flock.py`) and directly closes the
   gap this follow-up's audit identified, before concluding "no causal-
   interaction channel matters" as opposed to "no GEOMETRIC channel
   matters." This is a smaller, more targeted piece of unfinished business
   than a new experiment -- it could in principle be answered from a fresh
   run of the SAME K=1 states with `live_edges` diagnostics added, not a
   fundamentally new design.
4. **Larger state count**, exactly as every prior stage in this programme
   (6.12, 6.12B, 6.12C) has already flagged as the single highest-value
   lever for sharpening a CI-spans-zero finding into a real conclusion. This
   follow-up's `n=10` states inherits the same limitation -- none of its
   "near-zero" findings excludes a true small stable-actuator effect that a
   larger sample could reveal, particularly since `RANK_RELIABILITY.md`'s
   sample-efficiency curve was only probed up to 6 STREAMS per state, not
   more STATES.

## What may NOT be assumed by whoever picks this up next

- That stable actuator selectivity is proven impossible in this system --
  every null finding here is a small-sample, CI-spans-zero finding.
- That the interior-actuation experiment (`INTERIOR_ACTUATION_METHOD_NOTE.md`)
  is thereby ruled out -- Decision 2 argues against STATIC exterior-feature
  discovery specifically; whether interior membership changes the
  VARIANCE/RELIABILITY structure (as opposed to being one more static
  feature to search over) remains a live, distinct question this follow-up
  did not test, and the method note exists precisely so that experiment, if
  run, scores correctly.
- That geometric contact has been shown irrelevant to the true directed
  causal-influence channel -- only geometric contact was tested, by every
  stage so far (`CONTACT_METRIC_AUDIT.md`).
- That this follow-up's uniform `stochastic-opportunity` classification of
  all 10 states generalizes to states this sample did not include.

## Explicitly not done in this task

No new simulation. No design or implementation of the phase/timing,
probe-then-adapt, FOV-gated-contact, or interior-actuation experiments named
above -- these are next-task candidates, raised as hypotheses this
follow-up's own data motivates, not findings or designs of this bounded
analysis task.
