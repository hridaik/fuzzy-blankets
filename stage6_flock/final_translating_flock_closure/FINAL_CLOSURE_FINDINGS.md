# Final Closure Findings

Concise answers to the 6 final scientific questions this pass was tasked
to answer. Full detail in `ORGANIZATIONAL_ROLE_RESULTS.md`,
`LIVE_EDGE_CAUSAL_INTERFACE.md`, `TIMING_SUSCEPTIBILITY.md`.

## (1) Does being INSIDE the material collective confer causal privilege?

**No.** Pooled interior (core+boundary, A_minus_j-corrected) vs exterior
(live parent+non-parent) effect: mean diff −0.0020, 90% CI [−0.0156,
+0.0115] (8 states), spans zero, and the per-state sign is inconsistent
(5/8 positive, 3/8 negative, magnitudes spanning more than an order of
magnitude). See `ORGANIZATIONAL_ROLE_RESULTS.md`.

## (2) Is the moving collective's BOUNDARY privileged relative to its core?

**No.** Boundary vs core: mean diff +0.0021, 90% CI [−0.0105, +0.0147]
(n=3 co-occurring states), spans zero. Boundary vs live exterior parent is
numerically NEGATIVE (−0.0068, CI excludes zero at n=3 but sign is not
unanimous across the 3 states) — i.e. where boundary status shows any
significant difference at all, it is not in the privileged direction the
"boundary privilege" hypothesis predicts. See
`ORGANIZATIONAL_ROLE_RESULTS.md`.

## (3) Do actual FOV-gated exterior causal parents outperform equally nearby exterior non-parents?

**No.** Live exterior parent vs near exterior non-parent: mean diff
+0.0031, 90% CI [−0.0097, +0.0160] (n=3 co-occurring states), spans zero,
mixed per-state sign. This holds despite class C actuators being ~9x
closer to the target on average than class D (0.27 vs 2.25 distance
units) — if anything a conservative test in class C's favor. See
`LIVE_EDGE_CAUSAL_INTERFACE.md` Q1.

## (4) Does short multi-hop directed reachability explain exterior effects better than geometric contact?

**No.** Per-state Spearman ρ with ΔJ_conservative: geometric contact
−0.107 [−0.302,+0.096], live directed access −0.118 [−0.270,+0.036],
≤3-hop temporal reachability −0.090 [−0.293,+0.115] — all three CIs span
zero, overlap heavily, and are indistinguishable from each other. See
`LIVE_EDGE_CAUSAL_INTERFACE.md` Q2/Q3.

## (5) Is variation across intervention ONSET materially larger than stable actuator-identity variation?

**Not shown to dominate, in a bounded and sparsity-limited sample.** n=3
usable states (of the intended 4 — `sclosure_00` contributed zero usable
rollouts, see `TIMING_SUSCEPTIBILITY.md`'s disclosed sparsity note).
Pooled mean within-onset actuator spread (0.0109, 90% CI [0.0011,0.0207])
is numerically LARGER than pooled mean onset-range (0.0040, 90% CI
[0.0000,0.0080]); only 1/3 states shows onset variation dominating
actuator variation. This is read as inconclusive-to-negative for the
"timing dominates" hypothesis in this bounded sample — not oversold into
a positive timing-susceptibility finding, per the task's explicit
instruction not to manufacture a timing story.

## (6) Does any remaining result justify more translating-flock work?

**No.** All three closures return null or inconsistent results at the
class/topology/timing level, extending (not merely repeating) the prior
individual-actuator negative result. No critical unresolved validity
problem was discovered — the identity machinery, RNG/CRN protocol, and
outcome metrics all behaved as designed and were spot-checked during this
pass (see `IDENTITY_AND_DISRUPTION.md`). Per the task's default scientific
discipline, no further translating-flock work is initiated. The programme
moves to morphogenesis (`MORPHOGENESIS_HANDOFF.md`).

One methodological limitation IS disclosed and should inform how these
nulls are read: boundary-member and live-exterior-parent actuator classes
were available in only 3/8 (Closure A/B) and 3/4 (Closure C) states, at
the mean-field live-degree regime used throughout this programme
(`R_PRIMARY=0.9`, expected degree ≈0.77). This is a genuine property of
the tested regime, not a data-collection failure, but it means the
class-C/boundary-specific null results above are LESS powerful than the
core/non-parent comparisons (which had the full 8-state sample). This is
disclosed as a scope limitation, not treated as grounds to expand the
campaign (which the task's hard-stop discipline forbids) or as grounds to
doubt the headline "no stable class privilege" conclusion, which is
independently supported by the full-sample core-vs-non-parent and
pooled interior-vs-exterior comparisons.

## Which decision-language branch applies

**"None of these are strong" branch**: no stable spatial/organizational
actuator interface was demonstrated in the translating flock (Closure A);
true directed causal-interface membership does not show a discernible
advantage over geometric proximity, both being weak (Closure B); timing
variation is not shown to dominate over actuator-identity variation in
this bounded sample (Closure C). Conclusion: control opportunity in this
translating-flock system continues to look predominantly
stochastic/trajectory-conditioned under every intervention class and
timing variant tested across this programme, not attributable to a stable
spatial, organizational, topological, or (within this closure's small
timing sample) temporal actuator-selection interface. The flock programme
is closed on this basis — see
`stage6_flock/TRANSLATING_FLOCK_FINAL_SYNTHESIS.md`.
