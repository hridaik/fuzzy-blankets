# STAGE6_FINAL_REFINEMENT.md — closing the retargeting problem

Summarizes `v3_refinement/` and `interactive_demo/`, which refine and close
the single-core retargeting problem opened by `v1_mechanism_audit/` and
`v2_interface_control/` (see `STAGE6_SYNTHESIS.md` for that earlier work,
which remains unmodified and is the prerequisite reading for this
document). Full detail, raw data, and frozen protocols live in
`v3_refinement/` (`REFINEMENT_PLAN.md`, `INTEGRITY_DEFINITION.md`,
`PROTOCOL_V3.md`, `RESULTS_V3.md`) — this file is the short version.

## The question this phase asked

> What property of an interface intervention determines whether retargeting
> succeeds?

The working hypothesis going in was "distributed coverage of the true
interaction shell matters more than individual actuator strength,"
operationalized as `Gamma(A)` = fraction of the core with at least one
actuated neighbor. **This hypothesis, in its literal form, was not
confirmed** — and the refined answer the data actually support is more
interesting than the one that was proposed.

## 1. What predicts successful interface control

Fitting simple, interpretable models on 10,000 development-flock replicate
outcomes (`v3_refinement/data/success_model_fits.json`): plain coverage
`Gamma(A)` is the **weakest** of the structural predictors tested — even
slightly weaker than raw actuator count `f_A`. The strongest predictor is
**mean multiplicity** `mean_m` — the average number of actuated neighbors
each core bird has — because `Gamma` saturates almost immediately on this
lattice (most of the core acquires *some* actuated neighbor at low
budgets) while success keeps improving with added *redundant* support,
consistent with the model's own update rule pooling weighted, noisy
evidence across up to 8 neighbors per bird.

**Refined principle**: retargeting succeeds once enough of the core
receives *redundant* (not merely present) target-consistent input through
its true interaction interface — largely independent of which specific
shell IDs implement that support, but not independent of how many
*distinct, redundant* actuators reach each core bird.

## 2. How sparse the intervention can be

