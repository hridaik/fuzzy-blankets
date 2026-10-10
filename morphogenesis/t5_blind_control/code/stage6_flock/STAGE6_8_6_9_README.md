# Stages 6.8 and 6.9 — where to start

Two additive stages on top of `stage6_flock/`. **Nothing in Stages 6–6.7 is
modified, re-run or restated** — verified by `git status`: both stages add only
new files, and the frozen Stage 6 / 6.7 test suites (58 tests) still pass
unchanged.

## What each stage removed

| convenience in Stages 6–6.7 | removed by |
|---|---|
| the interaction graph is fixed and undirected | **6.8** — heading-dependent FOV makes it directed and time-varying |
| the causal estimator is the **exact** propagator | **6.8** — finite active probing, with real sampling error |
| the interior `I` is **supplied** | **6.8** — detected online from positions and headings |
| the collective is **stationary** | **6.9 — attempted; the feasibility gate FAILS at the specified interaction scale, so the stage stops before any steering experiment** |

## Reading order

1. `stage6_8_dynamic_interactions/PHASE_MAP.md` — the operating-point search,
   including the negative results at L1 and at `nn = 100`.
2. `stage6_8_dynamic_interactions/RESULTS_6_8.md` — the main Stage 6.8 result
   and the Stage 6.9 gate verdict.
3. `stage6_9_translating_collective/RESULTS_6_9.md` — the translating-identity
   pilot **and its gate failure**, including the specification error that
   produced an earlier, superseded positive result.
4. `stage6_9_translating_collective/figures/fig_6_9_G_gate_failure.png` — what
   fails, and how the phenomenon tracks interaction degree rather than the
   specification.
5. `stage6_9_translating_collective/figures/translating_identity.html` — the
   three-panel visualization; open it in a browser, no server needed. It now
   renders the specified model, and says on its face that the gate failed.
6. `STAGE6_8_6_9_SYNTHESIS.md` — the cross-stage synthesis.

Each stage's `PLAN.md` was written before its numbers existed, each
`PROTOCOL_*.md` records every threshold with its provenance, and each stage's
`logs/*_predeclared.txt` is a dated audit trail of what was declared when —
including every scan that failed, every threshold that was *not* moved, and
(in Stage 6.9's ADDENDUM 3) a retraction of a claim that the measurement
contradicted.

## The three results worth knowing

1. **Stage 6.7's "perfect causal recovery" was identifiability, not
   estimation.** It survives intact as identifiability (Jaccard = 1.000 on all
   23 candidates) and falls to recall 0.602 the moment the estimator is a finite
   probe. On the moving flock it falls further, to ~0.02 — the interface is
   resolvable in closed form but effectively unestimable by one-step probing at
   any feasible budget.
2. **On a fixed undirected graph this model family has no mesoscopic regime at
   all**, at any temperature, precision scale or lattice size tested, because
   `compute_G` never reads a bird's own heading. The FOV rule supplies the
   missing self-coupling.
3. **The translating-collective phenomenon is a property of connectivity, not
   of adding motion.** At the specified interaction degree (8.9, the Moore
   scale) the moving flock does not sustain a coherent translating group — the
   tracked set fragments into ~3.8 pieces and its organization does not persist
   (`R_F` 0.66). It appears only at ~3x that degree, where the dynamics are also
   locked hard enough that the *exact* causal interface collapses to one live
   channel of 47. You can have a trackable translating collective or an
   inferable causal interface; the parameter ranges do not overlap.

A fourth, methodological: **Stage 6.9's interaction radius was mis-specified by
~3x and the error survived a long way** before an anomaly — a near-empty causal
interface that the exact propagator reproduced — led back to it. The audit trail
records the wrong diagnosis and its retraction alongside the correction, rather
than presenting the corrected run as if it had been the plan.
