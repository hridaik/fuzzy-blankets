# Stage 6.12B — Experiment Spec and Compute Plan

## Frozen protocol

Identical simulator/detector/identity-tracker/primary-pool/RNG-separation
choices as Stage 6.12 (see that stage's `README.md`/`THEORY_AND_
ESTIMANDS.md`/`RNG_PROTOCOL.md`), reused unmodified via
`common_612b.py`/`intervention_612.py`. New for Stage 6.12B:

- `J_conservative`/`V_conservative`/`event_corrected` computed AT COMPUTE
  TIME for every rollout (`intervention_612b.add_conservative`) — closing
  the Phase-B/C data gap the Part I correction pass surfaced.
- `intervention_612b.kinematic_contact_scores`: deployable, no-future-truth
  predicted-contact score from current positions/headings + constant known
  speed `v` + torus geometry; physics-assisted (`R` given) and radius-free
  (`R=None`, mean predicted distance) variants.
- `intervention_612b.oracle_future_contact_scores`: AUDIT-ONLY score using
  a PAIRED no-control future trajectory (same `physics_seed`) as the
  source of "future truth" — never the intervention's own (forced)
  trajectory, and never presented as deployable.
- `refresh_612b.run_refresh_rollout`: interleaved simulate+trace+select
  loop for actuator sets that refresh every `q` steps, recomputing the
  exterior pool from the CURRENT state at each refresh.

## Compute benchmarking (measured before full launch, per task brief S27)

| Component | Measured cost | Basis |
|---|---|---|
| One simulator step | ~0.14s (dominated by `detect_69.propose`) | Stage 6.12 `logs/`, reconfirmed here |
| 6.12B-A: one fixed-set rollout | ~3.9-4.5s (28-32 steps: d=4 or d=8, +24 release) | 3-set truncated smoke test, `logs/` |
| 6.12B-A: one state, full K∈{1,2}×d∈{4,8} exhaustive (210×2 dev + 32 finalists×4×4 holdout) | ~39 min | measured directly (K1_d4/d8 + K2_d4/d8 cell timings in `logs/fixed_set_exhaustive_612b.log`) |
| 6.12B-B: one refresh rollout (48 steps, any q) | ~6.3-6.7s | smoke test, `logs/` |
| 6.12B-B: one state, full K∈{2,4}×q∈{24,8,4,2,1}×strategies (55 cells × 3 streams) | ~17-18 min | measured directly |

## Compute plan (frozen before the full run; not adjusted after seeing results)

- **6.12B-A**: exhaustive K=1 (20 sets) and K=2 (190 sets) coverage
  preserved in full, at both `d=4` and `d=8`, on **3 of the 5 sampled
  states** (2 development, 1 holdout) — chosen by state index order
  (`s612b_00`, `s612b_01`, `s612b_03`), not by any pilot outcome.
  `N_DEV_STREAMS=1`, `N_HOLDOUT_STREAMS=4` for an 8-set finalist pool per
  K,d cell (S_star, median-dev, worst-dev, 5 random comparators).
  Estimated: 3 × 39 min ≈ 2.0 hours.
- **6.12B-B**: full `K∈{2,4} × q∈{24,8,4,2,1} × {5-6 strategies}` grid
  preserved in full, on **all 5 sampled states**, `N_STREAMS=3`.
  Estimated: 5 × 17.5 min ≈ 1.5 hours.
- Both run as separate background batches (this machine has 8 cores;
  the two jobs were run concurrently without contention issues observed).
  No hidden reduction was applied after launch — if a job had run over
  budget, the response per S27 would have been to reduce stream depth
  further with explicit logging, never to silently drop exhaustive
  coverage or grid cells; this was not needed in practice (see
  `logs/*.log` for actual per-cell/per-state wall times).

## Contact-predictor validation design (S18/S19)

Uses the 6.12B-A exhaustive rollouts' own pre-registered mechanism/contact
fields (`intervention_612.mechanism_diagnostics`, always attached — cheap
post hoc analysis of an already-simulated trajectory) plus two NEW
pre-intervention predictors computed BEFORE each rollout is simulated:
static `t0` nearest-distance (already available), kinematic predicted
contact (`kinematic_contact_scores`, deployable), and oracle no-control
future contact (`oracle_future_contact_scores`, audit-only, computed from
a SEPARATE paired no-control rollout at the same physics_seed — never
from the forced rollout's own trajectory). Validated against paired
`DeltaJ_assoc`/`DeltaJ_conservative` via rank correlation, never a complex
learned model (per task brief S19/S31).