Reformulating the target as **double coverage** (`frac(I0 with m_i(A)>=2)
>= gamma`) and freezing the smallest `gamma` whose development-flock mean
success clears 0.8 gives `gamma=0.5` — a controller needing on average only
**54% of the shell** (vs. V2's blanket 75%), a genuine sparsification gain
from a better structural criterion rather than a better search.

This does **not** generalize perfectly. On 6 held-out flocks never touched
during threshold selection: mean success 0.844 (clears the pre-registered
bar) at 9.3 actuators on average, vs. 0.989 at 15.8 actuators for V2's
larger reference budget — and one held-out flock (seed 18) fails badly
(0.167) at the sparse criterion despite hitting its coverage target
exactly. **The sparsification is real but comes with a quantified
reliability cost on a minority of flocks**, not a free lunch.

A structural reason some flocks are much harder than others was found
along the way: the maximum achievable double-coverage, even forcing the
*entire* shell, ranges from 0.30 to 0.93 across development flocks and
tracks the shell-to-core size ratio almost exactly. The canonical seed-2
flock — independently the hardest flock across the entire V1/V2/V3 study —
has the smallest such ratio of all ten development flocks. Its difficulty
was never just "atypical"; it has a geometrically small shell relative to
its core.

## 3. What "integrity" now means

The original criterion (`C_{I0}(t)>=0.8` at *every* timestep of the control
window) is retained, unmodified, and reported in every table — but it is no
longer used as the sole word on whether control "worked," because it
cannot distinguish a group *changing its opinion* (which any real
retargeting must involve) from a group *losing its identity* (which it
should not). `v3_refinement/INTEGRITY_DEFINITION.md` develops this
distinction from first principles before any threshold was chosen.

The replacement, frozen only after examining baseline transition
statistics: temporary disagreement is allowed, but the same frozen core
must recover to `C_{I0}>=0.8` (the *same* numeric bar — the change is *when*
it is checked, not a weaker bar) and hold there for 3 consecutive steps,
within the 20-step control window. Under this criterion, ~99–100% of
propagation-based control episodes (both full-shell and the sparse V3
controller) satisfy transition-aware integrity, with a worst-case recovery
time of 17 of 20 steps — directly resolving the tension V2 found
unresolvable (`P(success & integrity)=0.000` under the old bar, on every
condition tested).

## 4. Does staged control improve the transition?

No. Comparing Pulse against Ramp-up, Sequential-sector-recruitment, and
Ramp-down at matched actuator *identity* on 4 development flocks: the depth
of the coherence dip (`mean_min_coherence`) is essentially schedule-
invariant (~0.50–0.58 regardless of schedule, on every flock tested).
What changes is total control effort — schedules that delay part of the
budget deliver strictly less forcing within the fixed window and succeed
less often as a direct result (catastrophically so on one flock: Ramp-up's
`p_success=0.00` where Pulse gets 0.90). **The coherence dip is intrinsic
to this state transition, not a scheduling artifact** — reported plainly,
per the task's own stopping rule, rather than forcing a "smoother is
better" conclusion the data do not support.

## 5. How predictive permeability changes with horizon

Extending the mechanism audit's one-step predictive-screening result to a
horizon sweep (`tau=1..6`, 4 development flocks): the dynamical shell
`B^D`'s excess predictive log-loss is indistinguishable from zero at
`tau=1` (confirming the exact one-step Markov-blanket property) and then
grows through `tau=2..5` as exterior information propagates `E -> B^D ->
I0` over multiple steps — conditioning on the shell's state at a single
initial time does not pin down its own future trajectory. The Fiedler
boundary `B^F` leaks *more* than `B^D` at **every horizon tested**, not
just at one step — extending "the spectral boundary is not the true
interaction interface" from a one-step to a longer-horizon,
information-theoretic result. This pattern was not uniform across all 4
flocks (2 of 4 showed it clearly; 2 stayed flat and noisy), reported
honestly as a possible limit of development-scale sampling rather than
smoothed into a stronger claim than the data support.

## 6. What the interactive demo shows

`interactive_demo/build/index.html` — a self-contained, single-file page
(data inlined, opens with no server) walking through emergence → identify
collective → compare boundaries → choose target → choose control method →
control → release, on real Python-simulator trajectories (never
reimplemented in JavaScript). It includes: 8 control methods on one
representative flock (near-median success under the frozen controller),
including the known-poor Fiedler-only and connected-patch comparators and
an explicitly-marked-inadmissible direct-core diagnostic; a dedicated
split-screen "Compare V1" view on the actual canonical seed-2 flock V1's
original exhaustive search ran on (V1's best pair vs. V3's frozen
controller, same starting state/target/horizon); an inspect mode where
clicking a core bird reveals which shell birds directly feed its update and
whether they are Fiedler-boundary members or selected actuators; live
metric sparklines (`H*`, `C_{I0}`, `Gamma`, `|A|`); and a provenance panel
on every scenario (seed, protocol hash, target heading, rule, success).
Built early and evolved alongside the science, per instruction — its data
schema was fixed once V1/V2 concepts were understood and did not need to
change as Parts 1–3's results landed.

## Remaining limitations

- **Held-out generalization is real but imperfect** (Section 2): the sparse
  criterion fails on a minority of flocks even where its coverage target is
  exactly met. A practitioner wanting V2-level reliability should use the
  more conservative `gamma=0.6` reference point, not the literal frozen
  optimum.
- **Predictive-permeability horizon growth was not uniform across flocks**
  (Section 5) — a development-scale Monte-Carlo budget (`N_MC=24`) may be
  too coarse to detect a real but smaller effect in every flock; this was
  not investigated further within this session's budget.
- **Static-lattice scope, unchanged from V1/V2**: birds still occupy fixed
  lattice positions; `B^D_t = B^D_0` within a single control episode. The
  literal moving-boundary extension `STAGE6_SYNTHESIS.md` calls for remains
  future work.
- **The multicover formulation is an aggregate criterion**: hitting a
  global coverage-fraction target does not guarantee every individual core
  bird is well-supported (Section 2's seed-4 case) — a per-bird worst-case
  guarantee, rather than a population-average one, is a natural next
  refinement.
- **The interactive demo has been validated for JS syntax correctness, data
  integrity, and manual code review, but not visually exercised in an
  actual browser** in this sandboxed environment (headless-browser
  dependencies were unavailable without a system-package install this
  session did not perform without asking first) — a human should open
  `interactive_demo/build/index.html` directly before presenting it.
- Sample sizes throughout (10 development flocks, 6 held-out, 20–30
  replicates/condition, 4 flocks for predictive permeability) remain
  development-scale, consistent with — and explicitly logged as such,
  matching — V1/V2's own transparency norm.
