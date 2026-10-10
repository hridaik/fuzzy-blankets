# RESULTS_6_5R.md

Full results for all three refinement parts. This document indexes and
cross-links the three part-level results files; it does not restate every
number, which live (with their generating JSON) in `causal_redundancy/
CAUSAL_REDUNDANCY_RESULTS.md`, `control_generalization/
CONTROL_GENERALIZATION_RESULTS.md`, and `identity_stability/
IDENTITY_STABILITY_RESULTS.md`.

## Part A: causal redundancy (Hard Gate A)

See `causal_redundancy/CAUSAL_REDUNDANCY_RESULTS.md`. Headline: **omitted
true-shell birds have real, sometimes large, causal effects on the interior's
true one-step distribution** (up to 2-4 nats KL, comparable to included-shell
effects on one flock) — `observationally redundant != causally redundant`
is demonstrated cleanly at the direct-effect level. The downstream
predictive consequence for the inferred boundary `\hat B`'s own excess loss
is much smaller (a reproducible but sub-0.005-nat tax on 2 of 3 flocks) —
`\hat B` bends under intervention, it does not break. The oracle shell
`B^D` stays robust across every condition tested.

## Part B: control generalization (Hard Gate B)

See `control_generalization/CONTROL_GENERALIZATION_RESULTS.md`. Headline:
on a newly-scanned, frozen-before-inference, 12-flock discriminating
benchmark (oracle succeeds, matched-budget random fails), **inferred-
boundary control does not outperform null intervention** — mean
`P(success)` 0.0017 vs. random's 0.0083, flock-level bootstrap CI for the
mean difference spans zero. Stage 6.5's original single discriminating
success (held-out seed 20) does not generalize. The likely mechanism: the
frozen `q=2`/`gamma=0.5` multicover objective's coverage requirement is a
sharply nonlinear function of actuator-set size, and `\hat B`'s
recall-capped budget (27-45% of the oracle's own) usually falls well short
of the threshold regardless of which specific birds fill it.

## Part C: identity stability

See `identity_stability/IDENTITY_STABILITY_RESULTS.md`. Headline: **some**
of Stage 6.5's original lineage turnover was detector jitter (weak positive
correlation between physical change and turnover, 0.10-0.42), but not most
of it, and a simple, transparent temporal-regularization knob could not
cleanly separate jitter from genuine transitions at any tested strength —
worse, regularization calibrated on passive baseline data actively
interfered with tracking during genuinely controlled episodes on 4 of 5
flocks. The identity-validity guard, by contrast, worked cleanly: it
reproduced Stage 6.5's one-bird-collapse pathology in an unguarded control
(nominal success 0.97-1.00 via a 1.8-2.2-bird remnant) and correctly
flagged 97-100% of the corresponding guarded episodes as IDENTITY COLLAPSE
/ UNRESOLVED while holding a materially larger (4-8x), defensible group
throughout. No efficiency gain survives once identity validity is
accounted for. A compact pathwise predictive boundary (0.006-0.043 nats)
survives under every stabilized description tested.

## Cross-cutting observation

All three parts land on a common, more sobering shape than Stage 6.5's own
"more interesting than expected" framing: **the mechanisms that looked
promising under narrow evidence (one discriminating flock for control
transfer; unconstrained identity definitions for adaptive control) do not
hold up under a harder, more deliberately adversarial test built before
seeing their outcome.** This is not a failure of the refinement — it is
exactly what Hard Gates A-C were built to check, and Part G's stopping
rules were followed throughout: no criterion was loosened, no
threshold retuned, no regularization strength chosen after inspecting
control or collapse outcomes. Where a mechanism worked (the closed-form
intervention machinery in Part A; the validity guard in Part C), it worked
cleanly and is reported as such; where a mechanism did not generalize or
resolve cleanly (control transfer in Part B; temporal regularization in
Part C), that is reported with equal weight.

See `../../STAGE6_5_REFINED_SYNTHESIS.md` for the full synthesis against
Stage 6.5's original framing.
