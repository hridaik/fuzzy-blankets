# Stage 6.12C — Next Stage Decision

## Decision: Case C

**Real singleton-actuator selective causal headroom exists in this
system (outcome oracle mean ΔJ_conservative ≈6.9× random, 90% CI cleanly
separated from every other tested strategy), but it is NOT explained by
physical contact between actuator and target — neither the deployable
kinematic-predicted-contact score nor a genuine forced-future realized-
contact upper bound identifies the high-effect actuators.**

This is based PRIMARILY on the 10 fresh confirmatory states sampled in
this stage (`ORACLE_DECOMPOSITION.md`), not on the old Stage 6.12B 3-state
lead, per the task brief's own instruction.

## Why not the other three endpoints, stated plainly

- **Case A (kinematic ≈ contact-oracle ≈ outcome-oracle >> random →
  proceed to a contact-aware authority estimator)**: REJECTED. The
  outcome oracle is far above the other three, not approximately equal to
  them; kinematic and contact-oracle both sit at essentially the random
  baseline.
- **Case B (contact-oracle >> random but kinematic ≈ random → improve
  the deployable predictor first)**: REJECTED. This requires the contact
  oracle itself to be well above random — it is not (mean 0.00128 vs.
  random's 0.00323, CI spanning zero and overlapping the random CI). There
  is no well-performing contact oracle for a better deployable predictor
  to chase.
- **Case D (outcome-oracle ≈ random → no selective headroom, don't build
  an authority learner)**: REJECTED. The outcome oracle's 90% CI
  ([0.0092, 0.0419]) is clearly and entirely above the random baseline's
  CI ([0.0012, 0.0057]) — this is the cleanest, most state-clustering-
  robust positive result in this entire stage. Real headroom exists.

**Case C is the one endpoint consistent with ALL of: (i) a large,
CI-separated outcome-oracle advantage, (ii) a contact-oracle that sits at
or below random, and (iii) a deployable kinematic predictor that tracks
the (weak) contact oracle rather than the (strong) outcome oracle.**

## What this implies for the next task

**Do NOT build a contact-aware authority estimator based on physical
proximity/predicted-future-contact.** This stage specifically, directly
tested that mechanism with both a deployable proxy and a genuine
non-deployable upper bound, and both failed to track the actual outcome
headroom. Building a learned authority model on top of the kinematic
contact score (or any refinement of it that stays within the
"physical-contact" family) would be building on a mechanism this stage's
own confirmatory data argues against.

**What SHOULD be investigated next, if this programme continues**: what
DOES separate a high-ΔJ_conservative singleton actuator from a low one,
if it is not physical contact? Candidate hypotheses this stage's data
cannot distinguish (raised here as hypotheses for the next task, not
findings of this one):

1. An indirect, social-field-mediated disruption pathway — the actuator's
   forced heading perturbs OTHER exterior/boundary birds' local alignment
   fields, which propagate into the target population without the
   actuator itself ever entering the target's interaction radius. This
   would predict that a candidate's local BIRD DENSITY/crowding, not its
   distance-to-target, correlates with effect — untested here.
2. Timing/phase effects relative to the target's own internal oscillation
   or turning dynamics — an actuator forced at the "right moment" in the
   target's natural dynamics could have outsized effect independent of
   contact — untested here (this stage used a single fixed d=8 onset per
   candidate, at t0, uniformly).
3. Genuinely idiosyncratic, state-specific structure with no generalizable
   candidate-level predictor at all (the outcome oracle's state-level
   values in `ORACLE_DECOMPOSITION.md` are themselves highly variable,
   0.0026 to 0.114) — if true, no authority ESTIMATOR (contact-based or
   otherwise) would generalize, and the next task should test this
   directly (e.g., does ANY simple pre-registered geometric/kinematic
   feature — density, phase, heading alignment with neighbors — show a
   state-clustered-reliable correlation with the outcome-oracle
   candidate's identity, before attempting to learn anything).

**A recommended concrete next step**: a further, focused confirmatory
experiment testing hypothesis (1) above specifically — a local-density or
neighbor-count predictor, computed the same deployable way the kinematic
score was, validated with the SAME oracle-decomposition discipline this
stage established (frozen predictor, forced-future realized oracle,
outcome oracle, state-clustered CIs) — rather than proceeding to build any
learned model on the current (contact-based) feature family.

## What may NOT be assumed by whoever picks this up next

- That the kinematic-contact-predictor lead is dead — its point estimates
  remain weakly positive throughout this stage; what is established is
  that it is NOT reliable enough, at this state count, to justify building
  on, and that a genuine contact-based upper bound does not do
  meaningfully better.
- That "no contact-based mechanism" implies "no controllability at all" —
  the outcome-oracle result is unambiguous: singleton actuator identity
  has real, sizeable causal consequence in this system. The mechanism is
  simply not (established to be) contact.
- That this stage's 10-state sample is large enough to rule out a true
  small kinematic-predictor effect — every "not established" finding in
  `FINAL_STAGE612C_FINDINGS.md` is a CI-spans-zero finding, not a
  CI-excludes-a-meaningful-effect finding. A larger state count remains
  the single highest-value lever for sharpening any of these questions
  further, exactly as Stage 6.12 and 6.12B's own next-step
  recommendations already established.

## Explicitly not done in this task

No learned authority/actuator-selection model was built or tuned. No
candidate mechanism (density, phase, or otherwise) beyond physical contact
was tested — those are next-task hypotheses, not this task's findings.
