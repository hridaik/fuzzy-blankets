# Stage 6.12B — Next Stage Decision

## Decision

**Decision A, CONDITIONALLY** — the evidence does not cleanly satisfy any
of the four named endpoints at full confidence, but among them, Decision A
(build a contact-aware authority estimator) is the one with genuine,
same-signed, cross-state-reproduced held-out-ish support: the
physics-assisted kinematic predicted-contact score. It is NOT strong
enough evidence to proceed straight to building that estimator without one
more confirmatory step.

**Why not the other three, stated plainly (task brief S30: pick the one
the evidence supports, not the most exciting):**

- **Decision B (temporal refreshing alone is enough)**: contradicted by
  Q5-7 — refreshed random did not consistently beat fixed random (opposite
  direction at K=2 vs K=4), and contact-aware refreshing did not
  consistently beat plain refreshing either.
- **Decision C (oracle works, deployable prediction doesn't)**: not
  supported — the oracle strategy did not "strongly work" in this data
  (below random/kinematic in most cells). Also this stage's oracle
  construction has a disclosed weakness (predicts from the no-control
  future, degraded once forcing itself perturbs the trajectory), so this
  data cannot cleanly distinguish "oracle access doesn't help" from "this
  particular oracle isn't a good enough upper bound" — Decision C requires
  a confident "oracle works" reading that is not available here.
- **Decision D (even oracle contact does not solve the problem)**: closest
  runner-up, but the same oracle-construction caveat that blocks C also
  blocks confidently choosing D — a genuinely stronger oracle (using the
  ACTUAL forced-trajectory's realized future contact opportunities under
  a range of candidate actuator choices, or a properly re-solved
  fixed-point oracle) has not yet been tested. D would be the right call
  if that stronger oracle also failed; it has not been run.

## What the recommended next step actually is

**Not** "start building the learned authority model." Instead: **run ONE
more focused confirmatory experiment**, at a properly powered state count
(the compute-budget lesson from both Stage 6.12 and 6.12B is that STATE
COUNT, not stream depth, is the binding constraint — `STATISTICAL_
ANALYSIS.md`), that:

1. Tests the physics-assisted kinematic predictor's correlation with paired
   effect on ≥15-20 fresh states (vs. this stage's 3), holding K, d fixed
   at one or two values rather than sweeping the full grid again.
2. Uses a STRONGER oracle construction (e.g., re-simulating with a small
   number of candidate forced trajectories to get a genuine forced-future
   upper bound, rather than the paired no-control future used here) to
   properly settle the C-vs-D question this stage left open.
3. Does NOT repeat the full 6.12B-B q/strategy/K grid at this stage —
   that grid produced uniformly wide, inconclusive CIs here and a bigger
   version of the same design is unlikely to resolve anything without a
   much larger state count than is likely affordable.

## What may NOT be assumed by whoever picks this up next

- That the kinematic-contact-predictor lead is validated — it is a
  3-state, single-dev-stream correlational result, the strongest lead
  found across two stages of work, but still provisional.
- That refreshing actuator identity is established as useless — the K=2
  vs K=4 sign flip means this is genuinely unresolved, not negative.
- That the oracle result rules out a real spatiotemporal control
  interface — the oracle construction used here is a disclosed
  approximation, not a true upper bound.
- That Stage 6.12B's elevated target-loss rate (15.5%) generalizes beyond
  the specific 24-step matched-effort design tested here — it may be a
  property of long, sustained forcing specifically, worth testing at
  intermediate durations before assuming it is fixed.

## Explicitly not done in this task

No learned authority/actuator-selection model was built or tuned, per the
task brief's own instruction (S30/S32). This document identifies what the
next controller-design task should try to learn (contact-persistence,
specifically a properly validated kinematic predictor), not how to build
it.
