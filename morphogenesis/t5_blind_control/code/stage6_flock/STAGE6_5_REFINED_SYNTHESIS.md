# STAGE6_5_REFINED_SYNTHESIS.md

Concise summary of `stage6_5/refinement/`, which resolves three questions
`STAGE6_5_SYNTHESIS.md` left open. Full evidence:
`stage6_5/refinement/RESULTS_6_5R.md` and its three part-level results
files. `STAGE6_5_SYNTHESIS.md` itself is unchanged — this document sits
alongside it, not in place of it.

## Four objects, kept distinct throughout

- **`B^D`** — the microscopic structural interface: every exterior state
  that directly enters the core's next-state update (a lattice fact, never
  used by the inference pipeline itself).
- **`\hat B`** — the observationally sufficient predictive interface: a
  compact set learned from trajectories alone, precision-1.0 but
  recall-capped (0.15-0.58 across all flocks tested in Stage 6.5 and this
  refinement), whose excess loss over the full exterior model tracks `B^D`'s
  own to within ~0.01 nats under natural trajectories.
- **`B^C`** — the intervention-relevant interface, newly operationalized in
  this refinement's Part A: the birds with non-negligible `D_j^{\rm do}`
  (measurable causal effect on the interior's true one-step distribution
  under independent perturbation). Established finding: `B^C` extends
  meaningfully beyond `\hat B` into `B^D \setminus \hat B` — some omitted
  shell birds have real, sometimes large, effects — but `B^C`'s *practical
  predictive consequence* for `\hat B`'s own sufficiency gap is much
  smaller than its raw causal-effect size would suggest.
- **`I_t`** — the lineage-constrained collective whose boundary is being
  discussed: this refinement's Part C shows this cannot be left
  unconstrained (it silently degenerates to a near-single-bird remnant)
  nor over-constrained by a naive continuity/turnover trade-off calibrated
  on the wrong regime (passive baseline dynamics, not active control) — a
  size-and-continuity **validity guard**, evaluated against the collective's
  own realized history, is what actually prevents the pathology, not a
  smarter formula for choosing candidates.

## Does `\hat B` remain sufficient under intervention?

**Mostly, with a real but modest, direction-consistent tax.** `B^D \setminus
\hat B` members have causal effects on the true dynamics comparable in
magnitude to `\hat B`'s own members on the flock where the effect is
clearest (seed 20: omitted-shell mean `D_j^{\rm do}` = 0.44 vs. included-shell's
0.79). Despite this, `\hat B`'s own excess-loss gap versus the full exterior
widens by at most ~0.005 nats when an omitted shell bird is deliberately
decorrelated from its natural correlates — two orders of magnitude below the
underlying causal effect sizes, and concentrated specifically on the
omitted-shell class on 2 of 3 flocks (the theoretically expected direction).
`\hat B \neq B^C` (not exact), but `\hat B \approx` an adequate reduced-order
predictive summary of `B^C` under the natural data distribution — the gap
opens, but does not blow up, under the stress test this refinement applied.

## How much microscopic structure must be recovered for control?

**On this evidence, more than `\hat B`'s recall ceiling typically provides —
Stage 6.5's original single success does not generalize.** Across 12
newly-scanned, frozen-before-inference discriminating flocks (oracle
succeeds, matched-budget random fails — a nontrivial, non-degenerate
benchmark by construction), inferred-boundary control is statistically
indistinguishable from a matched-budget random draw (mean `P(success)`
0.0017 vs. 0.0083; flock-level bootstrap CI spans zero). The mechanism is
plausibly structural, not incidental: the frozen `q=2`/`gamma=0.5`
multicover coverage objective is a sharply nonlinear function of actuator
budget, and `\hat B`'s recall-capped size (27-45% of the oracle's own
requirement, similar to the fraction on the one flock that DID succeed)
usually falls short of the coverage threshold. **The answer to "how much
structure is needed for useful control" is, on this evidence, closer to
"most of `B^D`'s coverage-relevant structure" than to "whatever a
precision-first predictive criterion happens to recover."** This is a
materially more cautious conclusion than Stage 6.5's own framing.

## How much membership flexibility can be allowed before collective identity becomes trivial?

**Very little, unless an explicit non-degeneracy guard is imposed — and
the guard, not a smarter adaptive-selection formula, is what actually
prevents triviality.** An unconstrained functional identity definition
reliably collapses to a 1.8-2.2-bird remnant under closed-loop control
while still registering 0.97-1.00 nominal success, on *every* flock tested
in this refinement, including a flock where the properly-constituted
20-bird collective only succeeds 10% of the time. A validity guard (a
lower-tail size/continuity envelope estimated from the collective's own
undisturbed baseline behavior, plus a short grace period before declaring
failure) does not solve the underlying tendency to shrink — it correctly
*exposes* it: 97-100% of guarded closed-loop episodes are flagged IDENTITY
COLLAPSE / UNRESOLVED, and no actuator-cost "efficiency gain" survives once
that flag is accounted for. A simpler, less punitive fix — temporal
turnover regularization alone, without an explicit validity concept — was
tried first and did not work cleanly: no single regularization strength
separated jitter from genuine transitions, and the strength that came
closest actively broke tracking during real control episodes because it had
only ever been calibrated against passive dynamics. **Adaptive boundary
membership (which birds are in `B_t`, given a fixed `I_t`) is fine and
already well-supported by Stage 6.5's pathwise-leakage evidence; adaptive
*collective identity* (which birds are in `I_t` itself) needs an explicit,
externally-anchored non-degeneracy check, not just a better internal
scoring rule.**

## Stage 6 closure, self-assessed against the target in the task brief

The task brief's strongest possible closure was: *observe a collective ->
infer a compact interface -> understand what information that interface
omits -> control through it -> verify that the same nontrivial collective
survives.* This refinement completes every step of that chain and finds a
break at the fourth: the compact interface's omissions are understood
(Part A) and are causally real, not merely topological; but controlling
through the compact interface does not reliably work on a fair benchmark
(Part B); and even where control nominally "works," verifying that the same
nontrivial collective survived requires machinery (Part C's guard) that
this port did not have until this refinement built it, and which — once
built — most often reports that it did *not* survive. **The honest
Stage 6 closure is therefore: the pipeline for asking all of these
questions rigorously now exists and works (the closed-form intervention
test, the frozen discriminating-flock benchmark, the validity guard); what
it reveals, applied honestly, is that Stage 6's control and identity claims
were narrower than they first appeared, not that they were wrong in kind.**
This is exactly the kind of result Stage 7's moving-shepherding model should
be designed to improve on, not paper over.
