# Stage 6.12B — RNG Protocol

Inherits Stage 6.12's architecture (`stage6_12_control_readiness/
RNG_PROTOCOL.md`) unmodified: physics streams
(`np.random.default_rng(physics_seed)`) are consumed ONLY inside
`mf.step`; design/selection streams are always separate generators, never
sharing a seed value with a physics stream. Verified for Stage 6.12B's
NEW code path (the online refresh loop) by
`rng_crn_diagnostic_612b.py` — 3/3 checks pass
(`logs/rng_crn_diagnostic_612b.log`): determinism under a fixed
(physics_seed, design_rng-seed) pair; distinct actuator picks under a
different design_rng seed at fixed physics_seed; successful joint
no-control/forced execution from the same physics_seed.

## Seed base registry (all disjoint)

| Script | Physics seed base | Design seed base |
|---|---|---|
| `world_sampling_612b.py` | `seed` (62200–62399) directly | n/a |
| `run_fixed_set_exhaustive_612b.py` dev search | `10_000_000 + state_idx*1000 + r` | n/a (exhaustive, no sampling) |
| `run_fixed_set_exhaustive_612b.py` holdout | `11_000_000 + state_idx*1000 + r` | `12_000_000 + state_idx*100 + K*10 + d` (comparator sampling only) |
| `run_refreshed_access_612b.py` | `20_000_000 + state_idx*1000 + r` | `21_000_000 + state_idx*100000 + K*1000 + q*10 + r` (strategy='random' only) |
| `contact_predictor_analysis_612b.py` | reuses the dev-search physics_seed (`10_000_000 + ...`) for the paired no-control/oracle source — same stream, by design, for legitimate CRN pairing | n/a |

`oracle` and `kinematic`/`kinematic_radius_free`/`nearest` strategies in
`run_refreshed_access_612b.py` consume NO design RNG at all — actuator
selection is a deterministic function of (current state, no-control future
trajectory for oracle), never randomized, so there is nothing to seed
beyond the physics stream that produced that current/future state.

## What oracle strategies use as "future truth"

`oracle_future_contact_scores` and 6.12B-B's `strategy='oracle'` use the
PAIRED NO-CONTROL trajectory (same `physics_seed` as the forced rollout
being evaluated) as their information source — never the forced
trajectory's own realized future. This is a legitimate, reproducible
upper-bound construction (the no-control branch is CRN-identical to the
forced branch up to the point forcing first diverges the dynamics) and is
labelled AUDIT/UPPER-BOUND ONLY throughout — never presented as
deployable, per task brief S18.3/S22.D/S31.
