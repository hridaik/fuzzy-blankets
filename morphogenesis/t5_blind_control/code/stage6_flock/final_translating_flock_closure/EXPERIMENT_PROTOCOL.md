# Final Translating-Flock Closure — Experiment Protocol

This is the final bounded experimental pass on the translating-flock system
(Stage 6.x) before the research programme moves to morphogenesis. It
completes three compact closures using the SAME simulation campaign for
Closures A and B, plus a small separate Closure-C timing sub-study.

## Reused infrastructure (unmodified)

- Simulator: `MovingFlock611` (`R=0.9, v=0.28, cohesion=1.0, social=raw`),
  via `stage6_12_control_readiness/code/common_612.py::make_flock`.
- Detector: `detect_69.propose`.
- Identity: `ForwardMaterialTrace611`, frozen Jaccard≥0.30 rule.
- Exterior pool: `nearest_M_pool` (nearest-20, position-only).
- Fixed-schedule rollout, tracing, and outcome metrics:
  `intervention_612.simulate_branch/trace_target/outcome_metrics`,
  `intervention_612b.add_conservative` (J_assoc, J_conservative,
  V, V_conservative — unchanged definitions).
- World-qualification rule (`world_sampling_closure.py`, logic reproduced
  from `world_sampling_612c.py`).

## New code (this stage only)

- `code/live_edge_utils.py` — organizational class assignment from
  `MovingFlock.live_edges` (directed, FOV-gated: `src -> recv` means `src`
  is a live source of influence into `recv`'s next-heading computation,
  requiring `D<=R` AND `(r_src-r_recv)·heading_recv >= 0`). Also: per-step
  live-edge diagnostic persistence and the minimal temporal-reachability
  diagnostic.
- `code/interior_correction.py` — implements
  `stage6_12C_kinematic_contact_confirmation/stable_selectivity_analysis/
  INTERIOR_ACTUATION_METHOD_NOTE.md`'s `A_minus_j`/`J_minus_j` correction
  exactly as specified: for an interior/boundary actuator `j`, alignment is
  recomputed over `target_members(t) \ {j}` using the tracer's own
  per-frame membership sets (genuine identity-aware exclusion, not
  count arithmetic).
- `code/rollout_closure.py` — one rollout wrapper combining the above with
  the reused intervention primitives.
- `code/run_closureAB.py`, `code/run_closureC_timing.py` — campaign
  runners.
- `code/analysis_closure.py` — state-paired/state-clustered statistics.

## Common intervention settings

Singleton intervention, K=1. Forcing duration d=8. Release=24 real steps.
`DeltaJ = J_intervention - J_no_control`, CRN-paired via identical
`physics_seed` (same convention as Stage 6.12/6.12B/6.12C). Primary metric:
`DeltaJ_conservative`; `DeltaJ_assoc` reported alongside.

## RNG protocol (disjoint from every prior stage)

| Component | Physics seed base | Design seed base |
|---|---|---|
| `world_sampling_closure.py` | `seed` (64200–64799) directly | n/a |
| `run_closureAB.py` | `40_000_000 + state_idx*1000 + r` (r=0..3) | `41_000_000 + state_idx` |
| `run_closureC_timing.py` (onset advance) | `42_000_000 + state_idx*10000 + offset*100 + 999` | n/a (deterministic advance, not sampled) |
| `run_closureC_timing.py` (evaluation) | `42_000_000 + state_idx*10000 + offset*100 + r` (r=0..2) | `43_000_000 + state_idx*10 + onset_idx` |

Physics streams are consumed only inside `mf.step`; design streams
(actuator sampling) are separate `np.random.default_rng` instances, never
passed to `mf.step` — identical discipline to
`stage6_12_control_readiness/RNG_PROTOCOL.md`.

## Closure A/B design (same campaign)

8 fresh states. At t0, classes assigned from the exact `live_edges` call:
core_member, boundary_member (target members touching a live edge crossing
the boundary in either direction), live_exterior_parent (non-target birds
in the nearest-20 pool with ≥1 live edge INTO the target), and
near_exterior_non_parent (pool members with zero such edge). Up to 3
actuators sampled per available class per state via a fixed design RNG
(never outcome-dependent). 4 paired physics streams per actuator (spec's
full recommendation — the runtime benchmark did not require reduction to
3; see below). Interior actuators (core/boundary) get both the ordinary
`DeltaJ` and the `DeltaJ_minus_j`-corrected value; exterior actuators'
`DeltaJ_minus_j == DeltaJ` by construction (no forced bird is in the
denominator).

## Closure C design (first 4 states, separate small sub-study)

Onset offsets `{0, 4, 8, 12}` real steps along the UNFORCED trajectory. At
each onset: material target, live edges, and classes are all recomputed
fresh (not reused from t0). Two class policies (live_exterior_parent,
boundary_member), up to 2 actuators each, 3 physics streams. K=1, d=8,
release=24 held fixed throughout.

## Runtime benchmark and compute estimate

Single-rollout wall time (d=8, n_steps=32, N=400 birds, 1 core): **≈4.2s**
(measured directly, `intervention_612b.run_one_b`/`run_no_control_full_b`
on an existing Stage 6.12C state before this campaign started). At this
per-rollout cost:

- Closure A/B: 8 states × (≤12 actuators/state × 4 streams + 4 no-control
  streams) ≈ 272 rollouts ≈ 19 minutes single-threaded.
- Closure C: 4 states × 4 onsets × (≤4 actuators × 3 streams + 3
  no-control streams, computed even when no actuator is available at an
  onset) ≈ 240 rollouts ≈ 17 minutes single-threaded.
- Total ≈ 512 rollouts, well inside the "hundreds, not thousands" target
  and the 1–3 hour overall budget. Both campaigns were run in parallel (8
  CPU cores available) with no reduction needed — the "reduce stream depth
  if runtime is materially worse than expected" contingency in the task
  spec was NOT triggered; all disclosed constants above (4 streams for
  A/B, 3 for C, ≤3 actuators/class) are the ORIGINAL target values, not a
  fallback.

## Deliberate scope limits (unchanged from the task spec, not reintroduced later)

- No new actuator-feature search beyond the four organizational classes.
- No learned/adaptive controller anywhere in this stage.
- No expansion of state count, K, d, or duration grid after seeing results.
- No use of after-the-fact per-stream/per-actuator maxima as evidence of
  selectivity (the winner's-curse lesson from
  `stable_selectivity_analysis/` is carried forward structurally: every
  comparison in `analysis_closure.py` aggregates to one row per state
  before combining across states).
