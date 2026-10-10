# Stage 6.12C — Kinematic Contact Predictor Confirmation

**Entry point.** This stage runs the confirmatory experiment recommended
by `stage6_12B_contact_persistence/NEXT_STAGE_DECISION.md`: does the
already-defined, frozen, physics-assisted kinematic future-contact
predictor (`PREDICTOR_FREEZE.md`) prospectively identify exterior
actuators with larger causal effects on a materially tracked moving
flock, on a properly powered fresh state sample — and, if not, is that
because future contact itself isn't causally informative, or because the
deployable predictor estimates it poorly?

## Reading order

1. `PREDICTOR_FREEZE.md` — the frozen predictor, hashed and quoted before
   any confirmatory result existed.
2. `STATE_MANIFEST.md` — the 10 fresh confirmatory states.
3. `CONFIRMATORY_PROTOCOL.md` — the full frozen design (K=1 primary, K=2
   secondary, duration sub-study, oracle decomposition, seed registry).
4. `K1_EXHAUSTIVE_RESULTS.md`, `PREDICTOR_VALIDATION.md`,
   `ORACLE_DECOMPOSITION.md`, `INCREMENTAL_VALUE_ANALYSIS.md`,
   `K2_SECONDARY.md`, `DURATION_SAFETY.md`, `IDENTITY_AND_DISRUPTION.md`,
   `STATISTICAL_ANALYSIS.md` — the results, in the order the protocol
   produces them.
5. `FINAL_STAGE612C_FINDINGS.md` — the synthesis.
6. `NEXT_STAGE_DECISION.md` — the explicit Case A/B/C/D call.

## DISCLOSED SCOPE REDUCTION (approved by the user before this run)

The full task brief calls for `N_STATES=20` and a full-stream K=2
secondary arm. Measured per-step simulation cost (~0.13-0.14s/step,
confirmed again by this stage's own pilot: 4.32s/rollout at d=8,
6.38s/rollout at d=24) made that full design's estimated compute
infeasible in one session. The user approved this reduced, disclosed
design instead — stated plainly, not hidden in a footnote:

| Design element | Full brief | This run | Reduction |
|---|---|---|---|
| N_STATES (confirmatory) | 20 | **10** | 2× Stage 6.12B's n=5; still a real reduction from the brief |
| K=1 primary | 20 candidates × 12 streams (4 search + 8 confirm), all states | UNCHANGED — full 20×12 at all 10 states | none (core deliverable preserved in full) |
| K=2 secondary | full stream depth, ≥ brief's pair coverage | 26 pairs/state (top + 24 random + 1 low), **6** confirmatory streams (not 8) | stream-depth cut |
| Duration safety sub-study | 10 states, 8 streams | **5** states (predeclared subset), 6 paired streams | state-count + stream-depth cut |
| Everything else (statistical discipline, oracle decomposition, predictor-freeze discipline, claims discipline, visualization, deliverable list) | — | UNCHANGED, implemented in full at the above scale | — |

This table is the authoritative record of what was cut and why. See
`STATE_MANIFEST.md` for the actual N_STATES achieved (10/10 seeds tried
qualified — no state was excluded after being seen) and
`STATISTICAL_ANALYSIS.md` / `FINAL_STAGE612C_FINDINGS.md` for the
measured total runtime.

## Prior-data caveat (disclosed, does not drive confirmatory analysis)

In the existing 3-state Stage 6.12B exhaustive data, the specific
K=1,d=8 cell — the cell this new experiment treats as PRIMARY — showed
ρ≈-0.06 for the kinematic predictor, versus K1,d4 (ρ≈+0.78) and K2,d8
(ρ≈+0.43); Stage 6.12B's headline pooled ρ≈0.23-0.29 spans multiple K/d
cells, not this cell specifically. This caveat is stated here and in
`FINAL_STAGE612C_FINDINGS.md` regardless of which way this stage's own
K1,d8 confirmatory result goes — it is disclosed context, not something
this stage's own analysis was tuned to match or refute.

## Directory structure

```
code/       implementation (state sampling, exhaustive runner, oracle
            computation, analysis, viz) -- matches stage6_12B_contact_
            persistence/'s structure
data/       machine-readable candidate-level and per-rollout JSON
figures/    static PNGs
logs/       timing/run logs
```

## What this stage does NOT do

Repeat the 6.12B-B refresh-cadence/strategy grid (explicitly excluded by
the task brief — that grid was already run and found inconclusive).
Retune the predictor on confirmatory states. Build or tune a learned
contact-aware authority estimator (that decision is deferred to
`NEXT_STAGE_DECISION.md`, per the task brief's own instruction).
