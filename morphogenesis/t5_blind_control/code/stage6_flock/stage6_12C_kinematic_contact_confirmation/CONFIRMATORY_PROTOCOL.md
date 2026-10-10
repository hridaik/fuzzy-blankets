# Stage 6.12C — Confirmatory Protocol (frozen before results)

This document records the exact design executed by `code/run_confirmatory_612c.py`,
written before any confirmatory outcome was analyzed. See `README.md` for
the disclosed, user-approved scope reduction from the full task brief.

## Identity semantics (unchanged from Stage 6.12/6.12B)

`ForwardMaterialTrace611` (Jaccard≥0.30) is a material-association layer,
NOT ground truth. `split_flag`/`merge_flag` are advisory material-overlap
heuristics, never confirmed physical events — Stage 6.12C never labels
them "confirmed." Both `J_assoc` (`V * A_release_late`, permissive) and
`J_conservative` (`V_conservative * A_release_late`, strict — requires
zero split/merge flags and zero unresolved steps anywhere in the traced
rollout) are carried for every rollout. `J_conservative` is PRIMARY for
control claims; `J_assoc` is the sensitivity analysis.

## Frozen predictor

See `PREDICTOR_FREEZE.md`. `C_hat_kin(j) = ` `intervention_612b.kinematic_contact_scores`
with `R=mf.R` (physics-assisted variant only), `window=d=8` for the
primary/secondary arms.

## Primary design: K=1 exhaustive, d=8

For each of the 10 confirmatory states:
1. The frozen nearest-20 exterior pool (`pool20`, saved at world-sampling
   time) is the candidate set — all 20 candidate IDs are evaluated, no
   subsampling.
2. For every candidate j: force bird j toward the frozen `h_star` for
   exactly 8 real simulator steps, release, evaluate over the standard
   24-step release interval (`R_RELEASE=24`, unchanged from Stage
   6.12/6.12B) — 32 total simulated steps per rollout.
3. Recorded BEFORE any intervention is simulated, per candidate:
   - **A.** `C_hat_kin(j)`, the frozen kinematic score (window=8, R=mf.R).
   - **B.** static t0 distance (min torus distance from j to any t0 target
     member).
   - **C.** direct contact at t0 (`dist ≤ R` to any target member) —
     audit/structural quantity, NEVER used for candidate ranking/selection.
   - **D.** metadata: candidate heading (`z0[j]`), target heading
     (`h_star`), relative bearing (cardinal direction from j to target
     centroid), predicted relative motion (dot of candidate's heading unit
     vector with the bearing-to-target unit vector), pool rank by static
     distance.
4. Physics streams per state:
   - 4 SEARCH/diagnostic streams (`physics_seed = 13_000_000 + state_idx*1000 + r`,
     r=0..3).
   - 8 CONFIRMATORY evaluation streams (`physics_seed = 14_000_000 +
     state_idx*1000 + r`, r=0..7).
   - Matched no-control branches use the IDENTICAL physics_seed per stream
     (`run_no_control_full_b`), computed once per (state, stream) and
     reused across every candidate — CRN by construction (every candidate's
     no-control comparison at a given stream index shares one physical
     RNG draw, up to the point forcing diverges the trajectory).
5. Paired outcome: `ΔJ_conservative(j,r) = J_conservative_forced(j,r) -
   J_conservative_no_control(r)`, and `ΔJ_assoc(j,r)` analogously. Raw
   `A_release_late`, end-of-control/end-of-release alignment, material
   membership size, split/merge flags, `V`/`V_conservative`, event
   classification, and `mech_cumulative_contact_edges` (the realized
   direct-contact count during the forcing window under j's OWN forced
   trajectory — this is the forced-future contact oracle's raw ingredient,
   see `ORACLE_DECOMPOSITION.md`) are preserved for every rollout.
   Primary analysis does NOT condition on post-treatment identity
   survival — identity failure (V=0, lost_dead, unresolved) is part of the
   outcome, not filtered out.

