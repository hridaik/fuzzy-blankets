# Stage 6.12 — Control Readiness and Selective Addressability in the Moving Flock

**Git commit at start of this stage**: `9ba830d0f8410b5e4bf071472bbd6b290fa714f9`
**Date**: 2026-09-22

## Scientific question

For a valid, materially tracked moving flock, under what states and
intervention budgets is the flock:

(a) **not demonstrably responsive**,
(b) **generically susceptible** to sustained exterior forcing (typical
random actuator sets help), or
(c) **selectively addressable** (WHICH exterior birds are actuated makes a
reproducible difference, beyond typical random forcing)?

Stage 6.11's final adjudication (`stage6_11_translating_torus/audit/
causal_reconciliation_step3_20260922/FINAL_STAGE611_ADJUDICATION.md`)
established that wherever sustained forcing has a detectable effect, the
*historical* authority-based actuator choice never demonstrably beats
duration/cardinality/cadence-matched random actuator sets. Stage 6.12 asks
the more general question directly, over a frozen budget grid and a fresh
sample of states, before any new authority estimator is designed. This is
**not** another audit of the Stage 6.11 result and **not** the final
repaired adaptive controller — see `NEXT_STAGE_RECOMMENDATIONS.md`.

## Frozen protocol summary

- **Identity**: `ForwardMaterialTrace611` (Jaccard ≥ 0.30), frozen and
  unmodified, imported from
  `stage6_11_translating_torus/audit/material_identity_step2_20260921/code/`.
- **Simulator**: `MovingFlock611` at the Section O/P primary operating point
  (`R=0.9, v=0.28, cohesion=1.0, social=raw`), unmodified, imported from
  `stage6_11_translating_torus/code/`.
- **Detector**: `detect_69.propose`, unmodified.
- **Primary actuator pool**: `blind_pool_611.nearest_M_pool(..., M=20)`
  (position-only nearest-20 exterior pool), unmodified.
- **Secondary/sensitivity pool**: `intervention_api_611.near_exterior`
  (true-R oracle pool), used only in `run_pool_sensitivity_612.py`.
- **Requested heading**: `h_star = ROT_CCW[bearing_to_cardinal(bulk_delta)]`,
  the exact historical convention quoted from
  `run_online_control_611.py`.
- **Intervention semantics**: fixed schedule — select `S ⊂ P_t0` once,
  force toward `h_star` for exactly `d` consecutive steps, release, observe
  24 more steps. No replanning. See `THEORY_AND_ESTIMANDS.md`.
- **K × d grid** (frozen before any result): `K ∈ {1,2,4,8}`,
  `d ∈ {1,2,4,8,16,24}` — 24 cells, preserved in full.
- **RNG**: dedicated physics-only streams (CRN-paired across no-control and
  every actuator set within a replicate), fully separated from the design
  RNG used to sample/search actuator sets. See `RNG_PROTOCOL.md`.

## Disclosed scale reduction

The task brief's nominal Monte Carlo budget (32 random sets × 8 physics
streams per state-budget cell, 24 development + 12 holdout states) is
computationally infeasible in this session: measured cost is ≈0.14s/step
(dominated by `detect_69.propose`), giving ≈644s for one state's full 24-cell
Phase-A sweep at even the reduced per-cell budget used here. Per the task
brief's own priority order (§13/§23: preserve the K,d grid and the state
sample first; reduce per-cell Monte Carlo only if still infeasible, with
explicit logging), this run uses:

| Quantity | Task-brief nominal | This run | Reduction |
|---|---|---|---|
| Development states | ≥24 | 6 | preserved state sampling structure, count reduced |
| Holdout states | ≥12 | 3 | " |
| K×d grid | 4×6=24 cells | 4×6=24 cells | **preserved in full** |
| Phase A random sets / cell | 32 | 3 | |
| Phase A physics streams / set | 8 | 2 | |
| Phase B (best-found) search budget | K-dependent, exhaustive at K≤2 | 15 sampled sets, one frozen budget (K=4,d=8) | |
| Phase C holdout streams | ≥24 | 5 | |

Every quantitative claim in this stage's deliverables is reported with its
exact sample size (state count, set count, stream count) so the reduced
precision is visible at the point of use, not just here.

## Commands (run from `code/`, `conda activate fuzzy-blankets`)

```
python3 world_sampling_612.py        # state manifest -> data/state_manifest_612.json
python3 rng_crn_diagnostic_612.py    # CRN pairing verification
python3 run_phaseA_612.py            # full K,d readiness grid -> data/phaseA_results_612.json
python3 run_phaseBC_612.py           # best-found search + holdout confirmation -> data/phaseBC_results_612.json
python3 run_pool_sensitivity_612.py  # primary vs oracle pool -> data/pool_sensitivity_612.json
python3 analysis_612.py              # aggregate stats -> data/analysis_summary_612.json
python3 viz_612.py                   # figures -> figures/
```

## Seed manifest

World-sampling seed range: **61200–61399** (fresh; never used by seeds
500–504, prior identity-validation worlds, prior audits, or this stage's own
development). Physics/design RNG seed bases are listed per-script and in
`RNG_PROTOCOL.md`. Exact per-state seeds are in
`data/state_manifest_612.json`.

## Deliverables

See `THEORY_AND_ESTIMANDS.md`, `STATE_SAMPLING.md`, `RNG_PROTOCOL.md`,
`READINESS_MAP.md`, `SELECTIVITY_ANALYSIS.md`, `IDENTITY_AND_DISRUPTION.md`,
`MECHANISM_ANALYSIS.md`, `PHYSICS_POOL_SENSITIVITY.md`,
`COLLATERAL_ANALYSIS.md`, `FINAL_STAGE612_FINDINGS.md`,
`NEXT_STAGE_RECOMMENDATIONS.md`, plus `data/*.json` (machine-readable) and
`figures/*.png`.

**Visualization note**: given the compute-budget constraints already
disclosed above, visualizations are static (matplotlib PNGs: per-state and
aggregate budget-map heatmaps, actuator-set distribution at the frozen
search budget, state-view scatterplots) rather than an interactive
artifact. State membership, pool, heading, and identity status are all
directly readable from `data/state_manifest_612.json` and
`data/phaseA_results_612.json` if an interactive view is wanted later.
