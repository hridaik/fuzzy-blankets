# Stage 6.12 — Next Stage Recommendations

## Endpoint call (see `FINAL_STAGE612_FINDINGS.md` for the full reasoning)

Stage 6.12's evidence sits closest to **Endpoint C (little controllability)
shading into Endpoint B (weak, inconsistent generic susceptibility)** at
the tested budgets, states, and Monte Carlo precision — **not** Endpoint A
(a robust selective regime). The overall `G_sus` 90% CI includes zero; the
frozen-budget `G_sel` is small, sign-inconsistent, and includes one
development state where the development-selected set actively reversed on
held-out streams.

**This is a provisional call, not a closed one** — the Monte Carlo budget
here (3 sets × 2 streams/cell, 6 dev + 3 holdout states) is far below the
task brief's nominal design, disclosed throughout. The honest statement is:
*at the precision this session could afford, no selective-addressability
regime was demonstrated, and generic susceptibility itself was not cleanly
demonstrated either* — which is itself new information relative to Stage
6.11 (which only established that the *historical* actuator choice wasn't
special; Stage 6.12 asked whether ANY actuator choice in this class matters
and found, at this precision, that even the forcing class itself barely
moves the needle).

## Do NOT yet build the learned authority estimator

Per the task brief's own instruction (§21) and the result above: building
or tuning a learned authority/actuator-selection model on top of this
budget class is not justified by Stage 6.12's evidence. The prerequisite
question — "does a nontrivial actuator-selection problem exist here?" — has
not received a clear "yes."

## What IS worth carrying forward

1. **Re-run this exact pipeline at full Monte Carlo precision before
   concluding Endpoint C.** The K,d grid, state-sampling rule, and
   estimand definitions in this stage are ready to scale up unchanged;
   only `N_SETS`, `N_STREAMS`, `SEARCH_BUDGET`, and state counts need
   raising (see README.md's reduction table for exact multipliers). Given
   the near-zero effect sizes found here, the priority is more physics
   replicates per cell (variance reduction), not necessarily more states.
2. **`MECHANISM_ANALYSIS.md`'s contact/coverage finding is the strongest
   positive lead in this dataset**: successful rollouts (rare, 34/1296)
   have an order of magnitude more sustained actuator-target contact than
   unsuccessful ones, while `t0` distance alone barely discriminates. This
   argues that if a next-stage authority estimator is eventually built, it
   should be asked to predict SUSTAINED CONTACT PERSISTENCE over the
   forcing window (a dynamic, motion-aware quantity), not a static `t0`
   proximity/authority score — closer in spirit to
   `NEXT_CONTROLLER_SPEC_INPUTS.md`'s open items than to the withdrawn
   Stage 6.11 authority method.
3. **The weaker intervention class question (task brief Endpoint B's
   prescribed next step) deserves consideration in parallel with #1**: if
   full-precision Phase A confirms near-zero `G_sus` at every tested
   budget, the next scientifically honest move is not a bigger search over
   the SAME intervention class, but either a different (more localized,
   more sustained-contact-aware, or longer-horizon) intervention class, or
   an explicit acceptance that this simulator/regime is not currently a
   useful control benchmark at the Section O/P operating point.
4. **`SELECTIVITY_ANALYSIS.md`'s development→holdout reversal
   (`s612_05`)** is worth preserving as a standing methodological warning
   in this repository: it is a second, independent demonstration (after
   Stage 6.11's historical-actuator finding) that development-only
   "best-found" results in this system are not reliable without held-out
   confirmation — any future controller-evaluation protocol in this
   repository should treat that as settled practice, not a one-off caution.
5. **Target-size drift via frequent (34%) but mostly non-fatal splits**
   (`IDENTITY_AND_DISRUPTION.md`, `COLLATERAL_ANALYSIS.md`) means any
   future controller that uses target size as a re-qualification or
   stopping signal should be tested against this split rate explicitly,
   not assumed away.

## What a fresh agent picking this up next should NOT assume

- That "no selectivity was found" at K=4,d=8 generalizes to every budget —
  the full grid in `READINESS_MAP.md` shows no consistent pattern across
  budgets either, so this is a statement about the WHOLE tested grid at
  this precision, not a single cell.
- That the mechanism-analysis contact/coverage correlation is causal or
  validated — it is explicitly exploratory (S16/S21) and was never used to
  select actuator sets in this stage's primary pipeline.
- That `ForwardMaterialTrace611`'s split-flag semantics are validated as a
  physical-split detector — `CURRENT_RESEARCH_STATUS.md` already states no
  physical-split/merge threshold has been independently calibrated in this
  repository; that remains true after Stage 6.12.