### Primary estimand: L_pred

Candidates ranked per state by `C_hat_kin` ONLY (never by realized
outcome). Using ONLY the 8 confirmatory streams:

```
L_pred(state) = mean_confirm(ΔJ_conservative of top-C_hat_kin candidate)
                / median_j [ mean_confirm(ΔJ_conservative(j)) ]
```

Summarized across states: state-level values, median, mean,
state-clustered bootstrap interval, fraction of states with L_pred>0.
Candidate-rollouts are never pooled as if independent. Repeated as a
sensitivity analysis with `ΔJ_assoc`.

### Predictor-ranking analysis

Per state: Spearman ρ between `C_hat_kin(j)` and `mean_confirm ΔJ_conservative(j)`
across the 20 candidates. All 10 state-level ρ summarized (median, mean,
sign consistency) rather than pooled into one number. Top-quartile vs.
bottom-quartile predictor candidates; rank of the true best-effect
candidate under `C_hat_kin`; recall of the true top-3 effect candidates
within the predictor's top-3/top-5.

## Oracle decomposition

1. **Forced-future contact oracle**: `C_forced_actual(j,r) =
   mech_cumulative_contact_edges` from j's OWN forced d=8 rollout (already
   computed by `intervention_612.mechanism_diagnostics`, reused, not
   reimplemented — see `ORACLE_DECOMPOSITION.md`). `j_contact_oracle(r) =
   argmax_j C_forced_actual(j,r)`. NOT deployable.
2. **Outcome oracle**: `j_effect_oracle(r) = argmax_j ΔJ_conservative(j,r)`.
   Non-deployable, per-stream.
3. **Stable best-effect set**: `j_best_search = argmax_j mean_search
   ΔJ_conservative(j,r)` using ONLY the 4 SEARCH streams; frozen, then
   evaluated on the 8 CONFIRMATORY streams. Not deployable authority
   inference — a reproducibility check.

Compared on confirmatory data: random/median candidate; kinematic-top;
search-selected best; forced-future contact oracle; outcome oracle.

## K=2 secondary (reduced scope — see README.md)

Same 10 states. Per state, 26 pairs: the top pair by the frozen Stage
6.12B pair-aggregation rule (`sum` of individual `C_hat_kin` scores — for a
pure-sum rule with no interaction term, this is provably the pair formed
by the top-2 individually-scored candidates), 24 uniformly sampled random
pairs (design RNG, `seed = 16_000_000 + state_idx`, never a physics
stream), and 1 low-predicted-contact pair (bottom-2 individually-scored
candidates). Evaluated on 6 CONFIRMATORY streams (first 6 of the 8 used
for K=1, same physics seeds — legitimate CRN reuse). d=8 only. The pair
aggregation rule itself is not modified on confirmatory data.

## Duration safety sub-study (reduced scope — see README.md)

5 of the 10 states (predeclared: the first 5 by seed order,
`s612c_00`..`s612c_04`), K=1, d=8 vs. d=24, for the top-`C_hat_kin`
candidate and one matched random candidate (drawn from the remaining 19
pool candidates via a separate design RNG, `seed = 17_000_000 +
state_idx`). Identical initial states and paired physics streams (first 6
of the 8 confirmatory streams) for both durations. d=8 values are reused
directly from the K=1 primary run (same candidate, same stream, same
physics_seed) rather than resimulated — the d=24 arm is the only new
simulation this sub-study requires. Reports paired lost/dead probability,
conservative identity-failure rate, and paired ΔJ effect at both
durations — a direct paired comparison, not an inference from cross-stage
percentage comparisons.

## What is explicitly NOT repeated

No refresh-cadence/strategy grid (Stage 6.12B found no stable benefit and
the task brief explicitly excludes re-running it here). No re-tuning of
the predictor after seeing confirmatory states. No exclusion of a state
because a preliminary look showed a small or negative effect.
