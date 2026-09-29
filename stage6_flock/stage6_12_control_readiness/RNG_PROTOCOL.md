# Stage 6.12 — RNG Protocol

## Two independent stream families

1. **Physics streams** — `np.random.default_rng(physics_seed)`, consumed
   ONLY inside `MovingFlock611.step`/`step_cached`. Drives simulation noise
   (action sampling given the policy posterior) and nothing else.
2. **Design streams** — `np.random.default_rng(design_seed)`, consumed ONLY
   by actuator-set sampling/search code (`sample_random_sets` in
   `run_phaseA_612.py`, `run_phaseBC_612.py`, `run_pool_sensitivity_612.py`).
   Never passed into `mf.step`, never read by any simulation code.

These two families never share a seed value or a generator instance
anywhere in this stage's code. This mirrors `causal_reconciliation_
step3_20260922/RNG_AND_CRN_AUDIT.md`'s established finding that
`forced_actions` alone does not change the physics stream's draw
count/order — Stage 6.12 goes further by never routing decision-making
(actuator selection) through the physics stream at all, since the PRIMARY
intervention semantics here are a fixed schedule (no online re-inference),
unlike the still-open "policy effect" estimand flagged as provisional in
`CURRENT_RESEARCH_STATUS.md`.

## CRN pairing

Within one physics replicate index `r` for a given state, the no-control
branch and every actuator-set branch use
`physics_seed = PHYSICS_SEED_BASE + state_idx*100 + r` — identical across
branches. Because `forced_actions` only overrides the forced birds' own
drawn action (never anyone else's `G_i` computation at that step — see
`intervention_api_611.py`'s documented one-step reachability argument,
quoted not re-derived here), non-forced birds' state at `t0+1` is
bit-identical between the no-control and forced branches for the same `r`.
Verified mechanically by `rng_crn_diagnostic_612.py` (3/3 checks pass,
`logs/rng_crn_diagnostic_612.log`).

## Seed base registry (all disjoint, by construction)

| Script | Physics seed base | Design seed base |
|---|---|---|
| `world_sampling_612.py` | `seed` (61200–61399) directly | n/a (no design RNG at sampling time) |
| `run_phaseA_612.py` | `6_000_000 + state_idx*100 + r` | `5_000_000 + state_idx` |
| `run_phaseBC_612.py` search | `7_000_000 + state_idx*100 + r` | `5_500_000 + state_idx` |
| `run_phaseBC_612.py` holdout | `8_000_000 + state_idx*100 + r` | `5_600_000 + state_idx` |
| `run_pool_sensitivity_612.py` | `9_000_000 + state_idx*100 + r` | `5_900_000 + state_idx (+500 for oracle pool)` |

No physics-seed range overlaps another script's physics-seed range; no
design-seed range overlaps another script's design-seed range; and no
physics base ever equals a design base. Holdout physics streams
(`8_000_000+...`) are never touched during Phase B search — a distinct
numeric range, not merely a distinct call site — so Phase C's confirmation
uses genuinely fresh physical randomness.

## What this protocol does NOT cover

The "policy effect" estimand (online re-inference during forcing, as
opposed to the fixed-schedule replay used throughout Stage 6.12) is out of
scope here, exactly as it remains provisional in `CURRENT_RESEARCH_STATUS.md`
— Stage 6.12's PRIMARY semantics never re-plan mid-rollout, so no
auxiliary decision-code RNG-stream-sharing question arises for the primary
results. This is a scope choice, not a finding that the question is closed.
